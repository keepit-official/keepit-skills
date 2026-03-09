---
name: keepit-account-health
description: Comprehensive Keepit backup account health checker and configuration validator. Use when users ask to check Keepit status, verify backup configuration, review account health, audit connector setup, or get an overview of their Keepit backup environment. Triggers on keywords like "Keepit status", "backup health", "check Keepit", "connector overview", "account configuration", "backup setup review".
---

# Keepit Account Health & Configuration Reporter

## Overview

This skill provides comprehensive health checking and configuration validation for Keepit backup accounts. It systematically analyzes account status, connector configuration, backup recency, and operational health to provide actionable insights.

**Primary Use Cases:**
- Initial account setup validation
- Regular health check reporting
- Configuration audits
- Troubleshooting connectivity issues
- Onboarding verification
- Quarterly/monthly backup reviews

**Keywords**: Keepit, backup health, account status, connector check, configuration audit, backup overview, health report, Keepit status

## Core Workflow

### Step 1: Account Information Retrieval

Always start by retrieving the account information to verify basic configuration:

```python
# Get account details
account_info = get_my_account_info()

# Verify critical fields:
# - enabled: Must be true
# - subscribed: Must be true
# - created: Account creation date
# - product: Product GUID assignment
```

**Key Validations:**
- Account must be enabled (enabled=true)
- Account must be subscribed (subscribed=true)
- Note the account creation date for context
- Store product and parent GUIDs for reference

### Step 2: Connector Discovery

Retrieve all configured connectors to understand backup coverage:

```python
# Get cloud connectors (primary backup sources)
cloud_connectors = get_cloud_connectors(connectorType="cloud")
```

**Analysis Points:**
- Count total connectors by type
- Identify connector types (o365-admin, azure-ad, sforce, etc.)
- Note creation dates to understand deployment timeline
- Check for empty connector lists (potential configuration issue)

### Step 3: Connector Health Assessment

For each connector discovered, check its health status:

```python
for connector in cloud_connectors:
    health = get_connector_health(guid=connector['guid'])

    # Analyze:
    # - health string (e.g., "healthy", "unhealthy", "critical")
```

**Health Categories (based on `health` string from API):**
- **Healthy**: `health` is "healthy"
- **Unhealthy**: `health` is "unhealthy"
- **Critical**: `health` indicates critical issues

**Important**: The `get_connector_health` endpoint returns a `health` string. This is the sole source for connector health assessment.

### Step 4: Backup Recency Verification

Check when the last successful backup completed for each connector:

```python
for connector in cloud_connectors:
    latest_snapshot = get_latest_snapshot(guid=connector['guid'])
    
    # Calculate time since last backup
    # Flag connectors with stale backups (>24-48 hours)
```

**Recency Thresholds:**
- **Current**: Backup within last 24 hours
- **Acceptable**: Backup within 24-48 hours
- **Stale**: Backup older than 48 hours (requires investigation)
- **No snapshots**: Critical - connector may not be properly configured

### Step 5: Check Currently Running Jobs

Check for active/in-progress jobs to provide real-time context:

```python
for connector in cloud_connectors:
    active_jobs = get_active_jobs(guid=connector['guid'])

    # active_jobs returns same schema as get_job_history
    # Each job has: type, progress (decimal "0.0" to "1.0"), started, description
    # If any jobs are active, report them:
    for job in active_jobs:
        progress_pct = float(job.get('progress', '0')) * 100
        # e.g., "Backup currently running (45% complete)"
```

**Why this matters:** Without checking active jobs, the health check may report "last backup was 23 hours ago" when a backup is actually in progress right now. Reporting active jobs prevents false alarms and gives users a complete picture.

**Add to report as:**

```markdown
### Currently Running Jobs

| Connector | Job Type | Progress | Started |
|-----------|----------|----------|---------|
| Microsoft 365 Backup | backup | ⏳ 45% | 12 minutes ago |
```

If no jobs are active, omit this section or note "No jobs currently running."

Synthesize all collected data into a clear, actionable report:

**Report Structure:**

1. **Executive Summary**
   - Account status (enabled/subscribed)
   - Total connector count
   - Overall health rating
   - Critical issues count

2. **Account Details**
   - Account GUID
   - Creation date
   - Product assignment
   - Subscription status

3. **Connector Overview Table**
   - Connector name
   - Type
   - Health status
   - Last backup timestamp
   - Retention policy
   - Age since creation

4. **Health Analysis**
   - Connectors requiring attention
   - Backup recency concerns
   - Configuration gaps

5. **Recommendations**
   - Immediate actions needed
   - Scheduled maintenance items
   - Best practice suggestions

## Output Formatting Guidelines

### Use Tables for Connector Data

Present connector information in clear, scannable tables:

```markdown
| Connector Name | Type | Health | Last Backup | Retention |
|---------------|------|--------|-------------|-----------|
| Microsoft 365 Backup | o365-admin | ✅ Healthy | 2 hours ago | ✅ 1 year |
| Entra ID Backup | azure-ad | ⚠️ Unhealthy | 1 day ago | ❌ Not set |
```

