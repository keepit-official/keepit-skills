#!/usr/bin/env python3
"""
Keepit Security Incident Investigation Utilities

Helper functions for threat detection, incident analysis, and severity scoring
used in the Keepit Security Incident Investigator skill.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from collections import defaultdict, Counter
import re


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp to datetime object.

    Handles common ISO 8601 variants including trailing Z, +00:00 offsets,
    and optional microseconds.

    Args:
        timestamp: ISO 8601 formatted timestamp string.

    Returns:
        Timezone-aware datetime object in UTC.
    """
    if not timestamp:
        return datetime.min.replace(tzinfo=timezone.utc)

    cleaned = timestamp.strip()

    # Normalise 'Z' suffix to +00:00
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        # Fallback: strip microseconds beyond 6 digits
        cleaned = re.sub(r"(\.\d{6})\d+", r"\1", cleaned)
        dt = datetime.fromisoformat(cleaned)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_metadata(event: Dict[str, Any]) -> Dict[str, str]:
    """Extract and flatten metadata array from an audit log event.

    Keepit audit events store metadata as a list of ``{key, value}`` dicts.
    This function flattens them into a simple dictionary for easier access.

    Args:
        event: A single audit log event dictionary.

    Returns:
        Flat dictionary of metadata key/value pairs.
    """
    metadata: Dict[str, str] = {}
    raw = event.get("metadata") or event.get("metaData") or []

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                key = item.get("key", item.get("Key", ""))
                value = item.get("value", item.get("Value", ""))
                if key:
                    metadata[key] = str(value)
    elif isinstance(raw, dict):
        metadata = {k: str(v) for k, v in raw.items()}

    return metadata


# ---------------------------------------------------------------------------
# Timeline reconstruction
# ---------------------------------------------------------------------------

