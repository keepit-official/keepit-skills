---
name: keepit-weekly-operations-digest
description: Automated weekly backup operations summary and status digest for Keepit environments. Use when users ask for weekly reports, operations summaries, Monday morning status, backup performance reports, or recurring status updates. Triggers on keywords like "weekly report", "weekly summary", "operations digest", "Monday morning report", "weekly status", "backup report", "what happened this week", "weekly review".
---

# Keepit Weekly Operations Digest

## Overview

The Weekly Operations Digest skill produces a comprehensive summary of backup operations
over the past week (or a custom period). It is designed for **Backup Admins** and
**IT Managers** who need a recurring, at-a-glance view of environment health, job
outcomes, configuration changes, and actionable follow-ups.

The digest answers the Monday-morning question: *"What happened with our backups
this week, and what do I need to do about it?"*

**Primary audience:** Backup Administrator, IT Manager
**Typical cadence:** Weekly (Monday morning), on-demand
**Default period:** Last 7 days (ISO 8601 `P7D`)

---

## Core Workflow

### Step 1: Establish Reporting Period

Determine the time window for the digest. Default to the last 7 days unless the
user specifies a different range.

```python
# Default reporting period
duration = "P7D"  # ISO 8601 — last 7 days

# Calculate human-readable boundaries
from datetime import datetime, timezone, timedelta
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=7)

period_label = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"
# e.g. "Feb 10 – Feb 17, 2026"
```

If the user requests a custom range (e.g., "last 14 days", "this month so far"),
adjust `duration` accordingly:

| User phrase           | ISO duration | Days |
|-----------------------|-------------|------|
| "this week"           | P7D         | 7    |
| "last two weeks"      | P14D        | 14   |
| "last 30 days"        | P30D        | 30   |
| "this month"          | P30D        | ~30  |

### Step 2: Gather Account Status

Retrieve account-level information to confirm the environment is reachable and
to display account context at the top of the digest.

```python
account_info = get_my_account_info()

# Extract relevant fields — get_my_account_info returns flat structure
# Fields: id, enabled (bool), created, product, parent, subscribed (bool)
account_id = account_info.get('id', 'Unknown')
account_enabled = account_info.get('enabled', False)
account_subscribed = account_info.get('subscribed', False)
account_state = "Active" if account_enabled and account_subscribed else "Inactive"
```

If the account state is `Inactive` (not enabled or not subscribed), flag this prominently
at the top of the digest as a critical finding.

### Step 3: Inventory Connectors

Retrieve the full list of cloud connectors to know what we are reporting on.

```python
connectors = get_cloud_connectors(connectorType="cloud")

# Build a lookup for quick reference
connector_map = {}
for c in connectors:
    connector_map[c['guid']] = {
        'name': c.get('name', 'Unnamed'),
        'type': c.get('type', 'unknown'),
        'guid': c['guid'],
    }

total_connectors = len(connectors)
```

### Step 4: Assess Current Health

For each connector, retrieve the current health status. This provides the
real-time component of the digest — where things stand right now.

```python
health_data = {}
for connector in connectors:
    health = get_connector_health(guid=connector['guid'])
    health_data[connector['guid']] = health

# Classify health statuses
healthy_count = 0
warning_count = 0
critical_count = 0

for guid, h in health_data.items():
    # get_connector_health returns {"healthStatus": "healthy"|"unhealthy"|"critical"|"unknown"}
    status = h.get('health', 'unknown').lower()
    if status == 'healthy':
        healthy_count += 1
    elif status in ('unhealthy', 'critical'):
        critical_count += 1
    else:
        warning_count += 1
```

**Health icon mapping:**

| Status   | Icon | Meaning                        |
|----------|------|--------------------------------|
| Healthy  | ✅   | Operating normally             |
| Warning  | ⚠️   | Degraded, needs attention      |
| Critical | ❌   | Failing, immediate action      |
| Unknown  | ❓   | Unable to determine            |

### Step 5: Check Active Operations

Check each connector for currently running jobs. This tells the reader what
is in-flight at the moment the digest is generated.

```python
active_operations = {}
for connector in connectors:
    active = get_active_jobs(guid=connector['guid'])
    if active:
        active_operations[connector['guid']] = active
```