### Retention Policy Display

Include retention policy from `backup_retention` and `retention_updated` connector fields:

```python
from health_utils import parse_retention_policy, assess_retention_compliance

for connector in cloud_connectors:
    retention = parse_retention_policy(connector.get('backup_retention'))
    status, icon, desc = assess_retention_compliance(retention, min_days=30)
    # Add to connector overview table
    # Note: backup_retention and retention_updated are optional fields —
    # some connectors may not have them set
```

Flag connectors with no retention policy or very short retention. Retention policies should be reviewed against organizational and regulatory requirements (GDPR, HIPAA, etc.).

### Health Status Icons

Use consistent visual indicators:
- ✅ Healthy / Enabled / Current
- ⚠️ Unhealthy / Stale
- ❌ Critical / Disabled / Failed
- ℹ️ Info / No data

### Time Formatting

Present timestamps in human-readable format:
- "2 hours ago"
- "1 day ago"
- "Created 3 months ago"
- Include ISO timestamp in parentheses for precision when needed

### Priority Flagging

Clearly highlight items requiring attention:

**🔴 Critical Issues:** (Require immediate action)
- Disabled or unsubscribed accounts
- Connectors with no snapshots
- Critical health status
- Backups older than 7 days

**🟡 Warnings:** (Should be addressed soon)
- Stale backups (48+ hours)
- Unhealthy health status

**🟢 Healthy:** (No action needed)
- Recent backups
- Healthy status

### Step 7: Backup Continuity Analysis (Optional)

For deeper analysis, use `get_snapshot_range` to examine backup continuity over time:

```python
for connector in cloud_connectors:
    snapshots = get_snapshot_range(
        guid=connector['guid'],
        timespan="P30D",   # Last 30 days
        count=99,           # Maximum snapshots
        reverse=False       # Oldest first
    )

    # Analyze gaps in backup coverage
    from health_utils import analyze_snapshot_gaps, analyze_snapshot_size_trend

    gap_analysis = analyze_snapshot_gaps(snapshots, expected_interval_hours=24)
    # gap_analysis['gaps'] — periods with no snapshots
    # gap_analysis['continuity_status'] — 'good', 'warning', or 'critical'
    # gap_analysis['max_gap_hours'] — largest gap found

    size_trend = analyze_snapshot_size_trend(snapshots)
    # size_trend['growth_percent'] — size change over period
    # size_trend['trend'] — 'growing', 'stable', or 'shrinking'
```

**When to use:** Run continuity analysis when:
- A connector shows stale backups in Step 4
- Preparing compliance reports that require proof of continuous protection
- Capacity planning (use size trends to forecast storage needs)
- Verifying RPO targets are being met

**Continuity Thresholds:**
- **Good**: No gap exceeds 1.5x the expected interval
- **Warning**: Gaps up to 3x the expected interval
- **Critical**: Any gap exceeds 3x the expected interval

**Add to report as:**

```markdown
### Backup Continuity (Last 30 Days)

| Connector | Snapshots | Max Gap | Avg Interval | Partial/Complete | Status |
|-----------|-----------|---------|--------------|------------------|--------|
| Microsoft 365 | 30 | 25.2h | 24.1h | 0p / 30c | ✅ Good |
| Entra ID | 28 | 52.3h | 25.7h | 2p / 26c | ⚠️ Warning |
```

## Advanced Features

### Connector Name Matching

The `get_connector_health` function accepts either:
- Full connector GUID
- Exact connector name
- Partial connector name

This allows users to ask: "Check the health of my Microsoft connector" or "How is the Entra backup doing?"

### Timeframe Analysis

When checking backup recency or job history, support flexible timeframes:
- "within the last day"
- "last week"
- "since Monday"

Convert these to ISO 8601 duration format (e.g., "P1D", "P7D").

### Proactive Issue Detection

Look for patterns that indicate problems:
- Multiple connectors with unhealthy or critical health status
- Gradual increase in backup times
- Connectors created but never backed up
- Retention policy gaps

## Error Handling

### Account Access Issues

If `get_my_account_info` fails:
- Verify API connectivity
- Check authentication/authorization
- Suggest contacting Keepit support

### Missing Connectors

If `get_cloud_connectors` returns empty:
- Confirm this is a new account
- Suggest running connector setup
- Provide link to Keepit documentation

### Health Check Failures

If `get_connector_health` fails for specific connector:
- Note the connector but continue checking others
- Flag in report as "Unable to retrieve health data"
- Suggest manual verification in Keepit UI

## Best Practices

1. **Always start with account info** - Verify basics before diving into details
2. **Check all connectors** - Don't stop at the first issue
3. **Provide context** - Include timeframes and thresholds in analysis
4. **Be actionable** - Every issue should have a suggested next step
5. **Stay concise** - Users want quick insights, not data dumps
6. **Use progressive disclosure** - Summary first, details on request

## Common User Requests

**"Check my Keepit status"**
→ Full workflow (Steps 1-5)

