#!/usr/bin/env python3
"""
Keepit Job History Analysis Utilities

Helper functions for analyzing backup job history, calculating metrics,
identifying patterns, and generating insights.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict, Counter


def parse_iso_timestamp(timestamp: str) -> datetime:
    """
    Parse ISO 8601 timestamp to datetime object.
    
    Args:
        timestamp: ISO 8601 formatted timestamp
    
    Returns:
        datetime object in UTC timezone
    """
    if timestamp.endswith('Z'):
        timestamp = timestamp.replace('Z', '+00:00')
    return datetime.fromisoformat(timestamp)


def parse_execsummary(xml_string: Optional[str]) -> Dict[str, Any]:
    """
    Parse the execsummary XML field from a job record.

    The execsummary field contains XML with error messages, exit reasons,
    and completion details. The exact schema is undocumented, so this
    function extracts whatever elements and attributes are present.

    Args:
        xml_string: XML string from the job's execsummary field, or None

    Returns:
        Dictionary with extracted fields:
        - errors: list of error message strings
        - exit_reason: exit reason string if found
        - warnings: list of warning strings
        - details: dict of all other key-value pairs found
        - raw_xml: the original XML string
        - parse_error: error message if XML parsing failed
    """
    result = {
        'errors': [],
        'exit_reason': None,
        'warnings': [],
        'details': {},
        'raw_xml': xml_string,
        'parse_error': None,
    }

    if not xml_string or not xml_string.strip():
        return result

    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        result['parse_error'] = str(e)
        return result

    def extract_text(element):
        """Get text content from element, including tail text of children."""
        return (element.text or '').strip()

    # Walk the entire tree and extract known patterns flexibly
    for elem in root.iter():
        tag = elem.tag.lower()
        text = extract_text(elem)

        # Extract errors
        if 'error' in tag:
            if text:
                result['errors'].append(text)
            # Check attributes for error messages
            for attr_key, attr_val in elem.attrib.items():
                if attr_val:
                    result['errors'].append(f"{attr_key}: {attr_val}")

        # Extract exit reasons
        elif 'exit' in tag or 'reason' in tag:
            if text:
                result['exit_reason'] = text
            for attr_key, attr_val in elem.attrib.items():
                if attr_val and not result['exit_reason']:
                    result['exit_reason'] = attr_val

        # Extract warnings
        elif 'warn' in tag:
            if text:
                result['warnings'].append(text)
            for attr_key, attr_val in elem.attrib.items():
                if attr_val:
                    result['warnings'].append(f"{attr_key}: {attr_val}")

        # Capture all other elements with text content as details
        else:
            if text:
                result['details'][elem.tag] = text
            for attr_key, attr_val in elem.attrib.items():
                if attr_val:
                    result['details'][f"{elem.tag}.{attr_key}"] = attr_val

    return result


def calculate_job_duration(start_time: str, end_time: str) -> timedelta:
    """
    Calculate duration between job start and end times.
    
    Args:
        start_time: ISO 8601 formatted start timestamp
        end_time: ISO 8601 formatted end timestamp
    
    Returns:
        timedelta representing job duration
    """
    start = parse_iso_timestamp(start_time)
    end = parse_iso_timestamp(end_time)
    return end - start


def format_duration(duration: timedelta) -> str:
    """
    Format timedelta as human-readable duration string.
    
    Args:
        duration: timedelta object
    
    Returns:
        Formatted string (e.g., "14m 32s", "1h 23m")
    """
    total_seconds = int(duration.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def calculate_success_rate(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate success rate metrics from job list.

    Status is inferred from API fields:
    - succeeded timestamp present → success
    - active == true → running
    - active == false and no succeeded → failed

    Args:
        jobs: List of job dictionaries from get_job_history API

    Returns:
        Dictionary with success rate metrics
    """
    if not jobs:
        return {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'running': 0,
            'success_rate': 0.0,
            'failure_rate': 0.0
        }

    total = len(jobs)
    successful = 0
    failed = 0
    running = 0

    for job in jobs:
        if job.get('active', False):
            running += 1
        elif job.get('failed'):
            failed += 1
        else:
            successful += 1

    success_rate = (successful / total * 100) if total > 0 else 0.0
    failure_rate = (failed / total * 100) if total > 0 else 0.0

    return {
        'total': total,
        'successful': successful,
        'failed': failed,
        'running': running,
        'success_rate': round(success_rate, 1),
        'failure_rate': round(failure_rate, 1)
    }