If active jobs are found, include a short "Currently Running" section so the
reader knows the digest is a snapshot, not a final state.

### Step 6: Compile Job History

This is the core data-gathering step. Retrieve job history for every connector
over the reporting period.

```python
all_jobs = {}  # keyed by connector GUID
for connector in connectors:
    jobs = get_job_history(guid=connector['guid'], duration="P7D")
    all_jobs[connector['guid']] = jobs

# Classify each job
for guid, job_list in all_jobs.items():
    for job in job_list:
        if job.get('active'):
            job['_status'] = 'running'
        elif job.get('failed'):
            job['_status'] = 'failed'
        else:
            job['_status'] = 'successful'
```

**Key metrics derived from job history:**

- Total jobs executed
- Successful job count and percentage
- Failed job count and percentage
- Average jobs per connector per day
- Peak activity day/time

### Step 7: Review Audit Events

Retrieve audit log entries to capture configuration changes, user actions,
and other administrative events during the period.

```python
audit_logs = get_audit_log_history(duration="P7D")

# Extract metadata from each event
for event in audit_logs:
    meta = {}
    for item in event.get('metadata', []):
        param = item.get('parameter', {})
        if param.get('key'):
            meta[param['key']] = param.get('value', '')
    event['_extracted_metadata'] = meta
```

**Audit event categories to highlight:**

- Connector creation or deletion
- Connector configuration changes
- User or token changes
- Policy modifications
- Retention rule changes

### Step 8: Check Backup Freshness

For each connector, check when the most recent backup was taken. Stale
backups are a key risk indicator.

```python
latest_snapshots = {}
for connector in connectors:
    latest = get_latest_snapshot(guid=connector['guid'])
    latest_snapshots[connector['guid']] = latest

# Flag stale backups (no backup in > 48 hours)
from datetime import datetime, timezone, timedelta
stale_threshold = datetime.now(timezone.utc) - timedelta(hours=48)

stale_connectors = []
for guid, snap in latest_snapshots.items():
    # get_latest_snapshot returns {"tstamp": ..., "size": ..., "type": "p"|"c", "account": ...} or null
    if snap and snap.get('tstamp'):
        snap_time = parse_iso_timestamp(snap['tstamp'])
        if snap_time < stale_threshold:
            stale_connectors.append(connector_map[guid]['name'])
```

**Freshness classification:**

| Age          | Label      | Icon |
|--------------|-----------|------|
| < 24 hours   | Fresh     | ✅   |
| 24–48 hours  | Aging     | ⚠️   |
| > 48 hours   | Stale     | ❌   |
| No snapshot  | Missing   | ❌   |

### Step 9: Analyze Backup Continuity

Retrieve the snapshot range over the week to detect gaps — periods where
backups should have occurred but did not.

```python
snapshot_ranges = {}
for connector in connectors:
    snapshots = get_snapshot_range(
        guid=connector['guid'],
        timespan="P7D",
        count=99
    )
    snapshot_ranges[connector['guid']] = snapshots

# Detect gaps (> 36 hours between consecutive snapshots)
gap_threshold = timedelta(hours=36)

gaps = []
for guid, snaps in snapshot_ranges.items():
    if not snaps or len(snaps) < 2:
        continue
    sorted_snaps = sorted(snaps, key=lambda s: s.get('timestamp', ''))
    for i in range(1, len(sorted_snaps)):
        prev_time = parse_iso_timestamp(sorted_snaps[i-1]['timestamp'])
        curr_time = parse_iso_timestamp(sorted_snaps[i]['timestamp'])
        delta = curr_time - prev_time
        if delta > gap_threshold:
            gaps.append({
                'connector': connector_map[guid]['name'],
                'gap_start': sorted_snaps[i-1]['timestamp'],
                'gap_end': sorted_snaps[i]['timestamp'],
                'gap_hours': delta.total_seconds() / 3600,
            })
```

### Step 10: Compile Metrics and Generate Digest

Aggregate all gathered data into a structured digest. Identify notable events,
generate action items, and format the final report.

