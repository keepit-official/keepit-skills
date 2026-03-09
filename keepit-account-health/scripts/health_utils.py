#!/usr/bin/env python3
"""
Keepit Health Check Utilities

Helper functions for time calculations, formatting, and status assessment
used in the Keepit Account Health & Configuration Reporter skill.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple


def parse_iso_timestamp(timestamp: str) -> datetime:
    """
    Parse ISO 8601 timestamp to datetime object.
    
    Args:
        timestamp: ISO 8601 formatted timestamp (e.g., "2025-10-22T14:35:00Z")
    
    Returns:
        datetime object in UTC timezone
    """
    if timestamp.endswith('Z'):
        timestamp = timestamp.replace('Z', '+00:00')
    return datetime.fromisoformat(timestamp)


def time_since_now(timestamp: str) -> timedelta:
    """
    Calculate time difference between a timestamp and now.
    
    Args:
        timestamp: ISO 8601 formatted timestamp
    
    Returns:
        timedelta object representing time since timestamp
    """
    past_time = parse_iso_timestamp(timestamp)
    now = datetime.now(timezone.utc)
    return now - past_time


def format_time_ago(timestamp: str) -> str:
    """
    Format a timestamp as human-readable "X time ago" string.
    
    Args:
        timestamp: ISO 8601 formatted timestamp
    
    Returns:
        Human-readable string (e.g., "2 hours ago", "3 days ago")
    
    Examples:
        >>> format_time_ago("2025-10-22T12:35:00Z")  # If now is 14:35
        "2 hours ago"
    """
    delta = time_since_now(timestamp)
    
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


def assess_backup_recency(timestamp: Optional[str]) -> Tuple[str, str, str]:
    """
    Assess backup recency and return status, icon, and description.
    
    Args:
        timestamp: ISO 8601 formatted timestamp of last backup, or None
    
    Returns:
        Tuple of (status, icon, description)
        - status: "current", "acceptable", "stale", or "never"
        - icon: Emoji icon for visual status
        - description: Human-readable status description
    """
    if not timestamp:
        return ("never", "❌", "No backups yet")
    
    delta = time_since_now(timestamp)
    hours = delta.total_seconds() / 3600
    
    if hours < 24:
        return ("current", "✅", "Current")
    elif hours < 48:
        return ("acceptable", "⚠️", "Acceptable")
    elif hours < 168:  # 1 week
        return ("stale", "⚠️", "Stale")
    else:
        return ("critical", "❌", "Critical - Very stale")


def assess_connector_health(health_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Assess overall connector health and return status and icon.
    
    Args:
        health_data: Health data from get_connector_health
    
    Returns:
        Tuple of (status_text, icon)
    """
    # The API returns health as a string

    if not health_data:
        return ("Unknown", "❓")

    # The API returns a health string (e.g., "healthy", "unhealthy", "critical")
    health_status = health_data.get('health', 'unknown').lower()

    if health_status == 'critical':
        return ("Critical", "❌")
    elif health_status == 'unhealthy':
        return ("Unhealthy", "⚠️")
    elif health_status == 'healthy':
        return ("Healthy", "✅")
    else:
        return ("Unknown", "❓")


