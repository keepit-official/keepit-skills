---
name: keepit-backup-failure-root-cause-analyzer
description: Automated root cause analysis for Keepit backup failures with cross-source correlation. Use when users ask why a backup failed, investigate backup errors, troubleshoot recurring failures, or need failure diagnosis. Triggers on keywords like "why did backup fail", "root cause", "backup error", "failure investigation", "troubleshoot backup", "diagnose failure", "backup not working".
---

# Keepit Backup Failure Root Cause Analyzer

## Overview

The Backup Failure Root Cause Analyzer is a diagnostic skill that systematically investigates why Keepit backup jobs have failed, correlates failures with environmental changes, classifies root causes, and provides actionable remediation guidance. It combines job history analysis, error parsing, audit log correlation, health checks, and snapshot gap assessment to deliver comprehensive failure investigations.

**Target Persona:** Backup Administrators, IT Managers, Support Engineers

**Primary Use Cases:**
- Investigating why a specific backup job failed
- Diagnosing recurring backup failures across connectors
- Correlating failures with configuration or environmental changes
- Assessing data risk from backup gaps caused by failures
- Generating remediation steps and post-fix verification checklists

**Trigger Keywords:**
- "why did backup fail", "root cause", "backup error"
- "failure investigation", "troubleshoot backup"
- "diagnose failure", "backup not working"
- "backup keeps failing", "recurring failure"
- "what caused the backup error"

## Core Workflow

### Step 1: Identify the Failure

Retrieve job history for the target connector and isolate failed jobs.

```python
# Get recent job history for the connector
jobs = get_job_history(guid=connector['guid'], duration="P7D")

# Filter to failed jobs — jobs with a 'failed' timestamp
failed_jobs = [j for j in jobs if j.get('failed')]

# Sort by failure time, most recent first
failed_jobs.sort(key=lambda j: j['failed'], reverse=True)

# If user asked about a specific failure, match by time or description
# Otherwise, investigate the most recent failure
target_failure = failed_jobs[0] if failed_jobs else None
```

If no failed jobs are found in the requested window, expand the search:

```python
# Expand to 30 days if no failures in 7 days
if not failed_jobs:
    jobs = get_job_history(guid=connector['guid'], duration="P30D")
    failed_jobs = [j for j in jobs if j.get('failed')]
```

### Step 2: Parse Error Details

Extract structured error information from the execsummary XML field.

```python
# Parse the execsummary XML for error details
from scripts.rootcause_utils import parse_execsummary

execsummary = parse_execsummary(target_failure.get('execsummary', ''))

# Key fields extracted:
# - execsummary['errors']        → List of error messages
# - execsummary['exit_reason']   → Why the job terminated
# - execsummary['warnings']      → Warning messages preceding failure
# - execsummary['details']       → Additional context fields
```

### Step 3: Gather Surrounding Context

Pull audit log events around the failure time window for correlation.

```python
# Get audit events from the past 30 days
audit_logs = get_audit_log_history(duration="P30D")

# Correlate events within +/- 24 hours of the failure
from scripts.rootcause_utils import correlate_failure_with_audit

correlation = correlate_failure_with_audit(
    failure_time=target_failure['failed'],
    audit_events=audit_logs,
    window_hours=24
)

# correlation['events_before']   → Events leading up to failure
# correlation['events_after']    → Events after the failure
# correlation['config_changes']  → Configuration modifications
# correlation['auth_events']     → Authentication-related events
# correlation['total_correlated'] → Count of correlated events
```

### Step 4: Check Current State

Verify whether the connector is still in a failed/unhealthy state.

```python
# Check connector health status
health = get_connector_health(guid=connector['guid'])

# Possible states:
# - "healthy"    → Connector recovered on its own
# - "unhealthy"  → Still broken, needs attention
# - "critical"   → Critical issues, needs immediate attention
# - "unknown"    → Cannot determine state
```

### Step 5: Check Active Recovery

Determine if a retry or recovery job is already running.

```python
# Check for active jobs (retry in progress?)
active = get_active_jobs(guid=connector['guid'])

# If active jobs exist, a retry may already be underway
# Report this to avoid duplicate remediation efforts
if active:
    print(f"Recovery job detected: {active[0].get('description', 'Unknown')}")
    print(f"Started: {active[0].get('started', 'Unknown')}")
```

### Step 6: Assess Data Impact

Calculate the backup gap and data at risk since the last successful backup.

```python
# Get the latest successful snapshot
latest = get_latest_snapshot(guid=connector['guid'])

# Get snapshot history for gap analysis
snapshots = get_snapshot_range(guid=connector['guid'], timespan="P30D", count=99)

# Assess data risk
from scripts.rootcause_utils import assess_data_risk

risk = assess_data_risk(latest_snapshot=latest, snapshot_range=snapshots)

# risk['gap_hours']               → Hours since last good backup
# risk['gap_description']         → Human-readable gap description
# risk['risk_level']              → "low" / "medium" / "high" / "critical"
# risk['last_good_backup']        → Timestamp of last successful backup
# risk['data_at_risk_description'] → What data may be unprotected
```