def reconstruct_incident_timeline(
    audit_events: List[Dict[str, Any]],
    jobs: List[Dict[str, Any]],
    health_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Chain related events into a unified, chronological incident timeline.

    Merges audit events, jobs, and health assessments into a single list
    sorted by timestamp. Each entry is annotated with its source type and
    a relevance tag derived from the event category.

    Args:
        audit_events: List of audit log event dicts.
        jobs: List of job history dicts.
        health_data: List of connector health/impact assessment dicts.

    Returns:
        Sorted list of timeline entry dicts, each containing:
            timestamp, source, event_type, actor, details, severity_hint, raw.
    """
    timeline: List[Dict[str, Any]] = []

    # --- Audit events ---
    for event in audit_events:
        ts = event.get("timestamp") or event.get("time") or ""
        category = event.get("category", "Unknown")
        result = event.get("result", "")
        token = event.get("tokenName", event.get("token", "unknown"))
        description = event.get("description", event.get("message", ""))

        severity_hint = "info"
        if category == "Authentication" and result == "Failure":
            severity_hint = "warning"
        elif category == "Authentication" and result == "Success":
            severity_hint = "info"
        elif category == "Configuration":
            severity_hint = "warning"

        timeline.append({
            "timestamp": ts,
            "parsed_time": parse_iso_timestamp(ts),
            "source": "audit",
            "event_type": category,
            "actor": token,
            "details": description or f"{category} — {result}",
            "result": result,
            "severity_hint": severity_hint,
            "raw": event,
        })

    # --- Jobs ---
    for job in jobs:
        ts = job.get("startTime") or job.get("start") or ""
        job_type = job.get("type", "Unknown")
        connector_name = job.get("connector_name", "Unknown")
        status = job.get("status", "")

        severity_hint = "info"
        if job_type in ("Export", "Restore", "ZipDownload"):
            severity_hint = "high"

        timeline.append({
            "timestamp": ts,
            "parsed_time": parse_iso_timestamp(ts),
            "source": "job",
            "event_type": job_type,
            "actor": connector_name,
            "details": f"{job_type} job — {status}",
            "result": status,
            "severity_hint": severity_hint,
            "raw": job,
        })

    # --- Health / impact data ---
    for entry in health_data:
        ts = entry.get("last_snapshot") or entry.get("timestamp") or ""
        assessment = entry.get("assessment", "unknown")
        connector = entry.get("connector", "Unknown")

        severity_hint = "info"
        if assessment == "compromised":
            severity_hint = "critical"
        elif assessment == "degraded":
            severity_hint = "warning"

        timeline.append({
            "timestamp": ts,
            "parsed_time": parse_iso_timestamp(ts),
            "source": "health",
            "event_type": "HealthAssessment",
            "actor": connector,
            "details": f"Connector assessment: {assessment}",
            "result": assessment,
            "severity_hint": severity_hint,
            "raw": entry,
        })

    # Sort chronologically
    timeline.sort(key=lambda e: e["parsed_time"])

    return timeline


# ---------------------------------------------------------------------------
# Authentication attack detection
# ---------------------------------------------------------------------------

def detect_auth_attack_pattern(
    audit_events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect authentication attack patterns in audit events.

    Groups authentication events by token and analyses failure/success
    sequences to identify credential compromise, brute force, and
    credential stuffing patterns.

    Args:
        audit_events: List of audit log event dicts.

    Returns:
        List of detected pattern dicts, each containing:
            token, pattern_type, failure_count, success_time,
            first_failure_time, window_seconds, confidence.
    """
    auth_events = [
        e for e in audit_events
        if e.get("category") == "Authentication"
    ]

    # Group by token
    by_token: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for event in auth_events:
        token = event.get("tokenName", event.get("token", "unknown"))
        by_token[token].append(event)

    findings: List[Dict[str, Any]] = []
    tokens_with_failures: List[str] = []

    for token, events in by_token.items():
        sorted_events = sorted(events, key=lambda e: parse_iso_timestamp(
            e.get("timestamp", e.get("time", ""))
        ))

        failure_streak: List[Dict[str, Any]] = []

        for event in sorted_events:
            result = event.get("result", "")
            event_time = parse_iso_timestamp(
                event.get("timestamp", event.get("time", ""))
            )

            if result == "Failure":
                failure_streak.append(event)
            elif result == "Success" and len(failure_streak) >= 3:
                first_failure_time = parse_iso_timestamp(
                    failure_streak[0].get("timestamp", failure_streak[0].get("time", ""))
                )
                window = (event_time - first_failure_time).total_seconds()

                # Classify pattern type
                if len(failure_streak) >= 10 and window <= 600:
                    pattern_type = "brute_force"
                    confidence = "high"
                elif len(failure_streak) >= 5 and window <= 600:
                    pattern_type = "brute_force"
                    confidence = "high"
                elif len(failure_streak) >= 3 and window <= 3600:
                    pattern_type = "credential_compromise"
                    confidence = "medium"
                else:
                    pattern_type = "credential_compromise"
                    confidence = "low"

                findings.append({
                    "token": token,
                    "pattern_type": pattern_type,
                    "failure_count": len(failure_streak),
                    "success_time": event.get("timestamp", event.get("time", "")),
                    "first_failure_time": failure_streak[0].get(
                        "timestamp", failure_streak[0].get("time", "")
                    ),
                    "window_seconds": window,
                    "confidence": confidence,
                })
                failure_streak = []
            else:
                # Reset on unrelated success or non-auth event
                if result == "Success":
                    failure_streak = []

        # Ongoing brute force (failures with no success yet)
        if len(failure_streak) >= 5:
            tokens_with_failures.append(token)
            first_time = parse_iso_timestamp(
                failure_streak[0].get("timestamp", failure_streak[0].get("time", ""))
            )
            last_time = parse_iso_timestamp(
                failure_streak[-1].get("timestamp", failure_streak[-1].get("time", ""))
            )
            window = (last_time - first_time).total_seconds()

            findings.append({
                "token": token,
                "pattern_type": "active_brute_force",
                "failure_count": len(failure_streak),
                "success_time": None,
                "first_failure_time": failure_streak[0].get(
                    "timestamp", failure_streak[0].get("time", "")
                ),
                "window_seconds": window,
                "confidence": "high" if len(failure_streak) >= 10 else "medium",
            })

    # Credential stuffing: failures across 3+ distinct tokens
    if len(tokens_with_failures) >= 3:
        findings.append({
            "token": ", ".join(tokens_with_failures),
            "pattern_type": "credential_stuffing",
            "failure_count": sum(
                1 for e in auth_events if e.get("result") == "Failure"
            ),
            "success_time": None,
            "first_failure_time": None,
            "window_seconds": None,
            "confidence": "medium",
        })

    return findings


# ---------------------------------------------------------------------------
# Data exfiltration detection
# ---------------------------------------------------------------------------

def detect_data_exfiltration_pattern(
    audit_events: List[Dict[str, Any]],
    jobs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect potential data exfiltration patterns.

    Correlates export, restore, and zip-download jobs with suspicious audit
    events such as unusual tokens, off-hours activity, or proximity to
    authentication anomalies.

    Args:
        audit_events: List of audit log event dicts.
        jobs: List of job history dicts.

    Returns:
        List of exfiltration indicator dicts, each containing:
            job, correlated_events, risk_factors, confidence.
    """
    HIGH_RISK_JOB_TYPES = {"Export", "Restore", "ZipDownload"}

    suspicious_jobs = [
        j for j in jobs if j.get("type") in HIGH_RISK_JOB_TYPES
    ]

    if not suspicious_jobs:
        return []

    # Build token failure map for correlation
    token_failures: Dict[str, int] = Counter()
    for event in audit_events:
        if event.get("category") == "Authentication" and event.get("result") == "Failure":
            token = event.get("tokenName", event.get("token", "unknown"))
            token_failures[token] += 1

    findings: List[Dict[str, Any]] = []

    for job in suspicious_jobs:
        job_time = parse_iso_timestamp(
            job.get("startTime", job.get("start", ""))
        )
        risk_factors: List[str] = []
        correlated_events: List[Dict[str, Any]] = []

        # Factor 1: Off-hours job execution
        if job_time.hour < 6 or job_time.hour >= 22:
            risk_factors.append("off_hours_execution")

        # Factor 2: Weekend execution
        if job_time.weekday() >= 5:
            risk_factors.append("weekend_execution")

        # Factor 3: Correlated with suspicious auth events (within 1 hour)
        for event in audit_events:
            event_time = parse_iso_timestamp(
                event.get("timestamp", event.get("time", ""))
            )
            delta = abs((job_time - event_time).total_seconds())
            if delta <= 3600:
                if event.get("category") == "Authentication" and event.get("result") == "Failure":
                    correlated_events.append(event)
                    risk_factors.append("auth_failure_correlation")

        # Factor 4: Token associated with high failure rate
        job_token = job.get("tokenName", job.get("token", ""))
        if job_token and token_failures.get(job_token, 0) >= 3:
            risk_factors.append("high_failure_token")

        # De-duplicate risk factors
        risk_factors = list(set(risk_factors))

        if risk_factors:
            confidence = "high" if len(risk_factors) >= 3 else (
                "medium" if len(risk_factors) >= 2 else "low"
            )
            findings.append({
                "job": {
                    "type": job.get("type"),
                    "startTime": job.get("startTime", job.get("start", "")),
                    "connector_name": job.get("connector_name", "Unknown"),
                    "connector_guid": job.get("connector_guid", ""),
                    "status": job.get("status", ""),
                },
                "correlated_events": correlated_events,
                "risk_factors": risk_factors,
                "confidence": confidence,
            })

    return findings


# ---------------------------------------------------------------------------
# Configuration tampering detection
# ---------------------------------------------------------------------------

def detect_config_tampering(
    audit_events: List[Dict[str, Any]],
    connectors: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Detect suspicious configuration changes in audit events.

    Looks for retention policy shortening, connector setting modifications,
    schedule changes, and configuration changes near suspicious auth events.

    Args:
        audit_events: List of audit log event dicts.
        connectors: List of connector dicts for context.

    Returns:
        List of tampering indicator dicts, each containing:
            event, change_type, risk_factors, affected_connector, confidence.
    """
    SENSITIVE_KEYWORDS = [
        "retention", "schedule", "delete", "disable", "remove",
        "policy", "configuration", "setting", "connector",
    ]

    config_events = [
        e for e in audit_events
        if e.get("category") == "Configuration"
    ]

    auth_failure_times: List[datetime] = []
    for event in audit_events:
        if event.get("category") == "Authentication" and event.get("result") == "Failure":
            auth_failure_times.append(
                parse_iso_timestamp(event.get("timestamp", event.get("time", "")))
            )

    # Build connector lookup
    connector_map: Dict[str, str] = {}
    for c in connectors:
        guid = c.get("guid", "")
        name = c.get("name", "Unknown")
        if guid:
            connector_map[guid] = name

    findings: List[Dict[str, Any]] = []

    for event in config_events:
        metadata = extract_metadata(event)
        description = event.get("description", event.get("message", "")).lower()
        event_time = parse_iso_timestamp(
            event.get("timestamp", event.get("time", ""))
        )

        risk_factors: List[str] = []
        change_type = "configuration_change"

        # Check for sensitive keyword matches
        combined_text = description + " " + " ".join(metadata.values()).lower()
        for keyword in SENSITIVE_KEYWORDS:
            if keyword in combined_text:
                risk_factors.append(f"sensitive_keyword:{keyword}")

        # Detect retention shortening
        if "retention" in combined_text:
            change_type = "retention_modification"
            risk_factors.append("retention_change")

        # Detect schedule modifications
        if "schedule" in combined_text:
            change_type = "schedule_modification"
            risk_factors.append("schedule_change")

        # Detect connector deletion or disabling
        if "delete" in combined_text or "disable" in combined_text or "remove" in combined_text:
            change_type = "destructive_change"
            risk_factors.append("destructive_operation")

        # Off-hours config change
        if event_time.hour < 6 or event_time.hour >= 22:
            risk_factors.append("off_hours_change")

        # Weekend config change
        if event_time.weekday() >= 5:
            risk_factors.append("weekend_change")

        # Proximity to auth failures (within 2 hours)
        for failure_time in auth_failure_times:
            if abs((event_time - failure_time).total_seconds()) <= 7200:
                risk_factors.append("near_auth_failure")
                break

        # Identify affected connector
        affected_connector = "Unknown"
        for guid, name in connector_map.items():
            if guid in combined_text or name.lower() in combined_text:
                affected_connector = name
                break

        # De-duplicate
        risk_factors = list(set(risk_factors))

        if risk_factors:
            confidence = "high" if len(risk_factors) >= 3 else (
                "medium" if len(risk_factors) >= 2 else "low"
            )
            findings.append({
                "event": {
                    "timestamp": event.get("timestamp", event.get("time", "")),
                    "description": event.get("description", event.get("message", "")),
                    "token": event.get("tokenName", event.get("token", "unknown")),
                    "category": event.get("category", ""),
                },
                "change_type": change_type,
                "risk_factors": risk_factors,
                "affected_connector": affected_connector,
                "confidence": confidence,
            })

    return findings


# ---------------------------------------------------------------------------
# Incident severity scoring
# ---------------------------------------------------------------------------

def score_incident_severity(findings: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate composite incident severity score.

    Scores range from 0 to 100 and map to severity levels. Points are
    awarded per finding type and multiplied by contextual factors.

    Args:
        findings: Aggregated findings dict with keys:
            auth_attacks, exfiltration_indicators, config_tampering,
            off_hours_anomalies, suspicious_tokens, affected_connectors.

    Returns:
        Dict with: severity, score, icon, factors, recommendations.
    """
    score = 0
    factors: List[str] = []
    recommendations: List[str] = []

    # --- Auth attack points ---
    auth_attacks = findings.get("auth_attacks", [])
    for attack in auth_attacks:
        pattern = attack.get("pattern_type", "")
        if pattern == "brute_force":
            score += 20
            factors.append("brute_force_detected")
        elif pattern == "active_brute_force":
            score += 25
            factors.append("active_brute_force")
        elif pattern == "credential_compromise":
            score += 30
            factors.append("credential_compromise")
        elif pattern == "credential_stuffing":
            score += 25
            factors.append("credential_stuffing")

    if auth_attacks:
        recommendations.append("Immediately revoke or rotate compromised API tokens")
        recommendations.append("Enable multi-factor authentication if available")

    # --- Exfiltration points ---
    exfil = findings.get("exfiltration_indicators", [])
    for indicator in exfil:
        confidence = indicator.get("confidence", "low")
        if confidence == "high":
            score += 40
        elif confidence == "medium":
            score += 25
        else:
            score += 10
        factors.append("data_exfiltration_indicator")

    if exfil:
        recommendations.append("Review export/restore job outputs for unauthorized data access")
        recommendations.append("Audit destination of exported data")

    # --- Config tampering points ---
    tampering = findings.get("config_tampering", [])
    for item in tampering:
        change_type = item.get("change_type", "")
        if change_type == "destructive_change":
            score += 30
        elif change_type == "retention_modification":
            score += 25
        else:
            score += 15
        factors.append(f"config_tampering:{change_type}")

    if tampering:
        recommendations.append("Review and revert unauthorized configuration changes")
        recommendations.append("Verify backup retention policies are intact")

    # --- Off-hours anomaly points ---
    off_hours = findings.get("off_hours_anomalies", [])
    if off_hours:
        score += min(15, len(off_hours) * 3)
        factors.append("off_hours_anomalies")

    # --- Suspicious token points ---
    sus_tokens = findings.get("suspicious_tokens", [])
    for token_info in sus_tokens:
        risk = token_info.get("risk_score", 0)
        score += min(20, risk)
        factors.append(f"suspicious_token:{token_info.get('token', 'unknown')}")

    if sus_tokens:
        recommendations.append("Investigate and consider revoking flagged API tokens")

    # --- Scope multiplier ---
    affected = findings.get("affected_connectors", [])
    compromised_count = sum(
        1 for c in affected if c.get("assessment") == "compromised"
    )
    if compromised_count > 0:
        score = int(score * 1.2)
        factors.append(f"compromised_connectors:{compromised_count}")
        recommendations.append("Verify backup integrity for compromised connectors")
        recommendations.append("Initiate backup recovery procedures if data loss confirmed")

    # --- Multi-pattern multiplier ---
    unique_pattern_types = set()
    for f in factors:
        unique_pattern_types.add(f.split(":")[0])
    if len(unique_pattern_types) >= 3:
        score = int(score * 1.3)
        factors.append("multi_pattern_correlation")

    # Cap at 100
    score = min(100, score)

    # De-duplicate factors
    factors = list(dict.fromkeys(factors))

    # Classify severity
    if score >= 80:
        severity = "critical"
        icon = "\u274c"  # red X
        recommendations.insert(0, "ACTIVATE INCIDENT RESPONSE — containment required immediately")
        recommendations.append("Notify security leadership and legal counsel")
    elif score >= 50:
        severity = "high"
        icon = "\U0001f534"  # red circle
        recommendations.insert(0, "Investigate immediately and escalate to security lead")
    elif score >= 20:
        severity = "medium"
        icon = "\U0001f7e1"  # yellow circle
        recommendations.insert(0, "Investigate within 24 hours")
    else:
        severity = "low"
        icon = "\U0001f7e2"  # green circle
        recommendations = ["Continue monitoring — no immediate action required"]

    # De-duplicate recommendations
    recommendations = list(dict.fromkeys(recommendations))

    return {
        "severity": severity,
        "score": score,
        "icon": icon,
        "factors": factors,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# Off-hours baseline and anomaly detection
# ---------------------------------------------------------------------------

def generate_off_hours_baseline(
    audit_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Establish normal activity hour distribution from historical events.

    Analyses the hourly distribution of events to determine business hours
    and typical activity patterns.

    Args:
        audit_events: List of audit log event dicts.

    Returns:
        Dict with: hourly_distribution, business_hours, peak_hour,
        avg_daily_events, weekend_activity_ratio.
    """
    hourly: Dict[int, int] = defaultdict(int)
    daily: Dict[str, int] = defaultdict(int)
    weekend_events = 0
    weekday_events = 0

    for event in audit_events:
        ts = event.get("timestamp", event.get("time", ""))
        if not ts:
            continue
        dt = parse_iso_timestamp(ts)
        hourly[dt.hour] += 1
        daily[dt.strftime("%Y-%m-%d")] += 1

        if dt.weekday() >= 5:
            weekend_events += 1
        else:
            weekday_events += 1

    # Determine business hours: contiguous block with highest activity
    if not hourly:
        return {
            "hourly_distribution": dict(hourly),
            "business_hours": (8, 18),
            "peak_hour": 12,
            "avg_daily_events": 0,
            "weekend_activity_ratio": 0.0,
        }

    # Find the 10-hour window with most activity
    best_start = 8
    best_count = 0
    for start in range(24):
        window_count = sum(hourly.get((start + h) % 24, 0) for h in range(10))
        if window_count > best_count:
            best_count = window_count
            best_start = start

    business_hours = (best_start, (best_start + 10) % 24)
    peak_hour = max(hourly, key=hourly.get) if hourly else 12

    total_events = sum(daily.values())
    num_days = max(len(daily), 1)
    avg_daily = total_events / num_days

    total_all = weekend_events + weekday_events
    weekend_ratio = weekend_events / total_all if total_all > 0 else 0.0

    return {
        "hourly_distribution": dict(hourly),
        "business_hours": business_hours,
        "peak_hour": peak_hour,
        "avg_daily_events": round(avg_daily, 1),
        "weekend_activity_ratio": round(weekend_ratio, 3),
    }


def detect_off_hours_anomalies(
    audit_events: List[Dict[str, Any]],
    baseline: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Flag events occurring outside established business hours.

    Compares each event's timestamp against the baseline business hours and
    assigns an anomaly score based on deviation from expected activity.

    Args:
        audit_events: List of audit log event dicts.
        baseline: Output from ``generate_off_hours_baseline``.

    Returns:
        List of anomaly dicts, each containing:
            event, hour, expected_activity_level, anomaly_score.
    """
    bh_start, bh_end = baseline.get("business_hours", (8, 18))
    hourly_dist = baseline.get("hourly_distribution", {})
    peak_activity = max(hourly_dist.values()) if hourly_dist else 1

    anomalies: List[Dict[str, Any]] = []

    for event in audit_events:
        ts = event.get("timestamp", event.get("time", ""))
        if not ts:
            continue
        dt = parse_iso_timestamp(ts)
        hour = dt.hour

        # Determine if hour is within business hours
        if bh_start < bh_end:
            is_business_hours = bh_start <= hour < bh_end
        else:
            # Wraps midnight
            is_business_hours = hour >= bh_start or hour < bh_end

        if is_business_hours:
            continue

        # Calculate anomaly score
        expected_activity = hourly_dist.get(hour, 0) / peak_activity if peak_activity else 0
        anomaly_score = round(1.0 - expected_activity, 2)

        # Weekend bonus
        if dt.weekday() >= 5:
            anomaly_score = min(1.0, anomaly_score + 0.2)

        anomalies.append({
            "event": {
                "timestamp": ts,
                "category": event.get("category", "Unknown"),
                "token": event.get("tokenName", event.get("token", "unknown")),
                "result": event.get("result", ""),
                "description": event.get("description", event.get("message", "")),
            },
            "hour": hour,
            "day_of_week": dt.strftime("%A"),
            "expected_activity_level": round(expected_activity, 3),
            "anomaly_score": anomaly_score,
        })

    # Sort by anomaly score descending
    anomalies.sort(key=lambda a: a["anomaly_score"], reverse=True)

    return anomalies


# ---------------------------------------------------------------------------
# Suspicious token identification
# ---------------------------------------------------------------------------

def identify_suspicious_tokens(
    audit_events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Identify tokens exhibiting suspicious activity patterns.

    Analyses each token for high failure rates, off-hours-only activity,
    access to sensitive operations, and multi-connector access patterns.

    Args:
        audit_events: List of audit log event dicts.

    Returns:
        List of suspicious token dicts, each containing:
            token, risk_score, risk_factors, event_count,
            failure_rate, sensitive_ops_count, active_hours.
    """
    token_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "total": 0,
        "failures": 0,
        "successes": 0,
        "hours": set(),
        "categories": Counter(),
        "connectors": set(),
        "first_seen": None,
        "last_seen": None,
    })

    SENSITIVE_CATEGORIES = {"Configuration", "Export", "Restore", "Administration"}

    for event in audit_events:
        token = event.get("tokenName", event.get("token", "unknown"))
        ts = event.get("timestamp", event.get("time", ""))
        dt = parse_iso_timestamp(ts)
        category = event.get("category", "Unknown")
        result = event.get("result", "")

        data = token_data[token]
        data["total"] += 1
        if result == "Failure":
            data["failures"] += 1
        elif result == "Success":
            data["successes"] += 1
        data["hours"].add(dt.hour)
        data["categories"][category] += 1

        # Track connectors accessed
        metadata = extract_metadata(event)
        connector_ref = metadata.get("connectorGuid", metadata.get("connector", ""))
        if connector_ref:
            data["connectors"].add(connector_ref)

        if data["first_seen"] is None or dt < data["first_seen"]:
            data["first_seen"] = dt
        if data["last_seen"] is None or dt > data["last_seen"]:
            data["last_seen"] = dt

    findings: List[Dict[str, Any]] = []

    for token, data in token_data.items():
        risk_score = 0
        risk_factors: List[str] = []

        # High failure rate
        if data["total"] > 0:
            failure_rate = data["failures"] / data["total"]
        else:
            failure_rate = 0.0

        if failure_rate > 0.5 and data["failures"] >= 3:
            risk_score += 20
            risk_factors.append("high_failure_rate")
        elif failure_rate > 0.2 and data["failures"] >= 3:
            risk_score += 10
            risk_factors.append("elevated_failure_rate")

        # Off-hours only activity
        business_hours = set(range(8, 18))
        active_hours = data["hours"]
        off_hours_only = active_hours and not active_hours.intersection(business_hours)
        if off_hours_only:
            risk_score += 20
            risk_factors.append("off_hours_only_activity")

        # Sensitive operations
        sensitive_count = sum(
            data["categories"].get(cat, 0) for cat in SENSITIVE_CATEGORIES
        )
        if sensitive_count >= 3:
            risk_score += 25
            risk_factors.append("frequent_sensitive_operations")
        elif sensitive_count >= 1:
            risk_score += 10
            risk_factors.append("sensitive_operations_access")

        # Multi-connector access
        if len(data["connectors"]) >= 3:
            risk_score += 10
            risk_factors.append("multi_connector_access")

        # New token (first seen within last 7 days)
        if data["first_seen"]:
            age = datetime.now(timezone.utc) - data["first_seen"]
            if age.days < 7:
                risk_score += 10
                risk_factors.append("recently_created_token")

        # Only report tokens with risk
        if risk_score >= 15:
            findings.append({
                "token": token,
                "risk_score": risk_score,
                "risk_factors": risk_factors,
                "event_count": data["total"],
                "failure_rate": round(failure_rate, 3),
                "sensitive_ops_count": sensitive_count,
                "active_hours": sorted(data["hours"]),
                "connectors_accessed": len(data["connectors"]),
                "first_seen": data["first_seen"].isoformat() if data["first_seen"] else None,
                "last_seen": data["last_seen"].isoformat() if data["last_seen"] else None,
            })

    # Sort by risk score descending
    findings.sort(key=lambda f: f["risk_score"], reverse=True)

    return findings


# ---------------------------------------------------------------------------
# IOC summary generation
# ---------------------------------------------------------------------------

def generate_ioc_summary(findings: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Indicator of Compromise summary from all findings.

    Aggregates IOCs from auth attacks, exfiltration indicators, config
    tampering, and suspicious tokens into a consolidated summary.

    Args:
        findings: Aggregated findings dict from all detectors.

    Returns:
        Dict with: suspicious_tokens, suspicious_time_windows,
        affected_connectors, ioc_count, summary_text.
    """
    suspicious_tokens: List[Dict[str, Any]] = []
    suspicious_time_windows: List[Dict[str, str]] = []
    affected_connectors: List[Dict[str, str]] = []

    # Tokens from auth attacks
    seen_tokens: set = set()
    for attack in findings.get("auth_attacks", []):
        token = attack.get("token", "")
        if token and token not in seen_tokens:
            seen_tokens.add(token)
            suspicious_tokens.append({
                "token": token,
                "reason": attack.get("pattern_type", "unknown"),
                "failure_count": attack.get("failure_count", 0),
            })

    # Tokens from suspicious token analysis
    for token_info in findings.get("suspicious_tokens", []):
        token = token_info.get("token", "")
        if token and token not in seen_tokens:
            seen_tokens.add(token)
            suspicious_tokens.append({
                "token": token,
                "reason": ", ".join(token_info.get("risk_factors", [])),
                "risk_score": token_info.get("risk_score", 0),
            })

    # Time windows from exfiltration indicators
    for indicator in findings.get("exfiltration_indicators", []):
        job = indicator.get("job", {})
        start_time = job.get("startTime", "")
        if start_time:
            dt = parse_iso_timestamp(start_time)
            window_start = (dt - timedelta(hours=1)).isoformat()
            window_end = (dt + timedelta(hours=1)).isoformat()
            suspicious_time_windows.append({
                "start": window_start,
                "end": window_end,
                "reason": f"{job.get('type', 'Unknown')} job with risk factors: "
                          f"{', '.join(indicator.get('risk_factors', []))}",
            })

    # Time windows from off-hours anomalies (cluster nearby anomalies)
    for anomaly in findings.get("off_hours_anomalies", [])[:10]:
        event = anomaly.get("event", {})
        ts = event.get("timestamp", "")
        if ts:
            suspicious_time_windows.append({
                "start": ts,
                "end": ts,
                "reason": f"Off-hours activity (score: {anomaly.get('anomaly_score', 0)})",
            })

    # Affected connectors
    seen_connectors: set = set()
    for indicator in findings.get("exfiltration_indicators", []):
        job = indicator.get("job", {})
        name = job.get("connector_name", "")
        guid = job.get("connector_guid", "")
        if guid and guid not in seen_connectors:
            seen_connectors.add(guid)
            affected_connectors.append({
                "name": name,
                "guid": guid,
                "reason": "exfiltration_target",
            })

    for entry in findings.get("affected_connectors", []):
        guid = entry.get("guid", "")
        if guid and guid not in seen_connectors:
            seen_connectors.add(guid)
            affected_connectors.append({
                "name": entry.get("connector", "Unknown"),
                "guid": guid,
                "reason": entry.get("assessment", "unknown"),
            })

    # Config tampering connectors
    for item in findings.get("config_tampering", []):
        connector_name = item.get("affected_connector", "")
        if connector_name and connector_name != "Unknown":
            affected_connectors.append({
                "name": connector_name,
                "guid": "",
                "reason": "config_tampering_target",
            })

    ioc_count = len(suspicious_tokens) + len(suspicious_time_windows) + len(affected_connectors)

    return {
        "suspicious_tokens": suspicious_tokens,
        "suspicious_time_windows": suspicious_time_windows,
        "affected_connectors": affected_connectors,
        "ioc_count": ioc_count,
        "summary_text": (
            f"Investigation identified {ioc_count} IOCs: "
            f"{len(suspicious_tokens)} suspicious token(s), "
            f"{len(suspicious_time_windows)} suspicious time window(s), "
            f"{len(affected_connectors)} affected connector(s)."
        ),
    }


# ---------------------------------------------------------------------------
# Self-test / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Keepit Security Incident Investigation Utilities — Self-Test")
    print("=" * 70)

    # Sample audit events
    sample_audit_events = [
        # Failed auth attempts
        {
            "timestamp": "2026-02-14T02:10:00Z",
            "category": "Authentication",
            "result": "Failure",
            "tokenName": "api-token-backup-svc",
            "description": "Authentication failed",
            "metadata": [{"key": "connectorGuid", "value": "abc-123"}],
        },
        {
            "timestamp": "2026-02-14T02:11:00Z",
            "category": "Authentication",
            "result": "Failure",
            "tokenName": "api-token-backup-svc",
            "description": "Authentication failed",
            "metadata": [{"key": "connectorGuid", "value": "abc-123"}],
        },
        {
            "timestamp": "2026-02-14T02:12:00Z",
            "category": "Authentication",
            "result": "Failure",
            "tokenName": "api-token-backup-svc",
            "description": "Authentication failed",
            "metadata": [{"key": "connectorGuid", "value": "abc-123"}],
        },
        # Successful auth after failures
        {
            "timestamp": "2026-02-14T02:14:00Z",
            "category": "Authentication",
            "result": "Success",
            "tokenName": "api-token-backup-svc",
            "description": "Authentication succeeded",
            "metadata": [{"key": "connectorGuid", "value": "abc-123"}],
        },
        # Normal business hours auth
        {
            "timestamp": "2026-02-14T10:00:00Z",
            "category": "Authentication",
            "result": "Success",
            "tokenName": "admin-token-primary",
            "description": "Authentication succeeded",
            "metadata": [],
        },
        {
            "timestamp": "2026-02-14T11:30:00Z",
            "category": "Authentication",
            "result": "Success",
            "tokenName": "admin-token-primary",
            "description": "Authentication succeeded",
            "metadata": [],
        },
        # Config change
        {
            "timestamp": "2026-02-15T23:45:00Z",
            "category": "Configuration",
            "result": "Success",
            "tokenName": "admin-token-legacy",
            "description": "Retention policy modified for Exchange connector",
            "metadata": [
                {"key": "connectorGuid", "value": "abc-123"},
                {"key": "setting", "value": "retention"},
            ],
        },
        # More normal activity
        {
            "timestamp": "2026-02-16T09:00:00Z",
            "category": "Authentication",
            "result": "Success",
            "tokenName": "admin-token-primary",
            "description": "Authentication succeeded",
            "metadata": [],
        },
        {
            "timestamp": "2026-02-16T14:00:00Z",
            "category": "Authentication",
            "result": "Success",
            "tokenName": "admin-token-primary",
            "description": "Authentication succeeded",
            "metadata": [],
        },
    ]

    # Sample jobs
    sample_jobs = [
        {
            "startTime": "2026-02-14T02:22:00Z",
            "type": "Export",
            "status": "Completed",
            "connector_name": "Exchange Online",
            "connector_guid": "abc-123",
            "tokenName": "api-token-backup-svc",
        },
        {
            "startTime": "2026-02-14T10:00:00Z",
            "type": "Backup",
            "status": "Completed",
            "connector_name": "SharePoint",
            "connector_guid": "def-456",
        },
    ]

    # Sample connectors
    sample_connectors = [
        {"guid": "abc-123", "name": "Exchange Online"},
        {"guid": "def-456", "name": "SharePoint"},
    ]

    # Sample health data
    sample_health = [
        {
            "connector": "Exchange Online",
            "guid": "abc-123",
            "health_status": "Healthy",
            "last_snapshot": "2026-02-16T06:00:00Z",
            "assessment": "intact",
        },
        {
            "connector": "SharePoint",
            "guid": "def-456",
            "health_status": "Warning",
            "last_snapshot": "2026-02-15T18:00:00Z",
            "assessment": "degraded",
        },
    ]

    # --- Test 1: Parse ISO timestamp ---
    print("\n--- Test 1: parse_iso_timestamp ---")
    ts = parse_iso_timestamp("2026-02-14T02:14:00Z")
    print(f"  Parsed: {ts} (tzinfo: {ts.tzinfo})")

    # --- Test 2: Extract metadata ---
    print("\n--- Test 2: extract_metadata ---")
    meta = extract_metadata(sample_audit_events[0])
    print(f"  Metadata: {meta}")

    # --- Test 3: Auth attack detection ---
    print("\n--- Test 3: detect_auth_attack_pattern ---")
    attacks = detect_auth_attack_pattern(sample_audit_events)
    for attack in attacks:
        print(f"  Pattern: {attack['pattern_type']} | Token: {attack['token']} "
              f"| Failures: {attack['failure_count']} | Confidence: {attack['confidence']}")

    # --- Test 4: Exfiltration detection ---
    print("\n--- Test 4: detect_data_exfiltration_pattern ---")
    exfil = detect_data_exfiltration_pattern(sample_audit_events, sample_jobs)
    for indicator in exfil:
        print(f"  Job: {indicator['job']['type']} on {indicator['job']['connector_name']} "
              f"| Risk factors: {indicator['risk_factors']} | Confidence: {indicator['confidence']}")

    # --- Test 5: Config tampering ---
    print("\n--- Test 5: detect_config_tampering ---")
    tampering = detect_config_tampering(sample_audit_events, sample_connectors)
    for item in tampering:
        print(f"  Change: {item['change_type']} | Token: {item['event']['token']} "
              f"| Factors: {item['risk_factors']} | Confidence: {item['confidence']}")

    # --- Test 6: Off-hours baseline ---
    print("\n--- Test 6: generate_off_hours_baseline ---")
    baseline = generate_off_hours_baseline(sample_audit_events)
    print(f"  Business hours: {baseline['business_hours']}")
    print(f"  Peak hour: {baseline['peak_hour']}")
    print(f"  Avg daily events: {baseline['avg_daily_events']}")

    # --- Test 7: Off-hours anomalies ---
    print("\n--- Test 7: detect_off_hours_anomalies ---")
    anomalies = detect_off_hours_anomalies(sample_audit_events, baseline)
    for anomaly in anomalies[:5]:
        print(f"  Hour: {anomaly['hour']} | Day: {anomaly['day_of_week']} "
              f"| Score: {anomaly['anomaly_score']} | Token: {anomaly['event']['token']}")

    # --- Test 8: Suspicious tokens ---
    print("\n--- Test 8: identify_suspicious_tokens ---")
    sus_tokens = identify_suspicious_tokens(sample_audit_events)
    for token_info in sus_tokens:
        print(f"  Token: {token_info['token']} | Risk: {token_info['risk_score']} "
              f"| Factors: {token_info['risk_factors']} | Failure rate: {token_info['failure_rate']}")

    # --- Test 9: Severity scoring ---
    print("\n--- Test 9: score_incident_severity ---")
    all_findings = {
        "auth_attacks": attacks,
        "exfiltration_indicators": exfil,
        "config_tampering": tampering,
        "off_hours_anomalies": anomalies,
        "suspicious_tokens": sus_tokens,
        "affected_connectors": sample_health,
    }
    severity = score_incident_severity(all_findings)
    print(f"  Severity: {severity['icon']} {severity['severity'].upper()} "
          f"(Score: {severity['score']}/100)")
    print(f"  Factors: {severity['factors']}")
    for rec in severity["recommendations"]:
        print(f"    - {rec}")

    # --- Test 10: IOC summary ---
    print("\n--- Test 10: generate_ioc_summary ---")
    iocs = generate_ioc_summary(all_findings)
    print(f"  {iocs['summary_text']}")
    for t in iocs["suspicious_tokens"]:
        print(f"    Token: {t['token']} — {t['reason']}")
    for c in iocs["affected_connectors"]:
        print(f"    Connector: {c['name']} ({c['guid']}) — {c['reason']}")

    # --- Test 11: Timeline reconstruction ---
    print("\n--- Test 11: reconstruct_incident_timeline ---")
    timeline = reconstruct_incident_timeline(sample_audit_events, sample_jobs, sample_health)
    print(f"  Timeline entries: {len(timeline)}")
    for entry in timeline[:8]:
        print(f"    {entry['timestamp'][:19]} | {entry['source']:6} | "
              f"{entry['event_type']:20} | {entry['actor']:25} | {entry['severity_hint']}")

    print("\n" + "=" * 70)
    print("All tests completed.")
    print("=" * 70)
