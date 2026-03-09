---
name: keepit-retention-policy-auditor
description: Retention policy compliance auditing and validation for Keepit backup environments. Use when users ask about retention policies, data retention compliance, GDPR/NIS2/DORA/HIPAA/SOX retention requirements, retention configuration review, or policy change tracking. Triggers on keywords like "retention policy", "retention audit", "data retention", "compliance check", "GDPR retention", "NIS2", "DORA", "how long is data kept", "retention settings".
---

# Keepit Retention Policy Auditor

## Overview

The Retention Policy Auditor provides comprehensive compliance auditing and validation of data retention policies across all Keepit-managed backup connectors. It inventories retention configurations, validates them against regulatory frameworks (GDPR, NIS2, DORA, HIPAA, SOX), tracks policy changes through audit logs and the `retention_updated` connector field, and verifies that actual snapshot retention matches stated policy.

**Target Persona:** Compliance Officer / Data Protection Officer (DPO), IT Manager

**Key Capabilities:**
- Full retention policy inventory with gap detection
- Multi-framework compliance checking (GDPR, NIS2, DORA, HIPAA, SOX)
- Unset/missing policy detection as critical findings
- Policy change audit trail (who changed what, when, old vs. new values)
- Enforcement verification comparing actual snapshots against stated retention
- Per-connector, per-framework compliance matrix generation

**Primary Data Sources:**
- `get_cloud_connectors(connectorType="cloud")` — connector inventory with `backup_retention` and `retention_updated` fields
- `get_audit_log_history()` — audit events for retention-related changes
- `get_snapshot_range()` — actual snapshot data for enforcement verification

---

## Core Workflow

### Step 1: Inventory Retention Policies

Retrieve all connectors and extract retention configuration from each one.

```python
# Fetch all connectors
connectors = get_cloud_connectors(connectorType="cloud")

# Extract retention fields per connector
for connector in connectors:
    name = connector.get('name', 'Unknown')
    connector_type = connector.get('type', 'unknown')
    retention_raw = connector.get('backup_retention')      # ISO 8601 duration, e.g. "P365D"
    retention_updated = connector.get('retention_updated')  # ISO 8601 timestamp of last change

    # Parse retention duration into actionable data
    retention = parse_retention_duration(retention_raw)
    # Returns: { raw, days, human_readable, is_set }
```

The `backup_retention` field stores an ISO 8601 duration string (e.g., "P365D" for 365 days, "P1Y" for 1 year, "P90D" for 90 days). If this field is `None` or empty, the connector has no explicit retention policy configured — a critical compliance finding.

The `retention_updated` field stores an ISO 8601 timestamp indicating when the retention policy was last modified. This is the first skill to leverage this field, enabling precise change tracking without relying solely on audit logs.

### Step 2: Parse and Validate Policies

Convert all ISO 8601 durations to a normalized day count for comparison.

```python
import re

def parse_retention_duration(iso_duration):
    if not iso_duration:
        return {'raw': None, 'days': 0, 'human_readable': 'Not set', 'is_set': False}

    match = re.match(
        r'^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?'
        r'(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$',
        iso_duration
    )
    if not match:
        return {'raw': iso_duration, 'days': 0, 'human_readable': 'Invalid format', 'is_set': False}

    years = int(match.group(1) or 0)
    months = int(match.group(2) or 0)
    weeks = int(match.group(3) or 0)
    days = int(match.group(4) or 0)
    total_days = years * 365 + months * 30 + weeks * 7 + days

    return {'raw': iso_duration, 'days': total_days, 'human_readable': f"{total_days} days", 'is_set': True}
```

**Validation checks at this stage:**
- Unset policies (`backup_retention` is `None` or empty)
- Invalid duration formats (malformed ISO 8601)
- Unusually short retention (< 30 days)
- Unusually long retention (> 3650 days / 10 years)

### Step 3: Check Framework Compliance

Compare each connector's retention against regulatory framework requirements.