### Step 7: Correlate Failure with Changes

Determine if configuration changes caused or contributed to the failure.

```python
# Get all connectors for cross-reference
connectors = get_cloud_connectors(connectorType="cloud")

# Check if config changes caused the failure
from scripts.rootcause_utils import detect_config_change_causality

causality = detect_config_change_causality(
    failure_time=target_failure['failed'],
    audit_events=audit_logs,
    connectors=connectors
)

# causality['causal_likely']  → True/False
# causality['changes_found']  → List of relevant changes
# causality['time_delta']     → Time between change and failure
# causality['confidence']     → "high" / "medium" / "low"
# causality['description']    → Human-readable causality assessment
```

### Step 8: Classify and Attribute

Categorize the root cause and assign confidence level.

```python
from scripts.rootcause_utils import classify_failure_type, classify_recurrence

# Classify the failure type
classification = classify_failure_type(
    job=target_failure,
    execsummary_parsed=execsummary
)

# classification['type']        → "auth_expired", "config_change", "api_limit",
#                                  "connectivity", "permission_denied",
#                                  "quota_exceeded", "service_unavailable", "unknown"
# classification['confidence']  → "high" / "medium" / "low"
# classification['indicators']  → Evidence supporting classification
# classification['description'] → Human-readable explanation

# Determine if this is a recurring issue
recurrence = classify_recurrence(
    job_history=jobs,
    current_failure=target_failure
)

# recurrence['classification']      → "first" / "recurring" / "chronic"
# recurrence['occurrence_count']     → Number of similar failures
# recurrence['first_seen']           → When this pattern first appeared
# recurrence['pattern_description']  → Description of the failure pattern
```

### Step 9: Generate Resolution Steps

Produce type-specific remediation guidance.

```python
from scripts.rootcause_utils import generate_resolution_steps

# Build context for resolution generation
context = {
    'connector': connector,
    'health': health,
    'execsummary': execsummary,
    'causality': causality,
    'recurrence': recurrence,
    'risk': risk
}

steps = generate_resolution_steps(
    failure_type=classification['type'],
    context=context
)

# Each step contains:
# - step['number']    → Step order
# - step['action']    → Brief action title
# - step['detail']    → Detailed instructions
# - step['priority']  → "critical" / "high" / "medium" / "low"
```

### Step 10: Provide Verification Checklist

Generate post-fix validation steps to confirm the issue is resolved.

```python
from scripts.rootcause_utils import generate_verification_checklist

checklist = generate_verification_checklist(
    failure_type=classification['type']
)

# Each checklist item:
# - item['check']           → What to verify
# - item['how_to_verify']   → How to perform the check
# - item['expected_result'] → What success looks like
```

## Output Formatting Guidelines

### Failure Investigation Header

```
# Backup Failure Root Cause Analysis

**Connector:** {connector_name} ({connector_type})
**Failure Time:** {failure_timestamp}
**Investigation Time:** {now}
**Status:** {current_health_status}
```

### Root Cause Classification Display

Use severity icons to indicate urgency:

- ❌ **Critical** — Backup completely non-functional, data at risk
- ⚠️ **Warning** — Backup degraded, intermittent failures
- ✅ **Resolved** — Issue has been corrected, backup operational

Use priority icons for resolution steps:

- 🔴 **High Priority** — Address immediately
- 🟡 **Medium Priority** — Address within 24 hours
- 🟢 **Low Priority** — Schedule for next maintenance window

### Summary Table Format

```markdown
| Field | Value |
|-------|-------|
| Root Cause | {classification_type} |
| Confidence | {confidence_level} |
| Recurrence | {first / recurring / chronic} |
| Backup Gap | {gap_hours}h ({gap_description}) |
| Risk Level | {risk_icon} {risk_level} |
| Active Recovery | {yes/no} |
```

### Timeline Display

```markdown
## Event Timeline

| Time | Event | Relevance |
|------|-------|-----------|
| {t-2h} | Retention policy updated | 🔴 Likely cause |
| {t-0} | Backup job failed | ❌ Target failure |
| {t+1h} | Retry job started | ✅ Auto-recovery |
```

### Resolution Steps Format

```markdown
## Resolution Steps

### 🔴 Step 1: {action_title}
{detailed_instructions}

### 🟡 Step 2: {action_title}
{detailed_instructions}

### 🟢 Step 3: {action_title}
{detailed_instructions}
```

### Verification Checklist Format

```markdown
## Post-Fix Verification Checklist

- [ ] {check_description}
  - **How:** {how_to_verify}
  - **Expected:** {expected_result}
```

