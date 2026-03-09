#!/usr/bin/env python3
"""
Keepit Snapshot Gap & Continuity Analysis Utilities

Helper functions for analyzing backup snapshot continuity, detecting gaps,
measuring RPO compliance, tracking size trends, and projecting storage needs.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional


def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp to datetime object."""
    if timestamp.endswith('Z'):
        timestamp = timestamp.replace('Z', '+00:00')
    return datetime.fromisoformat(timestamp)


def analyze_snapshot_gaps(snapshots: list,
                          expected_interval_hours: float = 24.0) -> Dict[str, Any]:
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
        - partial_count: number of partial ('p') snapshots
        - complete_count: number of complete ('c') snapshots
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

    sorted_snaps = sorted(snapshots, key=lambda s: s.get('timestamp', ''))

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


def calculate_rpo_compliance(snapshots: list,
                             target_rpo_hours: float = 24.0) -> Dict[str, Any]:
    """
    Calculate RPO (Recovery Point Objective) compliance from snapshot data.

    Measures whether the interval between consecutive snapshots stays within
    the target RPO. Every interval that exceeds the RPO is a violation.

    Args:
        snapshots: List of snapshot dicts from get_snapshot_range.
        target_rpo_hours: Maximum acceptable gap in hours (default 24h).

    Returns:
        Dictionary with RPO compliance results:
        - compliant: boolean (True if all intervals meet RPO)
        - target_hours: the target RPO
        - actual_max_gap_hours: worst-case RPO (largest interval)
        - compliance_pct: percentage of intervals that meet RPO
        - total_intervals: number of intervals measured
        - violations: list of intervals that exceeded RPO
    """
    if not snapshots:
        return {
            'compliant': False,
            'target_hours': target_rpo_hours,
            'actual_max_gap_hours': 0,
            'compliance_pct': 0.0,
            'total_intervals': 0,
            'violations': [],
        }

    sorted_snaps = sorted(snapshots, key=lambda s: s.get('timestamp', ''))

    timestamps = []
    for snap in sorted_snaps:
        ts = snap.get('timestamp')
        if ts:
            timestamps.append(parse_iso_timestamp(ts))

    if len(timestamps) < 2:
        return {
            'compliant': False,
            'target_hours': target_rpo_hours,
            'actual_max_gap_hours': 0,
            'compliance_pct': 0.0,
            'total_intervals': 0,
            'violations': [],
        }

    intervals = []
    violations = []
    for i in range(1, len(timestamps)):
        delta = timestamps[i] - timestamps[i - 1]
        hours = delta.total_seconds() / 3600
        intervals.append(hours)
        if hours > target_rpo_hours:
            violations.append({
                'start': timestamps[i - 1].isoformat(),
                'end': timestamps[i].isoformat(),
                'gap_hours': round(hours, 1),
                'exceeded_by_hours': round(hours - target_rpo_hours, 1),
            })

    max_gap = max(intervals) if intervals else 0
    compliant_count = sum(1 for h in intervals if h <= target_rpo_hours)
    compliance_pct = (compliant_count / len(intervals) * 100) if intervals else 0.0

    return {
        'compliant': len(violations) == 0,
        'target_hours': target_rpo_hours,
        'actual_max_gap_hours': round(max_gap, 1),
        'compliance_pct': round(compliance_pct, 1),
        'total_intervals': len(intervals),
        'violations': violations,
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
        - trend: 'growing', 'shrinking', 'stable', or 'insufficient_data'
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


def project_storage_needs(snapshots: list,
                          projection_days: int = 90) -> Dict[str, Any]:
    """
    Project future storage needs based on observed snapshot size trends.

    Args:
        snapshots: List of snapshot dicts from get_snapshot_range.
        projection_days: How many days ahead to project (default 90).

    Returns:
        Dictionary with storage projection:
        - current_size_bytes: most recent snapshot size
        - projected_size_bytes: estimated size in projection_days
        - daily_growth_bytes: average daily size increase
        - projection_days: number of days projected
        - confidence: 'high' (30+ data points), 'medium' (10-29), 'low' (<10)
    """
    sorted_snaps = sorted(snapshots, key=lambda s: s.get('timestamp', ''))

    sizes_with_time = []
    for snap in sorted_snaps:
        size_str = snap.get('size')
        ts = snap.get('timestamp')
        if size_str and ts:
            try:
                sizes_with_time.append((parse_iso_timestamp(ts), int(size_str)))
            except (ValueError, TypeError):
                continue

    if len(sizes_with_time) < 2:
        current = sizes_with_time[0][1] if sizes_with_time else 0
        return {
            'current_size_bytes': current,
            'projected_size_bytes': current,
            'daily_growth_bytes': 0,
            'projection_days': projection_days,
            'confidence': 'low',
        }

    first_time, first_size = sizes_with_time[0]
    last_time, last_size = sizes_with_time[-1]

    days_span = max((last_time - first_time).total_seconds() / 86400, 1)
    daily_growth = (last_size - first_size) / days_span
    projected = last_size + (daily_growth * projection_days)

    count = len(sizes_with_time)
    if count >= 30:
        confidence = 'high'
    elif count >= 10:
        confidence = 'medium'
    else:
        confidence = 'low'

    return {
        'current_size_bytes': last_size,
        'projected_size_bytes': max(int(projected), 0),
        'daily_growth_bytes': int(daily_growth),
        'projection_days': projection_days,
        'confidence': confidence,
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


def get_continuity_icon(status: str) -> str:
    """Get icon for continuity status."""
    return {
        'good': '✅',
        'warning': '⚠️',
        'critical': '❌',
    }.get(status, '❓')


def generate_continuity_summary(connectors_analysis: list) -> Dict[str, Any]:
    """
    Generate an overall continuity summary across multiple connectors.

    Args:
        connectors_analysis: List of dicts, each with:
            - name: connector name
            - gap_analysis: output from analyze_snapshot_gaps()
            - rpo_result: output from calculate_rpo_compliance()
            - size_trend: output from analyze_snapshot_size_trend()

    Returns:
        Dictionary with overall summary:
        - total_connectors: number analyzed
        - overall_status: worst status across all connectors
        - total_gaps: total number of gaps found
        - rpo_compliant_count: connectors meeting RPO
        - connectors_needing_attention: list of connector names with issues
    """
    if not connectors_analysis:
        return {
            'total_connectors': 0,
            'overall_status': 'critical',
            'total_gaps': 0,
            'rpo_compliant_count': 0,
            'connectors_needing_attention': [],
        }

    statuses = []
    total_gaps = 0
    rpo_compliant = 0
    needing_attention = []

    for c in connectors_analysis:
        gap = c.get('gap_analysis', {})
        rpo = c.get('rpo_result', {})

        status = gap.get('continuity_status', 'critical')
        statuses.append(status)
        total_gaps += len(gap.get('gaps', []))

        if rpo.get('compliant', False):
            rpo_compliant += 1

        if status != 'good' or not rpo.get('compliant', False):
            needing_attention.append(c.get('name', 'Unknown'))

    # Overall = worst individual status
    if 'critical' in statuses:
        overall = 'critical'
    elif 'warning' in statuses:
        overall = 'warning'
    else:
        overall = 'good'

    return {
        'total_connectors': len(connectors_analysis),
        'overall_status': overall,
        'total_gaps': total_gaps,
        'rpo_compliant_count': rpo_compliant,
        'connectors_needing_attention': needing_attention,
    }


# Example usage and testing
if __name__ == "__main__":
    # Example snapshot data
    sample_snapshots = [
        {'timestamp': '2026-02-01T02:00:00Z', 'type': 'c', 'size': '1073741824', 'account': 'test'},
        {'timestamp': '2026-02-02T02:00:00Z', 'type': 'c', 'size': '1083741824', 'account': 'test'},
        {'timestamp': '2026-02-03T02:00:00Z', 'type': 'c', 'size': '1093741824', 'account': 'test'},
        # Gap: Feb 4 missing
        {'timestamp': '2026-02-05T02:00:00Z', 'type': 'c', 'size': '1103741824', 'account': 'test'},
        {'timestamp': '2026-02-06T02:00:00Z', 'type': 'p', 'size': '1108741824', 'account': 'test'},
        {'timestamp': '2026-02-07T02:00:00Z', 'type': 'c', 'size': '1113741824', 'account': 'test'},
    ]

    print("Gap Analysis:")
    gaps = analyze_snapshot_gaps(sample_snapshots)
    print(f"  Status: {gaps['continuity_status']}")
    print(f"  Max gap: {gaps['max_gap_hours']}h")
    print(f"  Gaps found: {len(gaps['gaps'])}")
    print(f"  Partial/Complete: {gaps['partial_count']}p / {gaps['complete_count']}c")

    print("\nRPO Compliance:")
    rpo = calculate_rpo_compliance(sample_snapshots, target_rpo_hours=24)
    print(f"  Compliant: {rpo['compliant']}")
    print(f"  Compliance: {rpo['compliance_pct']}%")
    print(f"  Violations: {len(rpo['violations'])}")

    print("\nSize Trend:")
    trend = analyze_snapshot_size_trend(sample_snapshots)
    print(f"  Growth: {trend['growth_percent']}%")
    print(f"  Trend: {trend['trend']}")
    print(f"  From {format_bytes(trend['first_size_bytes'])} to {format_bytes(trend['last_size_bytes'])}")

    print("\nProjection (90 days):")
    proj = project_storage_needs(sample_snapshots, projection_days=90)
    print(f"  Current: {format_bytes(proj['current_size_bytes'])}")
    print(f"  Projected: {format_bytes(proj['projected_size_bytes'])}")
    print(f"  Daily growth: {format_bytes(proj['daily_growth_bytes'])}")