```python
# Framework minimum requirements (in days)
FRAMEWORK_REQUIREMENTS = {
    'gdpr': {
        'minimum_days': None,  # No fixed minimum; must be documented
        'description': 'Documented retention policy required (Art. 5(1)(e), Art. 30)',
    },
    'nis2': {
        'minimum_days': None,  # Must have documented backup policy
        'description': 'Documented backup and recovery policy required (Article 21)',
    },
    'dora': {
        'minimum_days': None,  # Specified in resilience plan
        'description': 'Retention specified in ICT resilience plan (Article 12)',
    },
    'hipaa': {
        'minimum_days': 2190,  # 6 years
        'description': 'Minimum 6-year retention for covered records (45 CFR 164.530(j))',
    },
    'sox': {
        'minimum_days': 2555,  # 7 years
        'description': 'Minimum 7-year retention for financial records (Section 802)',
    },
}

# Check a single connector against a framework
result = check_framework_compliance(retention_days=365, framework='hipaa')
# Returns: { framework, requirement, minimum_days, actual_days, compliant, icon, description }

# Check against all applicable frameworks
results = check_all_frameworks(retention_days=365, frameworks=['gdpr', 'nis2', 'hipaa'])
```

**Compliance logic:**
- For GDPR, NIS2, DORA: compliant if a retention policy is documented (i.e., `is_set` is True)
- For HIPAA: compliant if retention >= 2190 days (6 years)
- For SOX: compliant if retention >= 2555 days (7 years)
- Unset policies are always non-compliant across all frameworks

### Step 4: Audit Recent Changes

Search audit logs for retention-related modifications.

```python
# Fetch recent audit events (90 days lookback)
audit_logs = get_audit_log_history(duration="P90D")

# Filter for retention-related events
retention_events = []
for event in audit_logs:
    metadata = extract_metadata(event)
    # Look for retention-related keys in metadata
    if any(key in str(metadata).lower() for key in ['retention', 'backup_retention']):
        retention_events.append({
            'timestamp': event.get('time'),
            'token': event.get('token', 'Unknown'),
            'action': event.get('action', 'Unknown'),
            'metadata': metadata,
            'source': 'audit_log',
        })
```

### Step 5: Correlate with Connector Timestamps

Cross-reference the `retention_updated` field with audit events for a complete change timeline.

```python
# Build timeline from both sources
for connector in connectors:
    retention_updated = connector.get('retention_updated')
    if retention_updated:
        # Check if this timestamp matches any audit event
        matched = False
        for event in retention_events:
            if abs(parse_iso_timestamp(event['timestamp']) - parse_iso_timestamp(retention_updated)).total_seconds() < 300:
                event['connector_name'] = connector.get('name')
                matched = True
                break

        if not matched:
            # retention_updated exists but no matching audit event
            # This change may have occurred outside the audit log window
            retention_events.append({
                'timestamp': retention_updated,
                'connector_name': connector.get('name'),
                'action': 'retention_updated (from connector field)',
                'source': 'connector_field',
            })
```

This dual-source approach ensures that changes made before the audit log retention window are still captured via the `retention_updated` connector field.

### Step 6: Verify Enforcement

Retrieve actual snapshot data and verify that retention is being enforced as configured.

```python
for connector in connectors:
    retention = parse_retention_duration(connector.get('backup_retention'))
    if not retention['is_set']:
        continue

    # Get snapshot range matching the retention period
    snapshots = get_snapshot_range(
        guid=connector['guid'],
        timespan=connector.get('backup_retention', 'P365D'),
        count=99
    )

    # Verify enforcement
    enforcement = verify_enforcement(snapshots, retention)
    # Returns: {
    #   oldest_snapshot_age_days, expected_max_age_days,
    #   properly_enforced, over_retained, under_retained, description
    # }
```

**Enforcement states:**
- **Properly enforced**: Oldest snapshot age is within expected range
- **Over-retained**: Snapshots exist beyond the stated retention period (potential GDPR concern for right to erasure)
- **Under-retained**: No snapshots reaching the expected retention age (new connector, or data loss)

### Step 7: Generate Retention Audit Report

Compile all findings into a structured compliance report.

