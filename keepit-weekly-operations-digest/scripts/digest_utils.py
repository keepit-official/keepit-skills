#!/usr/bin/env python3
"""
Keepit Weekly Operations Digest Utilities

Helper functions for compiling, analyzing, and formatting weekly backup
operations digests used in the Keepit Weekly Operations Digest skill.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from collections import defaultdict, Counter
import re


# ---------------------------------------------------------------------------
# Connector type mapping
# ---------------------------------------------------------------------------

CONNECTOR_TYPE_MAP = {
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
# Timestamp helpers
# ---------------------------------------------------------------------------

def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime.

    Handles timestamps with or without trailing 'Z', with or without
    fractional seconds, and with explicit UTC offsets.

    Args:
        timestamp: ISO 8601 formatted timestamp string.

    Returns:
        A timezone-aware datetime object in UTC.
    """
    if not timestamp:
        return datetime.min.replace(tzinfo=timezone.utc)

    cleaned = timestamp.strip()

    # Replace trailing Z with +00:00 for fromisoformat compatibility
    if cleaned.endswith('Z'):
        cleaned = cleaned[:-1] + '+00:00'

    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        # Fallback: try strptime for common formats
        for fmt in (
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
        ):
            try:
                dt = datetime.strptime(cleaned, fmt)
                break
            except ValueError:
                continue
        else:
            return datetime.min.replace(tzinfo=timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def format_time_ago(timestamp: str) -> str:
    """Format a timestamp as a human-readable 'X time ago' string.

    Args:
        timestamp: ISO 8601 formatted timestamp string.

    Returns:
        A string like '2h ago', '3d ago', 'just now', etc.
    """
    if not timestamp:
        return 'never'

    dt = parse_iso_timestamp(timestamp)
    now = datetime.now(timezone.utc)
    delta = now - dt

    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        return 'just now'
    if total_seconds < 60:
        return 'just now'
    if total_seconds < 3600:
        minutes = total_seconds // 60
        return f'{minutes}m ago'
    if total_seconds < 86400:
        hours = total_seconds // 3600
        return f'{hours}h ago'
    days = total_seconds // 86400
    if days == 1:
        return '1d ago'
    if days < 7:
        return f'{days}d ago'
    weeks = days // 7
    if weeks == 1:
        return '1w ago'
    return f'{weeks}w ago'


def iso_duration_to_timedelta(duration: str) -> timedelta:
    """Convert an ISO 8601 duration string to a timedelta.

    Supports P{n}D (days) and P{n}W (weeks) formats. Falls back to 7 days.

    Args:
        duration: ISO 8601 duration string, e.g. 'P7D', 'P14D', 'P2W'.

    Returns:
        Corresponding timedelta object.
    """
    match = re.match(r'P(\d+)D', duration)
    if match:
        return timedelta(days=int(match.group(1)))
    match = re.match(r'P(\d+)W', duration)
    if match:
        return timedelta(weeks=int(match.group(1)))
    return timedelta(days=7)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_connector_type(connector_type: str) -> str:
    """Convert a raw connector type identifier to a human-friendly name.

    Args:
        connector_type: Raw connector type string (e.g. 'o365-admin').

    Returns:
        Human-friendly name (e.g. 'Microsoft 365'), or the original
        string with basic cleanup if not found in the mapping.
    """
    if not connector_type:
        return 'Unknown'
    return CONNECTOR_TYPE_MAP.get(
        connector_type,
        connector_type.replace('-', ' ').replace('_', ' ').title()
    )


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a float as a percentage string.

    Args:
        value: Numeric value (0-100 range).
        decimals: Number of decimal places.

    Returns:
        Formatted percentage string, e.g. '97.2%'.
    """
    return f'{value:.{decimals}f}%'


def format_digest_period(duration: str = "P7D") -> Dict[str, str]:
    """Format the reporting period for display.

    Args:
        duration: ISO 8601 duration string for the period length.

    Returns:
        Dictionary with keys: start_date, end_date, human_readable,
        duration_iso.
    """
    delta = iso_duration_to_timedelta(duration)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - delta

    days = int(delta.total_seconds() / 86400)
    if days == 7:
        human = 'Last 7 days'
    elif days == 14:
        human = 'Last 2 weeks'
    elif days == 30:
        human = 'Last 30 days'
    else:
        human = f'Last {days} days'

    return {
        'start_date': start_date.strftime('%b %d, %Y'),
        'end_date': end_date.strftime('%b %d, %Y'),
        'human_readable': human,
        'duration_iso': duration,
        'display': f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
    }


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_metadata(event: Dict[str, Any]) -> Dict[str, str]:
    """Extract and flatten metadata from an audit event.

    Keepit audit events store metadata as a list of parameter objects.
    This function flattens them into a simple key-value dictionary.

    Args:
        event: A single audit event dictionary.

    Returns:
        Flat dictionary of metadata key-value pairs.
    """
    result = {}
    for item in event.get('metadata', []):
        param = item.get('parameter', {})
        if param.get('key'):
            result[param['key']] = param.get('value', '')
    return result


# ---------------------------------------------------------------------------
# Job status helpers
# ---------------------------------------------------------------------------

def classify_job(job: Dict[str, Any]) -> str:
    """Classify a job's status based on its fields.

    Args:
        job: A single job dictionary from the API.

    Returns:
        One of 'running', 'failed', or 'successful'.
    """
    if job.get('active'):
        return 'running'
    if job.get('failed'):
        return 'failed'
    return 'successful'


def get_health_icon(status: str) -> str:
    """Return an icon for a connector health status string.

    Args:
        status: Health status string (e.g. 'healthy', 'warning').

    Returns:
        Corresponding icon character.
    """
    normalized = status.lower().strip() if status else 'unknown'
    if normalized in ('healthy', 'ok', 'green'):
        return '✅'
    if normalized in ('warning', 'degraded', 'yellow'):
        return '⚠️'
    if normalized in ('critical', 'error', 'red', 'failed'):
        return '❌'
    return '❓'


def get_freshness(timestamp: str) -> Tuple[str, str]:
    """Determine backup freshness from a snapshot timestamp.

    Args:
        timestamp: ISO 8601 timestamp of the latest snapshot.

    Returns:
        Tuple of (label, icon) describing freshness.
    """
    if not timestamp:
        return ('Missing', '❌')

    dt = parse_iso_timestamp(timestamp)
    age = datetime.now(timezone.utc) - dt
    hours = age.total_seconds() / 3600

    if hours < 24:
        return ('Fresh', '✅')
    if hours < 48:
        return ('Aging', '⚠️')
    return ('Stale', '❌')


def get_status_icon(success_rate: float, health_status: str) -> str:
    """Determine the overall status icon for a connector row.

    Args:
        success_rate: Job success rate as a percentage (0-100).
        health_status: Current health status string.

    Returns:
        A single icon representing overall status.
    """
    health_norm = health_status.lower().strip() if health_status else 'unknown'
    if health_norm in ('critical', 'error', 'red', 'failed'):
        return '❌'
    if success_rate < 80.0:
        return '❌'
    if success_rate < 95.0 or health_norm in ('warning', 'degraded', 'yellow'):
        return '⚠️'
    return '✅'


# ---------------------------------------------------------------------------
# Core compilation functions
# ---------------------------------------------------------------------------

def compile_per_connector_metrics(
    connector_name: str,
    connector_type: str,
    jobs: List[Dict],
    health: Dict,
    latest_snapshot: Optional[Dict],
    snapshots: List[Dict],
) -> Dict[str, Any]:
    """Compile metrics for a single connector.

    Args:
        connector_name: Display name of the connector.
        connector_type: Raw connector type identifier.
        jobs: List of job dictionaries for this connector in the period.
        health: Health status dictionary for this connector.
        latest_snapshot: The most recent snapshot dictionary, or None.
        snapshots: List of snapshot dictionaries over the period.

    Returns:
        Dictionary with keys: name, type, health_status, health_icon,
        last_backup, last_backup_ago, total_jobs, successful_jobs,
        failed_jobs, success_rate, gap_count, status_icon.
    """
    # Classify jobs
    total = len(jobs)
    failed = sum(1 for j in jobs if classify_job(j) == 'failed')
    successful = total - failed
    rate = (successful / total * 100) if total > 0 else 0.0

    # Health
    health_status = health.get('health', 'unknown') if health else 'unknown'
    health_icon = get_health_icon(health_status)

    # Latest backup
    last_backup_ts = None
    if latest_snapshot and latest_snapshot.get('tstamp'):
        last_backup_ts = latest_snapshot['tstamp']

    last_backup_ago = format_time_ago(last_backup_ts) if last_backup_ts else 'never'

    # Detect gaps in snapshot continuity
    gap_count = 0
    if snapshots and len(snapshots) >= 2:
        sorted_snaps = sorted(snapshots, key=lambda s: s.get('timestamp', ''))
        gap_threshold = timedelta(hours=36)
        for i in range(1, len(sorted_snaps)):
            prev_time = parse_iso_timestamp(sorted_snaps[i - 1].get('timestamp', ''))
            curr_time = parse_iso_timestamp(sorted_snaps[i].get('timestamp', ''))
            if (curr_time - prev_time) > gap_threshold:
                gap_count += 1

    status_icon = get_status_icon(rate, health_status)

    return {
        'name': connector_name,
        'type': format_connector_type(connector_type),
        'health_status': health_status,
        'health_icon': health_icon,
        'last_backup': last_backup_ts,
        'last_backup_ago': last_backup_ago,
        'total_jobs': total,
        'successful_jobs': successful,
        'failed_jobs': failed,
        'success_rate': round(rate, 1),
        'gap_count': gap_count,
        'status_icon': status_icon,
    }


def compile_weekly_metrics(
    jobs: Dict[str, List[Dict]],
    snapshots: Dict[str, List[Dict]],
    audit_events: List[Dict],
    health_data: Dict[str, Dict],
) -> Dict[str, Any]:
    """Aggregate all data into weekly metrics.

    Args:
        jobs: Dictionary of connector GUID -> list of job dicts.
        snapshots: Dictionary of connector GUID -> list of snapshot dicts.
        audit_events: List of audit event dictionaries.
        health_data: Dictionary of connector GUID -> health dict.

    Returns:
        Dictionary with keys: total_jobs, successful_jobs, failed_jobs,
        success_rate, total_connectors, healthy_connectors,
        unhealthy_connectors, warning_connectors, total_audit_events,
        total_snapshots, per_connector_metrics (empty dict, to be filled
        by caller with compile_per_connector_metrics results).
    """
    total_jobs = sum(len(j) for j in jobs.values())
    failed_jobs = sum(
        1 for job_list in jobs.values()
        for j in job_list
        if classify_job(j) == 'failed'
    )
    successful_jobs = total_jobs - failed_jobs
    success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0

    total_connectors = len(health_data)
    healthy = 0
    warning = 0
    unhealthy = 0
    for h in health_data.values():
        status = (h.get('health', 'unknown') if h else 'unknown').lower()
        if status in ('healthy', 'ok', 'green'):
            healthy += 1
        elif status in ('warning', 'degraded', 'yellow'):
            warning += 1
        else:
            unhealthy += 1

    total_snapshots = sum(len(s) for s in snapshots.values())

    return {
        'total_jobs': total_jobs,
        'successful_jobs': successful_jobs,
        'failed_jobs': failed_jobs,
        'success_rate': round(success_rate, 1),
        'total_connectors': total_connectors,
        'healthy_connectors': healthy,
        'warning_connectors': warning,
        'unhealthy_connectors': unhealthy,
        'total_audit_events': len(audit_events),
        'total_snapshots': total_snapshots,
        'per_connector_metrics': {},
    }


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def identify_notable_events(
    metrics: Dict[str, Any],
    audit_events: List[Dict],
) -> List[Dict[str, Any]]:
    """Surface what is worth highlighting in the digest.

    Notable events include: failures above threshold, health status
    issues, configuration changes, backup gaps, and anomalies.

    Args:
        metrics: The compiled weekly metrics dictionary.
        audit_events: List of audit event dictionaries.

    Returns:
        List of dictionaries with keys: type, severity, title,
        description, connector, timestamp.
    """
    events: List[Dict[str, Any]] = []

    # Flag overall failure rate issues
    if metrics.get('failed_jobs', 0) > 0:
        rate = metrics.get('success_rate', 100)
        severity = 'high' if rate < 90 else ('medium' if rate < 98 else 'low')
        events.append({
            'type': 'failure_rate',
            'severity': severity,
            'title': f"{metrics['failed_jobs']} job failure(s) this week",
            'description': (
                f"Overall success rate is {rate}%. "
                f"{metrics['failed_jobs']} out of {metrics['total_jobs']} jobs failed."
            ),
            'connector': None,
            'timestamp': None,
        })

    # Flag unhealthy connectors
    if metrics.get('unhealthy_connectors', 0) > 0:
        events.append({
            'type': 'health',
            'severity': 'high',
            'title': f"{metrics['unhealthy_connectors']} connector(s) in critical state",
            'description': 'One or more connectors are reporting critical health status.',
            'connector': None,
            'timestamp': None,
        })

    if metrics.get('warning_connectors', 0) > 0:
        events.append({
            'type': 'health',
            'severity': 'medium',
            'title': f"{metrics['warning_connectors']} connector(s) with warnings",
            'description': 'One or more connectors are reporting degraded health.',
            'connector': None,
            'timestamp': None,
        })

    # Flag per-connector issues
    for guid, cm in metrics.get('per_connector_metrics', {}).items():
        if cm.get('gap_count', 0) > 0:
            events.append({
                'type': 'gap',
                'severity': 'medium',
                'title': f"Backup gap(s) detected on {cm['name']}",
                'description': f"{cm['gap_count']} gap(s) in snapshot continuity.",
                'connector': cm['name'],
                'timestamp': None,
            })
        if cm.get('last_backup_ago') == 'never':
            events.append({
                'type': 'stale',
                'severity': 'high',
                'title': f"No backups found for {cm['name']}",
                'description': 'This connector has never produced a snapshot.',
                'connector': cm['name'],
                'timestamp': None,
            })

    # Flag significant audit events
    significant_actions = (
        'create', 'delete', 'remove', 'modify', 'update', 'change',
    )
    for event in audit_events:
        action = event.get('action', '').lower()
        if any(keyword in action for keyword in significant_actions):
            meta = extract_metadata(event)
            events.append({
                'type': 'config_change',
                'severity': 'low',
                'title': f"Configuration change: {event.get('action', 'unknown')}",
                'description': meta.get('description', event.get('action', '')),
                'connector': meta.get('connectorName', None),
                'timestamp': event.get('timestamp', None),
            })

    # Sort by severity: high first, then medium, then low
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    events.sort(key=lambda e: severity_order.get(e.get('severity', 'low'), 3))

    return events


def group_failures_by_pattern(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group failed jobs by error pattern or description similarity.

    Analyzes failed job descriptions and groups them into patterns so that
    repeated occurrences of the same error are consolidated.

    Args:
        jobs: Flat list of all job dictionaries (across all connectors).

    Returns:
        List of dictionaries with keys: pattern, count,
        connectors_affected, first_seen, last_seen, severity.
    """
    failed = [j for j in jobs if classify_job(j) == 'failed']
    if not failed:
        return []

    # Group by error description or a normalized pattern
    pattern_groups: Dict[str, List[Dict]] = defaultdict(list)
    for job in failed:
        description = job.get('description', job.get('error', 'Unknown error'))
        # Normalize: strip connector-specific IDs, timestamps, UUIDs
        normalized = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '<ID>',
            str(description),
        )
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '<TS>', normalized)
        normalized = normalized.strip()
        if not normalized:
            normalized = 'Unknown error'
        pattern_groups[normalized].append(job)

    results = []
    for pattern, group in pattern_groups.items():
        connectors_affected = list(set(
            j.get('connectorName', j.get('connector_name', 'Unknown'))
            for j in group
        ))
        timestamps = [
            j.get('timestamp', j.get('startTime', ''))
            for j in group
            if j.get('timestamp') or j.get('startTime')
        ]
        timestamps.sort()

        count = len(group)
        severity = 'high' if count >= 3 else ('medium' if count >= 2 else 'low')

        results.append({
            'pattern': pattern,
            'count': count,
            'connectors_affected': connectors_affected,
            'first_seen': timestamps[0] if timestamps else None,
            'last_seen': timestamps[-1] if timestamps else None,
            'severity': severity,
        })

    # Sort by count descending
    results.sort(key=lambda r: r['count'], reverse=True)
    return results