```python
# Aggregate totals
total_jobs = sum(len(j) for j in all_jobs.values())
failed_jobs = sum(
    1 for jobs in all_jobs.values()
    for j in jobs if j.get('failed')
)
successful_jobs = total_jobs - failed_jobs
success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0

# Compile the digest structure
digest = {
    'period': period_label,
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'week_at_a_glance': {
        'total_jobs': total_jobs,
        'successful_jobs': successful_jobs,
        'failed_jobs': failed_jobs,
        'success_rate': round(success_rate, 1),
        'total_connectors': total_connectors,
        'healthy_connectors': healthy_count,
        'gaps_detected': len(gaps),
        'audit_events': len(audit_logs),
        'notable_events': len(notable_events),
    },
    'connector_table': per_connector_rows,
    'failures': grouped_failures,
    'changes': audit_summary,
    'continuity': gaps,
    'action_items': action_items,
}
```

---

## Output Formatting Guidelines

### Week at a Glance

Present the top-level summary as a compact block:

```
## 📊 Weekly Operations Digest
**Period:** Feb 10 – Feb 17, 2026
**Account:** Contoso Corp (Active)

### Week at a Glance
| Metric               | Value       |
|----------------------|-------------|
| Total Jobs           | 142         |
| Success Rate         | 97.2%       |
| Failed Jobs          | 4           |
| Connectors           | 8           |
| Healthy Connectors   | 7 ✅        |
| Backup Gaps          | 1 ⚠️        |
| Config Changes       | 3           |
| Action Items         | 2           |
```

### Per-Connector Status Table

```
### Connector Status
| Connector          | Type           | Health | Last Backup   | Jobs | Failures | Rate   |
|-------------------|----------------|--------|---------------|------|----------|--------|
| M365 Production   | Microsoft 365  | ✅     | 2h ago        | 28   | 0        | 100%   |
| Entra ID Prod     | Entra ID       | ✅     | 4h ago        | 14   | 1        | 92.9%  |
| Salesforce CRM    | Salesforce     | ⚠️     | 26h ago       | 12   | 3        | 75.0%  |
```

### Failures & Issues

Group failures by pattern and present with severity:

```
### Failures & Issues
🔴 **Authentication Failures** (3 occurrences)
   Connectors: Salesforce CRM, Zendesk Support
   First seen: Feb 12, Last seen: Feb 14
   Pattern: OAuth token refresh failure

🟡 **Timeout Errors** (1 occurrence)
   Connector: M365 Production
   Seen: Feb 13
   Pattern: API rate limit exceeded, job retried successfully
```

### Configuration Changes

```
### Configuration Changes
| When         | Who           | Action                          |
|-------------|---------------|---------------------------------|
| Feb 11 09:15 | admin@corp   | Created connector "Power BI"    |
| Feb 13 14:30 | svc-backup   | Modified retention policy        |
| Feb 15 11:00 | admin@corp   | Updated Salesforce credentials   |
```

### Backup Continuity

```
### Backup Continuity
⚠️ **1 gap detected**
- **Salesforce CRM**: 38-hour gap (Feb 12 18:00 → Feb 14 08:00)
  Likely cause: Authentication failure during this window
```

### Action Items

Present action items in priority order:

```
### Action Items
1. 🔴 **Review Salesforce authentication** — 3 auth failures this week; re-authorize OAuth connection
2. 🟡 **Investigate backup gap** — Salesforce CRM had a 38-hour gap; confirm data coverage
3. 🟢 **Review new Power BI connector** — Created Feb 11; verify initial backup completed
```

---

## Advanced Features

### Week-over-Week Comparison

When previous-week data is available (or the user asks for trend analysis),
show deltas:

```
### Trend (vs. Previous Week)
| Metric         | This Week | Last Week | Delta  |
|---------------|-----------|-----------|--------|
| Success Rate   | 97.2%     | 94.8%     | +2.4%  |
| Failed Jobs    | 4         | 7         | -3     |
| Total Jobs     | 142       | 138       | +4     |
| Backup Gaps    | 1         | 2         | -1     |
```

### Connector-Type Grouping

For environments with many connectors, group by type:

```python
# Group connectors by friendly type
from collections import defaultdict
by_type = defaultdict(list)
for guid, info in connector_map.items():
    friendly = format_connector_type(info['type'])
    by_type[friendly].append(info)
```

### Scheduled Digest Mode

When the user wants a recurring report, note:
- The skill generates the same report structure each time
- The user can request "compare to last week" to get trend data
- Suggest the user run the digest on Monday mornings or after maintenance windows

### Executive Summary Mode

For IT Managers who want a shorter overview:
- Show only Week at a Glance and Action Items
- Collapse the connector table to connectors with issues only
- Omit audit changes unless they are high-severity

---

## Error Handling

### API Failures During Data Collection

```python
# If a connector's health check fails, note it and continue
try:
    health = get_connector_health(guid=connector['guid'])
except Exception as e:
    health = {'healthStatus': 'unknown', '_error': str(e)}
    # Include in digest as "Unable to assess"
```

### Empty Data Scenarios

- **No jobs in period:** Report "No backup jobs recorded" and flag as a concern
- **No connectors:** Report "No connectors configured" and suggest setup
- **No audit events:** Report "No configuration changes detected" (this is normal)
- **No snapshots:** Flag as critical — the connector may be newly created or broken

### Partial Data Collection

If some connectors fail to return data, still generate the digest for the
connectors that succeeded. Include a "Data Collection Issues" section listing
any connectors that could not be queried.

```
### Data Collection Notes
⚠️ Unable to retrieve job history for: Dynamics 365 (API timeout)
   Digest excludes this connector's metrics.
```

---

## Best Practices

1. **Always start with account info** — Confirms connectivity and provides context
2. **Process connectors in parallel conceptually** — Gather all data before analysis
3. **Flag anomalies, not just failures** — A connector with zero jobs is suspicious
4. **Provide context with numbers** — "4 failures" is less useful than "4 failures (up from 1 last week)"
5. **Keep action items actionable** — Include the specific connector and suggested next step
6. **Respect the user's time** — Lead with the summary, details below
7. **Default to 7 days** — Only change the period if the user explicitly requests it
8. **Include generation timestamp** — The reader should know when the digest was created
9. **Group related issues** — 3 auth failures on the same connector is one issue, not three
10. **Highlight what changed** — Config changes often explain job failures

---

## Common User Requests

| User says                                  | Interpretation                              |
|-------------------------------------------|---------------------------------------------|
| "Give me a weekly report"                  | Full digest, default P7D                    |
| "Monday morning status"                    | Full digest, default P7D                    |
| "What happened this week?"                 | Full digest, default P7D                    |
| "Weekly backup report"                     | Full digest, default P7D                    |
| "Summarize the last two weeks"             | Full digest, P14D                           |
| "Any problems this week?"                  | Focus on failures and action items          |
| "Weekly status for Salesforce"             | Digest filtered to Salesforce connectors    |
| "Compare this week to last week"           | Digest with week-over-week trend section    |
| "Executive summary"                        | Shortened digest: summary + actions only    |
| "What changed this week?"                  | Focus on audit log and config changes       |
| "Show me backup gaps this week"            | Focus on continuity analysis                |
| "How many jobs ran this week?"             | Quick metric extraction from job history    |
| "Weekly report for Microsoft 365 only"     | Filter connectors by type before gathering  |
| "Send me the weekly digest"                | Generate and format for copy-paste/export   |

---

## Cross-Skill Investigation Workflows

### From Digest to Deep Investigation

When the digest surfaces an issue, the user may want to drill down:

1. **Failure in digest** → Use **Keepit Backup Job Investigation** skill to analyze
   the specific failed job, root cause, and remediation.
2. **Config change flagged** → Use **Keepit Audit & Compliance Reporting** skill to
   get full audit trail and change impact analysis.
3. **Backup gap detected** → Use **Keepit Backup Health Check** skill to perform
   a real-time health assessment and identify current blockers.
4. **Stale connector** → Use **Keepit Connector Troubleshooting** skill to diagnose
   why the connector is not producing backups.

### Digest as Starting Point

The weekly digest is often the first skill invoked. It provides a map of
the environment's state, and the user then drills into specific areas:

```
Weekly Digest → identifies 3 Salesforce failures
  → User: "Investigate the Salesforce failures"
  → Route to: Backup Job Investigation skill
  → Provides: root cause, timeline, remediation steps
```

---

## Skill Integration Points

| Integration Point         | Data Shared                              | Direction   |
|--------------------------|------------------------------------------|-------------|
| Backup Health Check       | Connector health, freshness data         | Digest → HC |
| Job Investigation         | Failed job IDs, error patterns           | Digest → JI |
| Audit & Compliance        | Audit events, change summary             | Digest → AC |
| Connector Troubleshooting | Unhealthy connector GUIDs                | Digest → CT |
| Capacity Planning         | Job counts, snapshot volumes             | Digest → CP |

---

## Technical Notes

### MCP Functions Used

| Function                 | Purpose                          | Call Pattern           |
|-------------------------|----------------------------------|------------------------|
| `get_my_account_info()` | Account ID, enabled/subscribed status | Once per digest        |
| `get_cloud_connectors(connectorType="cloud")`| Full connector inventory         | Once per digest        |
| `get_connector_health()` | Per-connector health status     | Once per connector     |
| `get_active_jobs()`     | Currently running operations     | Once per connector     |
| `get_job_history()`     | Historical job outcomes          | Once per connector     |
| `get_audit_log_history()`| Configuration and admin changes | Once per digest        |
| `get_latest_snapshot()` | Most recent backup timestamp     | Once per connector     |
| `get_snapshot_range()`  | Snapshot timeline for gap detect | Once per connector     |

### Time Calculations

```python
# ISO 8601 duration to timedelta
def iso_duration_to_timedelta(duration: str) -> timedelta:
    """Convert ISO 8601 duration string to timedelta.
    Supports P{n}D format (days).
    """
    import re
    match = re.match(r'P(\d+)D', duration)
    if match:
        return timedelta(days=int(match.group(1)))
    return timedelta(days=7)  # fallback

# Freshness calculation
def calculate_freshness(snapshot_timestamp: str) -> Tuple[str, str]:
    """Return (label, icon) for backup freshness."""
    age = datetime.now(timezone.utc) - parse_iso_timestamp(snapshot_timestamp)
    hours = age.total_seconds() / 3600
    if hours < 24:
        return ('Fresh', '✅')
    elif hours < 48:
        return ('Aging', '⚠️')
    else:
        return ('Stale', '❌')
```

### Error Resilience

The digest should **never fail entirely** due to a single connector error.
The pattern is:

```python
results = {}
errors = []

for connector in connectors:
    try:
        data = get_connector_health(guid=connector['guid'])
        results[connector['guid']] = data
    except Exception as e:
        errors.append({
            'connector': connector.get('name', 'Unknown'),
            'operation': 'get_connector_health',
            'error': str(e),
        })

# Include errors in the digest output
if errors:
    # Add "Data Collection Notes" section
    pass
```

### API Call Budget

For an environment with `N` connectors, the digest makes approximately:

| Calls                     | Count       |
|--------------------------|-------------|
| Account info              | 1           |
| Connector list            | 1           |
| Health checks             | N           |
| Active job checks         | N           |
| Job history               | N           |
| Audit log                 | 1           |
| Latest snapshot           | N           |
| Snapshot range            | N           |
| **Total**                 | **4N + 3**  |

For 10 connectors: ~43 API calls. For 25 connectors: ~103 API calls.

---

## Success Metrics

A well-generated weekly digest should:

1. **Complete in a single pass** — All data gathered, analyzed, and formatted without follow-up
2. **Surface all failures** — No failed job goes unreported
3. **Prioritize correctly** — Critical issues appear before informational items
4. **Be scannable** — A reader should understand the week's status in 30 seconds from the summary
5. **Be actionable** — Every issue has a corresponding action item with a next step
6. **Provide context** — Numbers include comparison points (rates, trends, thresholds)
7. **Handle edge cases** — New connectors, empty histories, API errors are all addressed
8. **Match the user's scope** — If they asked about one connector, don't dump the whole environment
9. **Include timestamps** — Reader knows when the digest was generated and what period it covers
10. **Enable drill-down** — Issues reference connector names/GUIDs for follow-up investigation