```python
report = generate_retention_report(
    all_data={
        'connectors': connectors,
        'audit_events': retention_events,
        'enforcement_results': enforcement_results,
    },
    frameworks=['gdpr', 'nis2', 'hipaa']
)

# Report contains:
# - policy_inventory: summary of all retention policies
# - framework_compliance: per-framework compliance results
# - recent_changes: timeline of retention modifications
# - enforcement_status: actual vs. stated retention
# - findings: prioritized list of issues
# - recommendations: actionable next steps
```

---

## Output Formatting Guidelines

### Compliance Status Icons

Use consistent iconography across all output:

| Icon | Meaning | Usage |
|------|---------|-------|
| ✅ | Compliant | Policy meets framework requirements |
| ⚠️ | Warning | Policy exists but needs attention (short retention, approaching minimum) |
| ❌ | Non-compliant | Policy missing or below framework minimum |
| :red_circle: | High Priority | Critical finding requiring immediate action |

### Policy Inventory Table

```
## Retention Policy Inventory

| Connector | Type | Retention | Days | Last Updated | Status |
|-----------|------|-----------|------|--------------|--------|
| Exchange Online | Microsoft 365 | P1Y | 365 | 2025-11-15 | ✅ Set |
| SharePoint | Microsoft 365 | P365D | 365 | 2025-11-15 | ✅ Set |
| Google Drive | Google Workspace | — | 0 | — | ❌ Not Set |
```

### Compliance Matrix

```
## Framework Compliance Matrix

| Connector | GDPR | NIS2 | HIPAA | SOX |
|-----------|------|------|-------|-----|
| Exchange Online | ✅ Documented | ✅ Documented | ❌ 365d < 2190d | ❌ 365d < 2555d |
| Google Drive | ❌ No policy | ❌ No policy | ❌ No policy | ❌ No policy |
```

### Change Audit Timeline

```
## Recent Retention Changes (Last 90 Days)

| Date | User | Connector | Action | Old Value | New Value |
|------|------|-----------|--------|-----------|-----------|
| 2025-12-01 | admin@corp.com | Exchange | Policy Updated | P90D (90d) | P365D (365d) |
| 2025-11-15 | admin@corp.com | SharePoint | Policy Set | Not set | P1Y (365d) |
```

### Enforcement Verification

```
## Enforcement Verification

| Connector | Policy | Oldest Snapshot | Expected Max | Status |
|-----------|--------|-----------------|--------------|--------|
| Exchange | 365 days | 362 days | 365 days | ✅ Enforced |
| SharePoint | 365 days | 412 days | 365 days | ⚠️ Over-retained |
```

---

## Advanced Features

### Multi-Framework Compliance Assessment

The skill can simultaneously evaluate retention against multiple regulatory frameworks. This is critical for organizations subject to overlapping regulations (e.g., a European financial institution subject to GDPR, NIS2, and DORA).

```python
# Assess against all relevant frameworks
frameworks = ['gdpr', 'nis2', 'dora', 'hipaa', 'sox']
matrix = generate_compliance_matrix(connectors, frameworks)

# Each entry contains per-connector, per-framework compliance status
for entry in matrix:
    connector_name = entry['connector_name']
    for fw_result in entry['framework_results']:
        print(f"{connector_name} - {fw_result['framework']}: {fw_result['icon']} {fw_result['description']}")
```

### Retention Gap Analysis

Identify connectors without explicit retention policies — the most critical compliance finding.

```python
audit = audit_retention_policies(connectors)
missing = [p for p in audit['policy_details'] if not p['is_set']]

if missing:
    # 🔴 HIGH PRIORITY: Connectors without retention policies
    for m in missing:
        print(f"🔴 {m['connector_name']} ({m['connector_type']}): No retention policy configured")
```

### Change Attribution

Link retention changes to specific users and timestamps for full accountability.

```python
changes = detect_recent_changes(audit_events, connectors)
for change in changes:
    print(f"{change['timestamp']}: {change['token']} changed {change['connector_name']}")
    if change.get('old_value') and change.get('new_value'):
        print(f"  From: {change['old_value']} -> To: {change['new_value']}")
```

### Over-Retention Detection (GDPR Right to Erasure)

Data stored beyond the stated retention period may violate GDPR's data minimization principle and right to erasure requirements.