**"Is my backup healthy?"**
→ Focus on Steps 3-4 (health + recency)

**"What connectors do I have?"**
→ Step 2 only (connector list)

**"When was my last backup?"**
→ Step 4 only (snapshot recency)

**"Give me a Keepit report"**
→ Full workflow with formatted report output

## Example Interactions

### Example 1: Quick Health Check

**User:** "Check my Keepit backup status"

**Process:**
1. Get account info → Verify enabled/subscribed
2. Get connectors → Found 3 cloud connectors
3. Check health for each → 2 healthy, 1 unhealthy
4. Check latest snapshots → All within 24 hours
5. Generate summary report

**Output:** Brief status with table of connectors and any warnings

### Example 2: New Account Validation

**User:** "I just set up Keepit, can you verify everything is configured correctly?"

**Process:**
1. Get account info → Confirm account created recently
2. Get connectors → Check for expected connectors
3. Check health → Verify all healthy
4. Check snapshots → Verify initial backups completed
5. Provide onboarding confirmation

**Output:** Validation checklist with setup recommendations

### Example 3: Troubleshooting

**User:** "My Microsoft 365 backup seems to be having issues"

**Process:**
1. Get connectors → Find Microsoft 365 connector by name
2. Get health → Check health status
3. Get latest snapshot → Check backup recency
4. Get job history (if needed) → Review recent backup jobs
5. Provide diagnostic information

**Output:** Targeted troubleshooting report with specific recommendations

## Cross-Skill Investigation Workflows

When the health check reveals issues, chain into other skills with concrete tool call sequences:

### Unhealthy Connector → Job History Deep Dive

When a connector shows unhealthy status or stale backups:

```python
# 1. Health check identified unhealthy connector
unhealthy_guid = "2gfd9w-2l3knw-s50ffl"

# 2. Chain into job history analysis for that connector
job_history = get_job_history(guid=unhealthy_guid, duration="P7D")
# Use analysis_utils.identify_failure_patterns(job_history) for root cause

# 3. Check if a backup is currently running
active_jobs = get_active_jobs(guid=unhealthy_guid)
# If active, the "unhealthy" status may resolve once the job completes
```

### Stale Backup → Snapshot Continuity Check

When a connector's last backup is older than expected:

```python
# 1. Health check found stale backup (>48h old)
stale_guid = "2gfd9w-2l3knw-s50ffl"

# 2. Get full snapshot history to understand the gap
snapshots = get_snapshot_range(guid=stale_guid, timespan="P30D", count=99)
# Use health_utils.analyze_snapshot_gaps(snapshots) to find all gaps

# 3. Cross-reference with audit logs for config changes during the gap
audit_logs = get_audit_log_history(duration="P7D")
# Filter for events around the time the gap started
```

### Config Change Impact Verification

When audit logs reveal a configuration change, verify its effect:

```python
# 1. Audit log shows config change at timestamp T
change_time = "2026-02-10T14:00:00Z"
affected_guid = "2gfd9w-2l3knw-s50ffl"

# 2. Check connector health after the change
health = get_connector_health(guid=affected_guid)

# 3. Check latest snapshot to see if backups are still working
latest = get_latest_snapshot(guid=affected_guid)

# 4. Compare job history before and after the change
jobs = get_job_history(guid=affected_guid, duration="P14D")
# Split jobs by change_time and compare success rates
```

## Skill Integration Points

This skill works well with other Keepit skills:

- **Backup Job History Analyzer** - For deeper dive into job failures
- **Snapshot Gap & Continuity Analyzer** - When backup recency shows issues
- **Compliance Audit Log Extractor** - For account activity review

Suggest these follow-up skills when relevant to user needs.

## Technical Notes

### MCP Functions Used

- `get_my_account_info()` - Account status and configuration
- `get_cloud_connectors(connectorType="cloud")` - Connector discovery
- `get_connector_health(guid)` - Health status per connector
- `get_latest_snapshot(guid)` - Backup recency check
- `get_snapshot_range(guid, timespan, count)` - Backup continuity and gap analysis
- `get_active_jobs(guid)` - Currently running jobs

### Time Calculations

When calculating time since last backup:
```python
from datetime import datetime, timezone

def time_since_backup(snapshot_timestamp):
    now = datetime.now(timezone.utc)
    last_backup = datetime.fromisoformat(snapshot_timestamp.replace('Z', '+00:00'))
    delta = now - last_backup
    return delta
```

### Error Resilience

Continue checking all connectors even if one fails:
```python
for connector in connectors:
    try:
        health = get_connector_health(connector['guid'])
    except Exception as e:
        # Log error but continue
        results[connector['name']] = {'error': str(e)}
        continue
```

## Success Metrics

A successful health check provides:
- ✅ Clear account status
- ✅ Complete connector inventory
- ✅ Health status for all connectors
- ✅ Backup recency verification
- ✅ Actionable recommendations
- ✅ Easy-to-scan format

Users should be able to understand their Keepit backup status in under 30 seconds of reading the report.
