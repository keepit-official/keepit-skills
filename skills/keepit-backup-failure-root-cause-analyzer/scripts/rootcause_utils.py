#!/usr/bin/env python3
"""
Keepit Backup Failure Root Cause Analysis Utilities

Helper functions for failure investigation, error parsing, audit correlation,
and remediation guidance used in the Keepit Backup Failure Root Cause Analyzer skill.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from collections import defaultdict, Counter
import xml.etree.ElementTree as ET
import re


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime.

    Handles formats with and without microseconds, and with 'Z' or '+00:00'
    timezone designators.

    Args:
        timestamp: ISO 8601 formatted timestamp string.

    Returns:
        A timezone-aware datetime object in UTC.

    Raises:
        ValueError: If the timestamp cannot be parsed.
    """
    if not timestamp:
        raise ValueError("Empty timestamp string")

    # Normalise trailing 'Z' to '+00:00'
    ts = timestamp.strip()
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"

    # Try standard fromisoformat first (Python 3.7+)
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        # Fall back to strptime for edge-case formats
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ):
            try:
                dt = datetime.strptime(ts, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse timestamp: {timestamp}")

    # Ensure UTC if no timezone info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


# ---------------------------------------------------------------------------
# Execsummary XML parsing
# ---------------------------------------------------------------------------

def parse_execsummary(xml_string: Optional[str]) -> Dict[str, Any]:
    """Parse the execsummary XML field from a job record.

    Walks the XML tree looking for error, exit-reason, warning, and detail
    elements and returns them in a structured dictionary.

    Args:
        xml_string: Raw XML string from the job's execsummary field.
            May be None or empty.

    Returns:
        Dictionary with keys:
            errors (List[str]): Error messages found.
            exit_reason (Optional[str]): The exit/termination reason.
            warnings (List[str]): Warning messages found.
            details (Dict[str, str]): Additional key-value detail fields.
            raw_xml (Optional[str]): The original XML string.
            parse_error (Optional[str]): Error message if parsing failed.
    """
    result: Dict[str, Any] = {
        "errors": [],
        "exit_reason": None,
        "warnings": [],
        "details": {},
        "raw_xml": xml_string,
        "parse_error": None,
    }

    if not xml_string or not xml_string.strip():
        result["parse_error"] = "Empty or missing execsummary XML"
        return result

    try:
        root = ET.fromstring(xml_string.strip())
    except ET.ParseError as exc:
        result["parse_error"] = f"XML parse error: {exc}"
        return result

    # Walk every element in the tree
    for elem in root.iter():
        tag_lower = elem.tag.lower()
        text = (elem.text or "").strip()

        # Errors
        if "error" in tag_lower and text:
            result["errors"].append(text)
        # Exit / termination reason
        elif tag_lower in ("exit", "exitreason", "exit_reason", "exit-reason", "termination"):
            if text:
                result["exit_reason"] = text
        # Warnings
        elif "warn" in tag_lower and text:
            result["warnings"].append(text)
        # Everything else with text goes into details
        elif text and tag_lower not in ("execsummary", "summary", "root"):
            result["details"][elem.tag] = text

        # Also check attributes for error/exit/warning values
        for attr_name, attr_val in elem.attrib.items():
            attr_lower = attr_name.lower()
            if "error" in attr_lower and attr_val:
                result["errors"].append(attr_val)
            elif attr_lower in ("exit", "exitreason", "exit_reason", "exit-reason"):
                result["exit_reason"] = attr_val
            elif "warn" in attr_lower and attr_val:
                result["warnings"].append(attr_val)

    # Deduplicate while preserving order
    result["errors"] = list(dict.fromkeys(result["errors"]))
    result["warnings"] = list(dict.fromkeys(result["warnings"]))

    return result


# ---------------------------------------------------------------------------
# Audit log correlation
# ---------------------------------------------------------------------------

def correlate_failure_with_audit(
    failure_time: str,
    audit_events: List[Dict[str, Any]],
    window_hours: int = 24,
) -> Dict[str, Any]:
    """Find audit events within +/- window_hours of a failure timestamp.

    Classifies correlated events into config changes, auth events, and
    general categories.

    Args:
        failure_time: ISO 8601 timestamp of the backup failure.
        audit_events: List of audit event dicts (must contain a 'timestamp'
            or 'time' key).
        window_hours: Number of hours before and after the failure to
            search for correlated events. Defaults to 24.

    Returns:
        Dictionary with keys:
            events_before (List[Dict]): Events in the window before failure.
            events_after (List[Dict]): Events in the window after failure.
            config_changes (List[Dict]): Config-related events in window.
            auth_events (List[Dict]): Authentication-related events in window.
            total_correlated (int): Total number of correlated events.
            failure_time (str): The original failure timestamp.
            window_hours (int): The correlation window used.
    """
    result: Dict[str, Any] = {
        "events_before": [],
        "events_after": [],
        "config_changes": [],
        "auth_events": [],
        "total_correlated": 0,
        "failure_time": failure_time,
        "window_hours": window_hours,
    }

    try:
        fail_dt = parse_iso_timestamp(failure_time)
    except ValueError:
        return result

    window = timedelta(hours=window_hours)
    window_start = fail_dt - window
    window_end = fail_dt + window

    config_keywords = {
        "config", "configuration", "retention", "policy", "schedule",
        "update", "modify", "change", "edit", "setting",
    }
    auth_keywords = {
        "auth", "login", "logout", "token", "credential", "password",
        "permission", "access", "oauth", "reauthorize", "session",
    }

    for event in audit_events:
        # Extract timestamp from common field names
        event_time_str = (
            event.get("timestamp")
            or event.get("time")
            or event.get("created")
            or event.get("date")
        )
        if not event_time_str:
            continue

        try:
            event_dt = parse_iso_timestamp(str(event_time_str))
        except ValueError:
            continue

        if window_start <= event_dt <= window_end:
            event_copy = dict(event)
            event_copy["_parsed_time"] = event_dt.isoformat()

            # Before or after failure
            if event_dt <= fail_dt:
                result["events_before"].append(event_copy)
            else:
                result["events_after"].append(event_copy)

            # Classify the event
            event_text = " ".join(
                str(v).lower() for v in event.values() if isinstance(v, str)
            )

            if any(kw in event_text for kw in config_keywords):
                result["config_changes"].append(event_copy)

            if any(kw in event_text for kw in auth_keywords):
                result["auth_events"].append(event_copy)

    # Sort sublists by time
    for key in ("events_before", "events_after", "config_changes", "auth_events"):
        result[key].sort(key=lambda e: e.get("_parsed_time", ""))

    result["total_correlated"] = len(result["events_before"]) + len(result["events_after"])

    return result


# ---------------------------------------------------------------------------
# Failure type classification
# ---------------------------------------------------------------------------

_FAILURE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "auth_expired": {
        "patterns": [
            r"token.{0,20}expir",
            r"auth(?:entication|orization)?.{0,20}(?:fail|error|invalid|expir)",
            r"401\b",
            r"unauthorized",
            r"credentials?.{0,20}(?:invalid|expired|revoked)",
            r"oauth.{0,20}(?:error|fail|expir)",
            r"refresh.{0,10}token",
        ],
        "description": "Authentication credentials have expired or become invalid",
    },
    "config_change": {
        "patterns": [
            r"config(?:uration)?.{0,20}(?:error|invalid|missing|changed)",
            r"retention.{0,20}(?:error|conflict|invalid)",
            r"policy.{0,20}(?:violation|error|conflict)",
            r"setting.{0,20}(?:invalid|missing|changed)",
        ],
        "description": "A configuration change has caused the backup to fail",
    },
    "api_limit": {
        "patterns": [
            r"rate.{0,10}limit",
            r"429\b",
            r"too.{0,10}many.{0,10}requests",
            r"throttl",
            r"quota.{0,20}(?:exceed|limit|reached)",
            r"api.{0,20}limit",
        ],
        "description": "API rate limits or request quotas have been exceeded",
    },
    "connectivity": {
        "patterns": [
            r"timeout",
            r"connect(?:ion)?.{0,20}(?:refused|reset|failed|error|lost)",
            r"dns.{0,20}(?:error|fail|resolv)",
            r"network.{0,20}(?:error|unreachable)",
            r"socket.{0,20}(?:error|closed|timeout)",
            r"econnrefused",
            r"enotfound",
            r"ssl.{0,20}(?:error|handshake|cert)",
        ],
        "description": "Network connectivity issue prevented the backup from reaching the service",
    },
    "permission_denied": {
        "patterns": [
            r"403\b",
            r"forbidden",
            r"permission.{0,20}denied",
            r"access.{0,20}denied",
            r"insufficient.{0,20}(?:permission|privilege|access)",
            r"not.{0,10}authorized",
        ],
        "description": "The service account lacks required permissions",
    },
    "quota_exceeded": {
        "patterns": [
            r"storage.{0,20}(?:full|quota|limit|exceed)",
            r"disk.{0,20}(?:full|space|quota)",
            r"license.{0,20}(?:limit|exceed|expired)",
            r"capacity.{0,20}(?:exceed|limit|full)",
            r"no.{0,10}space",
        ],
        "description": "Storage or license quota has been exceeded",
    },
    "service_unavailable": {
        "patterns": [
            r"503\b",
            r"service.{0,20}unavailable",
            r"maintenance",
            r"temporarily.{0,20}unavailable",
            r"server.{0,20}(?:down|error|unavailable)",
            r"502\b",
            r"bad.{0,10}gateway",
        ],
        "description": "The target service is temporarily unavailable",
    },
}