def format_connector_type(connector_type: str) -> str:
    """
    Format connector type into human-readable name.
    
    Args:
        connector_type: Raw connector type (e.g., "o365-admin", "azure-ad")
    
    Returns:
        Human-readable connector type name
    """
    type_map = {
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
    
    return type_map.get(connector_type, connector_type.replace('-', ' ').title())


def calculate_health_score(connectors_data: list) -> Dict[str, Any]:
    """
    Calculate overall health score based on connector data.
    
    Args:
        connectors_data: List of connector data with health and backup info
    
    Returns:
        Dictionary with health metrics
    """
    if not connectors_data:
        return {
            'total': 0,
            'healthy': 0,
            'warnings': 0,
            'critical': 0,
            'score': 0,
            'status': 'No connectors'
        }
    
    total = len(connectors_data)
    healthy = sum(1 for c in connectors_data if c.get('health_status') == 'Healthy')
    warnings = sum(1 for c in connectors_data if c.get('health_status') == 'Unhealthy')
    critical = sum(1 for c in connectors_data if c.get('health_status') == 'Critical')
    
    # Calculate percentage score
    score = int((healthy / total) * 100) if total > 0 else 0
    
    # Determine overall status
    if critical > 0:
        status = 'Critical Issues Detected'
    elif warnings > 0:
        status = 'Operational with Warnings'
    else:
        status = 'All Systems Healthy'
    
    return {
        'total': total,
        'healthy': healthy,
        'warnings': warnings,
        'critical': critical,
        'score': score,
        'status': status
    }


def generate_recommendations(health_score: Dict[str, Any], 
                            connectors_data: list) -> list:
    """
    Generate actionable recommendations based on health assessment.
    
    Args:
        health_score: Overall health metrics
        connectors_data: List of connector data with issues
    
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Critical issues
    if health_score['critical'] > 0:
        recommendations.append({
            'priority': 'immediate',
            'text': 'Address critical issues within 1 hour',
            'icon': '🔴'
        })
        recommendations.append({
            'priority': 'immediate',
            'text': 'Contact Keepit support for critical connector failures',
            'icon': '🔴'
        })
    
    # Warnings
    if health_score['warnings'] > 0:
        recommendations.append({
            'priority': 'soon',
            'text': 'Investigate warning-level issues within 24 hours',
            'icon': '🟡'
        })
        recommendations.append({
            'priority': 'soon',
            'text': 'Review connector health warnings in Keepit dashboard',
            'icon': '🟡'
        })
    
    # Stale backups
    stale_connectors = [c for c in connectors_data 
                       if c.get('backup_recency_status') in ['stale', 'critical']]
    if stale_connectors:
        recommendations.append({
            'priority': 'immediate',
            'text': f'Trigger manual backups for {len(stale_connectors)} stale connector(s)',
            'icon': '🔴'
        })
    
    # All healthy
    if health_score['critical'] == 0 and health_score['warnings'] == 0:
        recommendations.append({
            'priority': 'maintenance',
            'text': 'No immediate actions required - all systems healthy',
            'icon': '✅'
        })
        recommendations.append({
            'priority': 'maintenance',
            'text': 'Continue regular monitoring and schedule next health check',
            'icon': '✅'
        })
    
    return recommendations


def format_duration_iso8601(days: int = 0, hours: int = 0) -> str:
    """
    Format duration in ISO 8601 format for API calls.
    
    Args:
        days: Number of days
        hours: Number of hours
    
    Returns:
        ISO 8601 duration string (e.g., "P7D" for 7 days)
    """
    if days > 0:
        return f"P{days}D"
    elif hours > 0:
        return f"PT{hours}H"
    else:
        return "P1D"


def parse_retention_policy(iso_duration: Optional[str]) -> Dict[str, Any]:
    """
    Parse an ISO 8601 duration string for retention policy analysis.

    Handles formats like P7D (7 days), P1Y (1 year), P365D, P90D, etc.

    Args:
        iso_duration: ISO 8601 duration string from connector's backup_retention
                      field, or None if not set.

    Returns:
        Dictionary with:
        - raw: original string
        - days: approximate total days
        - human: human-readable string
        - set: whether a retention policy is configured
    """
    if not iso_duration:
        return {'raw': None, 'days': 0, 'human': 'Not configured', 'set': False}

    result = {'raw': iso_duration, 'days': 0, 'human': iso_duration, 'set': True}

    # Simple ISO 8601 duration parser for common patterns
    import re
    match = re.match(
        r'^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?'
        r'(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$',
        iso_duration
    )
    if not match:
        return result

    years = int(match.group(1) or 0)
    months = int(match.group(2) or 0)
    weeks = int(match.group(3) or 0)
    days = int(match.group(4) or 0)

    total_days = years * 365 + months * 30 + weeks * 7 + days
    result['days'] = total_days

    # Build human-readable string
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if weeks:
        parts.append(f"{weeks} week{'s' if weeks != 1 else ''}")
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if parts:
        result['human'] = ', '.join(parts)

    return result


def assess_retention_compliance(retention: Dict[str, Any],
                                min_days: int = 30) -> Tuple[str, str, str]:
    """
    Assess whether a connector's retention policy meets requirements.

    Args:
        retention: Output from parse_retention_policy()
        min_days: Minimum acceptable retention in days (default 30)

    Returns:
        Tuple of (status, icon, description):
        - status: 'compliant', 'short', 'not_set'
        - icon: visual indicator
        - description: human-readable assessment
    """
    if not retention['set']:
        return ('not_set', '❌', 'No retention policy configured')

    days = retention['days']
    if days >= min_days:
        return ('compliant', '✅', f"Retention: {retention['human']}")
    else:
        return (
            'short',
            '⚠️',
            f"Retention only {retention['human']} (minimum {min_days} days recommended)",
        )


def analyze_snapshot_gaps(snapshots: list, expected_interval_hours: float = 24.0) -> Dict[str, Any]:
    """
    Analyze a list of snapshots for backup gaps and continuity issues.

    Args:
        snapshots: List of snapshot dicts from get_snapshot_range, each with
                   'timestamp', 'type', 'size', and 'account' fields.
        expected_interval_hours: Expected interval between backups (default 24h).

    Returns:
        Dictionary with gap analysis results:
        - total_snapshots: count of snapshots analyzed
        - gaps: list of gap dicts with start, end, duration_hours
        - max_gap_hours: largest gap found
        - avg_interval_hours: average time between snapshots
        - continuity_status: 'good', 'warning', or 'critical'
        - partial_count: number of partial snapshots
        - complete_count: number of complete snapshots
    """
    if not snapshots:
        return {
            'total_snapshots': 0,
            'gaps': [],
            'max_gap_hours': 0,
            'avg_interval_hours': 0,
            'continuity_status': 'critical',
            'partial_count': 0,
            'complete_count': 0,
        }

    # Sort by timestamp ascending
    sorted_snaps = sorted(snapshots, key=lambda s: s.get('timestamp', ''))

    # Parse timestamps and count types
    timestamps = []
    partial_count = 0
    complete_count = 0
    for snap in sorted_snaps:
        ts = snap.get('timestamp')
        if ts:
            timestamps.append(parse_iso_timestamp(ts))
        snap_type = snap.get('type', '').lower()
        if snap_type == 'p':
            partial_count += 1
        elif snap_type == 'c':
            complete_count += 1

    # Detect gaps
    gaps = []
    intervals = []
    for i in range(1, len(timestamps)):
        delta = timestamps[i] - timestamps[i - 1]
        interval_hours = delta.total_seconds() / 3600
        intervals.append(interval_hours)
        if interval_hours > expected_interval_hours * 1.5:
            gaps.append({
                'start': timestamps[i - 1].isoformat(),
                'end': timestamps[i].isoformat(),
                'duration_hours': round(interval_hours, 1),
            })

    max_gap = max(intervals) if intervals else 0
    avg_interval = sum(intervals) / len(intervals) if intervals else 0

    # Determine continuity status
    if max_gap > expected_interval_hours * 3:
        continuity_status = 'critical'
    elif max_gap > expected_interval_hours * 1.5:
        continuity_status = 'warning'
    else:
        continuity_status = 'good'

    return {
        'total_snapshots': len(sorted_snaps),
        'gaps': gaps,
        'max_gap_hours': round(max_gap, 1),
        'avg_interval_hours': round(avg_interval, 1),
        'continuity_status': continuity_status,
        'partial_count': partial_count,
        'complete_count': complete_count,
    }


def analyze_snapshot_size_trend(snapshots: list) -> Dict[str, Any]:
    """
    Analyze backup size trends from snapshot data.

    Args:
        snapshots: List of snapshot dicts from get_snapshot_range.

    Returns:
        Dictionary with size trend analysis:
        - data_points: number of snapshots with size data
        - first_size_bytes: earliest snapshot size
        - last_size_bytes: most recent snapshot size
        - growth_bytes: absolute size change
        - growth_percent: percentage change
        - trend: 'growing', 'shrinking', or 'stable'
    """
    sized_snaps = []
    for snap in sorted(snapshots, key=lambda s: s.get('timestamp', '')):
        size_str = snap.get('size')
        if size_str:
            try:
                sized_snaps.append(int(size_str))
            except (ValueError, TypeError):
                continue

    if len(sized_snaps) < 2:
        return {
            'data_points': len(sized_snaps),
            'first_size_bytes': sized_snaps[0] if sized_snaps else 0,
            'last_size_bytes': sized_snaps[-1] if sized_snaps else 0,
            'growth_bytes': 0,
            'growth_percent': 0.0,
            'trend': 'insufficient_data',
        }

    first = sized_snaps[0]
    last = sized_snaps[-1]
    growth = last - first
    growth_pct = (growth / first * 100) if first > 0 else 0.0

    if abs(growth_pct) < 2:
        trend = 'stable'
    elif growth > 0:
        trend = 'growing'
    else:
        trend = 'shrinking'

    return {
        'data_points': len(sized_snaps),
        'first_size_bytes': first,
        'last_size_bytes': last,
        'growth_bytes': growth,
        'growth_percent': round(growth_pct, 1),
        'trend': trend,
    }


def format_bytes(size_bytes: int) -> str:
    """Format byte count as human-readable string (e.g., '1.5 GB')."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024**2:.1f} MB"
    elif size_bytes < 1024 ** 4:
        return f"{size_bytes / 1024**3:.1f} GB"
    else:
        return f"{size_bytes / 1024**4:.1f} TB"


# Example usage and testing
if __name__ == "__main__":
    # Test timestamp formatting
    test_timestamp = "2025-10-22T12:35:00Z"
    print(f"Time ago: {format_time_ago(test_timestamp)}")
    
    # Test backup recency assessment
    status, icon, desc = assess_backup_recency(test_timestamp)
    print(f"Backup status: {icon} {status} - {desc}")
    
    # Test connector type formatting
    print(f"Connector type: {format_connector_type('o365-admin')}")
    
    # Test duration formatting
    print(f"7 days duration: {format_duration_iso8601(days=7)}")
    print(f"24 hours duration: {format_duration_iso8601(hours=24)}")
