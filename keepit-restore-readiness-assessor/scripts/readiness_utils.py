#!/usr/bin/env python3
"""
Keepit Restore Readiness Utilities

Helper functions for restore readiness and recovery capability assessment
used in the Keepit Restore Readiness Assessor skill.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from collections import defaultdict, Counter
import statistics


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HEALTH_WEIGHT = 0.25
FRESHNESS_WEIGHT = 0.30
CONTINUITY_WEIGHT = 0.20
RESTORE_WEIGHT = 0.25

RESTORE_JOB_TYPES = {"restore", "srestore", "pstrestore"}

CONNECTOR_TYPE_MAP: Dict[str, str] = {
    "o365-admin": "Microsoft 365",
    "azure-ad": "Entra ID",
    "gsuite": "Google Workspace",
    "dynamics365": "Dynamics 365",
    "sforce": "Salesforce",
    "powerbi": "Power BI",
    "zendesk": "Zendesk",
    "okta": "Okta",
    "docusign": "DocuSign",
    "bamboohr": "BambooHR",
    "confluence": "Confluence",
    "jira": "Jira",
    "azure-do": "Azure DevOps",
}

GRADE_THRESHOLDS: List[Tuple[float, str, str]] = [
    (90.0, "A", "\u2705"),
    (80.0, "B", "\u2705"),
    (70.0, "C", "\u26a0\ufe0f"),
    (60.0, "D", "\u274c"),
    (0.0, "F", "\u274c"),
]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime.

    Handles timestamps with or without trailing 'Z', with or without
    microseconds, and with explicit UTC offset.

    Args:
        timestamp: ISO 8601 formatted timestamp string.

    Returns:
        Timezone-aware datetime object in UTC.
    """
    if not timestamp:
        raise ValueError("Empty timestamp string")

    cleaned = timestamp.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    # Try multiple formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    raise ValueError(f"Unable to parse timestamp: {timestamp}")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_connector_type(connector_type: str) -> str:
    """Convert a raw connector type identifier to a human-readable name.

    Args:
        connector_type: Raw connector type string (e.g. 'o365-admin').

    Returns:
        Human-friendly display name (e.g. 'Microsoft 365').
    """
    return CONNECTOR_TYPE_MAP.get(connector_type, connector_type or "Unknown")