def calculate_duration_statistics(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate duration statistics from job list.
    
    Args:
        jobs: List of job dictionaries with start/end times
    
    Returns:
        Dictionary with duration statistics
    """
    durations = []
    
    for job in jobs:
        start = job.get('started')
        end = job.get('succeeded')
        
        if start and end:
            duration = calculate_job_duration(start, end)
            durations.append(duration.total_seconds())
    
    if not durations:
        return {
            'count': 0,
            'average': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'total': 0
        }
    
    durations.sort()
    count = len(durations)
    
    return {
        'count': count,
        'average': sum(durations) / count,
        'median': durations[count // 2],
        'min': min(durations),
        'max': max(durations),
        'total': sum(durations),
        'p95': durations[int(count * 0.95)] if count > 0 else 0
    }


def identify_failure_patterns(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify patterns in failed jobs, including execsummary XML analysis.

    Args:
        jobs: List of job dictionaries

    Returns:
        Dictionary with failure pattern analysis including execsummary insights
    """
    failed_jobs = [j for j in jobs if j.get('failed') and not j.get('active', False)]

    if not failed_jobs:
        return {'has_failures': False}

    # Analyze error messages from description
    error_messages = [j.get('description', 'Unknown error') for j in failed_jobs]
    error_counts = Counter(error_messages)

    # Parse execsummary XML for richer error data
    execsummary_errors = []
    exit_reasons = Counter()
    execsummary_warnings = []
    jobs_with_execsummary = 0

    for job in failed_jobs:
        parsed = parse_execsummary(job.get('execsummary'))
        if parsed['errors'] or parsed['exit_reason'] or parsed['warnings']:
            jobs_with_execsummary += 1
        execsummary_errors.extend(parsed['errors'])
        if parsed['exit_reason']:
            exit_reasons[parsed['exit_reason']] += 1
        execsummary_warnings.extend(parsed['warnings'])

    execsummary_error_counts = Counter(execsummary_errors)

    # Analyze temporal patterns
    failure_times = []
    failure_days = []

    for job in failed_jobs:
        created = job.get('start') or job.get('started')
        if created:
            dt = parse_iso_timestamp(created)
            failure_times.append(dt.hour)
            failure_days.append(dt.strftime('%A'))

    # Identify recurring vs one-time failures
    recurring_errors = {err: count for err, count in error_counts.items() if count > 1}
    one_time_errors = {err: count for err, count in error_counts.items() if count == 1}

    return {
        'has_failures': True,
        'total_failures': len(failed_jobs),
        'unique_errors': len(error_counts),
        'most_common_error': error_counts.most_common(1)[0] if error_counts else None,
        'recurring_errors': recurring_errors,
        'one_time_errors': one_time_errors,
        'failure_by_hour': Counter(failure_times),
        'failure_by_day': Counter(failure_days),
        # Execsummary-derived fields
        'execsummary_available': jobs_with_execsummary,
        'execsummary_errors': dict(execsummary_error_counts.most_common(10)),
        'exit_reasons': dict(exit_reasons.most_common(10)),
        'execsummary_warnings': list(set(execsummary_warnings)),
    }


def detect_performance_trends(jobs_by_period: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Detect performance trends across time periods.
    
    Args:
        jobs_by_period: Dictionary mapping period names to job lists
    
    Returns:
        Dictionary with trend analysis
    """
    trends = {}
    
    for period, jobs in sorted(jobs_by_period.items()):
        metrics = calculate_success_rate(jobs)
        duration_stats = calculate_duration_statistics(jobs)
        
        trends[period] = {
            'success_rate': metrics['success_rate'],
            'avg_duration': duration_stats['average'],
            'job_count': metrics['total']
        }
    
    # Calculate trend direction
    periods = list(trends.keys())
    if len(periods) >= 2:
        first_period = trends[periods[0]]
        last_period = trends[periods[-1]]
        
        success_trend = 'improving' if last_period['success_rate'] > first_period['success_rate'] else \
                       'degrading' if last_period['success_rate'] < first_period['success_rate'] else 'stable'
        
        duration_trend = 'increasing' if last_period['avg_duration'] > first_period['avg_duration'] else \
                        'decreasing' if last_period['avg_duration'] < first_period['avg_duration'] else 'stable'
    else:
        success_trend = 'insufficient_data'
        duration_trend = 'insufficient_data'
    
    return {
        'periods': trends,
        'success_rate_trend': success_trend,
        'duration_trend': duration_trend
    }


def categorize_jobs(jobs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize jobs by type (backup, restore, etc.).
    
    Args:
        jobs: List of job dictionaries
    
    Returns:
        Dictionary mapping job types to job lists
    """
    categorized = defaultdict(list)
    
    for job in jobs:
        job_type = job.get('type', 'unknown').lower()
        
        # Normalize job type names
        if 'backup' in job_type:
            categorized['backup'].append(job)
        elif 'restore' in job_type:
            categorized['restore'].append(job)
        elif 'validation' in job_type or 'verify' in job_type:
            categorized['validation'].append(job)
        else:
            categorized['other'].append(job)
    
    return dict(categorized)


def assess_sla_compliance(success_rate: float, target_rate: float = 95.0) -> Dict[str, Any]:
    """
    Assess SLA compliance based on success rate.
    
    Args:
        success_rate: Actual success rate percentage
        target_rate: Target SLA success rate (default 95%)
    
    Returns:
        Dictionary with compliance assessment
    """
    variance = success_rate - target_rate
    
    if success_rate >= target_rate:
        status = 'compliant'
        icon = '✅'
    elif success_rate >= target_rate - 1.0:
        status = 'near_target'
        icon = '⚠️'
    else:
        status = 'below_target'
        icon = '❌'
    
    return {
        'status': status,
        'icon': icon,
        'target': target_rate,
        'actual': success_rate,
        'variance': round(variance, 1),
        'compliant': success_rate >= target_rate
    }


def generate_recommendations(analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate actionable recommendations based on analysis.
    
    Args:
        analysis: Analysis results dictionary
    
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    # Check success rate
    if 'success_rate' in analysis and analysis['success_rate'] < 95:
        recommendations.append({
            'priority': 'high',
            'category': 'reliability',
            'title': 'Improve Success Rate',
            'description': f"Current success rate ({analysis['success_rate']}%) is below target (95%)",
            'action': 'Investigate and resolve recurring failures',
            'timeline': 'This week'
        })
    
    # Check for recurring failures
    if analysis.get('failure_patterns', {}).get('recurring_errors'):
        recommendations.append({
            'priority': 'high',
            'category': 'failures',
            'title': 'Address Recurring Failures',
            'description': 'Multiple instances of the same errors detected',
            'action': 'Resolve root cause of recurring error patterns',
            'timeline': 'Immediate'
        })
    
    # Check duration trends
    if analysis.get('duration_trend') == 'increasing':
        recommendations.append({
            'priority': 'medium',
            'category': 'performance',
            'title': 'Monitor Performance Degradation',
            'description': 'Job durations are increasing over time',
            'action': 'Review capacity and optimize backup strategy',
            'timeline': 'Next 30 days'
        })
    
    # Check for temporal patterns
    failure_patterns = analysis.get('failure_patterns', {})
    if failure_patterns.get('failure_by_day'):
        day_counts = failure_patterns['failure_by_day']
        max_day = max(day_counts, key=day_counts.get)
        if day_counts[max_day] > len(day_counts) * 2:  # One day has >2x average
            recommendations.append({
                'priority': 'medium',
                'category': 'scheduling',
                'title': f'Optimize {max_day} Schedule',
                'description': f'{max_day} has significantly more failures than other days',
                'action': f'Adjust backup schedule for {max_day} to avoid conflicts',
                'timeline': 'This week'
            })
    
    # If no issues, provide maintenance recommendations
    if not recommendations:
        recommendations.append({
            'priority': 'low',
            'category': 'maintenance',
            'title': 'Continue Regular Monitoring',
            'description': 'No issues detected - performance is good',
            'action': 'Maintain current monitoring schedule',
            'timeline': 'Ongoing'
        })
    
    return recommendations


def format_time_range_human(duration_iso: str) -> str:
    """
    Convert ISO 8601 duration to human-readable time range.
    
    Args:
        duration_iso: ISO 8601 duration (e.g., "P7D", "PT24H")
    
    Returns:
        Human-readable string (e.g., "Last 7 days", "Last 24 hours")
    """
    duration_map = {
        'PT1H': 'Last hour',
        'PT24H': 'Last 24 hours',
        'P1D': 'Last day',
        'P7D': 'Last 7 days',
        'P14D': 'Last 2 weeks',
        'P30D': 'Last 30 days',
        'P90D': 'Last 90 days',
        'P1M': 'Last month',
        'P3M': 'Last quarter',
    }
    
    return duration_map.get(duration_iso, duration_iso)


def get_status_icon(status: str) -> str:
    """
    Get appropriate icon for job status.
    
    Args:
        status: Job status string
    
    Returns:
        Emoji icon representing status
    """
    status_lower = status.lower()
    
    if status_lower in ['success', 'completed', 'successful']:
        return '✅'
    elif status_lower in ['failed', 'error', 'failure']:
        return '❌'
    elif status_lower in ['running', 'in_progress', 'active']:
        return '⏳'
    elif status_lower in ['cancelled', 'canceled', 'aborted']:
        return '🚫'
    elif status_lower in ['pending', 'queued', 'scheduled']:
        return '⏸️'
    else:
        return '❓'


def summarize_active_jobs(active_jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarize currently active/running jobs for reporting context.

    Args:
        active_jobs: List of job dicts from get_active_jobs (same schema as job history)

    Returns:
        Dictionary with active job summary:
        - count: number of currently running jobs
        - jobs: list of dicts with type, progress_pct, started, description
    """
    summary = {'count': len(active_jobs), 'jobs': []}

    for job in active_jobs:
        progress_str = job.get('progress', '0')
        try:
            progress_pct = round(float(progress_str) * 100, 1)
        except (ValueError, TypeError):
            progress_pct = 0.0

        summary['jobs'].append({
            'type': job.get('type', 'unknown'),
            'progress_pct': progress_pct,
            'started': job.get('started', ''),
            'description': job.get('description', ''),
        })

    return summary


def get_success_rate_assessment(rate: float) -> Tuple[str, str]:
    """
    Get assessment and icon for success rate.
    
    Args:
        rate: Success rate percentage
    
    Returns:
        Tuple of (assessment string, icon)
    """
    if rate >= 95:
        return ('Excellent', '✅')
    elif rate >= 90:
        return ('Good', '🟢')
    elif rate >= 85:
        return ('Acceptable', '🟡')
    elif rate >= 75:
        return ('Concerning', '⚠️')
    else:
        return ('Critical', '🔴')


# Example usage and testing
if __name__ == "__main__":
    # Example job data
    sample_jobs = [
        {
            'type': 'backup',
            'active': False,
            'start': '2025-10-22T02:15:00Z',
            'started': '2025-10-22T02:15:00Z',
            'failed': None,
            'succeeded': '2025-10-22T02:27:30Z',
            'progress': '1.0',
            'description': 'Backup job completed'
        },
        {
            'type': 'backup',
            'active': False,
            'start': '2025-10-22T03:00:00Z',
            'started': '2025-10-22T03:00:00Z',
            'failed': '2025-10-22T03:05:00Z',
            'progress': '0.3',
            'description': 'Authentication token expired'
        },
        {
            'type': 'backup',
            'active': False,
            'start': '2025-10-22T04:30:00Z',
            'started': '2025-10-22T04:30:00Z',
            'failed': None,
            'succeeded': '2025-10-22T04:42:45Z',
            'progress': '1.0',
            'description': 'Backup job completed'
        }
    ]
    
    # Test functions
    print("Success Rate Analysis:")
    print(calculate_success_rate(sample_jobs))
    
    print("\nDuration Statistics:")
    print(calculate_duration_statistics(sample_jobs))
    
    print("\nFailure Patterns:")
    print(identify_failure_patterns(sample_jobs))
    
    print("\nRecommendations:")
    analysis = {
        'success_rate': 66.7,
        'failure_patterns': identify_failure_patterns(sample_jobs)
    }
    for rec in generate_recommendations(analysis):
        print(f"- [{rec['priority']}] {rec['title']}: {rec['action']}")
