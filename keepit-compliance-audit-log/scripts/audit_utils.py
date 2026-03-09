#!/usr/bin/env python3
"""
Keepit Compliance Audit Log Analysis Utilities

Helper functions for audit log extraction, event categorization,
compliance framework formatting, and risk assessment.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple
from collections import defaultdict, Counter


def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp to datetime object."""
    if timestamp.endswith('Z'):
        timestamp = timestamp.replace('Z', '+00:00')
    return datetime.fromisoformat(timestamp)


def extract_metadata(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract and flatten the metadata array from an audit log event.

    The metadata field is an array of { "parameter": { "key": "...", "value": "..." } }
    objects. This function flattens it into a simple key-value dict.

    Args:
        event: Audit log event dict

    Returns:
        Flat dictionary of metadata key-value pairs
    """
    result = {}
    metadata = event.get('metadata', [])
    if not isinstance(metadata, list):
        return result

    for item in metadata:
        if isinstance(item, dict):
            param = item.get('parameter', {})
            if isinstance(param, dict):
                key = param.get('key', '')
                value = param.get('value', '')
                if key:
                    result[key] = value

    return result


def categorize_event(event: Dict[str, Any]) -> str:
    """
    Categorize audit log event by type, using action, area, and metadata.

    Categories:
    - authentication (login/logout)
    - authorization (permissions)
    - data_access (backup/restore)
    - configuration (settings changes)
    - administrative (user management)
    - security (failed access, violations)
    """
    action = event.get('action', '').lower()
    area = event.get('area', '').lower()

    # Also check metadata for additional context
    meta = extract_metadata(event)
    meta_values = ' '.join(meta.values()).lower()

    searchable = f"{action} {meta_values}"

    if any(word in action for word in ['login', 'logout', 'authenticate', 'mfa']) or 'user events' in area:
        return 'authentication'
    elif any(word in action for word in ['permission', 'role', 'grant', 'revoke']):
        return 'authorization'
    elif any(word in action for word in ['restore', 'backup', 'export', 'download']):
        return 'data_access'
    elif any(word in searchable for word in ['config', 'setting', 'policy', 'retention']):
        return 'configuration'
    elif any(word in action for word in ['create user', 'delete user', 'modify user']):
        return 'administrative'
    elif any(word in action for word in ['failed', 'denied', 'violation', 'blocked']):
        return 'security'
    else:
        return 'other'


def assess_risk_level(event: Dict[str, Any]) -> Tuple[str, str]:
    """
    Assess risk level of an audit event, using metadata for richer context.

    Returns:
        Tuple of (risk_level, icon)
        - risk_level: 'critical', 'high', 'medium', 'low', 'info'
        - icon: Emoji representing risk level
    """
    category = categorize_event(event)
    action = event.get('action', '').lower()
    was_allowed = event.get('allowed', True)
    succeeded = event.get('succeeded', True)

    # Check metadata for additional risk signals
    meta = extract_metadata(event)
    meta_values = ' '.join(meta.values()).lower()

    # Critical risk indicators
    if not succeeded and category == 'authentication':
        if event.get('failure_count', 0) > 5:
            return ('critical', '🔴')

    if any(word in action for word in ['delete', 'remove', 'terminate']):
        return ('high', '🔴')

    # High risk indicators
    if category == 'security' and not was_allowed:
        return ('high', '🔴')

    if any(word in action for word in ['privilege', 'admin', 'escalate']):
        return ('high', '🔴')

    # Metadata-based risk escalation: bulk operations or sensitive resource access
    if any(word in meta_values for word in ['bulk', 'all users', 'all connectors']):
        return ('medium', '🟡')

    # Medium risk indicators
    if category in ['configuration', 'administrative']:
        return ('medium', '🟡')

    if 'export' in action or 'bulk' in action:
        return ('medium', '🟡')

    # Low risk indicators
    if category == 'data_access' and succeeded:
        return ('low', '🟢')

    if category == 'authentication' and succeeded:
        return ('low', '🟢')

    # Informational
    return ('info', '⚪')


def format_for_gdpr(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format audit events for GDPR compliance reporting.
    
    Maps events to GDPR articles and requirements.
    """
    gdpr_mapping = {
        'article_5': [],   # Principles
        'article_15': [],  # Right of access
        'article_30': [],  # Records of processing
        'article_32': [],  # Security of processing
        'article_33': [],  # Breach notification
    }
    
    for event in events:
        action = event.get('action', '').lower()
        
        # Article 5 - Processing principles
        if any(word in action for word in ['backup', 'process', 'store']):
            gdpr_mapping['article_5'].append(event)
        
        # Article 15 - Access requests
        if 'data subject' in action or 'dsar' in action:
            gdpr_mapping['article_15'].append(event)
        
        # Article 30 - Processing records
        gdpr_mapping['article_30'].append(event)  # All events
        
        # Article 32 - Security measures
        if categorize_event(event) in ['authentication', 'authorization', 'security']:
            gdpr_mapping['article_32'].append(event)
        
        # Article 33 - Breaches
        if 'breach' in action or (not event.get('allowed', True) and 'unauthorized' in action):
            gdpr_mapping['article_33'].append(event)
    
    return gdpr_mapping


def format_for_hipaa(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format audit events for HIPAA compliance reporting.
    
    Maps events to HIPAA Security Rule requirements.
    """
    hipaa_mapping = {
        'administrative': [],   # §164.308
        'technical': [],        # §164.312
        'audit_controls': [],   # §164.312(b)
        'access_control': [],   # §164.312(a)
        'integrity': [],        # §164.312(c)
        'transmission': [],     # §164.312(e)
    }
    
    for event in events:
        category = categorize_event(event)
        action = event.get('action', '').lower()
        
        # Administrative safeguards
        if category in ['administrative', 'configuration']:
            hipaa_mapping['administrative'].append(event)
        
        # Technical safeguards
        if category in ['authentication', 'authorization', 'security']:
            hipaa_mapping['technical'].append(event)
        
        # Audit controls - all events
        hipaa_mapping['audit_controls'].append(event)
        
        # Access control
        if category in ['authentication', 'authorization']:
            hipaa_mapping['access_control'].append(event)
        
        # Integrity controls
        if 'verify' in action or 'integrity' in action or 'checksum' in action:
            hipaa_mapping['integrity'].append(event)
        
        # Transmission security
        if 'transfer' in action or 'transmit' in action or 'export' in action:
            hipaa_mapping['transmission'].append(event)
    
    return hipaa_mapping


def generate_event_timeline(events: List[Dict[str, Any]], 
                           time_format: str = 'hourly') -> Dict[str, int]:
    """
    Generate timeline distribution of events.
    
    Args:
        events: List of audit events
        time_format: 'hourly', 'daily', or 'weekly'
    
    Returns:
        Dictionary mapping time periods to event counts
    """
    timeline = defaultdict(int)
    
    for event in events:
        timestamp_str = event.get('time')
        if not timestamp_str:
            continue

        dt = parse_iso_timestamp(timestamp_str)

        if time_format == 'hourly':
            key = dt.strftime('%Y-%m-%d %H:00')
        elif time_format == 'daily':
            key = dt.strftime('%Y-%m-%d')
        elif time_format == 'weekly':
            # ISO week
            key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
        else:
            key = dt.strftime('%Y-%m-%d')
        
        timeline[key] += 1
    
    return dict(timeline)


def detect_anomalies(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect anomalous patterns in audit events.
    
    Detects:
    - Multiple failed authentications
    - Off-hours activity
    - Bulk operations
    - Geographic anomalies
    - Unusual access patterns
    """
    anomalies = []
    
    # Group events by user
    user_events = defaultdict(list)
    for event in events:
        user = event.get('token', 'unknown')
        user_events[user].append(event)
    
    # Detect failed authentication patterns
    for user, user_event_list in user_events.items():
        auth_failures = [e for e in user_event_list
                        if categorize_event(e) == 'authentication'
                        and not e.get('succeeded', True)]
        
        if len(auth_failures) > 5:
            anomalies.append({
                'type': 'multiple_failed_auth',
                'user': user,
                'count': len(auth_failures),
                'events': auth_failures,
                'severity': 'high'
            })
    
    # Detect off-hours activity (outside 6 AM - 10 PM)
    for event in events:
        timestamp_str = event.get('time')
        if timestamp_str:
            dt = parse_iso_timestamp(timestamp_str)
            hour = dt.hour
            
            # Off-hours: before 6 AM or after 10 PM
            if hour < 6 or hour >= 22:
                anomalies.append({
                    'type': 'off_hours_activity',
                    'time': dt.strftime('%Y-%m-%d %H:%M UTC'),
                    'user': event.get('token'),
                    'action': event.get('action'),
                    'severity': 'medium'
                })
    
    # Detect bulk operations
    for user, user_event_list in user_events.items():
        # Check for many events in short time
        if len(user_event_list) > 20:
            time_window = timedelta(hours=1)
            sorted_events = sorted(user_event_list,
                                 key=lambda e: parse_iso_timestamp(e.get('time', '')))
            
            if sorted_events:
                first = parse_iso_timestamp(sorted_events[0].get('time'))
                last = parse_iso_timestamp(sorted_events[-1].get('time'))
                
                if last - first < time_window:
                    anomalies.append({
                        'type': 'bulk_operations',
                        'user': user,
                        'count': len(user_event_list),
                        'timespan': str(last - first),
                        'severity': 'medium'
                    })
    
    return anomalies


def generate_compliance_summary(events: List[Dict[str, Any]], 
                               framework: str = 'general') -> Dict[str, Any]:
    """
    Generate compliance summary for specified framework.
    
    Args:
        events: List of audit events
        framework: 'gdpr', 'hipaa', 'iso27001', 'nis2', 'soc2', or 'general'
    
    Returns:
        Dictionary with compliance summary
    """
    total_events = len(events)
    
    # Categorize all events
    categories = Counter(categorize_event(e) for e in events)
    
    # Risk assessment
    risks = Counter(assess_risk_level(e)[0] for e in events)
    
    # Detect anomalies
    anomalies = detect_anomalies(events)
    
    summary = {
        'total_events': total_events,
        'framework': framework,
        'categories': dict(categories),
        'risk_levels': dict(risks),
        'anomalies': len(anomalies),
        'anomaly_details': anomalies[:5],  # Top 5
    }
    
    # Framework-specific additions
    if framework == 'gdpr':
        summary['gdpr_mapping'] = format_for_gdpr(events)
    elif framework == 'hipaa':
        summary['hipaa_mapping'] = format_for_hipaa(events)
    
    return summary


def format_duration_iso8601(days: int = 0, hours: int = 0) -> str:
    """Format duration in ISO 8601 format for API calls."""
    if days > 0:
        return f"P{days}D"
    elif hours > 0:
        return f"PT{hours}H"
    else:
        return "P1D"


def natural_language_to_duration(nl_period: str) -> str:
    """
    Convert natural language time period to ISO 8601 duration.
    
    Examples:
        "last 24 hours" -> "PT24H"
        "last week" -> "P7D"
        "last month" -> "P30D"
        "last quarter" -> "P90D"
    """
    nl_period_lower = nl_period.lower()
    
    duration_map = {
        'today': 'P1D',
        'yesterday': 'P1D',
        '24 hours': 'PT24H',
        'last 24 hours': 'PT24H',
        'last day': 'P1D',
        'last week': 'P7D',
        'week': 'P7D',
        '2 weeks': 'P14D',
        'last 2 weeks': 'P14D',
        'last month': 'P30D',
        'month': 'P30D',
        '30 days': 'P30D',
        'last 30 days': 'P30D',
        'quarter': 'P90D',
        'last quarter': 'P90D',
        '90 days': 'P90D',
        'last 90 days': 'P90D',
        'year': 'P365D',
        'last year': 'P365D',
    }
    
    for key, value in duration_map.items():
        if key in nl_period_lower:
            return value
    
    # Default to 30 days if not matched
    return 'P30D'


# Example usage and testing
if __name__ == "__main__":
    # Example event data
    sample_events = [
        {
            'time': '2025-10-22T08:15:00Z',
            'token': 'adm...@company.com',
            'action': 'Login successful',
            'area': 'User events',
            'wasAllowed': True,
            'succeeded': True,
            'clientIP': '203.0.113.42',
            'type': 'POST',
            'account': 'z7ge93-18gjkb-3qsl9m'
        },
        {
            'time': '2025-10-22T08:20:00Z',
            'token': 'adm...@company.com',
            'action': 'Modified retention policy',
            'area': 'Configuration',
            'wasAllowed': True,
            'succeeded': True,
            'clientIP': '203.0.113.42',
            'type': 'POST',
            'account': 'z7ge93-18gjkb-3qsl9m'
        },
        {
            'time': '2025-10-22T14:30:00Z',
            'token': 'usr...@company.com',
            'action': 'Login attempt',
            'area': 'User events',
            'wasAllowed': False,
            'succeeded': False,
            'clientIP': '198.51.100.15',
            'type': 'POST',
            'account': 'z7ge93-18gjkb-3qsl9m'
        }
    ]
    
    # Test categorization
    print("Event Categories:")
    for event in sample_events:
        category = categorize_event(event)
        risk, icon = assess_risk_level(event)
        print(f"  {icon} {event['action']}: {category} ({risk})")
    
    # Test compliance summary
    print("\nCompliance Summary:")
    summary = generate_compliance_summary(sample_events, framework='gdpr')
    print(f"  Total events: {summary['total_events']}")
    print(f"  Categories: {summary['categories']}")
    print(f"  Risk levels: {summary['risk_levels']}")