def classify_failure_type(
    job: Dict[str, Any],
    execsummary_parsed: Dict[str, Any],
) -> Dict[str, Any]:
    """Classify a backup failure into a root cause category.

    Examines error messages, exit reasons, and job metadata to determine
    the most likely failure type.

    Args:
        job: The failed job record dictionary.
        execsummary_parsed: Parsed execsummary dict from parse_execsummary().

    Returns:
        Dictionary with keys:
            type (str): Failure category identifier.
            confidence (str): "high", "medium", or "low".
            indicators (List[str]): Evidence that led to this classification.
            description (str): Human-readable explanation.
    """
    # Build a searchable text corpus from all available data
    corpus_parts: List[str] = []
    corpus_parts.extend(execsummary_parsed.get("errors", []))
    if execsummary_parsed.get("exit_reason"):
        corpus_parts.append(execsummary_parsed["exit_reason"])
    corpus_parts.extend(execsummary_parsed.get("warnings", []))
    for val in execsummary_parsed.get("details", {}).values():
        corpus_parts.append(str(val))
    if job.get("description"):
        corpus_parts.append(str(job["description"]))

    corpus = " ".join(corpus_parts).lower()

    # Score each failure type
    scores: Dict[str, List[str]] = defaultdict(list)

    for failure_type, spec in _FAILURE_PATTERNS.items():
        for pattern in spec["patterns"]:
            matches = re.findall(pattern, corpus, re.IGNORECASE)
            if matches:
                scores[failure_type].append(pattern)

    if not scores:
        return {
            "type": "unknown",
            "confidence": "low",
            "indicators": ["No matching error patterns found in job data"],
            "description": "Unable to classify the failure from available data. "
                           "Manual investigation recommended.",
        }

    # Pick the type with the most pattern matches
    best_type = max(scores, key=lambda t: len(scores[t]))
    match_count = len(scores[best_type])

    # Confidence heuristic
    if match_count >= 3:
        confidence = "high"
    elif match_count == 2:
        confidence = "medium"
    else:
        confidence = "low"

    indicators = [
        f"Matched pattern: {p}" for p in scores[best_type][:5]
    ]

    # Add specific error messages as indicators
    for err in execsummary_parsed.get("errors", [])[:3]:
        indicators.append(f"Error message: {err[:120]}")

    return {
        "type": best_type,
        "confidence": confidence,
        "indicators": indicators,
        "description": _FAILURE_PATTERNS[best_type]["description"],
    }


# ---------------------------------------------------------------------------
# Config change causality detection
# ---------------------------------------------------------------------------