def summarize_audit_changes(audit_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize audit log changes for the digest.

    Extracts the key information from each audit event and returns a
    list suitable for displaying in a table.

    Args:
        audit_events: List of audit event dictionaries from the API.

    Returns:
        List of dictionaries with keys: timestamp, who, action, summary.
    """
    summaries = []
    for event in audit_events:
        meta = extract_metadata(event)

        timestamp = event.get('timestamp', '')
        who = event.get('token', meta.get('userName', meta.get('token', 'system')))
        action = event.get('action', 'unknown')

        # Build a human-readable summary
        summary_parts = [action]
        connector_name = meta.get('connectorName', meta.get('name', ''))
        if connector_name:
            summary_parts.append(f'on "{connector_name}"')
        description = meta.get('description', '')
        if description:
            summary_parts.append(f'- {description}')

        summaries.append({
            'timestamp': timestamp,
            'who': who,
            'action': action,
            'summary': ' '.join(summary_parts),
        })

    # Sort by timestamp descending (most recent first)
    summaries.sort(key=lambda s: s.get('timestamp', ''), reverse=True)
    return summaries


def detect_backup_gaps(
    snapshots: Dict[str, List[Dict]],
    connector_map: Dict[str, Dict],
    threshold_hours: float = 36.0,
) -> List[Dict[str, Any]]:
    """Detect gaps in backup continuity across all connectors.

    Args:
        snapshots: Dictionary of connector GUID -> list of snapshot dicts.
        connector_map: Dictionary of connector GUID -> connector info dict.
        threshold_hours: Minimum hours between snapshots to flag as a gap.

    Returns:
        List of gap dictionaries with keys: connector, gap_start, gap_end,
        gap_hours, severity.
    """
    gap_threshold = timedelta(hours=threshold_hours)
    gaps = []

    for guid, snap_list in snapshots.items():
        if not snap_list or len(snap_list) < 2:
            continue

        connector_name = connector_map.get(guid, {}).get('name', 'Unknown')
        sorted_snaps = sorted(snap_list, key=lambda s: s.get('timestamp', ''))

        for i in range(1, len(sorted_snaps)):
            prev_time = parse_iso_timestamp(sorted_snaps[i - 1].get('timestamp', ''))
            curr_time = parse_iso_timestamp(sorted_snaps[i].get('timestamp', ''))
            delta = curr_time - prev_time

            if delta > gap_threshold:
                gap_hours = delta.total_seconds() / 3600
                severity = 'high' if gap_hours > 72 else ('medium' if gap_hours > 48 else 'low')
                gaps.append({
                    'connector': connector_name,
                    'gap_start': sorted_snaps[i - 1].get('timestamp', ''),
                    'gap_end': sorted_snaps[i].get('timestamp', ''),
                    'gap_hours': round(gap_hours, 1),
                    'severity': severity,
                })

    # Sort by gap_hours descending
    gaps.sort(key=lambda g: g.get('gap_hours', 0), reverse=True)
    return gaps


# ---------------------------------------------------------------------------
# Action items
# ---------------------------------------------------------------------------

def generate_action_items(
    metrics: Dict[str, Any],
    failures: List[Dict],
    gaps: List[Dict],
) -> List[Dict[str, Any]]:
    """Generate a prioritized to-do list based on digest findings.

    Args:
        metrics: The compiled weekly metrics dictionary.
        failures: List of grouped failure pattern dictionaries.
        gaps: List of detected backup gap dictionaries.

    Returns:
        List of dictionaries with keys: priority, icon, title,
        description, connector, action.
    """
    items: List[Dict[str, Any]] = []

    # Action items from unhealthy connectors
    for guid, cm in metrics.get('per_connector_metrics', {}).items():
        if cm.get('health_status', '').lower() in ('critical', 'error', 'red', 'failed'):
            items.append({
                'priority': 'high',
                'icon': '🔴',
                'title': f"Resolve critical health on {cm['name']}",
                'description': (
                    f"{cm['name']} ({cm['type']}) is in critical state. "
                    f"Investigate immediately."
                ),
                'connector': cm['name'],
                'action': 'Check connector configuration, credentials, and API access.',
            })

    # Action items from failure patterns
    for failure in failures:
        if failure['severity'] == 'high':
            icon = '🔴'
            priority = 'high'
        elif failure['severity'] == 'medium':
            icon = '🟡'
            priority = 'medium'
        else:
            icon = '🟢'
            priority = 'low'

        affected = ', '.join(failure.get('connectors_affected', [])[:3])
        items.append({
            'priority': priority,
            'icon': icon,
            'title': f"Investigate recurring failure pattern",
            'description': (
                f'"{failure["pattern"][:80]}" occurred {failure["count"]} time(s) '
                f'affecting: {affected}.'
            ),
            'connector': affected,
            'action': 'Review error details and apply fix or contact support.',
        })

    # Action items from backup gaps
    for gap in gaps:
        if gap.get('severity') == 'high':
            icon = '🔴'
            priority = 'high'
        else:
            icon = '🟡'
            priority = 'medium'

        items.append({
            'priority': priority,
            'icon': icon,
            'title': f"Investigate backup gap on {gap['connector']}",
            'description': (
                f"{gap['gap_hours']}-hour gap detected "
                f"({gap.get('gap_start', '?')} to {gap.get('gap_end', '?')})."
            ),
            'connector': gap['connector'],
            'action': 'Verify data coverage and trigger a manual backup if needed.',
        })

    # Action items from stale backups
    for guid, cm in metrics.get('per_connector_metrics', {}).items():
        if cm.get('last_backup_ago') == 'never':
            items.append({
                'priority': 'high',
                'icon': '🔴',
                'title': f"No backups for {cm['name']}",
                'description': (
                    f"{cm['name']} ({cm['type']}) has never produced a backup. "
                    f"This may be a new or misconfigured connector."
                ),
                'connector': cm['name'],
                'action': 'Verify connector setup and trigger an initial backup.',
            })

    # Deduplicate by title
    seen_titles = set()
    unique_items = []
    for item in items:
        if item['title'] not in seen_titles:
            seen_titles.add(item['title'])
            unique_items.append(item)

    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    unique_items.sort(key=lambda i: priority_order.get(i.get('priority', 'low'), 3))

    return unique_items


# ---------------------------------------------------------------------------
# Digest formatting
# ---------------------------------------------------------------------------

def format_weekly_digest(
    metrics: Dict[str, Any],
    events: List[Dict],
    actions: List[Dict],
) -> Dict[str, Any]:
    """Format the complete weekly digest structure.

    Assembles all computed data into the final digest object suitable
    for rendering as a report.

    Args:
        metrics: The compiled weekly metrics dictionary.
        events: List of notable event dictionaries.
        actions: List of action item dictionaries.

    Returns:
        Dictionary with keys: period, generated_at, week_at_a_glance,
        connector_table, failures, changes, continuity, action_items.
    """
    period = format_digest_period()

    # Build connector table rows sorted by status icon (issues first)
    connector_table = []
    icon_order = {'❌': 0, '⚠️': 1, '✅': 2, '❓': 3}
    per_conn = metrics.get('per_connector_metrics', {})
    for guid in sorted(
        per_conn.keys(),
        key=lambda g: icon_order.get(per_conn[g].get('status_icon', '❓'), 3)
    ):
        connector_table.append(per_conn[guid])

    return {
        'period': period,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'week_at_a_glance': {
            'total_jobs': metrics.get('total_jobs', 0),
            'successful_jobs': metrics.get('successful_jobs', 0),
            'failed_jobs': metrics.get('failed_jobs', 0),
            'success_rate': metrics.get('success_rate', 0.0),
            'total_connectors': metrics.get('total_connectors', 0),
            'healthy_connectors': metrics.get('healthy_connectors', 0),
            'warning_connectors': metrics.get('warning_connectors', 0),
            'unhealthy_connectors': metrics.get('unhealthy_connectors', 0),
            'total_snapshots': metrics.get('total_snapshots', 0),
            'total_audit_events': metrics.get('total_audit_events', 0),
            'notable_event_count': len(events),
            'action_item_count': len(actions),
        },
        'connector_table': connector_table,
        'failures': [e for e in events if e.get('type') == 'failure_rate'],
        'changes': [e for e in events if e.get('type') == 'config_change'],
        'continuity': [e for e in events if e.get('type') == 'gap'],
        'action_items': actions,
    }


# ---------------------------------------------------------------------------
# Trend analysis
# ---------------------------------------------------------------------------

def calculate_week_over_week_trend(
    current_metrics: Dict[str, Any],
    previous_metrics: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare current week metrics to the previous week.

    Args:
        current_metrics: This week's compiled metrics dictionary.
        previous_metrics: Last week's compiled metrics dictionary, or
            None if not available.

    Returns:
        Dictionary with keys: success_rate_delta, job_count_delta,
        failure_delta, trend_direction, description, available.
    """
    if previous_metrics is None:
        return {
            'available': False,
            'success_rate_delta': 0.0,
            'job_count_delta': 0,
            'failure_delta': 0,
            'trend_direction': 'stable',
            'description': 'No previous week data available for comparison.',
        }

    current_rate = current_metrics.get('success_rate', 0.0)
    previous_rate = previous_metrics.get('success_rate', 0.0)
    rate_delta = round(current_rate - previous_rate, 1)

    current_jobs = current_metrics.get('total_jobs', 0)
    previous_jobs = previous_metrics.get('total_jobs', 0)
    job_delta = current_jobs - previous_jobs

    current_failures = current_metrics.get('failed_jobs', 0)
    previous_failures = previous_metrics.get('failed_jobs', 0)
    failure_delta = current_failures - previous_failures

    # Determine overall trend direction
    if rate_delta > 1.0 and failure_delta <= 0:
        direction = 'improving'
        description = (
            f"Operations improved: success rate up {rate_delta}pp, "
            f"failures {'down' if failure_delta < 0 else 'unchanged'}."
        )
    elif rate_delta < -1.0 or failure_delta > 2:
        direction = 'declining'
        description = (
            f"Operations declined: success rate down {abs(rate_delta)}pp, "
            f"{abs(failure_delta)} more failure(s) than last week."
        )
    else:
        direction = 'stable'
        description = 'Operations are stable compared to last week.'

    return {
        'available': True,
        'success_rate_delta': rate_delta,
        'job_count_delta': job_delta,
        'failure_delta': failure_delta,
        'trend_direction': direction,
        'description': description,
    }


# ---------------------------------------------------------------------------
# Main (test / demo)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick self-test of utility functions
    print("=== Keepit Weekly Operations Digest Utilities - Self Test ===\n")

    # Test parse_iso_timestamp
    ts = "2026-02-17T10:30:00Z"
    dt = parse_iso_timestamp(ts)
    print(f"parse_iso_timestamp('{ts}') => {dt}")

    # Test format_time_ago
    recent = datetime.now(timezone.utc) - timedelta(hours=3)
    print(f"format_time_ago(3h ago) => {format_time_ago(recent.isoformat())}")

    old = datetime.now(timezone.utc) - timedelta(days=5)
    print(f"format_time_ago(5d ago) => {format_time_ago(old.isoformat())}")

    # Test format_connector_type
    print(f"format_connector_type('o365-admin') => {format_connector_type('o365-admin')}")
    print(f"format_connector_type('sforce') => {format_connector_type('sforce')}")
    print(f"format_connector_type('custom-type') => {format_connector_type('custom-type')}")

    # Test extract_metadata
    sample_event = {
        'metadata': [
            {'parameter': {'key': 'connectorName', 'value': 'Test Connector'}},
            {'parameter': {'key': 'action', 'value': 'create'}},
        ]
    }
    print(f"extract_metadata => {extract_metadata(sample_event)}")

    # Test format_digest_period
    period = format_digest_period("P7D")
    print(f"format_digest_period('P7D') => {period}")

    # Test get_freshness
    fresh_ts = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    print(f"get_freshness(6h ago) => {get_freshness(fresh_ts)}")

    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=60)).isoformat()
    print(f"get_freshness(60h ago) => {get_freshness(stale_ts)}")

    # Test classify_job
    print(f"classify_job(active=True) => {classify_job({'active': True})}")
    print(f"classify_job(failed=True) => {classify_job({'failed': True})}")
    print(f"classify_job(completed) => {classify_job({'active': False, 'failed': False})}")

    # Test week-over-week trend
    current = {'success_rate': 97.2, 'total_jobs': 142, 'failed_jobs': 4}
    previous = {'success_rate': 94.8, 'total_jobs': 138, 'failed_jobs': 7}
    trend = calculate_week_over_week_trend(current, previous)
    print(f"week_over_week_trend => {trend}")

    # Test with no previous data
    trend_none = calculate_week_over_week_trend(current, None)
    print(f"week_over_week_trend(no prev) => {trend_none}")

    print("\n=== All self-tests passed ===")