```python
for result in enforcement_results:
    if result['over_retained']:
        days_over = result['oldest_snapshot_age_days'] - result['expected_max_age_days']
        print(f"⚠️ {result['connector_name']}: {days_over} days over-retained")
        print(f"   GDPR Art. 5(1)(e): Data kept longer than necessary")
```

---

## Error Handling

### Common Error Scenarios

| Error | Cause | Handling |
|-------|-------|----------|
| Empty connector list | No connectors configured | Report as "No connectors found — unable to perform retention audit" |
| Missing `backup_retention` | Field not present on connector | Treat as unset policy; flag as ❌ Non-compliant |
| Invalid ISO 8601 duration | Malformed retention string | Log warning, treat as unset, include in findings |
| Audit log empty | No events in timeframe | Note "No audit events found in the specified period" |
| Snapshot retrieval failure | Connector GUID invalid or inaccessible | Skip enforcement check for that connector, note in report |
| `retention_updated` missing | Field not populated | Use audit log as sole source of change history |

### Graceful Degradation

The skill operates in a layered fashion. If any data source is unavailable, the remaining sources still produce value:

1. **Connectors only**: Policy inventory + framework compliance (core value)
2. **Connectors + audit logs**: Adds change tracking
3. **Connectors + audit logs + snapshots**: Full enforcement verification

```python
# Graceful handling if audit logs are unavailable
try:
    audit_logs = get_audit_log_history(duration="P90D")
except Exception:
    audit_logs = []
    # Note: Change tracking will rely on retention_updated field only
```

---

## Best Practices

### For Compliance Officers / DPOs

1. **Run quarterly retention audits** — Regulatory requirements evolve; schedule regular reviews
2. **Always check all applicable frameworks** — Organizations often fall under multiple regulatory regimes
3. **Prioritize unset policies** — A missing retention policy is the most critical finding
4. **Document exceptions** — If a connector intentionally has no retention policy, document the rationale
5. **Monitor change frequency** — Frequent retention changes may indicate configuration instability

### For IT Managers

1. **Standardize retention periods** — Use consistent durations across similar connector types
2. **Set retention policies before production** — Configure retention at connector creation time
3. **Verify enforcement monthly** — Ensure actual snapshot age matches policy
4. **Use the `retention_updated` field** — It provides authoritative last-change timestamps
5. **Coordinate with legal/compliance** — Retention periods should be driven by regulatory requirements, not storage concerns

### Policy Configuration Recommendations

| Scenario | Recommended Retention | Rationale |
|----------|----------------------|-----------|
| General business data | P1Y (365 days) | Standard business cycle coverage |
| HIPAA-regulated data | P6Y (2190 days) | Minimum regulatory requirement |
| SOX financial records | P7Y (2555 days) | Minimum regulatory requirement |
| GDPR personal data | As documented in ROPA | Data minimization principle |
| Transient/test data | P90D (90 days) | Minimal retention for non-critical data |

---

## Common User Requests

### "Show me our retention policies"
Run Step 1 and Step 2 to produce the Policy Inventory Table. Highlight any unset policies.

### "Are we GDPR compliant on retention?"
Run the full workflow with `frameworks=['gdpr']`. For GDPR, the key question is whether a policy is documented (set), not whether it meets a specific day count.

### "Are we HIPAA compliant?"
Run with `frameworks=['hipaa']`. Highlight any connectors with retention below 2190 days (6 years).

### "Who changed our retention policies?"
Run Steps 4 and 5 to produce the Change Audit Timeline. Correlate audit log events with `retention_updated` timestamps.

### "Is our retention actually being enforced?"
Run Step 6 for enforcement verification. Compare oldest snapshot age against stated policy for each connector.

### "Run a full retention compliance audit"
Execute the complete 7-step workflow with all applicable frameworks. Produce the full report including inventory, compliance matrix, change timeline, enforcement verification, findings, and recommendations.

### "Which connectors don't have retention policies?"
Run Step 1 and filter for connectors where `backup_retention` is null or empty. These are the highest-priority findings.

### "Compare our retention against NIS2 and DORA"
Run with `frameworks=['nis2', 'dora']`. Both require documented backup policies as part of broader resilience requirements.