def detect_config_change_causality(
    failure_time: str,
    audit_events: List[Dict[str, Any]],
    connectors: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Determine whether configuration changes caused a backup failure.

    Checks both the audit log and connector-level retention_updated
    timestamps for changes preceding the failure.

    Args:
        failure_time: ISO 8601 timestamp of the backup failure.
        audit_events: List of audit event dicts.
        connectors: List of connector dicts from get_cloud_connectors(connectorType="cloud").

    Returns:
        Dictionary with keys:
            causal_likely (bool): Whether a config change likely caused failure.
            changes_found (List[Dict]): Relevant changes detected.
            time_delta (Optional[str]): Human-readable delta between change
                and failure.
            confidence (str): "high", "medium", or "low".
            description (str): Human-readable causality assessment.
    """
    result: Dict[str, Any] = {
        "causal_likely": False,
        "changes_found": [],
        "time_delta": None,
        "confidence": "low",
        "description": "No configuration changes detected near the failure time.",
    }

    try:
        fail_dt = parse_iso_timestamp(failure_time)
    except ValueError:
        result["description"] = "Could not parse failure timestamp for causality analysis."
        return result

    # --- Check audit events for config changes within 24h before failure ---
    config_keywords = {
        "config", "configuration", "retention", "policy", "schedule",
        "update", "modify", "change", "edit", "setting", "create", "delete",
    }
    candidate_changes: List[Tuple[datetime, Dict[str, Any]]] = []

    for event in audit_events:
        event_time_str = (
            event.get("timestamp")
            or event.get("time")
            or event.get("created")
            or event.get("date")
        )
        if not event_time_str:
            continue

        try:
            event_dt = parse_iso_timestamp(str(event_time_str))
        except ValueError:
            continue

        # Only look at events BEFORE the failure (up to 24h)
        delta = fail_dt - event_dt
        if timedelta(0) <= delta <= timedelta(hours=24):
            event_text = " ".join(
                str(v).lower() for v in event.values() if isinstance(v, str)
            )
            if any(kw in event_text for kw in config_keywords):
                candidate_changes.append((event_dt, event))

    # --- Check connector retention_updated fields ---
    for conn in connectors:
        retention_updated = conn.get("retention_updated") or conn.get("retentionUpdated")
        if not retention_updated:
            continue
        try:
            ret_dt = parse_iso_timestamp(str(retention_updated))
        except ValueError:
            continue

        delta = fail_dt - ret_dt
        if timedelta(0) <= delta <= timedelta(hours=24):
            candidate_changes.append((ret_dt, {
                "type": "retention_update",
                "connector": conn.get("name", conn.get("guid", "unknown")),
                "timestamp": str(retention_updated),
                "description": f"Retention policy updated on connector '{conn.get('name', 'unknown')}'",
            }))

    if not candidate_changes:
        return result

    # Sort by time, closest to failure first
    candidate_changes.sort(key=lambda x: x[0], reverse=True)

    closest_dt, closest_event = candidate_changes[0]
    delta = fail_dt - closest_dt
    delta_hours = delta.total_seconds() / 3600

    # Format time delta as human-readable string
    if delta_hours < 1:
        delta_str = f"{int(delta.total_seconds() / 60)} minutes"
    elif delta_hours < 24:
        delta_str = f"{delta_hours:.1f} hours"
    else:
        delta_str = f"{delta_hours / 24:.1f} days"

    # Determine confidence based on proximity
    if delta_hours <= 4:
        confidence = "high"
    elif delta_hours <= 12:
        confidence = "medium"
    else:
        confidence = "low"

    changes_found = []
    for change_dt, change_event in candidate_changes:
        change_delta = fail_dt - change_dt
        change_hours = change_delta.total_seconds() / 3600
        changes_found.append({
            "event": change_event,
            "time_before_failure": f"{change_hours:.1f}h",
            "timestamp": change_dt.isoformat(),
            "description": change_event.get("description", str(change_event.get("type", "config change"))),
        })

    result["causal_likely"] = confidence in ("high", "medium")
    result["changes_found"] = changes_found
    result["time_delta"] = delta_str
    result["confidence"] = confidence
    result["description"] = (
        f"Configuration change detected {delta_str} before the failure. "
        f"{len(changes_found)} change(s) found in the 24h window. "
        f"Confidence: {confidence}."
    )

    return result


# ---------------------------------------------------------------------------
# Data risk assessment
# ---------------------------------------------------------------------------

def assess_data_risk(
    latest_snapshot: Dict[str, Any],
    snapshot_range: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Assess the data risk from a backup gap since the last good snapshot.

    Calculates the duration of the backup gap and assigns a risk level
    based on how long data has been unprotected.

    Args:
        latest_snapshot: The most recent snapshot dict (from get_latest_snapshot).
            Expected to contain a 'timestamp', 'time', or 'created' field.
        snapshot_range: List of snapshot dicts (from get_snapshot_range) for
            trend analysis.

    Returns:
        Dictionary with keys:
            gap_hours (float): Hours since last good backup.
            gap_description (str): Human-readable gap description.
            risk_level (str): "low", "medium", "high", or "critical".
            last_good_backup (Optional[str]): Timestamp of last good backup.
            data_at_risk_description (str): Description of unprotected data.
            snapshot_count (int): Number of snapshots in the range.
            avg_interval_hours (Optional[float]): Average interval between snapshots.
    """
    result: Dict[str, Any] = {
        "gap_hours": 0.0,
        "gap_description": "Unknown",
        "risk_level": "unknown",
        "last_good_backup": None,
        "data_at_risk_description": "Unable to determine data risk.",
        "snapshot_count": len(snapshot_range) if snapshot_range else 0,
        "avg_interval_hours": None,
    }

    now = datetime.now(timezone.utc)

    # Determine last good backup time
    last_backup_str = None
    if latest_snapshot:
        last_backup_str = (
            latest_snapshot.get("timestamp")
            or latest_snapshot.get("time")
            or latest_snapshot.get("created")
            or latest_snapshot.get("date")
        )

    if not last_backup_str:
        result["gap_description"] = "No snapshot data available"
        result["risk_level"] = "critical"
        result["data_at_risk_description"] = (
            "No snapshot found. All data since connector creation may be unprotected."
        )
        return result

    try:
        last_backup_dt = parse_iso_timestamp(str(last_backup_str))
    except ValueError:
        result["gap_description"] = "Could not parse last snapshot timestamp"
        result["risk_level"] = "critical"
        return result

    result["last_good_backup"] = last_backup_dt.isoformat()

    # Calculate gap
    gap = now - last_backup_dt
    gap_hours = gap.total_seconds() / 3600
    result["gap_hours"] = round(gap_hours, 1)

    # Human-readable gap description
    if gap_hours < 1:
        result["gap_description"] = f"{int(gap.total_seconds() / 60)} minutes"
    elif gap_hours < 24:
        result["gap_description"] = f"{gap_hours:.1f} hours"
    elif gap_hours < 168:
        days = gap_hours / 24
        result["gap_description"] = f"{days:.1f} days ({gap_hours:.0f} hours)"
    else:
        weeks = gap_hours / 168
        result["gap_description"] = f"{weeks:.1f} weeks ({gap_hours:.0f} hours)"

    # Risk level thresholds
    if gap_hours < 24:
        result["risk_level"] = "low"
        result["data_at_risk_description"] = (
            f"Backup gap of {result['gap_description']}. "
            "Minimal data at risk, within normal backup window."
        )
    elif gap_hours < 72:
        result["risk_level"] = "medium"
        result["data_at_risk_description"] = (
            f"Backup gap of {result['gap_description']}. "
            "Data created or modified in this window is unprotected. "
            "Prioritize remediation to avoid further gap."
        )
    elif gap_hours < 168:
        result["risk_level"] = "high"
        result["data_at_risk_description"] = (
            f"Backup gap of {result['gap_description']}. "
            "Significant amount of data may be unprotected. "
            "Urgent remediation required. Notify stakeholders."
        )
    else:
        result["risk_level"] = "critical"
        result["data_at_risk_description"] = (
            f"Backup gap of {result['gap_description']}. "
            "Extended outage period. All data changes during this window "
            "are at risk. Immediate executive notification and emergency "
            "remediation required."
        )

    # Calculate average interval between snapshots
    if snapshot_range and len(snapshot_range) >= 2:
        snapshot_times: List[datetime] = []
        for snap in snapshot_range:
            snap_time_str = (
                snap.get("timestamp")
                or snap.get("time")
                or snap.get("created")
                or snap.get("date")
            )
            if snap_time_str:
                try:
                    snapshot_times.append(parse_iso_timestamp(str(snap_time_str)))
                except ValueError:
                    continue

        snapshot_times.sort()
        if len(snapshot_times) >= 2:
            intervals = [
                (snapshot_times[i + 1] - snapshot_times[i]).total_seconds() / 3600
                for i in range(len(snapshot_times) - 1)
            ]
            result["avg_interval_hours"] = round(
                sum(intervals) / len(intervals), 1
            )

    return result


# ---------------------------------------------------------------------------
# Recurrence classification
# ---------------------------------------------------------------------------

def classify_recurrence(
    job_history: List[Dict[str, Any]],
    current_failure: Dict[str, Any],
) -> Dict[str, Any]:
    """Classify whether a failure is first-time, recurring, or chronic.

    Examines job history for similar failures based on error message
    patterns and job descriptions.

    Args:
        job_history: Full list of job records (including successes).
        current_failure: The specific failed job being investigated.

    Returns:
        Dictionary with keys:
            classification (str): "first", "recurring", or "chronic".
            occurrence_count (int): Total similar failures found.
            first_seen (Optional[str]): Timestamp of first similar failure.
            pattern_description (str): Description of the failure pattern.
            similar_failures (List[Dict]): List of similar failure summaries.
    """
    result: Dict[str, Any] = {
        "classification": "first",
        "occurrence_count": 1,
        "first_seen": current_failure.get("failed"),
        "pattern_description": "First observed occurrence of this failure.",
        "similar_failures": [],
    }

    # Extract the current failure's signature
    current_desc = str(current_failure.get("description", "")).lower().strip()
    current_exec = str(current_failure.get("execsummary", "")).lower().strip()

    # Build search terms from the current failure
    search_terms: List[str] = []
    if current_desc:
        # Extract significant words (skip common terms)
        skip_words = {"the", "a", "an", "is", "was", "for", "of", "to", "in", "on", "at", "job", "backup"}
        words = [w for w in re.findall(r'\w+', current_desc) if w not in skip_words and len(w) > 2]
        search_terms.extend(words[:5])

    # Also look for error codes in execsummary
    error_codes = re.findall(r'\b[45]\d{2}\b', current_exec)
    search_terms.extend(error_codes)

    current_failed_time = current_failure.get("failed")

    # Search history for similar failures
    similar: List[Dict[str, Any]] = []

    for job in job_history:
        # Skip if not failed or if it's the same job
        if not job.get("failed"):
            continue
        if job.get("failed") == current_failed_time and job.get("description") == current_failure.get("description"):
            continue

        job_desc = str(job.get("description", "")).lower().strip()
        job_exec = str(job.get("execsummary", "")).lower().strip()
        combined_text = f"{job_desc} {job_exec}"

        # Calculate similarity score
        match_count = sum(1 for term in search_terms if term in combined_text)
        similarity = match_count / max(len(search_terms), 1)

        if similarity >= 0.4 or (current_desc and current_desc == job_desc):
            similar.append({
                "failed": job.get("failed"),
                "description": job.get("description", "N/A"),
                "similarity": round(similarity, 2),
            })

    if not similar:
        return result

    # Sort by failure time
    similar.sort(key=lambda s: s.get("failed", ""))

    total_occurrences = len(similar) + 1  # Include current failure

    result["occurrence_count"] = total_occurrences
    result["first_seen"] = similar[0].get("failed")
    result["similar_failures"] = similar[:10]  # Limit to 10 most relevant

    if total_occurrences >= 5:
        result["classification"] = "chronic"
        result["pattern_description"] = (
            f"Chronic failure pattern: {total_occurrences} similar failures detected. "
            f"First seen: {similar[0].get('failed', 'unknown')}. "
            "Systemic issue requiring escalation."
        )
    elif total_occurrences >= 2:
        result["classification"] = "recurring"
        result["pattern_description"] = (
            f"Recurring failure: {total_occurrences} similar failures detected. "
            f"First seen: {similar[0].get('failed', 'unknown')}. "
            "Pattern established, prioritize resolution."
        )

    return result


# ---------------------------------------------------------------------------
# Resolution step generation
# ---------------------------------------------------------------------------

_RESOLUTION_MAP: Dict[str, List[Dict[str, Any]]] = {
    "auth_expired": [
        {
            "number": 1,
            "action": "Re-authorize the connector",
            "detail": (
                "Navigate to the Keepit admin console, select the affected connector, "
                "and initiate re-authorization. This will refresh the OAuth tokens or "
                "service account credentials used for backup access."
            ),
            "priority": "critical",
        },
        {
            "number": 2,
            "action": "Verify credential validity",
            "detail": (
                "Confirm that the service account or user credentials are still valid "
                "in the source system (e.g., Microsoft 365 admin center, Google Admin). "
                "Check for password resets, MFA changes, or conditional access policies."
            ),
            "priority": "high",
        },
        {
            "number": 3,
            "action": "Trigger a manual backup",
            "detail": (
                "After re-authorization, run a manual backup job to verify that "
                "authentication is working correctly."
            ),
            "priority": "high",
        },
        {
            "number": 4,
            "action": "Set up token expiry monitoring",
            "detail": (
                "Configure alerts for upcoming token expirations to prevent "
                "future auth-related failures. Review token renewal schedule."
            ),
            "priority": "medium",
        },
    ],
    "config_change": [
        {
            "number": 1,
            "action": "Review recent configuration changes",
            "detail": (
                "Examine the audit log for configuration changes made in the "
                "24 hours before the failure. Identify which specific setting "
                "was modified and by whom."
            ),
            "priority": "critical",
        },
        {
            "number": 2,
            "action": "Revert the change if appropriate",
            "detail": (
                "If the configuration change is confirmed as the cause, revert "
                "to the previous setting. Document the change and the revert "
                "for the change management record."
            ),
            "priority": "high",
        },
        {
            "number": 3,
            "action": "Test with corrected configuration",
            "detail": (
                "Run a manual backup with the corrected configuration to confirm "
                "the issue is resolved."
            ),
            "priority": "high",
        },
        {
            "number": 4,
            "action": "Implement change control process",
            "detail": (
                "Establish or reinforce a change management process that requires "
                "review and approval before modifying backup configurations."
            ),
            "priority": "medium",
        },
    ],
    "api_limit": [
        {
            "number": 1,
            "action": "Adjust backup schedule",
            "detail": (
                "Stagger backup jobs to avoid hitting API rate limits. Space out "
                "connector backup windows so they do not all run simultaneously."
            ),
            "priority": "high",
        },
        {
            "number": 2,
            "action": "Review concurrent job count",
            "detail": (
                "Reduce the number of parallel backup operations if the source "
                "service enforces strict rate limiting. Consider sequential "
                "scheduling for rate-limited services."
            ),
            "priority": "high",
        },
        {
            "number": 3,
            "action": "Check vendor rate limit documentation",
            "detail": (
                "Review the source service's API rate limit documentation to "
                "understand current limits and plan backup schedules accordingly."
            ),
            "priority": "medium",
        },
        {
            "number": 4,
            "action": "Contact vendor for limit increase",
            "detail": (
                "If backup volume legitimately requires higher throughput, contact "
                "the source service vendor to request a rate limit increase."
            ),
            "priority": "low",
        },
    ],
    "connectivity": [
        {
            "number": 1,
            "action": "Verify network connectivity",
            "detail": (
                "Check that the Keepit service can reach the target endpoint. "
                "Verify DNS resolution, firewall rules, and proxy settings."
            ),
            "priority": "critical",
        },
        {
            "number": 2,
            "action": "Check source service status",
            "detail": (
                "Verify that the source service is operational by checking its "
                "status page (e.g., status.microsoft.com, status.google.com)."
            ),
            "priority": "high",
        },
        {
            "number": 3,
            "action": "Review firewall and proxy rules",
            "detail": (
                "Confirm that no recent firewall or proxy changes are blocking "
                "the connection. Check for IP allowlist changes or SSL inspection "
                "issues."
            ),
            "priority": "high",
        },
        {
            "number": 4,
            "action": "Retry the backup",
            "detail": (
                "If the connectivity issue was transient, trigger a manual backup "
                "to verify connectivity is restored."
            ),
            "priority": "medium",
        },
    ],
    "permission_denied": [
        {
            "number": 1,
            "action": "Review service account permissions",
            "detail": (
                "Verify that the service account used by the Keepit connector "
                "still has the required permissions in the source system. Check "
                "for recent role or permission changes."
            ),
            "priority": "critical",
        },
        {
            "number": 2,
            "action": "Re-grant required permissions",
            "detail": (
                "If permissions were revoked, re-grant the necessary access. "
                "Refer to Keepit documentation for the minimum required permission set."
            ),
            "priority": "high",
        },
        {
            "number": 3,
            "action": "Test with manual backup",
            "detail": (
                "After updating permissions, trigger a manual backup to confirm "
                "the access issue is resolved."
            ),
            "priority": "high",
        },
    ],
    "quota_exceeded": [
        {
            "number": 1,
            "action": "Check storage quota usage",
            "detail": (
                "Review current storage consumption in the Keepit account. "
                "Identify which connectors are consuming the most space."
            ),
            "priority": "critical",
        },
        {
            "number": 2,
            "action": "Free up storage or increase quota",
            "detail": (
                "Remove unnecessary snapshots or old data to free space, or "
                "contact Keepit to increase your storage allocation."
            ),
            "priority": "high",
        },
        {
            "number": 3,
            "action": "Review retention policies",
            "detail": (
                "Optimize retention policies to avoid unnecessary storage "
                "consumption. Consider reducing retention periods for "
                "non-critical data."
            ),
            "priority": "medium",
        },
    ],
    "service_unavailable": [
        {
            "number": 1,
            "action": "Check source service status page",
            "detail": (
                "Verify whether the source service is experiencing an outage "
                "by checking its official status page."
            ),
            "priority": "high",
        },
        {
            "number": 2,
            "action": "Wait and retry",
            "detail": (
                "If the service is undergoing maintenance or experiencing a "
                "temporary outage, wait for it to recover and then retry "
                "the backup."
            ),
            "priority": "medium",
        },
        {
            "number": 3,
            "action": "Set up service health monitoring",
            "detail": (
                "Subscribe to the source service's status notifications to "
                "receive advance warning of planned maintenance windows."
            ),
            "priority": "low",
        },
    ],
    "unknown": [
        {
            "number": 1,
            "action": "Collect full diagnostic data",
            "detail": (
                "Gather the complete job record, execsummary, connector health "
                "status, and audit logs for the affected time window."
            ),
            "priority": "high",
        },
        {
            "number": 2,
            "action": "Check connector health",
            "detail": (
                "Verify the connector's current health status. If unhealthy, "
                "try re-authorizing or reconfiguring the connector."
            ),
            "priority": "high",
        },
        {
            "number": 3,
            "action": "Escalate to Keepit support",
            "detail": (
                "If the root cause cannot be determined from available data, "
                "open a support ticket with Keepit. Include the diagnostic data "
                "collected in Step 1."
            ),
            "priority": "medium",
        },
    ],
}


def generate_resolution_steps(
    failure_type: str,
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate type-specific remediation steps for a classified failure.

    Provides ordered, prioritized resolution guidance tailored to the
    root cause category.

    Args:
        failure_type: The classified failure type string (e.g., "auth_expired").
        context: Contextual information including connector details, health
            status, execsummary, causality analysis, recurrence data, and
            risk assessment.

    Returns:
        List of step dicts, each with keys: number, action, detail, priority.
    """
    steps = _RESOLUTION_MAP.get(failure_type, _RESOLUTION_MAP["unknown"])

    # Deep copy to avoid mutating the template
    steps = [dict(s) for s in steps]

    # Enrich steps with contextual details
    connector_name = "the affected connector"
    if context.get("connector"):
        connector_name = context["connector"].get("name", connector_name)

    for step in steps:
        step["detail"] = step["detail"].replace("the affected connector", connector_name)
        step["detail"] = step["detail"].replace("the Keepit connector", f"the '{connector_name}' connector")

    # Add recurrence-specific step if chronic
    recurrence = context.get("recurrence", {})
    if recurrence.get("classification") == "chronic":
        steps.append({
            "number": len(steps) + 1,
            "action": "Escalate chronic failure pattern",
            "detail": (
                f"This failure has occurred {recurrence.get('occurrence_count', 'multiple')} "
                f"times (first seen: {recurrence.get('first_seen', 'unknown')}). "
                "Open an escalation ticket and schedule a dedicated investigation session."
            ),
            "priority": "critical",
        })

    # Add risk-specific step if data risk is high
    risk = context.get("risk", {})
    if risk.get("risk_level") in ("high", "critical"):
        steps.insert(0, {
            "number": 0,
            "action": "Address data risk immediately",
            "detail": (
                f"Backup gap: {risk.get('gap_description', 'significant')}. "
                f"Risk level: {risk.get('risk_level', 'high')}. "
                "Notify data protection stakeholders and prioritize restoring "
                "backup operations before further data is lost."
            ),
            "priority": "critical",
        })
        # Re-number steps
        for i, step in enumerate(steps):
            step["number"] = i + 1

    return steps


# ---------------------------------------------------------------------------
# Verification checklist generation
# ---------------------------------------------------------------------------

_VERIFICATION_CHECKLISTS: Dict[str, List[Dict[str, str]]] = {
    "auth_expired": [
        {
            "check": "Connector re-authorization successful",
            "how_to_verify": "Check connector status in Keepit admin console shows 'Authorized' or 'Connected'",
            "expected_result": "Connector status is healthy with valid credentials",
        },
        {
            "check": "Manual backup completes successfully",
            "how_to_verify": "Trigger a manual backup and monitor job status until completion",
            "expected_result": "Job completes without auth errors; no 'failed' timestamp",
        },
        {
            "check": "Next scheduled backup succeeds",
            "how_to_verify": "Wait for the next scheduled backup window and check job history",
            "expected_result": "Scheduled backup completes successfully",
        },
        {
            "check": "Token expiry alert configured",
            "how_to_verify": "Verify monitoring/alert configuration for credential expiration",
            "expected_result": "Alert rules exist and will fire before next token expiry",
        },
    ],
    "config_change": [
        {
            "check": "Configuration reverted or corrected",
            "how_to_verify": "Compare current config against last known good configuration",
            "expected_result": "Configuration matches the desired state",
        },
        {
            "check": "Manual backup completes successfully",
            "how_to_verify": "Trigger a manual backup and monitor to completion",
            "expected_result": "Job completes without configuration errors",
        },
        {
            "check": "Audit log confirms the change",
            "how_to_verify": "Review audit log for the corrective config change entry",
            "expected_result": "Audit log shows revert/correction with appropriate timestamp",
        },
    ],
    "api_limit": [
        {
            "check": "Backup schedule adjusted",
            "how_to_verify": "Review the backup schedule for staggered timing",
            "expected_result": "Jobs are spread across different time windows",
        },
        {
            "check": "Backup completes without rate limit errors",
            "how_to_verify": "Run a backup during off-peak hours and check for 429 errors",
            "expected_result": "Job completes successfully without throttling",
        },
        {
            "check": "Sustained success over 48 hours",
            "how_to_verify": "Monitor job history for 48 hours after schedule change",
            "expected_result": "No rate limit failures in the monitoring window",
        },
    ],
    "connectivity": [
        {
            "check": "Network connectivity restored",
            "how_to_verify": "Verify the connector can reach the source service endpoint",
            "expected_result": "Connection succeeds without timeout or DNS errors",
        },
        {
            "check": "Manual backup completes successfully",
            "how_to_verify": "Trigger a manual backup and monitor to completion",
            "expected_result": "Job completes without connectivity errors",
        },
        {
            "check": "Connector health shows healthy",
            "how_to_verify": "Check connector health status in Keepit admin console",
            "expected_result": "Health status is 'healthy' or 'connected'",
        },
    ],
    "permission_denied": [
        {
            "check": "Service account permissions verified",
            "how_to_verify": "Confirm permissions in the source system's admin console",
            "expected_result": "All required permissions are granted to the service account",
        },
        {
            "check": "Manual backup completes successfully",
            "how_to_verify": "Trigger a manual backup and monitor to completion",
            "expected_result": "Job completes without permission errors",
        },
    ],
    "quota_exceeded": [
        {
            "check": "Storage quota sufficient",
            "how_to_verify": "Check storage usage in Keepit admin console",
            "expected_result": "Sufficient free storage for upcoming backup operations",
        },
        {
            "check": "Backup completes successfully",
            "how_to_verify": "Trigger a manual backup after freeing space or increasing quota",
            "expected_result": "Job completes without quota errors",
        },
    ],
    "service_unavailable": [
        {
            "check": "Source service operational",
            "how_to_verify": "Check the source service status page",
            "expected_result": "Service status shows operational / all systems normal",
        },
        {
            "check": "Backup completes on retry",
            "how_to_verify": "Trigger a manual backup after service recovery",
            "expected_result": "Job completes successfully without 503 errors",
        },
    ],
    "unknown": [
        {
            "check": "Connector health check passes",
            "how_to_verify": "Check connector health in Keepit admin console",
            "expected_result": "Health status is 'healthy'",
        },
        {
            "check": "Manual backup completes",
            "how_to_verify": "Trigger a manual backup and monitor to completion",
            "expected_result": "Job completes without errors",
        },
        {
            "check": "Support ticket opened (if unresolved)",
            "how_to_verify": "Confirm a support ticket exists with diagnostic data attached",
            "expected_result": "Ticket is open and assigned to Keepit support",
        },
    ],
}


def generate_verification_checklist(failure_type: str) -> List[Dict[str, str]]:
    """Generate a post-fix verification checklist for a given failure type.

    Each checklist item describes what to verify, how to verify it, and
    what the expected result should be.

    Args:
        failure_type: The classified failure type string.

    Returns:
        List of checklist item dicts with keys: check, how_to_verify,
        expected_result.
    """
    return list(_VERIFICATION_CHECKLISTS.get(failure_type, _VERIFICATION_CHECKLISTS["unknown"]))


# ---------------------------------------------------------------------------
# Time-to-resolution calculation
# ---------------------------------------------------------------------------

def calculate_time_to_resolution(
    failure_time: str,
    resolution_time: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate elapsed time since failure for urgency assessment.

    If a resolution time is provided, calculates the total time to
    resolution. Otherwise, calculates the ongoing elapsed time.

    Args:
        failure_time: ISO 8601 timestamp of when the failure occurred.
        resolution_time: Optional ISO 8601 timestamp of when the issue
            was resolved. If None, uses current time.

    Returns:
        Dictionary with keys:
            elapsed_hours (float): Hours since failure.
            elapsed_description (str): Human-readable elapsed time.
            resolved (bool): Whether the issue has been resolved.
            urgency (str): "low", "medium", "high", or "critical".
            urgency_description (str): Context for the urgency level.
    """
    result: Dict[str, Any] = {
        "elapsed_hours": 0.0,
        "elapsed_description": "Unknown",
        "resolved": False,
        "urgency": "unknown",
        "urgency_description": "Unable to calculate urgency.",
    }

    try:
        fail_dt = parse_iso_timestamp(failure_time)
    except ValueError:
        return result

    if resolution_time:
        try:
            end_dt = parse_iso_timestamp(resolution_time)
            result["resolved"] = True
        except ValueError:
            end_dt = datetime.now(timezone.utc)
    else:
        end_dt = datetime.now(timezone.utc)

    elapsed = end_dt - fail_dt
    elapsed_hours = max(elapsed.total_seconds() / 3600, 0)
    result["elapsed_hours"] = round(elapsed_hours, 1)

    # Human-readable elapsed time
    if elapsed_hours < 1:
        result["elapsed_description"] = f"{int(elapsed.total_seconds() / 60)} minutes"
    elif elapsed_hours < 24:
        result["elapsed_description"] = f"{elapsed_hours:.1f} hours"
    elif elapsed_hours < 168:
        result["elapsed_description"] = f"{elapsed_hours / 24:.1f} days"
    else:
        result["elapsed_description"] = f"{elapsed_hours / 168:.1f} weeks"

    # Urgency assessment
    if result["resolved"]:
        result["urgency"] = "resolved"
        result["urgency_description"] = (
            f"Issue resolved. Time to resolution: {result['elapsed_description']}."
        )
    elif elapsed_hours < 4:
        result["urgency"] = "low"
        result["urgency_description"] = (
            f"Failure occurred {result['elapsed_description']} ago. "
            "Within standard response window."
        )
    elif elapsed_hours < 24:
        result["urgency"] = "medium"
        result["urgency_description"] = (
            f"Failure occurred {result['elapsed_description']} ago. "
            "Approaching one full backup cycle without protection."
        )
    elif elapsed_hours < 72:
        result["urgency"] = "high"
        result["urgency_description"] = (
            f"Failure occurred {result['elapsed_description']} ago. "
            "Extended backup gap. Prioritize remediation."
        )
    else:
        result["urgency"] = "critical"
        result["urgency_description"] = (
            f"Failure occurred {result['elapsed_description']} ago. "
            "Prolonged backup outage. Immediate action required."
        )

    return result


# ---------------------------------------------------------------------------
# Failure summary formatting
# ---------------------------------------------------------------------------

def format_failure_summary(
    job: Dict[str, Any],
    classification: Dict[str, Any],
    risk: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a structured failure summary for reporting.

    Combines job details, failure classification, and risk assessment
    into a single summary suitable for display or export.

    Args:
        job: The failed job record dictionary.
        classification: Failure classification from classify_failure_type().
        risk: Risk assessment from assess_data_risk().

    Returns:
        Dictionary with keys:
            title (str): One-line summary title.
            failure_time (str): When the failure occurred.
            failure_type (str): Classified failure category.
            confidence (str): Classification confidence level.
            risk_level (str): Data risk level.
            backup_gap (str): Human-readable backup gap.
            description (str): Full description of the failure.
            status_icon (str): Icon representing severity.
            priority_label (str): Priority for remediation.
    """
    failure_type = classification.get("type", "unknown")
    confidence = classification.get("confidence", "low")
    risk_level = risk.get("risk_level", "unknown")

    # Determine status icon
    icon_map = {
        "critical": "❌",
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢",
        "unknown": "⚠️",
    }
    status_icon = icon_map.get(risk_level, "⚠️")

    # Determine priority label
    if risk_level in ("critical", "high"):
        priority_label = "P1 - Immediate"
    elif risk_level == "medium":
        priority_label = "P2 - High"
    elif risk_level == "low":
        priority_label = "P3 - Normal"
    else:
        priority_label = "P2 - High"  # Default to high when unknown

    # Build title
    type_labels = {
        "auth_expired": "Authentication Failure",
        "config_change": "Configuration Change Failure",
        "api_limit": "API Rate Limit Failure",
        "connectivity": "Connectivity Failure",
        "permission_denied": "Permission Denied Failure",
        "quota_exceeded": "Quota Exceeded Failure",
        "service_unavailable": "Service Unavailable Failure",
        "unknown": "Unclassified Backup Failure",
    }
    type_label = type_labels.get(failure_type, "Backup Failure")
    connector_desc = job.get("description", "Unknown connector")
    title = f"{status_icon} {type_label}: {connector_desc}"

    # Build description
    description_parts = [
        classification.get("description", "Failure details unavailable."),
    ]
    if risk.get("data_at_risk_description"):
        description_parts.append(risk["data_at_risk_description"])
    if classification.get("indicators"):
        indicators_str = "; ".join(classification["indicators"][:3])
        description_parts.append(f"Evidence: {indicators_str}")

    return {
        "title": title,
        "failure_time": job.get("failed", "Unknown"),
        "failure_type": failure_type,
        "confidence": confidence,
        "risk_level": risk_level,
        "backup_gap": risk.get("gap_description", "Unknown"),
        "description": " | ".join(description_parts),
        "status_icon": status_icon,
        "priority_label": priority_label,
    }


# ---------------------------------------------------------------------------
# Main — self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Keepit Backup Failure Root Cause Utilities — Self-Test ===\n")

    # Test 1: parse_iso_timestamp
    print("Test 1: parse_iso_timestamp")
    ts = parse_iso_timestamp("2025-01-15T08:30:00Z")
    assert ts.year == 2025 and ts.month == 1 and ts.day == 15
    print(f"  Parsed: {ts.isoformat()}")

    ts2 = parse_iso_timestamp("2025-03-20T14:00:00+00:00")
    assert ts2.year == 2025 and ts2.month == 3
    print(f"  Parsed: {ts2.isoformat()}")
    print("  PASSED\n")

    # Test 2: parse_execsummary
    print("Test 2: parse_execsummary")
    xml = """<execsummary>
        <error>Token expired for Microsoft Graph API</error>
        <exitreason>Authentication failure - 401 Unauthorized</exitreason>
        <warning>Retry limit reached</warning>
        <items_processed>0</items_processed>
    </execsummary>"""
    parsed = parse_execsummary(xml)
    assert len(parsed["errors"]) >= 1
    assert parsed["exit_reason"] is not None
    assert len(parsed["warnings"]) >= 1
    assert parsed["parse_error"] is None
    print(f"  Errors: {parsed['errors']}")
    print(f"  Exit reason: {parsed['exit_reason']}")
    print(f"  Warnings: {parsed['warnings']}")
    print(f"  Details: {parsed['details']}")
    print("  PASSED\n")

    # Test 3: parse_execsummary with empty input
    print("Test 3: parse_execsummary (empty)")
    empty = parse_execsummary(None)
    assert empty["parse_error"] is not None
    print(f"  Parse error: {empty['parse_error']}")
    print("  PASSED\n")

    # Test 4: classify_failure_type
    print("Test 4: classify_failure_type")
    job = {"failed": "2025-01-15T08:30:00Z", "description": "Exchange Online backup"}
    classification = classify_failure_type(job, parsed)
    assert classification["type"] == "auth_expired"
    assert classification["confidence"] in ("high", "medium", "low")
    print(f"  Type: {classification['type']}")
    print(f"  Confidence: {classification['confidence']}")
    print(f"  Indicators: {classification['indicators'][:2]}")
    print("  PASSED\n")

    # Test 5: correlate_failure_with_audit
    print("Test 5: correlate_failure_with_audit")
    audit_events = [
        {"timestamp": "2025-01-15T06:00:00Z", "description": "Retention policy updated"},
        {"timestamp": "2025-01-15T04:00:00Z", "description": "User login successful"},
        {"timestamp": "2025-01-14T10:00:00Z", "description": "Config change: schedule modified"},
        {"timestamp": "2025-01-10T08:00:00Z", "description": "Unrelated event"},
    ]
    corr = correlate_failure_with_audit("2025-01-15T08:30:00Z", audit_events)
    assert corr["total_correlated"] >= 2
    assert len(corr["config_changes"]) >= 1
    print(f"  Total correlated: {corr['total_correlated']}")
    print(f"  Config changes: {len(corr['config_changes'])}")
    print(f"  Auth events: {len(corr['auth_events'])}")
    print("  PASSED\n")

    # Test 6: detect_config_change_causality
    print("Test 6: detect_config_change_causality")
    connectors = [
        {"guid": "abc-123", "name": "Exchange Online", "retention_updated": "2025-01-15T06:30:00Z"},
    ]
    causality = detect_config_change_causality("2025-01-15T08:30:00Z", audit_events, connectors)
    assert causality["causal_likely"] is True
    assert causality["confidence"] in ("high", "medium")
    print(f"  Causal likely: {causality['causal_likely']}")
    print(f"  Confidence: {causality['confidence']}")
    print(f"  Time delta: {causality['time_delta']}")
    print(f"  Changes found: {len(causality['changes_found'])}")
    print("  PASSED\n")

    # Test 7: assess_data_risk
    print("Test 7: assess_data_risk")
    from datetime import datetime, timezone, timedelta
    recent_time = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    latest = {"timestamp": recent_time}
    snap_range = [
        {"timestamp": (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat()}
        for h in range(6, 168, 24)
    ]
    risk = assess_data_risk(latest, snap_range)
    assert risk["risk_level"] == "low"
    assert risk["gap_hours"] < 24
    print(f"  Gap hours: {risk['gap_hours']}")
    print(f"  Risk level: {risk['risk_level']}")
    print(f"  Avg interval: {risk['avg_interval_hours']}h")
    print("  PASSED\n")

    # Test 8: classify_recurrence
    print("Test 8: classify_recurrence")
    job_history = [
        {"failed": "2025-01-15T08:30:00Z", "description": "Exchange backup auth error"},
        {"failed": "2025-01-14T08:30:00Z", "description": "Exchange backup auth error"},
        {"failed": "2025-01-13T08:30:00Z", "description": "Exchange backup auth error"},
        {"description": "Exchange backup", "started": "2025-01-12T08:30:00Z"},  # success
    ]
    current = {"failed": "2025-01-15T08:30:00Z", "description": "Exchange backup auth error"}
    recurrence = classify_recurrence(job_history, current)
    assert recurrence["classification"] in ("recurring", "chronic")
    assert recurrence["occurrence_count"] >= 2
    print(f"  Classification: {recurrence['classification']}")
    print(f"  Count: {recurrence['occurrence_count']}")
    print("  PASSED\n")

    # Test 9: generate_resolution_steps
    print("Test 9: generate_resolution_steps")
    context = {"connector": {"name": "Exchange Online"}, "recurrence": recurrence, "risk": risk}
    steps = generate_resolution_steps("auth_expired", context)
    assert len(steps) >= 3
    for s in steps:
        print(f"  Step {s['number']}: [{s['priority']}] {s['action']}")
    print("  PASSED\n")

    # Test 10: generate_verification_checklist
    print("Test 10: generate_verification_checklist")
    checklist = generate_verification_checklist("auth_expired")
    assert len(checklist) >= 2
    for item in checklist:
        print(f"  [ ] {item['check']}")
    print("  PASSED\n")

    # Test 11: calculate_time_to_resolution
    print("Test 11: calculate_time_to_resolution")
    ttr = calculate_time_to_resolution("2025-01-15T08:30:00Z")
    assert ttr["elapsed_hours"] > 0
    assert ttr["urgency"] == "critical"  # Very old failure
    print(f"  Elapsed: {ttr['elapsed_description']}")
    print(f"  Urgency: {ttr['urgency']}")
    print("  PASSED\n")

    # Test 12: format_failure_summary
    print("Test 12: format_failure_summary")
    summary = format_failure_summary(current, classification, risk)
    assert summary["failure_type"] == "auth_expired"
    print(f"  Title: {summary['title']}")
    print(f"  Priority: {summary['priority_label']}")
    print("  PASSED\n")

    print("=== All tests passed ===")
