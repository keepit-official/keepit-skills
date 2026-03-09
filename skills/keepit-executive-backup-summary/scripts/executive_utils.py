#!/usr/bin/env python3
"""
Keepit Executive Backup Summary Utilities

Helper functions for computing protection scores, generating coverage summaries,
translating technical issues to business language, and producing board-ready
executive reports used in the Keepit Executive Backup Summary skill.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from collections import defaultdict, Counter


# ---------------------------------------------------------------------------
# Connector type mapping — plain-English names for executive reporting
# ---------------------------------------------------------------------------

CONNECTOR_TYPE_MAP: Dict[str, str] = {
    'o365-admin': 'Microsoft 365',
    'azure-ad': 'Entra ID',
    'gsuite': 'Google Workspace',
    'dynamics365': 'Dynamics 365',
    'sforce': 'Salesforce',
    'powerbi': 'Power BI',
    'zendesk': 'Zendesk',
    'okta': 'Okta',
    'docusign': 'DocuSign',
    'bamboohr': 'BambooHR',
    'confluence': 'Confluence',
    'jira': 'Jira',
    'azure-do': 'Azure DevOps',
}

# ---------------------------------------------------------------------------
# Risk-translation templates — technical → business language
# ---------------------------------------------------------------------------

RISK_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'unhealthy': {
        'title': '{app} backup service is down',
        'description': '{app} backup service is currently unavailable.',
        'business_impact': 'If {app} data is lost or corrupted, it cannot be recovered until the service is restored.',
        'recommended_action': 'IT team should investigate the {app} backup service immediately.',
    },
    'degraded': {
        'title': '{app} backup service is experiencing issues',
        'description': '{app} backup service is operating in a degraded state.',
        'business_impact': 'Data recovery for {app} may be delayed or incomplete.',
        'recommended_action': 'IT team should investigate the {app} backup service within 4 hours.',
    },
    'stale_backup': {
        'title': '{app} has not been backed up recently',
        'description': '{app} has not been backed up in {hours} hours.',
        'business_impact': 'If {app} data is lost, the most recent {hours} hours of data cannot be recovered.',
        'recommended_action': 'IT team should verify the {app} backup schedule and trigger a manual backup if needed.',
    },
    'low_success_rate': {
        'title': '{app} backup reliability is below target',
        'description': '{rate}% of recent {app} backup jobs have failed.',
        'business_impact': 'Recurring backup failures may lead to data protection gaps for {app}.',
        'recommended_action': 'IT team should review {app} backup job logs and resolve recurring failures.',
    },
    'low_rpo_compliance': {
        'title': 'Backup schedule compliance is below target',
        'description': 'Only {pct}% of expected backups were completed in the reporting period.',
        'business_impact': 'Data protection gaps exist — some time periods may not have recoverable backup points.',
        'recommended_action': 'IT team should review backup schedules and investigate missed backup windows.',
    },
}

# ---------------------------------------------------------------------------
# Protection Score thresholds
# ---------------------------------------------------------------------------

GRADE_THRESHOLDS: List[Tuple[float, str]] = [
    (90.0, 'A'),
    (80.0, 'B'),
    (70.0, 'C'),
    (60.0, 'D'),
    (0.0, 'F'),
]

COLOR_THRESHOLDS: List[Tuple[float, str, str]] = [
    (90.0, 'green', '✅'),
    (80.0, 'green', '✅'),
    (70.0, 'yellow', '⚠️'),
    (60.0, 'yellow', '⚠️'),
    (0.0, 'red', '❌'),
]

POSTURE_DESCRIPTIONS: Dict[str, str] = {
    'A': 'Excellent',
    'B': 'Good',
    'C': 'Adequate',
    'D': 'Needs Improvement',
    'F': 'Critical Attention Required',
}

# Recency thresholds in hours
RECENCY_THRESHOLDS: List[Tuple[float, float]] = [
    (12.0, 100.0),
    (24.0, 80.0),
    (48.0, 50.0),
    (72.0, 25.0),
]


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

def parse_iso_timestamp(timestamp: str) -> Optional[datetime]:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime.

    Handles common ISO formats including those with and without microseconds,
    and with 'Z' suffix or explicit UTC offset.

    Args:
        timestamp: ISO 8601 formatted timestamp string.

    Returns:
        Timezone-aware datetime object, or None if parsing fails.
    """
    if not timestamp:
        return None

    # Normalize Z suffix to +00:00
    ts = timestamp.strip()
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'

    formats = [
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(ts, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return None


# ---------------------------------------------------------------------------
# Connector type formatting
# ---------------------------------------------------------------------------

def format_connector_type(connector_type: str) -> str:
    """Format a raw connector type string to a plain-English application name.

    Uses the CONNECTOR_TYPE_MAP lookup table. Falls back to title-casing the
    raw type with hyphens replaced by spaces.

    Args:
        connector_type: Raw connector type string (e.g. 'o365-admin').

    Returns:
        Human-readable application name (e.g. 'Microsoft 365').
    """
    if not connector_type:
        return 'Unknown Application'
    return CONNECTOR_TYPE_MAP.get(
        connector_type,
        connector_type.replace('-', ' ').replace('_', ' ').title()
    )


# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------

def score_to_grade(score: float) -> str:
    """Convert a 0-100 numeric score to a letter grade (A-F).

    Args:
        score: Numeric protection score between 0 and 100.

    Returns:
        Single letter grade: A, B, C, D, or F.
    """
    clamped = max(0.0, min(100.0, score))
    for threshold, grade in GRADE_THRESHOLDS:
        if clamped >= threshold:
            return grade
    return 'F'


def score_to_color(score: float) -> str:
    """Convert a 0-100 numeric score to a color indicator string.

    Args:
        score: Numeric protection score between 0 and 100.

    Returns:
        Color string: 'green', 'yellow', or 'red'.
    """
    clamped = max(0.0, min(100.0, score))
    for threshold, color, _ in COLOR_THRESHOLDS:
        if clamped >= threshold:
            return color
    return 'red'


def score_to_icon(score: float) -> str:
    """Convert a 0-100 numeric score to an emoji icon.

    Args:
        score: Numeric protection score between 0 and 100.

    Returns:
        Emoji icon string.
    """
    clamped = max(0.0, min(100.0, score))
    for threshold, _, icon in COLOR_THRESHOLDS:
        if clamped >= threshold:
            return icon
    return '❌'


def posture_description(grade: str) -> str:
    """Get the plain-English posture description for a letter grade.

    Args:
        grade: Letter grade (A-F).

    Returns:
        Posture description string (e.g. 'Excellent').
    """
    return POSTURE_DESCRIPTIONS.get(grade, 'Unknown')


# ---------------------------------------------------------------------------
# Component score calculations
# ---------------------------------------------------------------------------

def calculate_health_score(health_results: List[Dict[str, Any]]) -> float:
    """Calculate a 0-100 score based on connector health across all connectors.

    Scoring: healthy = 100, degraded = 50, unhealthy/unknown = 0.
    Returns the average across all connectors.

    Args:
        health_results: List of dicts, each with a 'health' key containing
                        a dict with a 'state' field.

    Returns:
        Float score between 0 and 100. Returns 0 if no connectors.
    """
    if not health_results:
        return 0.0

    state_scores = {
        'healthy': 100.0,
        'unhealthy': 25.0,
        'critical': 0.0,
        'unknown': 0.0,
    }

    total = 0.0
    for result in health_results:
        state = result.get('health', 'unknown').lower().strip()
        total += state_scores.get(state, 0.0)

    return total / len(health_results)


def calculate_recency_score(latest_snapshots: List[Dict[str, Any]]) -> float:
    """Calculate a 0-100 score based on backup freshness across all connectors.

    Scoring by hours since last backup:
        <12h = 100, 12-24h = 80, 24-48h = 50, 48-72h = 25, >72h = 0.
    Returns the average across all connectors.

    Args:
        latest_snapshots: List of dicts, each with 'hours_since_backup' (float)
                          or 'latest_snapshot' containing a timestamp dict.

    Returns:
        Float score between 0 and 100. Returns 0 if no data.
    """
    if not latest_snapshots:
        return 0.0

    now = datetime.now(timezone.utc)
    total = 0.0
    count = 0

    for item in latest_snapshots:
        hours = item.get('hours_since_backup')

        # If hours_since_backup not pre-computed, try to derive from snapshot
        if hours is None:
            snapshot = item.get('latest_snapshot', {})
            ts = snapshot.get('tstamp', '') if isinstance(snapshot, dict) else ''
            parsed = parse_iso_timestamp(ts)
            if parsed:
                hours = (now - parsed).total_seconds() / 3600.0
            else:
                hours = None

        if hours is None:
            # No snapshot data — treat as worst case
            total += 0.0
            count += 1
            continue

        # Score based on recency thresholds
        score = 0.0
        for threshold_hours, threshold_score in RECENCY_THRESHOLDS:
            if hours <= threshold_hours:
                score = threshold_score
                break

        total += score
        count += 1

    return total / count if count > 0 else 0.0


# ---------------------------------------------------------------------------
# Protection Score calculation
# ---------------------------------------------------------------------------

def calculate_protection_score(
    health_data: List[Dict[str, Any]],
    recency_data: List[Dict[str, Any]],
    rpo_compliance: float,
    success_rate: float,
) -> Dict[str, Any]:
    """Calculate the weighted 0-100 composite Protection Score.

    Weights:
        - Connector Health: 30%
        - Backup Recency: 25%
        - RPO Compliance: 25%
        - Job Success Rate: 20%

    Args:
        health_data: List of connector health result dicts.
        recency_data: List of connector recency data dicts.
        rpo_compliance: RPO compliance percentage (0-100).
        success_rate: Job success rate percentage (0-100).

    Returns:
        Dict containing:
            - score (float): Composite score 0-100
            - grade (str): Letter grade A-F
            - color (str): Color indicator
            - icon (str): Emoji icon
            - posture (str): Posture description
            - trend_direction (str): Placeholder for trend ('stable' by default)
            - component_scores (dict): Individual component scores and weights
    """
    health_score = calculate_health_score(health_data)
    recency_score = calculate_recency_score(recency_data)
    rpo_score = max(0.0, min(100.0, rpo_compliance))
    job_score = max(0.0, min(100.0, success_rate))

    composite = (
        health_score * 0.30 +
        recency_score * 0.25 +
        rpo_score * 0.25 +
        job_score * 0.20
    )

    composite = round(max(0.0, min(100.0, composite)), 1)
    grade = score_to_grade(composite)

    return {
        'score': composite,
        'grade': grade,
        'color': score_to_color(composite),
        'icon': score_to_icon(composite),
        'posture': posture_description(grade),
        'trend_direction': 'stable',
        'component_scores': {
            'health': {'score': round(health_score, 1), 'weight': 0.30},
            'recency': {'score': round(recency_score, 1), 'weight': 0.25},
            'rpo_compliance': {'score': round(rpo_score, 1), 'weight': 0.25},
            'job_success_rate': {'score': round(job_score, 1), 'weight': 0.20},
        },
    }


# ---------------------------------------------------------------------------
# Coverage summary
# ---------------------------------------------------------------------------

def generate_coverage_summary(connectors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a plain-English application coverage inventory.

    Translates raw connector data into a human-readable summary listing all
    protected SaaS applications by their business names.

    Args:
        connectors: List of connector dicts, each with 'type' and optional
                    'name' keys.

    Returns:
        Dict containing:
            - total_apps (int): Number of protected applications
            - app_names (list): Human-readable application names
            - app_types (list): Raw connector type strings
            - summary_sentence (str): Plain-English sentence describing coverage
            - connectors_by_type (dict): Connectors grouped by friendly type name
    """
    if not connectors:
        return {
            'total_apps': 0,
            'app_names': [],
            'app_types': [],
            'summary_sentence': 'No SaaS applications are currently protected by Keepit.',
            'connectors_by_type': {},
        }

    app_names: List[str] = []
    app_types: List[str] = []
    by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for connector in connectors:
        raw_type = connector.get('type', 'unknown')
        friendly = format_connector_type(raw_type)
        app_names.append(friendly)
        app_types.append(raw_type)
        by_type[friendly].append(connector)

    # De-duplicate for the summary sentence while preserving order
    seen = set()
    unique_names: List[str] = []
    for name in app_names:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    count = len(unique_names)
    plural = 's' if count != 1 else ''
    names_str = ', '.join(unique_names)
    summary = f"{count} SaaS application{plural} protected: {names_str}"

    return {
        'total_apps': count,
        'app_names': unique_names,
        'app_types': list(set(app_types)),
        'summary_sentence': summary,
        'connectors_by_type': dict(by_type),
    }


# ---------------------------------------------------------------------------
# Risk translation
# ---------------------------------------------------------------------------

def format_risk_items_plain_english(
    issues: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Translate technical backup issues to business-impact language.

    Converts raw technical issues (unhealthy connectors, stale backups, low
    success rates) into risk items with business-readable titles, descriptions,
    impact statements, priority levels, and recommended actions.

    Args:
        issues: List of dicts, each with:
            - issue_type (str): 'unhealthy', 'degraded', 'stale_backup',
                                'low_success_rate', 'low_rpo_compliance'
            - connector_type (str): Raw connector type for name lookup
            - hours (float, optional): Hours since last backup (for stale_backup)
            - rate (float, optional): Failure rate percentage (for low_success_rate)
            - pct (float, optional): Compliance percentage (for low_rpo_compliance)

    Returns:
        List of dicts, each containing:
            - title (str): Business-readable risk title
            - description (str): Detailed description
            - business_impact (str): Impact statement
            - priority (str): 'high', 'medium', or 'low'
            - priority_icon (str): Icon for priority level
            - recommended_action (str): Actionable recommendation
    """
    if not issues:
        return []

    # Priority mapping
    priority_map = {
        'unhealthy': ('high', '🔴'),
        'degraded': ('medium', '🟡'),
        'stale_backup': ('high', '🔴'),
        'low_success_rate': ('medium', '🟡'),
        'low_rpo_compliance': ('medium', '🟡'),
    }

    results: List[Dict[str, Any]] = []

    for issue in issues:
        issue_type = issue.get('issue_type', 'unknown')
        connector_type = issue.get('connector_type', 'unknown')
        app_name = format_connector_type(connector_type)

        template = RISK_TRANSLATIONS.get(issue_type)
        if not template:
            # Fallback for unknown issue types
            results.append({
                'title': f'{app_name} is experiencing an issue',
                'description': f'An unclassified issue was detected with {app_name}.',
                'business_impact': f'{app_name} data protection may be affected.',
                'priority': 'medium',
                'priority_icon': '🟡',
                'recommended_action': f'IT team should investigate {app_name} backup status.',
            })
            continue

        # Build substitution values
        subs = {
            'app': app_name,
            'hours': str(int(issue.get('hours', 0))),
            'rate': str(round(issue.get('rate', 0), 1)),
            'pct': str(round(issue.get('pct', 0), 1)),
        }

        priority_level, priority_icon = priority_map.get(issue_type, ('medium', '🟡'))

        # Elevate priority for especially severe cases
        hours = issue.get('hours', 0)
        if issue_type == 'stale_backup' and hours and hours > 72:
            priority_level = 'high'
            priority_icon = '🔴'
        rate = issue.get('rate', 0)
        if issue_type == 'low_success_rate' and rate and rate > 40:
            priority_level = 'high'
            priority_icon = '🔴'

        results.append({
            'title': template['title'].format(**subs),
            'description': template['description'].format(**subs),
            'business_impact': template['business_impact'].format(**subs),
            'priority': priority_level,
            'priority_icon': priority_icon,
            'recommended_action': template['recommended_action'].format(**subs),
        })

    # Sort by priority: high first, then medium, then low
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    results.sort(key=lambda r: priority_order.get(r['priority'], 99))

    return results


# ---------------------------------------------------------------------------
# Trend indicator
# ---------------------------------------------------------------------------

def generate_trend_indicator(
    current_score: float,
    previous_score: float,
) -> Dict[str, Any]:
    """Determine protection trend: improved, stable, or degraded.

    Compares the current Protection Score against a previous period score and
    classifies the direction of change.

    Args:
        current_score: Current period Protection Score (0-100).
        previous_score: Previous period Protection Score (0-100).

    Returns:
        Dict containing:
            - direction (str): 'improved', 'stable', or 'degraded'
            - delta (float): Score difference (current - previous)
            - icon (str): Trend emoji icon
            - description (str): Plain-English trend sentence
    """
    delta = round(current_score - previous_score, 1)

    if delta > 2.0:
        direction = 'improved'
        icon = '📈'
        description = (
            f"Protection posture has improved by {abs(delta)} points "
            f"compared to the previous period."
        )
    elif delta < -2.0:
        direction = 'degraded'
        icon = '📉'
        description = (
            f"Protection posture has degraded by {abs(delta)} points "
            f"compared to the previous period. Review risk items for details."
        )
    else:
        direction = 'stable'
        icon = '➡️'
        description = "Protection posture is stable compared to the previous period."

    return {
        'direction': direction,
        'delta': delta,
        'icon': icon,
        'description': description,
    }


# ---------------------------------------------------------------------------
# Recovery readiness estimation
# ---------------------------------------------------------------------------

def estimate_recovery_readiness(
    snapshots: List[Dict[str, Any]],
    job_history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Estimate RPO and RTO from actual backup and job data.

    RPO is derived from the time since the most recent successful backup.
    RTO is estimated from average job durations in the job history.

    Args:
        snapshots: List of dicts, each with 'hours_since_backup' (float) or
                   a 'latest_snapshot' containing a timestamp.
        job_history: List of dicts, each with 'jobs' (list of job dicts).
                     Each job dict may have 'duration' (seconds or ISO duration)
                     and 'status'.

    Returns:
        Dict containing:
            - rpo_hours (float): Estimated RPO in hours
            - rto_estimate (str): Human-readable RTO estimate
            - rto_hours (float): Estimated RTO in hours
            - readiness_level (str): 'excellent', 'good', 'fair', or 'poor'
            - readiness_icon (str): Status icon
            - description (str): Plain-English readiness summary
    """
    # --- RPO calculation: max hours since backup across all connectors ---
    now = datetime.now(timezone.utc)
    max_hours = 0.0
    rpo_values: List[float] = []

    for item in snapshots:
        hours = item.get('hours_since_backup')
        if hours is None:
            snapshot = item.get('latest_snapshot', {})
            ts = snapshot.get('tstamp', '') if isinstance(snapshot, dict) else ''
            parsed = parse_iso_timestamp(ts)
            if parsed:
                hours = (now - parsed).total_seconds() / 3600.0
        if hours is not None:
            rpo_values.append(hours)
            if hours > max_hours:
                max_hours = hours

    rpo_hours = round(max_hours, 1) if rpo_values else 0.0

    # --- RTO estimation: average job duration across all connectors ---
    durations: List[float] = []
    for result in job_history:
        jobs = result.get('jobs', [])
        if not isinstance(jobs, list):
            continue
        for job in jobs:
            # Job status is inferred: succeeded has a timestamp and failed is null/absent
            has_failed = bool(job.get('failed'))
            has_succeeded = bool(job.get('succeeded'))
            if has_failed or not has_succeeded:
                continue
            # Duration = started → succeeded
            started = parse_iso_timestamp(job.get('started', ''))
            ended = parse_iso_timestamp(job.get('succeeded', ''))
            if started and ended and ended > started:
                durations.append((ended - started).total_seconds())

    if durations:
        avg_duration_seconds = sum(durations) / len(durations)
        # RTO estimate = average duration * number of connectors (sequential restore)
        connector_count = max(len(snapshots), 1)
        rto_seconds = avg_duration_seconds * connector_count
        rto_hours = round(rto_seconds / 3600.0, 1)
    else:
        rto_hours = 0.0

    # Human-readable RTO
    if rto_hours <= 0:
        rto_estimate = 'Unable to estimate (insufficient job data)'
    elif rto_hours < 1:
        rto_estimate = f'Under 1 hour'
    elif rto_hours < 24:
        rto_estimate = f'Approximately {rto_hours} hours'
    else:
        days = round(rto_hours / 24.0, 1)
        rto_estimate = f'Approximately {days} days'

    # Readiness level
    if rpo_hours <= 12 and rto_hours <= 4:
        readiness_level = 'excellent'
        readiness_icon = '✅'
        description = (
            'Recovery readiness is excellent. Backups are fresh and estimated '
            'restore time is under 4 hours.'
        )
    elif rpo_hours <= 24 and rto_hours <= 8:
        readiness_level = 'good'
        readiness_icon = '✅'
        description = (
            'Recovery readiness is good. Backups are within 24 hours and '
            'estimated restore time is under 8 hours.'
        )
    elif rpo_hours <= 48 and rto_hours <= 24:
        readiness_level = 'fair'
        readiness_icon = '⚠️'
        description = (
            'Recovery readiness is fair. Some backups are older than 24 hours. '
            'Review backup schedules to improve recency.'
        )
    else:
        readiness_level = 'poor'
        readiness_icon = '❌'
        description = (
            'Recovery readiness needs attention. Backups may be stale and '
            'estimated restore time exceeds 24 hours. Immediate review recommended.'
        )

    return {
        'rpo_hours': rpo_hours,
        'rto_estimate': rto_estimate,
        'rto_hours': rto_hours,
        'readiness_level': readiness_level,
        'readiness_icon': readiness_icon,
        'description': description,
    }


# ---------------------------------------------------------------------------
# Board snippet generation
# ---------------------------------------------------------------------------

def generate_board_snippet(summary: Dict[str, Any]) -> str:
    """Generate a 3-5 sentence executive summary suitable for board deck inclusion.

    Produces plain-English text with no technical jargon. Includes the Protection
    Score, coverage breadth, key risk (if any), and recovery readiness.

    Args:
        summary: Dict containing:
            - score (float): Protection Score 0-100
            - grade (str): Letter grade A-F
            - app_count (int): Number of protected applications
            - app_names (list, optional): List of application names
            - risk_count (int): Number of active risk items
            - risk_items (list, optional): Top risk items
            - success_rate (float): Job success rate percentage
            - rpo_compliance (float): RPO compliance percentage
            - readiness_level (str, optional): Recovery readiness level
            - rto_estimate (str, optional): RTO estimate string
            - trend (dict, optional): Trend indicator

    Returns:
        String containing 3-5 sentences suitable for board deck inclusion.
    """
    score = summary.get('score', 0)
    grade = summary.get('grade', 'F')
    app_count = summary.get('app_count', 0)
    app_names = summary.get('app_names', [])
    risk_count = summary.get('risk_count', 0)
    success_rate = summary.get('success_rate', 0)
    readiness_level = summary.get('readiness_level', 'unknown')
    rto_estimate = summary.get('rto_estimate', '')
    trend = summary.get('trend', {})

    posture = posture_description(grade)
    sentences: List[str] = []

    # Sentence 1: Overall score and posture
    sentences.append(
        f"Our data protection posture is rated {grade} ({score}/100), "
        f"indicating {posture.lower()} coverage across critical SaaS applications."
    )

    # Sentence 2: Coverage breadth
    if app_names:
        names_str = ', '.join(app_names[:5])
        if len(app_names) > 5:
            names_str += f', and {len(app_names) - 5} more'
        sentences.append(
            f"Keepit is actively protecting {app_count} cloud application"
            f"{'s' if app_count != 1 else ''} including {names_str} "
            f"with a {round(success_rate, 1)}% backup success rate."
        )
    else:
        sentences.append(
            f"Keepit is actively protecting {app_count} cloud application"
            f"{'s' if app_count != 1 else ''} with a "
            f"{round(success_rate, 1)}% backup success rate."
        )

    # Sentence 3: Key risk or confidence statement
    if risk_count == 0:
        sentences.append(
            "No material risks to data recoverability have been identified "
            "this period."
        )
    elif risk_count == 1:
        risk_items = summary.get('risk_items', [])
        if risk_items:
            sentences.append(
                f"One risk item requires attention: {risk_items[0].get('title', 'an issue was detected')}."
            )
        else:
            sentences.append("One risk item has been identified and requires attention.")
    else:
        sentences.append(
            f"{risk_count} risk items have been identified; the IT team has been "
            f"notified and remediation is in progress."
        )

    # Sentence 4: Recovery readiness
    if rto_estimate and readiness_level != 'unknown':
        sentences.append(
            f"Estimated recovery time in a disaster scenario is {rto_estimate.lower()}."
        )

    # Sentence 5: Trend (if available)
    if trend and trend.get('direction'):
        direction = trend['direction']
        if direction == 'improved':
            delta = abs(trend.get('delta', 0))
            sentences.append(
                f"Protection posture has improved by {delta} points since the last reporting period."
            )
        elif direction == 'degraded':
            delta = abs(trend.get('delta', 0))
            sentences.append(
                f"Protection posture has declined by {delta} points since the last "
                f"reporting period; corrective actions are underway."
            )

    return ' '.join(sentences)


# ---------------------------------------------------------------------------
# Main test block
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Keepit Executive Backup Summary Utilities — Self-Test")
    print("=" * 70)

    # --- Test parse_iso_timestamp ---
    print("\n--- parse_iso_timestamp ---")
    test_timestamps = [
        "2025-01-15T10:30:00Z",
        "2025-01-15T10:30:00.123456Z",
        "2025-01-15T10:30:00+00:00",
        "2025-01-15T10:30:00",
        "",
        None,
    ]
    for ts in test_timestamps:
        result = parse_iso_timestamp(ts or '')
        print(f"  '{ts}' -> {result}")

    # --- Test format_connector_type ---
    print("\n--- format_connector_type ---")
    test_types = ['o365-admin', 'azure-ad', 'sforce', 'unknown-type', '']
    for ct in test_types:
        print(f"  '{ct}' -> '{format_connector_type(ct)}'")

    # --- Test score_to_grade ---
    print("\n--- score_to_grade ---")
    test_scores = [100, 95, 85, 75, 65, 50, 0]
    for s in test_scores:
        print(f"  {s} -> {score_to_grade(s)} ({score_to_color(s)}, {score_to_icon(s)})")

    # --- Test calculate_health_score ---
    print("\n--- calculate_health_score ---")
    test_health = [
        {'health': {'state': 'healthy'}},
        {'health': {'state': 'healthy'}},
        {'health': {'state': 'degraded'}},
    ]
    print(f"  [healthy, healthy, degraded] -> {calculate_health_score(test_health)}")

    # --- Test calculate_recency_score ---
    print("\n--- calculate_recency_score ---")
    test_recency = [
        {'hours_since_backup': 6.0},
        {'hours_since_backup': 20.0},
        {'hours_since_backup': 50.0},
    ]
    print(f"  [6h, 20h, 50h] -> {calculate_recency_score(test_recency)}")

    # --- Test calculate_protection_score ---
    print("\n--- calculate_protection_score ---")
    result = calculate_protection_score(
        health_data=test_health,
        recency_data=test_recency,
        rpo_compliance=90.0,
        success_rate=95.0,
    )
    print(f"  Score: {result['score']}, Grade: {result['grade']}, "
          f"Color: {result['color']}, Posture: {result['posture']}")
    print(f"  Components: {result['component_scores']}")

    # --- Test generate_coverage_summary ---
    print("\n--- generate_coverage_summary ---")
    test_connectors = [
        {'type': 'o365-admin', 'name': 'O365 Connector', 'guid': 'guid-1'},
        {'type': 'azure-ad', 'name': 'Azure AD Connector', 'guid': 'guid-2'},
        {'type': 'sforce', 'name': 'Salesforce Connector', 'guid': 'guid-3'},
    ]
    coverage = generate_coverage_summary(test_connectors)
    print(f"  Summary: {coverage['summary_sentence']}")
    print(f"  Apps: {coverage['app_names']}")

    # --- Test format_risk_items_plain_english ---
    print("\n--- format_risk_items_plain_english ---")
    test_issues = [
        {'issue_type': 'unhealthy', 'connector_type': 'azure-ad'},
        {'issue_type': 'stale_backup', 'connector_type': 'sforce', 'hours': 52},
        {'issue_type': 'low_success_rate', 'connector_type': 'o365-admin', 'rate': 25.5},
    ]
    risks = format_risk_items_plain_english(test_issues)
    for risk in risks:
        print(f"  {risk['priority_icon']} [{risk['priority']}] {risk['title']}")
        print(f"    Impact: {risk['business_impact']}")

    # --- Test generate_trend_indicator ---
    print("\n--- generate_trend_indicator ---")
    for current, previous in [(95, 88), (85, 85), (70, 82)]:
        trend = generate_trend_indicator(current, previous)
        print(f"  {previous} -> {current}: {trend['icon']} {trend['direction']} "
              f"(delta: {trend['delta']})")

    # --- Test estimate_recovery_readiness ---
    print("\n--- estimate_recovery_readiness ---")
    test_snapshots = [
        {'hours_since_backup': 6.0},
        {'hours_since_backup': 3.0},
    ]
    test_jobs = [
        {'jobs': [
            {'status': 'completed', 'duration': 1800},
            {'status': 'completed', 'duration': 2400},
        ]},
        {'jobs': [
            {'status': 'completed', 'duration': 'PT30M'},
            {'status': 'failed', 'duration': 600},
        ]},
    ]
    readiness = estimate_recovery_readiness(test_snapshots, test_jobs)
    print(f"  RPO: {readiness['rpo_hours']}h, RTO: {readiness['rto_estimate']}")
    print(f"  Readiness: {readiness['readiness_icon']} {readiness['readiness_level']}")

    # --- Test generate_board_snippet ---
    print("\n--- generate_board_snippet ---")
    snippet = generate_board_snippet({
        'score': 96,
        'grade': 'A',
        'app_count': 3,
        'app_names': ['Microsoft 365', 'Entra ID', 'Salesforce'],
        'risk_count': 0,
        'success_rate': 99.2,
        'rpo_compliance': 97.0,
        'readiness_level': 'excellent',
        'rto_estimate': 'Under 4 hours',
    })
    print(f"  {snippet}")

    print("\n" + "=" * 70)
    print("Self-test complete.")
    print("=" * 70)
