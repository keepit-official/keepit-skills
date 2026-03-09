#!/usr/bin/env python3
"""
Keepit Retention Policy Utilities

Helper functions for retention policy auditing and compliance validation
used in the Keepit Retention Policy Auditor skill.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from collections import defaultdict, Counter
import re


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONNECTOR_TYPE_MAP: Dict[str, str] = {
    'o365-admin': 'Microsoft 365', 'azure-ad': 'Entra ID',
    'gsuite': 'Google Workspace', 'dynamics365': 'Dynamics 365',
    'sforce': 'Salesforce', 'powerbi': 'Power BI',
    'zendesk': 'Zendesk', 'okta': 'Okta',
    'docusign': 'DocuSign', 'bamboohr': 'BambooHR',
    'confluence': 'Confluence', 'jira': 'Jira', 'azure-do': 'Azure DevOps',
}

FRAMEWORK_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
    'gdpr': {
        'minimum_days': None,
        'description': 'Documented retention policy required (Art. 5(1)(e), Art. 30)',
        'requirement': 'Policy must be documented',
    },
    'nis2': {
        'minimum_days': None,
        'description': 'Documented backup and recovery policy required (Article 21)',
        'requirement': 'Backup policy must be documented',
    },
    'dora': {
        'minimum_days': None,
        'description': 'Retention specified in ICT resilience plan (Article 12)',
        'requirement': 'Retention defined in resilience plan',
    },
    'hipaa': {
        'minimum_days': 2190,
        'description': 'Minimum 6-year retention for covered records (45 CFR 164.530(j))',
        'requirement': 'Minimum 2190 days (6 years)',
    },
    'sox': {
        'minimum_days': 2555,
        'description': 'Minimum 7-year retention for financial records (Section 802)',
        'requirement': 'Minimum 2555 days (7 years)',
    },
}

ENFORCEMENT_TOLERANCE_DAYS: int = 7
OVER_RETENTION_THRESHOLD_DAYS: int = 30
SHORT_RETENTION_THRESHOLD_DAYS: int = 30
LONG_RETENTION_THRESHOLD_DAYS: int = 3650

RETENTION_KEYWORDS: List[str] = [
    'retention', 'backup_retention', 'retention_policy', 'retention_updated',
]


# ---------------------------------------------------------------------------
# Timestamp and Format Helpers
# ---------------------------------------------------------------------------

def parse_iso_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp to timezone-aware datetime in UTC.

    Args:
        timestamp: ISO 8601 string (e.g. "2025-12-01T14:30:00Z").

    Returns:
        Timezone-aware datetime in UTC.
    """
    if not timestamp:
        raise ValueError("Empty timestamp string")
    cleaned = timestamp.strip()
    if cleaned.endswith('Z'):
        cleaned = cleaned[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z',
                    '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(cleaned, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse timestamp: {timestamp}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_connector_type(connector_type: str) -> str:
    """Map raw connector type key to human-readable name.

    Args:
        connector_type: Raw type string (e.g. "o365-admin").

    Returns:
        Display name (e.g. "Microsoft 365").
    """
    if not connector_type:
        return 'Unknown'
    return CONNECTOR_TYPE_MAP.get(connector_type, connector_type.replace('-', ' ').title())


def _format_days_human(total_days: int) -> str:
    """Return concise human-readable string for a day count."""
    if total_days == 0:
        return 'Not set'
    if total_days >= 365 and total_days % 365 == 0:
        years = total_days // 365
        return f"{years} year{'s' if years > 1 else ''} ({total_days} days)"
    if total_days >= 30 and total_days % 30 == 0:
        months = total_days // 30
        return f"{months} month{'s' if months > 1 else ''} ({total_days} days)"
    return f"{total_days} days"


# ---------------------------------------------------------------------------
# Retention Duration Parsing
# ---------------------------------------------------------------------------

def parse_retention_duration(iso_duration: Optional[str]) -> Dict[str, Any]:
    """Parse ISO 8601 duration for retention analysis.

    Args:
        iso_duration: ISO 8601 duration string, or None if not set.

    Returns:
        Dict with: raw, days, human_readable, is_set (bool).
    """
    if not iso_duration or not isinstance(iso_duration, str):
        return {'raw': None, 'days': 0, 'human_readable': 'Not set', 'is_set': False}

    iso_duration = iso_duration.strip()
    match = re.match(
        r'^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?'
        r'(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$',
        iso_duration
    )
    if not match:
        return {'raw': iso_duration, 'days': 0, 'human_readable': f'Invalid format ({iso_duration})', 'is_set': False}

    years = int(match.group(1) or 0)
    months = int(match.group(2) or 0)
    weeks = int(match.group(3) or 0)
    days = int(match.group(4) or 0)
    total_days = years * 365 + months * 30 + weeks * 7 + days
    # Add fractional days from time components
    hours = int(match.group(5) or 0)
    minutes = int(match.group(6) or 0)
    seconds = int(match.group(7) or 0)
    if hours or minutes or seconds:
        total_days += max(1, (hours * 3600 + minutes * 60 + seconds) // 86400)

    if total_days == 0:
        return {'raw': iso_duration, 'days': 0, 'human_readable': 'Zero duration', 'is_set': False}
    return {'raw': iso_duration, 'days': total_days, 'human_readable': _format_days_human(total_days), 'is_set': True}


# ---------------------------------------------------------------------------
# Policy Inventory and Auditing
# ---------------------------------------------------------------------------

def audit_retention_policies(connectors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inventory all retention policies across connectors, flag gaps.

    Args:
        connectors: List of connector dicts from get_cloud_connectors(connectorType="cloud").

    Returns:
        Dict with: total_connectors, policies_set, policies_missing,
        policy_details, shortest_retention_days, longest_retention_days, summary.
    """
    policy_details: List[Dict[str, Any]] = []
    set_days: List[int] = []

    for connector in connectors:
        parsed = parse_retention_duration(connector.get('backup_retention'))
        detail: Dict[str, Any] = {
            'connector_name': connector.get('name', 'Unknown'),
            'connector_type': format_connector_type(connector.get('type', 'unknown')),
            'connector_type_raw': connector.get('type', 'unknown'),
            'guid': connector.get('guid', ''),
            'retention_raw': connector.get('backup_retention'),
            'retention_days': parsed['days'],
            'retention_human': parsed['human_readable'],
            'is_set': parsed['is_set'],
            'retention_updated': connector.get('retention_updated'),
            'warnings': [],
        }
        if not parsed['is_set']:
            detail['warnings'].append('No retention policy configured')
        elif parsed['days'] < SHORT_RETENTION_THRESHOLD_DAYS:
            detail['warnings'].append(f'Unusually short retention ({parsed["days"]} days)')
        elif parsed['days'] > LONG_RETENTION_THRESHOLD_DAYS:
            detail['warnings'].append(f'Unusually long retention ({parsed["days"]} days)')
        if parsed['is_set']:
            set_days.append(parsed['days'])
        policy_details.append(detail)

    policies_missing = len(connectors) - len(set_days)
    summary = (f"All {len(connectors)} connectors have retention policies configured."
               if policies_missing == 0 else
               f"{policies_missing} of {len(connectors)} connectors are missing "
               f"retention policies — this is a critical compliance finding.")
    return {
        'total_connectors': len(connectors), 'policies_set': len(set_days),
        'policies_missing': policies_missing, 'policy_details': policy_details,
        'shortest_retention_days': min(set_days) if set_days else 0,
        'longest_retention_days': max(set_days) if set_days else 0, 'summary': summary,
    }


# ---------------------------------------------------------------------------
# Framework Compliance
# ---------------------------------------------------------------------------

def check_framework_compliance(retention_days: int, framework: str,
                                policy_is_set: bool = True) -> Dict[str, Any]:
    """Compare retention against a regulatory framework minimum.

    Args:
        retention_days: Actual retention in days.
        framework: Framework key (e.g. "gdpr", "hipaa").
        policy_is_set: Whether the connector has an explicit retention policy.

    Returns:
        Dict with: framework, requirement, minimum_days, actual_days, compliant, icon, description.
    """
    fw_info = FRAMEWORK_REQUIREMENTS.get(framework.lower())
    if not fw_info:
        return {'framework': framework, 'requirement': 'Unknown framework', 'minimum_days': None,
                'actual_days': retention_days, 'compliant': False, 'icon': '❌',
                'description': f'Unknown framework: {framework}'}

    minimum_days = fw_info['minimum_days']
    if not policy_is_set:
        return {'framework': framework.upper(), 'requirement': fw_info['requirement'],
                'minimum_days': minimum_days, 'actual_days': retention_days, 'compliant': False,
                'icon': '❌', 'description': f'No retention policy set — non-compliant with {framework.upper()}'}
    elif minimum_days is None:
        # Documentation-based frameworks (GDPR, NIS2, DORA)
        return {'framework': framework.upper(), 'requirement': fw_info['requirement'],
                'minimum_days': None, 'actual_days': retention_days, 'compliant': True,
                'icon': '✅', 'description': f'Policy documented ({retention_days} days) — meets {framework.upper()} requirement'}
    elif retention_days >= minimum_days:
        return {'framework': framework.upper(), 'requirement': fw_info['requirement'],
                'minimum_days': minimum_days, 'actual_days': retention_days, 'compliant': True,
                'icon': '✅', 'description': f'{retention_days} days meets {framework.upper()} minimum of {minimum_days} days'}
    else:
        shortfall = minimum_days - retention_days
        return {'framework': framework.upper(), 'requirement': fw_info['requirement'],
                'minimum_days': minimum_days, 'actual_days': retention_days, 'compliant': False,
                'icon': '❌', 'description': f'{retention_days} days is {shortfall} days below {framework.upper()} minimum of {minimum_days} days'}


def check_all_frameworks(retention_days: int, frameworks: List[str],
                          policy_is_set: bool = True) -> List[Dict[str, Any]]:
    """Check retention against multiple frameworks at once."""
    return [check_framework_compliance(retention_days, fw, policy_is_set) for fw in frameworks]


# ---------------------------------------------------------------------------
# Audit Log Analysis
# ---------------------------------------------------------------------------

def extract_metadata(event: Dict[str, Any]) -> Dict[str, str]:
    """Extract and flatten metadata from an audit event.

    Args:
        event: A single audit event dict.

    Returns:
        Flat dictionary of metadata key-value pairs.
    """
    result: Dict[str, str] = {}
    metadata = event.get('metadata', [])
    for item in metadata:
        param = item.get('parameter', {})
        key = param.get('key', '')
        value = param.get('value', '')
        if key:
            result[key] = value
    return result


def _is_retention_related(event: Dict[str, Any], metadata: Dict[str, str]) -> bool:
    """Check if an audit event is retention-related based on metadata content."""
    searchable = str(metadata).lower() + ' ' + str(event.get('action', '')).lower()
    return any(kw in searchable for kw in RETENTION_KEYWORDS)


def detect_recent_changes(audit_events: List[Dict[str, Any]],
                           connectors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find retention-related changes from audit logs and connector fields.

    Combines audit log events with the retention_updated connector timestamp.
    Deduplicates within a 5-minute window and sorts descending by time.

    Args:
        audit_events: Audit event dicts from get_audit_log_history().
        connectors: Connector dicts from get_cloud_connectors(connectorType="cloud").

    Returns:
        List of dicts: timestamp, token, action, connector_name, old_value, new_value, source.
    """
    changes: List[Dict[str, Any]] = []
    matched_guids: set = set()

    # Source 1: Audit log events
    for event in audit_events:
        metadata = extract_metadata(event)
        if not _is_retention_related(event, metadata):
            continue
        change = {
            'timestamp': event.get('timestamp', ''), 'token': event.get('token', 'Unknown'),
            'action': event.get('action', 'Unknown'),
            'connector_name': metadata.get('connector_name', metadata.get('name', '')),
            'old_value': metadata.get('old_value', metadata.get('previous_retention', '')),
            'new_value': metadata.get('new_value', metadata.get('new_retention', '')),
            'source': 'audit_log',
        }
        # Match with connector retention_updated (5-min window)
        if change['timestamp']:
            try:
                event_dt = parse_iso_timestamp(change['timestamp'])
                for conn in connectors:
                    ru = conn.get('retention_updated')
                    if not ru:
                        continue
                    try:
                        if abs((event_dt - parse_iso_timestamp(ru)).total_seconds()) < 300:
                            change['connector_name'] = change['connector_name'] or conn.get('name', '')
                            matched_guids.add(conn.get('guid', ''))
                    except ValueError:
                        continue
            except ValueError:
                pass
        changes.append(change)

    # Source 2: Unmatched connector retention_updated fields
    for conn in connectors:
        guid = conn.get('guid', '')
        if guid in matched_guids or not conn.get('retention_updated'):
            continue
        changes.append({
            'timestamp': conn['retention_updated'], 'token': '',
            'action': 'Retention policy updated (from connector field)',
            'connector_name': conn.get('name', 'Unknown'),
            'old_value': '', 'new_value': conn.get('backup_retention', ''),
            'source': 'connector_field',
        })

    def _sort_key(c):
        try:
            return parse_iso_timestamp(c.get('timestamp', ''))
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)
    changes.sort(key=_sort_key, reverse=True)
    return changes


# ---------------------------------------------------------------------------
# Enforcement Verification
# ---------------------------------------------------------------------------

def verify_enforcement(snapshots: List[Dict[str, Any]],
                        retention_policy: Dict[str, Any]) -> Dict[str, Any]:
    """Check if actual snapshot timestamps align with stated retention.

    Args:
        snapshots: Snapshot dicts from get_snapshot_range().
        retention_policy: Parsed retention dict from parse_retention_duration().

    Returns:
        Dict with: oldest_snapshot_age_days, expected_max_age_days,
        properly_enforced, over_retained, under_retained, description.
    """
    expected_max = retention_policy.get('days', 0)
    now = datetime.now(timezone.utc)
    _base = {'expected_max_age_days': expected_max, 'properly_enforced': False,
             'over_retained': False, 'under_retained': True}

    if not snapshots:
        return {**_base, 'oldest_snapshot_age_days': 0,
                'description': 'No snapshots found — unable to verify enforcement'}

    # Find oldest snapshot
    oldest_dt: Optional[datetime] = None
    for snap in snapshots:
        ts = snap.get('timestamp') or snap.get('created') or snap.get('date')
        if not ts:
            continue
        try:
            snap_dt = parse_iso_timestamp(ts)
            if oldest_dt is None or snap_dt < oldest_dt:
                oldest_dt = snap_dt
        except ValueError:
            continue

    if oldest_dt is None:
        return {**_base, 'oldest_snapshot_age_days': 0,
                'description': 'No valid snapshot timestamps found'}

    age = (now - oldest_dt).days

    if age > expected_max + OVER_RETENTION_THRESHOLD_DAYS:
        over = age - expected_max
        return {'oldest_snapshot_age_days': age, 'expected_max_age_days': expected_max,
                'properly_enforced': False, 'over_retained': True, 'under_retained': False,
                'description': f'Over-retained by {over} days: oldest snapshot is {age} days '
                               f'(policy: {expected_max} days). Potential GDPR data minimization concern.'}
    elif age >= expected_max - ENFORCEMENT_TOLERANCE_DAYS:
        return {'oldest_snapshot_age_days': age, 'expected_max_age_days': expected_max,
                'properly_enforced': True, 'over_retained': False, 'under_retained': False,
                'description': f'Properly enforced: oldest snapshot is {age} days (policy: {expected_max} days)'}
    else:
        return {'oldest_snapshot_age_days': age, 'expected_max_age_days': expected_max,
                'properly_enforced': True, 'over_retained': False, 'under_retained': False,
                'description': f'Within policy: oldest snapshot is {age} days (policy allows up to {expected_max} days)'}


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_retention_report(all_data: Dict[str, Any],
                               frameworks: List[str]) -> Dict[str, Any]:
    """Generate structured retention audit report from all collected data.

    Args:
        all_data: Dict with connectors, audit_events, enforcement_results.
        frameworks: List of framework keys to assess.

    Returns:
        Dict with: policy_inventory, framework_compliance, recent_changes,
        enforcement_status, findings, recommendations.
    """
    connectors = all_data.get('connectors', [])
    audit_events = all_data.get('audit_events', [])
    enforcement_results = all_data.get('enforcement_results', {})

    inventory = audit_retention_policies(connectors)

    # Per-connector framework compliance
    compliance = []
    for detail in inventory['policy_details']:
        fw_results = check_all_frameworks(detail['retention_days'], frameworks, detail['is_set'])
        compliance.append({'connector_name': detail['connector_name'],
                           'connector_type': detail['connector_type'],
                           'retention_days': detail['retention_days'],
                           'framework_results': fw_results})

    changes = detect_recent_changes(audit_events, connectors)

    # Prioritized findings
    findings: List[Dict[str, Any]] = []
    for detail in inventory['policy_details']:
        if not detail['is_set']:
            findings.append({'priority': 'high', 'icon': '🔴', 'category': 'Missing Policy',
                             'connector': detail['connector_name'],
                             'description': f"{detail['connector_name']} ({detail['connector_type']}) has no retention policy configured"})
    for entry in compliance:
        for fw in entry['framework_results']:
            if not fw['compliant']:
                findings.append({'priority': 'high', 'icon': '❌',
                                 'category': f"{fw['framework']} Non-Compliance",
                                 'connector': entry['connector_name'], 'description': fw['description']})
    for guid, enf in enforcement_results.items():
        if enf.get('over_retained'):
            findings.append({'priority': 'medium', 'icon': '⚠️', 'category': 'Over-Retention',
                             'connector': enf.get('connector_name', guid), 'description': enf['description']})
    for detail in inventory['policy_details']:
        for w in detail.get('warnings', []):
            if 'No retention policy' not in w:
                findings.append({'priority': 'low', 'icon': '⚠️', 'category': 'Configuration Warning',
                                 'connector': detail['connector_name'], 'description': w})

    # Recommendations
    recommendations: List[str] = []
    if inventory['policies_missing'] > 0:
        recommendations.append(f"CRITICAL: Configure retention policies on {inventory['policies_missing']} connector(s) missing policies immediately.")
    non_compliant_fws = {fw['framework'] for e in compliance for fw in e['framework_results'] if not fw['compliant']}
    for fw in sorted(non_compliant_fws):
        recommendations.append(f"Review and increase retention periods to meet {fw} requirements.")
    over_count = sum(1 for e in enforcement_results.values() if e.get('over_retained'))
    if over_count > 0:
        recommendations.append(f"Investigate {over_count} connector(s) with data retained beyond stated policy — potential GDPR data minimization concern.")
    if not changes:
        recommendations.append("No recent retention changes detected. Consider scheduling regular retention policy reviews (quarterly recommended).")

    return {'policy_inventory': inventory, 'framework_compliance': compliance,
            'recent_changes': changes, 'enforcement_status': enforcement_results,
            'findings': findings, 'recommendations': recommendations}


def generate_compliance_matrix(connectors: List[Dict[str, Any]],
                                frameworks: List[str]) -> List[Dict[str, Any]]:
    """Generate per-connector, per-framework compliance matrix.

    Args:
        connectors: Connector dicts from get_cloud_connectors(connectorType="cloud").
        frameworks: Framework keys (e.g. ["gdpr", "hipaa", "sox"]).

    Returns:
        List of dicts: connector_name, connector_type, retention_days,
        retention_human, is_set, framework_results.
    """
    matrix = []
    for conn in connectors:
        parsed = parse_retention_duration(conn.get('backup_retention'))
        fw_results = check_all_frameworks(parsed['days'], frameworks, parsed['is_set'])
        matrix.append({
            'connector_name': conn.get('name', 'Unknown'),
            'connector_type': format_connector_type(conn.get('type', 'unknown')),
            'retention_days': parsed['days'], 'retention_human': parsed['human_readable'],
            'is_set': parsed['is_set'], 'framework_results': fw_results,
        })
    return matrix


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Retention Utils Self-Test ===\n")

    # parse_retention_duration
    for raw, exp_set, exp_days in [("P365D",True,365),("P1Y",True,365),("P6M",True,180),
            ("P1Y6M",True,545),("P2W",True,14),("P90D",True,90),(None,False,0),
            ("",False,0),("INVALID",False,0),("P0D",False,0)]:
        r = parse_retention_duration(raw)
        ok = "PASS" if r['is_set'] == exp_set and r['days'] == exp_days else "FAIL"
        print(f"  {ok}: {raw!r} -> set={r['is_set']}, days={r['days']}")

    # parse_iso_timestamp
    for ts in ["2025-12-01T14:30:00Z","2025-12-01T14:30:00+00:00","2025-12-01"]:
        print(f"  PASS: {ts!r} -> {parse_iso_timestamp(ts).isoformat()}")

    # check_framework_compliance
    for days, fw, is_set in [(365,'gdpr',True),(365,'hipaa',True),(2190,'hipaa',True),(0,'gdpr',False)]:
        r = check_framework_compliance(days, fw, is_set)
        print(f"  {r['icon']} {fw.upper()} @ {days}d: {r['description']}")

    # audit_retention_policies
    mock = [
        {'name':'Exchange','type':'o365-admin','backup_retention':'P1Y','retention_updated':'2025-11-15T10:00:00Z','guid':'aaa'},
        {'name':'Google Drive','type':'gsuite','backup_retention':None,'guid':'bbb'},
    ]
    a = audit_retention_policies(mock)
    print(f"  Set: {a['policies_set']}, Missing: {a['policies_missing']}")

    # verify_enforcement
    snaps = [{'timestamp': (datetime.now(timezone.utc) - timedelta(days=360)).isoformat()}]
    e = verify_enforcement(snaps, {'days': 365})
    print(f"  Enforcement: {e['description']}")

    print("\n=== Self-Test Complete ===")