def score_to_grade(score: float) -> Tuple[str, str]:
    """Convert a numeric score (0-100) to a letter grade and icon.

    Grade thresholds:
        A = 90+, B = 80+, C = 70+, D = 60+, F = below 60.

    Args:
        score: Numeric readiness score between 0 and 100.

    Returns:
        Tuple of (grade letter, icon string).
    """
    clamped = max(0.0, min(100.0, score))
    for threshold, grade, icon in GRADE_THRESHOLDS:
        if clamped >= threshold:
            return grade, icon
    return "F", "\u274c"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string.

    Examples: '2m 15s', '1h 30m', '3h 0m 45s', '45s'.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human-readable duration string.
    """
    if seconds < 0:
        return "N/A"

    total = int(round(seconds))
    if total == 0:
        return "0s"

    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)

    parts: List[str] = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Health scoring
# ---------------------------------------------------------------------------


def _score_health(health: Dict[str, Any]) -> Tuple[float, str]:
    """Score connector health status on a 0-100 scale.

    Args:
        health: Health data dict with at least a 'healthStatus' key.

    Returns:
        Tuple of (score, description).
    """
    state = health.get("health", "unknown").lower()
    mapping = {
        "healthy": (100.0, "Connector is healthy and reachable"),
        "unhealthy": (60.0, "Connector is unhealthy — may affect restores"),
        "critical": (20.0, "Connector in critical state — restores likely impacted"),
        "unknown": (40.0, "Health status unknown — cannot confirm readiness"),
    }
    return mapping.get(state, (40.0, f"Unrecognized health state: {state}"))


# ---------------------------------------------------------------------------
# Freshness scoring
# ---------------------------------------------------------------------------


def _score_freshness(latest_snapshot: Optional[Dict[str, Any]], now: Optional[datetime] = None) -> Tuple[float, str, float]:
    """Score backup freshness based on the latest snapshot age.

    Args:
        latest_snapshot: Latest snapshot data with a 'timestamp' key, or None.
        now: Current time (defaults to utcnow).

    Returns:
        Tuple of (score, description, hours_since_backup).
    """
    if now is None:
        now = datetime.now(timezone.utc)

    if not latest_snapshot or not latest_snapshot.get("timestamp"):
        return 0.0, "No backups found — data is unprotected", -1.0

    try:
        last_backup = parse_iso_timestamp(latest_snapshot["timestamp"])
    except (ValueError, TypeError):
        return 0.0, "Unable to parse last backup timestamp", -1.0

    hours = (now - last_backup).total_seconds() / 3600.0

    if hours < 24:
        return 100.0, f"Last backup {hours:.1f}h ago — within 24h target", hours
    elif hours < 48:
        return 75.0, f"Last backup {hours:.1f}h ago — slightly stale", hours
    elif hours < 72:
        return 50.0, f"Last backup {hours:.1f}h ago — moderately stale", hours
    elif hours < 168:
        return 25.0, f"Last backup {hours:.1f}h ago — significantly stale", hours
    else:
        return 0.0, f"Last backup {hours:.1f}h ago — critically stale", hours


# ---------------------------------------------------------------------------
# Continuity scoring
# ---------------------------------------------------------------------------


def _score_continuity(gaps: Dict[str, Any]) -> Tuple[float, str]:
    """Score backup continuity based on gap analysis.

    Args:
        gaps: Gap analysis dict with keys like 'total_snapshots',
              'largest_gap_hours', 'median_interval_hours', 'gap_count'.

    Returns:
        Tuple of (score, description).
    """
    total = gaps.get("total_snapshots", 0)
    if total == 0:
        return 0.0, "No snapshots — continuity cannot be assessed"

    if total == 1:
        return 25.0, "Only 1 snapshot — no continuity history"

    largest_gap = gaps.get("largest_gap_hours", 0.0)
    median_interval = gaps.get("median_interval_hours", 24.0)
    gap_count = gaps.get("gap_count", 0)

    if median_interval <= 0:
        median_interval = 24.0

    gap_ratio = largest_gap / median_interval if median_interval > 0 else 0

    if gap_count == 0 or gap_ratio < 1.5:
        return 100.0, f"No significant gaps in {total} snapshots"
    elif gap_ratio < 2.0:
        return 75.0, f"Minor gaps detected (largest: {largest_gap:.1f}h)"
    elif gap_ratio < 4.0:
        return 50.0, f"Moderate gaps detected (largest: {largest_gap:.1f}h, {gap_count} gaps)"
    else:
        return 25.0, f"Severe gaps detected (largest: {largest_gap:.1f}h, {gap_count} gaps)"


# ---------------------------------------------------------------------------
# Restore history scoring
# ---------------------------------------------------------------------------


def _score_restore_history(restore_history: Dict[str, Any]) -> Tuple[float, str]:
    """Score restore history based on test results and success rates.

    Args:
        restore_history: Output from analyze_restore_history().

    Returns:
        Tuple of (score, description).
    """
    total = restore_history.get("total_restores", 0)
    if total == 0:
        return 40.0, "No restore history — recovery capability unverified"

    success_rate = restore_history.get("success_rate", 0.0)
    last_restore = restore_history.get("last_restore_date")

    recency_note = ""
    if last_restore:
        try:
            last_dt = parse_iso_timestamp(last_restore) if isinstance(last_restore, str) else last_restore
            days_ago = (datetime.now(timezone.utc) - last_dt).days
            recency_note = f", last restore {days_ago}d ago"
        except (ValueError, TypeError):
            recency_note = ""

    if success_rate >= 100.0:
        return 100.0, f"All {total} restores successful{recency_note}"
    elif success_rate >= 90.0:
        return 80.0, f"{success_rate:.0f}% success rate ({total} restores){recency_note}"
    elif success_rate >= 70.0:
        return 60.0, f"{success_rate:.0f}% success rate — some failures{recency_note}"
    else:
        failed = restore_history.get("failed", 0)
        return 20.0, f"{success_rate:.0f}% success rate — {failed} failures{recency_note}"


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------


def analyze_restore_history(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Filter jobs for restore types and calculate success metrics.

    Restore job types include 'restore', 'srestore', and 'pstrestore'.
    Job status is inferred from the job dict:
      - job.get('active') is truthy -> running (excluded from stats)
      - job.get('failed') is truthy -> failed
      - else -> successful

    Args:
        jobs: List of job dicts from get_job_history().

    Returns:
        Dict with keys: total_restores, successful, failed, running,
        success_rate, durations, avg_duration_seconds, median_duration_seconds,
        p95_duration_seconds, last_restore_date.
    """
    restore_jobs = [
        j for j in jobs
        if j.get("type", "").lower() in RESTORE_JOB_TYPES
    ]

    result: Dict[str, Any] = {
        "total_restores": len(restore_jobs),
        "successful": 0,
        "failed": 0,
        "running": 0,
        "success_rate": 0.0,
        "durations": [],
        "avg_duration_seconds": 0.0,
        "median_duration_seconds": 0.0,
        "p95_duration_seconds": 0.0,
        "last_restore_date": None,
    }

    if not restore_jobs:
        return result

    durations: List[float] = []
    last_date: Optional[datetime] = None

    for job in restore_jobs:
        # Determine status
        if job.get("active"):
            result["running"] += 1
            continue
        elif job.get("failed"):
            result["failed"] += 1
        else:
            result["successful"] += 1

        # Extract duration if available
        duration = job.get("duration")
        if duration is not None and isinstance(duration, (int, float)) and duration >= 0:
            durations.append(float(duration))
        else:
            # Try to compute from start/end timestamps
            start_str = job.get("start") or job.get("startTime")
            end_str = job.get("end") or job.get("endTime")
            if start_str and end_str:
                try:
                    start_dt = parse_iso_timestamp(start_str)
                    end_dt = parse_iso_timestamp(end_str)
                    dur = (end_dt - start_dt).total_seconds()
                    if dur >= 0:
                        durations.append(dur)
                except (ValueError, TypeError):
                    pass

        # Track last restore date
        ts_str = job.get("end") or job.get("endTime") or job.get("start") or job.get("startTime")
        if ts_str:
            try:
                ts = parse_iso_timestamp(ts_str)
                if last_date is None or ts > last_date:
                    last_date = ts
            except (ValueError, TypeError):
                pass

    completed = result["successful"] + result["failed"]
    if completed > 0:
        result["success_rate"] = (result["successful"] / completed) * 100.0

    result["durations"] = sorted(durations)

    if durations:
        result["avg_duration_seconds"] = statistics.mean(durations)
        result["median_duration_seconds"] = statistics.median(durations)
        result["p95_duration_seconds"] = _percentile(sorted(durations), 95)

    if last_date:
        result["last_restore_date"] = last_date.isoformat()

    return result