## Advanced Features

### Automatic Time-Window Correlation

The skill automatically correlates audit events with failure timing:

- **-24h to failure:** Events that may have caused the failure
- **Failure to +24h:** Events that may indicate recovery or further degradation
- **Config changes within 4h:** High-confidence causal attribution
- **Auth events within 24h:** Potential token/credential issues

### Config Change Attribution

When audit logs show configuration changes near the failure time:

```python
# Example: "Retention policy changed 2h before first failure"
if causality['causal_likely'] and causality['confidence'] == 'high':
    report += f"⚠️ Configuration change detected {causality['time_delta']} before failure\n"
    report += f"   Change: {causality['changes_found'][0]['description']}\n"
    report += f"   Recommendation: Review and potentially revert this change\n"
```

### Failure Classification Categories

| Category | Indicators | Typical Resolution |
|----------|------------|-------------------|
| `auth_expired` | Token expired, 401 errors, auth failure messages | Refresh or reauthorize credentials |
| `config_change` | Recent config audit events, retention changes | Review and revert recent changes |
| `api_limit` | Rate limit errors, 429 responses, throttling | Adjust backup schedule, stagger jobs |
| `connectivity` | Timeout errors, DNS failures, connection refused | Check network, firewall, DNS settings |
| `permission_denied` | 403 errors, access denied messages | Review and update service account permissions |
| `quota_exceeded` | Storage quota, license limit messages | Increase quota or remove stale data |
| `service_unavailable` | 503 errors, maintenance messages | Wait and retry, check vendor status page |
| `unknown` | No clear indicators | Escalate to support with full diagnostic |

### Recurring vs. New Failure Detection

```python
# Classification thresholds
# 1 occurrence        → "first"     — Investigate root cause
# 2-4 occurrences     → "recurring" — Establish pattern, prioritize fix
# 5+ occurrences      → "chronic"   — Escalate, systemic issue
```

### Data Risk Assessment Thresholds

| Gap Duration | Risk Level | Icon | Action |
|-------------|------------|------|--------|
| < 24 hours | Low | 🟢 | Monitor, standard remediation |
| 24-72 hours | Medium | 🟡 | Prioritize fix, notify stakeholders |
| 72-168 hours | High | 🔴 | Urgent remediation required |
| > 168 hours | Critical | ❌ | Emergency response, executive notification |

## Error Handling

### No Failed Jobs Found

```
✅ No backup failures detected for {connector_name} in the past {duration}.

All recent jobs completed successfully. If you believe a failure occurred,
try expanding the search window:
- "Check for failures in the last 30 days"
- "Show all job history for this connector"
```

### Execsummary Parse Failure

```
⚠️ Could not parse error details from job execution summary.

The job record indicates a failure at {failure_time}, but the error details
could not be extracted. This may indicate a truncated or malformed record.

**Available information:**
- Job failed: {failure_timestamp}
- Job description: {description}
- Connector: {connector_name}

**Recommendation:** Check Keepit admin console for detailed error logs.
```

### Insufficient Audit Data

```
⚠️ Limited audit log data available for correlation.

Only {count} audit events found in the correlation window.
Root cause analysis may be incomplete without full audit context.

**Proceeding with available data...**
```

### Connector Not Found

```
❌ Connector "{connector_name}" not found.

Please verify the connector name or GUID. Available connectors:
{list_of_connectors}
```

## Best Practices

### Investigation Approach

1. **Start with the most recent failure** — It has the freshest context and audit data
2. **Always check current health first** — The issue may already be resolved
3. **Correlate before concluding** — Never attribute root cause without checking audit logs
4. **Assess recurrence** — A first-time failure is different from a chronic one
5. **Quantify data risk** — Stakeholders need to know impact, not just cause

### Escalation Guidelines

- **First occurrence, low risk:** Standard remediation, monitor
- **Recurring, medium risk:** Escalate to team lead, create tracking ticket
- **Chronic, high risk:** Escalate to management, schedule dedicated investigation
- **Any critical risk:** Immediate notification to data protection officer

### Communication Guidelines

- Lead with impact: "Your Exchange backup has a 48-hour gap" before "Token expired"
- Provide time context: "This started failing 2 hours after the retention policy change"
- Be specific about remediation: "Re-authorize the Microsoft 365 connector" not "Fix auth"
- Include verification: "After fixing, run a manual backup and confirm it succeeds"

## Common User Requests

### "Why did my backup fail?"

1. Identify the connector and most recent failure
2. Parse error details from execsummary
3. Classify the failure type
4. Provide root cause with confidence level
5. Give resolution steps

### "Is this a recurring issue?"

1. Pull 30-day job history
2. Classify recurrence pattern
3. Show failure timeline with dates
4. Identify if pattern exists (e.g., every Monday)
5. Recommend schedule or configuration changes