---

## Cross-Skill Investigation Workflows

### Retention + Backup Health Assessment

When retention policy issues are found, investigate backup health to determine if the underlying backup infrastructure is functioning correctly.

```
1. Retention Policy Auditor → Identifies connectors with misconfigured retention
2. Backup Health Assessment → Checks if those connectors are actually producing backups
3. Combined finding: "Connector X has P1Y retention but hasn't backed up in 30 days"
```

### Retention + Audit Event Analyzer

For deep investigation of retention changes, combine with the Audit Event Analyzer skill.

```
1. Retention Policy Auditor → Identifies recent retention changes
2. Audit Event Analyzer → Provides full context on the user session and related changes
3. Combined finding: "Admin changed retention on 5 connectors in a single session"
```

### Retention + License & Connector Inventory

Cross-reference retention policies with the full connector inventory for organizational context.

```
1. License & Connector Inventory → Full connector listing with org context
2. Retention Policy Auditor → Retention compliance overlay
3. Combined finding: "3 of 12 connectors in Production org lack retention policies"
```

---

## Skill Integration Points

### Data Shared with Other Skills

| Data Point | Used By | Purpose |
|------------|---------|---------|
| `backup_retention` parsed to days | Backup Health Assessment | Context for snapshot age evaluation |
| Compliance matrix results | Executive reporting | Organization-wide compliance posture |
| Change timeline | Audit Event Analyzer | Enrichment of audit investigation |
| Enforcement verification | Backup Health Assessment | Verification of backup lifecycle |

### Data Consumed from Other Skills

| Source Skill | Data Point | Usage |
|-------------|------------|-------|
| License & Connector Inventory | Connector list with org context | Organizational grouping of retention policies |
| Backup Health Assessment | Backup frequency and status | Context for enforcement verification |
| Audit Event Analyzer | Detailed audit event context | Enrichment of retention change events |

---

## Technical Notes

### MCP Functions Used

| Function | Purpose | Parameters |
|----------|---------|------------|
| `get_cloud_connectors(connectorType="cloud")` | Retrieve all connectors with retention fields | None |
| `get_audit_log_history()` | Fetch audit events for change tracking | `duration="P90D"` |
| `get_snapshot_range()` | Retrieve snapshots for enforcement verification | `guid`, `timespan`, `count=99` |

### Key Connector Fields

| Field | Type | Description |
|-------|------|-------------|
| `backup_retention` | String (ISO 8601 duration) | Configured retention period, e.g., "P365D", "P1Y", "P90D" |
| `retention_updated` | String (ISO 8601 timestamp) | When the retention policy was last modified |
| `guid` | String (UUID) | Connector unique identifier for snapshot queries |
| `name` | String | Human-readable connector name |
| `type` | String | Connector type key, e.g., "o365-admin", "gsuite" |

### Time Calculations

- ISO 8601 duration parsing: `P1Y` = 365 days, `P6M` = 180 days, `P1W` = 7 days
- Month approximation: 1 month = 30 days (standard approximation)
- Year approximation: 1 year = 365 days (leap years not considered for compliance thresholds)
- Enforcement tolerance: snapshots within 7 days of expected maximum age are considered properly enforced
- Over-retention threshold: snapshots older than policy + 30 days trigger a warning

### Error Resilience

- Missing `backup_retention`: treated as unset (0 days), flagged as ❌
- Missing `retention_updated`: change tracking falls back to audit logs only
- Malformed ISO 8601: logged as invalid, treated as unset
- Empty audit log response: report notes absence of change data
- Snapshot retrieval failure: enforcement check skipped for that connector with a note

---

## Success Metrics

A successful retention policy audit should provide:

1. **Complete inventory** — Every connector accounted for with retention status
2. **Zero unset policies** — All connectors have explicit retention policies configured
3. **Framework compliance** — All applicable regulatory minimums met
4. **Change accountability** — All recent changes attributed to specific users and timestamps
5. **Enforcement confirmation** — Actual snapshot retention matches stated policy
6. **Actionable recommendations** — Clear next steps for any non-compliant findings
7. **Audit-ready documentation** — Report suitable for regulatory audit evidence