def _percentile(sorted_values: List[float], pct: float) -> float:
    """Calculate the given percentile from a sorted list of values.

    Args:
        sorted_values: Sorted list of numeric values.
        pct: Percentile to calculate (0-100).

    Returns:
        The value at the given percentile.
    """
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]

    k = (pct / 100.0) * (len(sorted_values) - 1)
    f = int(k)
    c = f + 1
    if c >= len(sorted_values):
        return sorted_values[-1]
    d = k - f
    return sorted_values[f] + d * (sorted_values[c] - sorted_values[f])


def estimate_rto(restore_history: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate RTO based on actual restore job durations.

    Confidence levels are determined by sample size:
      - High: 10+ completed restores
      - Medium: 3-9 completed restores
      - Low: 1-2 completed restores
      - None: 0 completed restores

    Args:
        restore_history: Output from analyze_restore_history().

    Returns:
        Dict with keys: median_seconds, p95_seconds, estimate_confidence,
        formatted_median, formatted_p95, sample_size, description.
    """
    durations = restore_history.get("durations", [])
    sample_size = len(durations)

    result: Dict[str, Any] = {
        "median_seconds": 0.0,
        "p95_seconds": 0.0,
        "estimate_confidence": "none",
        "formatted_median": "N/A",
        "formatted_p95": "N/A",
        "sample_size": sample_size,
        "description": "",
    }

    if sample_size == 0:
        result["description"] = "No restore history — RTO cannot be estimated. Perform a test restore to establish a baseline."
        return result

    median_s = restore_history.get("median_duration_seconds", 0.0)
    p95_s = restore_history.get("p95_duration_seconds", 0.0)

    result["median_seconds"] = median_s
    result["p95_seconds"] = p95_s
    result["formatted_median"] = format_duration(median_s)
    result["formatted_p95"] = format_duration(p95_s)

    if sample_size >= 10:
        result["estimate_confidence"] = "high"
        result["description"] = (
            f"RTO estimate based on {sample_size} restores: "
            f"median {format_duration(median_s)}, P95 {format_duration(p95_s)} (high confidence)"
        )
    elif sample_size >= 3:
        result["estimate_confidence"] = "medium"
        result["description"] = (
            f"RTO estimate based on {sample_size} restores: "
            f"median {format_duration(median_s)}, P95 {format_duration(p95_s)} (medium confidence — more data recommended)"
        )
    else:
        result["estimate_confidence"] = "low"
        result["description"] = (
            f"RTO estimate based on {sample_size} restore(s): "
            f"median {format_duration(median_s)}, P95 {format_duration(p95_s)} (low confidence — more restore tests recommended)"
        )

    return result


def calculate_rpo_achievement(
    latest_snapshot: Optional[Dict[str, Any]],
    target_hours: float = 24.0,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calculate actual vs target RPO for a connector.

    Args:
        latest_snapshot: Latest snapshot data with a 'timestamp' key, or None.
        target_hours: Target RPO in hours (default 24.0).
        now: Current time (defaults to utcnow).

    Returns:
        Dict with keys: actual_hours, target_hours, achieved, gap_hours,
        status, icon, description.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    result: Dict[str, Any] = {
        "actual_hours": -1.0,
        "target_hours": target_hours,
        "achieved": False,
        "gap_hours": 0.0,
        "status": "unknown",
        "icon": "\u274c",
        "description": "",
    }

    if not latest_snapshot or not latest_snapshot.get("timestamp"):
        result["status"] = "no_data"
        result["description"] = "No backups exist — RPO cannot be calculated"
        return result

    try:
        last_backup = parse_iso_timestamp(latest_snapshot["timestamp"])
    except (ValueError, TypeError):
        result["status"] = "parse_error"
        result["description"] = "Unable to parse last backup timestamp"
        return result

    actual_hours = (now - last_backup).total_seconds() / 3600.0
    result["actual_hours"] = round(actual_hours, 2)

    if actual_hours <= target_hours:
        result["achieved"] = True
        result["gap_hours"] = 0.0
        result["status"] = "achieved"
        result["icon"] = "\u2705"
        result["description"] = (
            f"RPO achieved: actual {actual_hours:.1f}h vs target {target_hours:.0f}h"
        )
    elif actual_hours <= target_hours * 1.5:
        result["achieved"] = False
        result["gap_hours"] = round(actual_hours - target_hours, 2)
        result["status"] = "at_risk"
        result["icon"] = "\u26a0\ufe0f"
        result["description"] = (
            f"RPO at risk: actual {actual_hours:.1f}h vs target {target_hours:.0f}h "
            f"(gap: {result['gap_hours']:.1f}h)"
        )
    else:
        result["achieved"] = False
        result["gap_hours"] = round(actual_hours - target_hours, 2)
        result["status"] = "breached"
        result["icon"] = "\u274c"
        result["description"] = (
            f"RPO breached: actual {actual_hours:.1f}h vs target {target_hours:.0f}h "
            f"(gap: {result['gap_hours']:.1f}h)"
        )

    return result


def calculate_connector_readiness(
    health: Dict[str, Any],
    latest_snapshot: Optional[Dict[str, Any]],
    gaps: Dict[str, Any],
    restore_history: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate per-connector readiness score (0-100).

    Factors and weights:
      - Health status:     25%
      - Backup freshness:  30%
      - Backup continuity: 20%
      - Restore history:   25%

    Args:
        health: Connector health data (from get_connector_health).
        latest_snapshot: Latest snapshot data (from get_latest_snapshot).
        gaps: Gap analysis data with total_snapshots, largest_gap_hours, etc.
        restore_history: Output from analyze_restore_history().

    Returns:
        Dict with keys: score, grade, icon, status, description, factors.
        Each factor contains: score, weight, weighted_score, description.
    """
    health_score, health_desc = _score_health(health)
    freshness_score, freshness_desc, hours_since = _score_freshness(latest_snapshot)
    continuity_score, continuity_desc = _score_continuity(gaps)
    restore_score, restore_desc = _score_restore_history(restore_history)

    factors = {
        "health": {
            "score": health_score,
            "weight": HEALTH_WEIGHT,
            "weighted_score": health_score * HEALTH_WEIGHT,
            "description": health_desc,
        },
        "freshness": {
            "score": freshness_score,
            "weight": FRESHNESS_WEIGHT,
            "weighted_score": freshness_score * FRESHNESS_WEIGHT,
            "description": freshness_desc,
            "hours_since_backup": hours_since,
        },
        "continuity": {
            "score": continuity_score,
            "weight": CONTINUITY_WEIGHT,
            "weighted_score": continuity_score * CONTINUITY_WEIGHT,
            "description": continuity_desc,
        },
        "restore_history": {
            "score": restore_score,
            "weight": RESTORE_WEIGHT,
            "weighted_score": restore_score * RESTORE_WEIGHT,
            "description": restore_desc,
        },
    }

    total_score = sum(f["weighted_score"] for f in factors.values())
    total_score = round(total_score, 1)
    grade, icon = score_to_grade(total_score)

    if total_score >= 90:
        status = "ready"
        description = "Fully ready for recovery operations"
    elif total_score >= 80:
        status = "ready"
        description = "Ready with minor improvements recommended"
    elif total_score >= 70:
        status = "partial"
        description = "Partially ready — some gaps need attention"
    elif total_score >= 60:
        status = "at_risk"
        description = "At risk — significant gaps in recovery capability"
    else:
        status = "not_ready"
        description = "Not ready — critical issues require immediate action"

    return {
        "score": total_score,
        "grade": grade,
        "icon": icon,
        "status": status,
        "description": description,
        "factors": factors,
    }


def calculate_overall_readiness(connector_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate weighted aggregate readiness grade (A-F) across all connectors.

    All connectors are weighted equally.

    Args:
        connector_scores: List of per-connector readiness results
            (output from calculate_connector_readiness).

    Returns:
        Dict with keys: score, grade, icon, status, connector_count,
        ready_count, at_risk_count, not_ready_count, description.
    """
    if not connector_scores:
        return {
            "score": 0.0,
            "grade": "F",
            "icon": "\u274c",
            "status": "no_connectors",
            "connector_count": 0,
            "ready_count": 0,
            "at_risk_count": 0,
            "not_ready_count": 0,
            "description": "No connectors configured — backup estate is empty",
        }

    scores = [c["score"] for c in connector_scores]
    overall = round(statistics.mean(scores), 1)
    grade, icon = score_to_grade(overall)

    ready = sum(1 for c in connector_scores if c.get("status") in ("ready",))
    at_risk = sum(1 for c in connector_scores if c.get("status") in ("partial", "at_risk"))
    not_ready = sum(1 for c in connector_scores if c.get("status") in ("not_ready",))

    if overall >= 90:
        status = "fully_ready"
        description = f"Fully ready — all {len(scores)} connectors assessed, grade {grade}"
    elif overall >= 80:
        status = "ready"
        description = f"Ready — {ready} of {len(scores)} connectors ready, minor improvements recommended"
    elif overall >= 70:
        status = "partial"
        description = f"Partially ready — {at_risk} connector(s) need attention"
    elif overall >= 60:
        status = "at_risk"
        description = f"At risk — {at_risk + not_ready} connector(s) have significant gaps"
    else:
        status = "not_ready"
        description = f"Not ready — {not_ready} connector(s) have critical issues"

    return {
        "score": overall,
        "grade": grade,
        "icon": icon,
        "status": status,
        "connector_count": len(scores),
        "ready_count": ready,
        "at_risk_count": at_risk,
        "not_ready_count": not_ready,
        "description": description,
    }


def identify_recovery_gaps(
    connectors: List[Dict[str, Any]],
    latest_snapshots: Dict[str, Optional[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Find connectors with no protection or critical coverage gaps.

    Args:
        connectors: List of connector dicts (from get_cloud_connectors).
        latest_snapshots: Mapping of connector GUID to latest snapshot data
            (None if no snapshots exist).

    Returns:
        List of gap dicts with keys: connector_name, connector_type,
        guid, issue, severity, icon, recommendation.
    """
    gaps: List[Dict[str, Any]] = []

    for conn in connectors:
        guid = conn.get("guid", "")
        name = conn.get("name", "Unknown")
        ctype = format_connector_type(conn.get("type", ""))
        snapshot = latest_snapshots.get(guid)

        if snapshot is None or not snapshot:
            gaps.append({
                "connector_name": name,
                "connector_type": ctype,
                "guid": guid,
                "issue": "No backups exist — data is completely unprotected",
                "severity": "critical",
                "icon": "\U0001f534",
                "recommendation": "Initiate an immediate backup for this connector",
            })
            continue

        ts = snapshot.get("timestamp")
        if not ts:
            gaps.append({
                "connector_name": name,
                "connector_type": ctype,
                "guid": guid,
                "issue": "Backup exists but timestamp is missing — freshness unknown",
                "severity": "high",
                "icon": "\U0001f534",
                "recommendation": "Investigate connector configuration and trigger a new backup",
            })
            continue

        try:
            last_dt = parse_iso_timestamp(ts)
            hours_ago = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600.0
        except (ValueError, TypeError):
            gaps.append({
                "connector_name": name,
                "connector_type": ctype,
                "guid": guid,
                "issue": "Unable to parse backup timestamp",
                "severity": "high",
                "icon": "\U0001f534",
                "recommendation": "Check connector logs and trigger a manual backup",
            })
            continue

        if hours_ago > 168:
            gaps.append({
                "connector_name": name,
                "connector_type": ctype,
                "guid": guid,
                "issue": f"Last backup is {hours_ago:.0f}h ({hours_ago / 24:.0f} days) old — critically stale",
                "severity": "critical",
                "icon": "\U0001f534",
                "recommendation": "Investigate why backups have stopped and trigger an immediate backup",
            })
        elif hours_ago > 72:
            gaps.append({
                "connector_name": name,
                "connector_type": ctype,
                "guid": guid,
                "issue": f"Last backup is {hours_ago:.0f}h ({hours_ago / 24:.0f} days) old — stale",
                "severity": "high",
                "icon": "\U0001f7e1",
                "recommendation": "Check backup schedule and ensure the connector is running on schedule",
            })

    return gaps


def generate_compliance_evidence(readiness_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate NIS2/DORA compliance evidence for backup testing.

    Maps readiness assessment data to specific regulatory articles:
      - NIS2 Article 21: Business continuity and disaster recovery
      - DORA Article 12: Backup policies and procedures, restoration and recovery

    Args:
        readiness_data: Full readiness report data containing overall_grade,
            connector_details, rpo_summary, rto_summary, and gaps.

    Returns:
        Dict with keys: nis2_article_21, dora_article_12, evidence_items, gaps.
    """
    evidence_items: List[str] = []
    compliance_gaps: List[str] = []

    overall = readiness_data.get("overall_grade", {})
    connector_details = readiness_data.get("connector_details", [])
    rpo_summary = readiness_data.get("rpo_summary", {})
    rto_summary = readiness_data.get("rto_summary", {})
    recovery_gaps = readiness_data.get("gaps", [])

    # --- NIS2 Article 21 evidence ---
    nis2: Dict[str, Any] = {
        "article": "NIS2 Article 21 — Business continuity and disaster recovery",
        "status": "partial",
        "findings": [],
    }

    connector_count = overall.get("connector_count", 0)
    if connector_count > 0:
        evidence_items.append(
            f"Backup coverage: {connector_count} connector(s) configured and monitored"
        )
        nis2["findings"].append(f"{connector_count} data sources under backup protection")

    grade = overall.get("grade", "F")
    score = overall.get("score", 0)
    evidence_items.append(f"Overall readiness grade: {grade} ({score}/100)")

    if grade in ("A", "B"):
        nis2["status"] = "compliant"
        nis2["findings"].append("Backup and recovery readiness meets requirements")
    elif grade == "C":
        nis2["status"] = "partial"
        nis2["findings"].append("Backup readiness partially meets requirements — gaps identified")
        compliance_gaps.append("NIS2: Readiness grade below B — improvements needed for full compliance")
    else:
        nis2["status"] = "non_compliant"
        nis2["findings"].append("Backup readiness does not meet requirements")
        compliance_gaps.append("NIS2: Readiness grade below C — critical remediation required")

    # Check for restore testing evidence
    has_restore_tests = False
    for detail in connector_details:
        rh = detail.get("restore_history", {})
        if rh.get("total_restores", 0) > 0:
            has_restore_tests = True
            evidence_items.append(
                f"Restore testing: {rh['total_restores']} restore(s) recorded "
                f"for {detail.get('connector_name', 'Unknown')} "
                f"({rh.get('success_rate', 0):.0f}% success)"
            )

    if not has_restore_tests:
        compliance_gaps.append(
            "NIS2: No restore tests recorded — Article 21 requires regular testing "
            "of business continuity and disaster recovery measures"
        )

    # --- DORA Article 12 evidence ---
    dora: Dict[str, Any] = {
        "article": "DORA Article 12 — Backup policies and procedures, restoration and recovery",
        "status": "partial",
        "findings": [],
    }

    # RPO documentation
    rpo_connectors = rpo_summary.get("connectors", [])
    achieved_count = sum(1 for r in rpo_connectors if r.get("achieved"))
    total_rpo = len(rpo_connectors)
    if total_rpo > 0:
        evidence_items.append(
            f"RPO achievement: {achieved_count}/{total_rpo} connectors meeting target"
        )
        dora["findings"].append(
            f"RPO documented and measured: {achieved_count}/{total_rpo} targets met"
        )
    else:
        compliance_gaps.append("DORA: No RPO data available — Article 12 requires documented RPO")

    # RTO documentation
    rto_data = rto_summary.get("connectors", [])
    rto_documented = sum(1 for r in rto_data if r.get("estimate_confidence", "none") != "none")
    if rto_documented > 0:
        evidence_items.append(
            f"RTO estimation: {rto_documented} connector(s) with measured RTO"
        )
        dora["findings"].append(
            f"RTO estimated from historical data for {rto_documented} connector(s)"
        )
    else:
        compliance_gaps.append(
            "DORA: No RTO data available — Article 12 requires documented and tested RTO"
        )

    # Restore success rate
    for detail in connector_details:
        rh = detail.get("restore_history", {})
        sr = rh.get("success_rate", 0)
        total = rh.get("total_restores", 0)
        if total > 0 and sr < 95.0:
            compliance_gaps.append(
                f"DORA: Restore success rate for {detail.get('connector_name', 'Unknown')} "
                f"is {sr:.0f}% (below 95% threshold)"
            )

    if recovery_gaps:
        for gap in recovery_gaps:
            if gap.get("severity") == "critical":
                compliance_gaps.append(
                    f"DORA: Critical gap — {gap['connector_name']}: {gap['issue']}"
                )

    # Determine DORA overall status
    if not compliance_gaps or all("NIS2" in g for g in compliance_gaps):
        dora["status"] = "compliant"
    elif any("critical" in g.lower() for g in compliance_gaps):
        dora["status"] = "non_compliant"
    else:
        dora["status"] = "partial"

    return {
        "nis2_article_21": nis2,
        "dora_article_12": dora,
        "evidence_items": evidence_items,
        "gaps": compliance_gaps,
    }


def generate_readiness_report(all_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured readiness assessment combining all analyses.

    This is the top-level report function that assembles all individual
    analyses into a single comprehensive report structure.

    Args:
        all_data: Dict with keys:
            - connectors: list of connector dicts
            - health: dict mapping guid -> health data
            - latest_snapshots: dict mapping guid -> latest snapshot data
            - gap_analyses: dict mapping guid -> gap analysis data
            - restore_histories: dict mapping guid -> restore history data
            - active_jobs: dict mapping guid -> active jobs list
            - target_rpo_hours: float (default 24.0)

    Returns:
        Dict with keys: overall_grade, connector_details, rpo_summary,
        rto_summary, gaps, recommendations, compliance_evidence,
        assessment_timestamp.
    """
    connectors = all_data.get("connectors", [])
    health_map = all_data.get("health", {})
    snapshot_map = all_data.get("latest_snapshots", {})
    gap_map = all_data.get("gap_analyses", {})
    restore_map = all_data.get("restore_histories", {})
    active_map = all_data.get("active_jobs", {})
    target_rpo = all_data.get("target_rpo_hours", 24.0)

    connector_details: List[Dict[str, Any]] = []
    connector_scores: List[Dict[str, Any]] = []
    rpo_connectors: List[Dict[str, Any]] = []
    rto_connectors: List[Dict[str, Any]] = []

    for conn in connectors:
        guid = conn.get("guid", "")
        name = conn.get("name", "Unknown")
        ctype = format_connector_type(conn.get("type", ""))

        health = health_map.get(guid, {"healthStatus": "unknown"})
        snapshot = snapshot_map.get(guid)
        gaps = gap_map.get(guid, {"total_snapshots": 0})
        restore_hist = restore_map.get(guid, {"total_restores": 0})
        active = active_map.get(guid, [])

        # Per-connector readiness
        readiness = calculate_connector_readiness(health, snapshot, gaps, restore_hist)
        connector_scores.append(readiness)

        # RPO achievement
        rpo = calculate_rpo_achievement(snapshot, target_hours=target_rpo)
        rpo_connectors.append({
            "connector_name": name,
            "connector_type": ctype,
            "guid": guid,
            **rpo,
        })

        # RTO estimation
        rto = estimate_rto(restore_hist)
        rto_connectors.append({
            "connector_name": name,
            "connector_type": ctype,
            "guid": guid,
            **rto,
        })

        detail = {
            "connector_name": name,
            "connector_type": ctype,
            "guid": guid,
            "readiness": readiness,
            "rpo": rpo,
            "rto": rto,
            "restore_history": restore_hist,
            "active_jobs": len(active),
            "active_job_details": active,
        }
        connector_details.append(detail)

    # Overall grade
    overall = calculate_overall_readiness(connector_scores)

    # Coverage gaps
    recovery_gaps = identify_recovery_gaps(connectors, snapshot_map)

    # Build recommendations
    recommendations = _build_recommendations(connector_details, recovery_gaps, overall)

    # RPO summary
    rpo_achieved = sum(1 for r in rpo_connectors if r.get("achieved"))
    rpo_summary = {
        "target_hours": target_rpo,
        "achieved_count": rpo_achieved,
        "total_count": len(rpo_connectors),
        "connectors": rpo_connectors,
    }

    # RTO summary
    rto_known = sum(1 for r in rto_connectors if r.get("estimate_confidence", "none") != "none")
    rto_summary = {
        "known_count": rto_known,
        "total_count": len(rto_connectors),
        "connectors": rto_connectors,
    }

    # Compliance evidence
    report_for_compliance = {
        "overall_grade": overall,
        "connector_details": connector_details,
        "rpo_summary": rpo_summary,
        "rto_summary": rto_summary,
        "gaps": recovery_gaps,
    }
    compliance = generate_compliance_evidence(report_for_compliance)

    return {
        "overall_grade": overall,
        "connector_details": connector_details,
        "rpo_summary": rpo_summary,
        "rto_summary": rto_summary,
        "gaps": recovery_gaps,
        "recommendations": recommendations,
        "compliance_evidence": compliance,
        "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_recommendations(
    connector_details: List[Dict[str, Any]],
    recovery_gaps: List[Dict[str, Any]],
    overall: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build prioritized list of recommendations from assessment data.

    Args:
        connector_details: Per-connector detail dicts.
        recovery_gaps: Coverage gap findings.
        overall: Overall readiness summary.

    Returns:
        Sorted list of recommendation dicts with keys: priority, icon,
        category, recommendation, connector_name (optional).
    """
    recs: List[Dict[str, Any]] = []

    # Critical gaps first
    for gap in recovery_gaps:
        severity = gap.get("severity", "medium")
        if severity == "critical":
            priority = 1
            icon = "\U0001f534"
        elif severity == "high":
            priority = 2
            icon = "\U0001f534"
        else:
            priority = 3
            icon = "\U0001f7e1"

        recs.append({
            "priority": priority,
            "icon": icon,
            "category": "Coverage Gap",
            "recommendation": gap.get("recommendation", "Address this gap"),
            "connector_name": gap.get("connector_name", "Unknown"),
        })

    # Per-connector recommendations
    for detail in connector_details:
        name = detail.get("connector_name", "Unknown")
        readiness = detail.get("readiness", {})
        factors = readiness.get("factors", {})

        # Unhealthy connectors
        health_score = factors.get("health", {}).get("score", 100)
        if health_score <= 20:
            recs.append({
                "priority": 1,
                "icon": "\U0001f534",
                "category": "Health",
                "recommendation": f"Resolve connector health errors for {name}",
                "connector_name": name,
            })
        elif health_score <= 60:
            recs.append({
                "priority": 2,
                "icon": "\U0001f7e1",
                "category": "Health",
                "recommendation": f"Investigate health warnings for {name}",
                "connector_name": name,
            })

        # No restore history
        rh = detail.get("restore_history", {})
        if rh.get("total_restores", 0) == 0:
            recs.append({
                "priority": 2,
                "icon": "\U0001f7e1",
                "category": "Restore Testing",
                "recommendation": f"Perform a test restore for {name} to validate recovery capability",
                "connector_name": name,
            })
        elif rh.get("success_rate", 100) < 70:
            recs.append({
                "priority": 1,
                "icon": "\U0001f534",
                "category": "Restore Reliability",
                "recommendation": f"Investigate restore failures for {name} — success rate is {rh['success_rate']:.0f}%",
                "connector_name": name,
            })

        # RPO at risk or breached
        rpo = detail.get("rpo", {})
        if rpo.get("status") == "breached":
            recs.append({
                "priority": 1,
                "icon": "\U0001f534",
                "category": "RPO",
                "recommendation": f"RPO breached for {name} — trigger immediate backup and investigate schedule",
                "connector_name": name,
            })
        elif rpo.get("status") == "at_risk":
            recs.append({
                "priority": 2,
                "icon": "\U0001f7e1",
                "category": "RPO",
                "recommendation": f"RPO at risk for {name} — monitor closely and consider more frequent backups",
                "connector_name": name,
            })

    # Overall recommendation
    if overall.get("grade") in ("A", "B"):
        recs.append({
            "priority": 4,
            "icon": "\U0001f7e2",
            "category": "Maintenance",
            "recommendation": "Schedule quarterly readiness reassessments to maintain grade",
        })
    elif overall.get("grade") == "C":
        recs.append({
            "priority": 3,
            "icon": "\U0001f7e1",
            "category": "Improvement",
            "recommendation": "Address identified gaps within 30 days to improve readiness grade",
        })
    else:
        recs.append({
            "priority": 1,
            "icon": "\U0001f534",
            "category": "Critical",
            "recommendation": "Immediate action required — readiness grade is below acceptable threshold",
        })

    # Sort by priority (1 = highest)
    recs.sort(key=lambda r: r["priority"])

    return recs


# ---------------------------------------------------------------------------
# Main — test / demo
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=== Keepit Restore Readiness Utilities — Self-Test ===\n")

    # Test parse_iso_timestamp
    ts1 = parse_iso_timestamp("2025-01-15T10:30:00Z")
    ts2 = parse_iso_timestamp("2025-01-15T10:30:00.000+00:00")
    assert ts1 == ts2, "Timestamp parsing mismatch"
    print(f"[OK] parse_iso_timestamp: {ts1}")

    # Test format_connector_type
    assert format_connector_type("o365-admin") == "Microsoft 365"
    assert format_connector_type("gsuite") == "Google Workspace"
    assert format_connector_type("unknown-type") == "unknown-type"
    print("[OK] format_connector_type")

    # Test score_to_grade
    assert score_to_grade(95) == ("A", "\u2705")
    assert score_to_grade(85) == ("B", "\u2705")
    assert score_to_grade(75) == ("C", "\u26a0\ufe0f")
    assert score_to_grade(65) == ("D", "\u274c")
    assert score_to_grade(50) == ("F", "\u274c")
    print("[OK] score_to_grade")

    # Test format_duration
    assert format_duration(45) == "45s"
    assert format_duration(135) == "2m 15s"
    assert format_duration(3661) == "1h 1m 1s"
    assert format_duration(3600) == "1h"
    print("[OK] format_duration")

    # Test analyze_restore_history
    test_jobs = [
        {"type": "restore", "duration": 120},
        {"type": "restore", "duration": 180, "failed": True},
        {"type": "srestore", "duration": 90},
        {"type": "backup", "duration": 300},  # not a restore
        {"type": "pstrestore", "active": True},  # running
    ]
    rh = analyze_restore_history(test_jobs)
    assert rh["total_restores"] == 4
    assert rh["successful"] == 2
    assert rh["failed"] == 1
    assert rh["running"] == 1
    print(f"[OK] analyze_restore_history: {rh['total_restores']} restores, "
          f"{rh['success_rate']:.0f}% success")

    # Test estimate_rto
    rto = estimate_rto(rh)
    print(f"[OK] estimate_rto: median={rto['formatted_median']}, "
          f"p95={rto['formatted_p95']}, confidence={rto['estimate_confidence']}")

    # Test calculate_rpo_achievement
    now = datetime(2025, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
    rpo = calculate_rpo_achievement(
        {"timestamp": "2025-01-15T22:00:00Z"},
        target_hours=24.0,
        now=now,
    )
    assert rpo["achieved"] is True
    print(f"[OK] calculate_rpo_achievement: {rpo['description']}")

    rpo_breach = calculate_rpo_achievement(
        {"timestamp": "2025-01-10T10:00:00Z"},
        target_hours=24.0,
        now=now,
    )
    assert rpo_breach["achieved"] is False
    assert rpo_breach["status"] == "breached"
    print(f"[OK] calculate_rpo_achievement (breach): {rpo_breach['description']}")

    # Test calculate_connector_readiness
    fresh_ts = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    readiness = calculate_connector_readiness(
        health={"state": "healthy"},
        latest_snapshot={"timestamp": fresh_ts},
        gaps={"total_snapshots": 30, "largest_gap_hours": 25, "median_interval_hours": 24, "gap_count": 0},
        restore_history=rh,
    )
    print(f"[OK] calculate_connector_readiness: {readiness['grade']} "
          f"({readiness['score']}/100) — {readiness['description']}")

    # Test calculate_overall_readiness
    overall = calculate_overall_readiness([readiness, readiness])
    print(f"[OK] calculate_overall_readiness: {overall['grade']} "
          f"({overall['score']}/100) — {overall['description']}")

    # Test identify_recovery_gaps
    recent_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    test_connectors = [
        {"guid": "a", "name": "M365", "type": "o365-admin"},
        {"guid": "b", "name": "Salesforce", "type": "sforce"},
    ]
    test_snapshots = {"a": {"timestamp": recent_ts}, "b": None}
    gaps = identify_recovery_gaps(test_connectors, test_snapshots)
    assert len(gaps) == 1, f"Expected 1 gap, got {len(gaps)}"
    assert gaps[0]["connector_name"] == "Salesforce"
    print(f"[OK] identify_recovery_gaps: {len(gaps)} gap(s) found")

    # Test generate_compliance_evidence
    ce = generate_compliance_evidence({
        "overall_grade": overall,
        "connector_details": [],
        "rpo_summary": {"connectors": []},
        "rto_summary": {"connectors": []},
        "gaps": [],
    })
    print(f"[OK] generate_compliance_evidence: NIS2={ce['nis2_article_21']['status']}, "
          f"DORA={ce['dora_article_12']['status']}")

    print("\n=== All self-tests passed ===")