### "What data am I missing?"

1. Get latest snapshot timestamp
2. Calculate backup gap
3. Assess risk level
4. Describe what data may be unprotected
5. Provide urgency context

### "Was it caused by the config change?"

1. Pull audit logs around failure time
2. Run config change causality analysis
3. Show timeline of changes vs. failures
4. Provide confidence assessment
5. Recommend revert if causal

### "What do I need to fix?"

1. Complete root cause analysis
2. Generate type-specific resolution steps
3. Prioritize by urgency
4. Provide verification checklist
5. Estimate time to resolution

### "Give me a full RCA report"

1. Run complete 10-step workflow
2. Format as structured report with all sections
3. Include timeline, classification, impact, resolution
4. Add verification checklist
5. Provide executive summary

## Cross-Skill Investigation Workflows

### With Job History Analyzer

When failure investigation requires broader job trend context:

```python
# Use job-history-analyzer patterns for trend detection
# Then drill into specific failures with this skill
jobs = get_job_history(guid=connector['guid'], duration="P30D")
# Analyze success/failure trends, then investigate individual failures
```

### With Account Health Skill

When failure may be part of a broader account health issue:

```python
# Check overall account health for systemic problems
health = get_connector_health(guid=connector['guid'])
# If multiple connectors are unhealthy, this may be an account-level issue
connectors = get_cloud_connectors(connectorType="cloud")
```

### With Compliance Audit Log

When investigation requires detailed audit trail:

```python
# Get comprehensive audit history for compliance-grade investigation
audit_logs = get_audit_log_history(duration="P30D")
# Use for change management correlation and compliance reporting
```

### With Snapshot Analyzer

When failure impact requires detailed snapshot gap analysis:

```python
# Deep dive into snapshot history for precise gap measurement
snapshots = get_snapshot_range(guid=connector['guid'], timespan="P30D", count=99)
latest = get_latest_snapshot(guid=connector['guid'])
# Combine with failure timeline for complete impact picture
```

### With Retention Policy Auditor

When config change causality involves retention policies:

```python
# Cross-reference retention policy changes with failure timing
connectors = get_cloud_connectors(connectorType="cloud")
# Check retention_updated fields against failure timestamps
```

## Skill Integration Points

| Skill | Integration | When to Use |
|-------|-------------|-------------|
| Job History Analyzer | Trend context for failures | Recurring failures, pattern detection |
| Account Health | Systemic health check | Multiple connector failures |
| Compliance Audit Log | Detailed change tracking | Config change attribution |
| Snapshot Analyzer | Precise gap measurement | Data risk assessment |
| Retention Policy Auditor | Policy change correlation | Retention-related failures |
| Security Incident Investigator | Auth event correlation | Authentication failures |
| Executive Backup Summary | Impact reporting | Management escalation |

## Technical Notes

### MCP Functions Used

| Function | Purpose | Parameters |
|----------|---------|------------|
| `get_job_history` | Retrieve job records | `guid`, `duration` (ISO 8601) |
| `get_audit_log_history` | Retrieve audit events | `duration` |
| `get_connector_health` | Check connector status | `guid` |
| `get_active_jobs` | Check running jobs | `guid` |
| `get_latest_snapshot` | Get most recent snapshot | `guid` |
| `get_snapshot_range` | Get snapshot history | `guid`, `timespan`, `count` |
| `get_cloud_connectors` | List all connectors | `connectorType="cloud"` |

### Time Calculations

- **Failure time parsing:** ISO 8601 format (`2025-01-15T08:30:00Z`)
- **Correlation window:** Default +/- 24 hours from failure time
- **Config change window:** High confidence within 4 hours, medium within 24 hours
- **Backup gap:** Difference between `now` and last successful snapshot
- **Recurrence window:** 30 days for pattern detection
- **Duration formats:** ISO 8601 durations (`P7D` = 7 days, `P30D` = 30 days)

### Error Resilience

- **Missing execsummary:** Fall back to job-level metadata (description, timestamps)
- **Empty audit logs:** Proceed with job-only analysis, note limited correlation
- **Connector health unavailable:** Skip health check, note in report
- **Snapshot data missing:** Estimate gap from job history timestamps
- **Parse failures:** Catch XML parse errors, return raw data with error flag
- **API timeouts:** Retry once, then proceed with partial data and note gaps

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Root cause identified | 85%+ of investigations | Classification != "unknown" |
| Correct classification | 90%+ accuracy | User confirms resolution worked |
| Resolution provided | 100% of investigations | Steps generated for all types |
| Time to diagnosis | < 30 seconds | From query to full RCA report |
| Correlation accuracy | 80%+ | Config changes correctly attributed |
| Risk assessment accuracy | 90%+ | Gap calculation matches reality |
