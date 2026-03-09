---
name: keepit-snapshot-analyzer
description: Keepit backup snapshot gap and continuity analyzer. Use when users ask to verify backup continuity, detect snapshot gaps, check RPO compliance, analyze backup size trends, or review backup frequency. Triggers on keywords like "snapshot gaps", "backup continuity", "RPO compliance", "backup frequency", "snapshot analysis", "missed backups", "backup size trend", "capacity planning".
---

# Keepit Snapshot Gap & Continuity Analyzer

## Overview

This skill provides deep analysis of Keepit backup snapshots to verify data protection continuity, detect gaps in coverage, measure RPO compliance, and forecast storage capacity needs. It leverages the `get_snapshot_range` and `get_latest_snapshot` MCP tools — which are purpose-built for snapshot analysis but underutilized by other skills.

**Primary Use Cases:**
- Backup continuity verification (no gaps in protection)
- RPO (Recovery Point Objective) compliance measurement
- Backup size growth trending and capacity forecasting
- Partial vs. complete backup ratio analysis
- Per-connector backup frequency reporting
- Gap investigation and root cause correlation

**Keywords**: snapshot gaps, backup continuity, RPO compliance, backup frequency, snapshot analysis, missed backups, backup size trend, capacity planning, backup verification

## Core Workflow

### Step 1: Define Analysis Scope

Clarify what needs to be analyzed:

**Connector Selection:**
- Specific connector by name or GUID
- All connectors (comprehensive continuity review)
- Connector type (e.g., all Microsoft 365 connectors)

**Time Range:**
- Last 7 days (P7D) — quick spot check
- Last 30 days (P30D) — standard continuity review
- Last 90 days (P90D) — quarterly compliance evidence
- Custom range via `startTime` and `timespan` parameters

**Expected Backup Frequency:**
- Daily (24h interval) — most common
- Twice daily (12h interval)
- Custom interval — set by organizational policy

### Step 2: Retrieve Connector Information

```python
# Get connector list for context
connectors = get_cloud_connectors(connectorType="cloud")

# For each connector, note:
# - guid (required for snapshot queries)
# - name (for readable reports)
# - type (context for expected behavior)
# - backup_retention (retention policy, if set)
```

### Step 3: Retrieve Snapshot Data

For each connector in scope, retrieve snapshot history:

```python
for connector in selected_connectors:
    # Get full snapshot range for analysis
    snapshots = get_snapshot_range(
        guid=connector['guid'],
        timespan="P30D",    # Analysis period
        count=99,            # Maximum snapshots (API limit)
        reverse=False        # Oldest first for chronological analysis
    )
    # Returns array of: { timestamp, type, size, account }

    # Also get the latest snapshot for current-state context
    latest = get_latest_snapshot(guid=connector['guid'])
    # Returns: { tstamp, type, size, account } or null
```

**Parameters for `get_snapshot_range`:**
- `guid` (required): Connector GUID
- `startTime` (optional): ISO 8601 timestamp (defaults to now)
- `timespan` (optional): ISO 8601 duration (default P7D)
- `reverse` (optional): If true, newest first (default false)
- `count` (optional): Max snapshots to return (default 99, max 99)

**Important — field name difference between snapshot endpoints:**
- `get_snapshot_range` returns snapshots with field `timestamp`
- `get_latest_snapshot` returns a snapshot with field `tstamp`
Do not confuse these. Use `snap.get('timestamp')` for range results and `latest.get('tstamp')` for latest snapshot results.

**Note:** `get_snapshot_range` may return an empty array for some connectors. When this happens, fall back to `get_job_history` for backup continuity information. Skills should treat empty snapshot ranges gracefully rather than failing.

**Note:** If the total snapshots in the range exceed 100, only the first 100 are returned. For longer periods, consider splitting into multiple calls with different `startTime` values.

### Step 4: Analyze Backup Continuity

#### Gap Detection

Identify periods where no snapshots exist:

```python
from snapshot_utils import analyze_snapshot_gaps

gap_analysis = analyze_snapshot_gaps(
    snapshots,
    expected_interval_hours=24.0  # Adjust per organizational policy
)

# gap_analysis returns:
# - gaps: list of { start, end, duration_hours } for each gap
# - max_gap_hours: largest gap found
# - avg_interval_hours: average time between snapshots
# - continuity_status: 'good', 'warning', or 'critical'
```

**Gap Thresholds:**
- **Good**: No gap exceeds 1.5x the expected interval
- **Warning**: A gap exceeds 1.5x but stays under 3x the expected interval
- **Critical**: Any gap exceeds 3x the expected interval

#### Partial vs. Complete Snapshot Analysis

```python
# Snapshot type field: "p" = partial, "c" = complete
# High partial ratio may indicate:
# - Incremental backup strategy (normal)
# - Interrupted full backups (concerning)
# - Configuration issues (needs investigation)

partial_ratio = gap_analysis['partial_count'] / gap_analysis['total_snapshots']
```

### Step 5: Measure RPO Compliance

Calculate whether backups meet Recovery Point Objective targets:

```python
from snapshot_utils import calculate_rpo_compliance

rpo_result = calculate_rpo_compliance(
    snapshots,
    target_rpo_hours=24.0  # Organizational RPO target
)

# rpo_result returns:
# - compliant: boolean
# - target_hours: the target RPO
# - actual_max_gap_hours: worst-case RPO (largest gap)
# - compliance_pct: percentage of intervals that meet RPO
# - violations: list of intervals that exceeded RPO
```

### Step 6: Analyze Size Trends

Track backup data growth for capacity planning:

```python
from snapshot_utils import analyze_snapshot_size_trend, project_storage_needs

size_trend = analyze_snapshot_size_trend(snapshots)
# size_trend returns:
# - growth_percent: size change over the period
# - trend: 'growing', 'stable', or 'shrinking'
# - first_size_bytes / last_size_bytes

projection = project_storage_needs(
    snapshots,
    projection_days=90
)
# projection returns:
# - projected_size_bytes: estimated size in N days
# - daily_growth_bytes: average daily size increase
```

### Step 7: Generate Report

**Report Structure:**

```markdown
# Backup Continuity Analysis Report
[Connector(s)] | [Time period] | Generated: [timestamp]

## Executive Summary
- Connectors analyzed: N
- Total snapshots: N across N days
- Continuity status: [Good/Warning/Critical]
- RPO compliance: [Compliant/Non-compliant] (target: Xh)
- Size trend: [Growing/Stable/Shrinking] (X% over period)

## Continuity Analysis

### Per-Connector Summary

| Connector | Snapshots | Max Gap | Avg Interval | P/C Ratio | Continuity |
|-----------|-----------|---------|--------------|-----------|------------|
| M365      | 30        | 25.2h   | 24.1h        | 0p / 30c  | Good       |
| Entra ID  | 28        | 52.3h   | 25.7h        | 2p / 26c  | Warning    |

### Gaps Detected

[List each gap with start time, end time, and duration]

## RPO Compliance

| Connector | Target RPO | Worst Gap | Compliance | Violations |
|-----------|-----------|-----------|------------|------------|
| M365      | 24h       | 25.2h     | 96.7%      | 1          |
| Entra ID  | 24h       | 52.3h     | 89.3%      | 3          |

## Size Trend Analysis

| Connector | First Size | Latest Size | Growth | Trend |
|-----------|-----------|-------------|--------|-------|
| M365      | 1.2 GB    | 1.4 GB      | +16.7% | Growing |
| Entra ID  | 450 MB    | 460 MB      | +2.2%  | Stable  |

### Capacity Projection (90 days)
[Projected sizes per connector]

## Recommendations
[Prioritized actions based on findings]
```

## Output Formatting Guidelines

### Continuity Status Icons
- ✅ **Good**: All intervals within expected range
- ⚠️ **Warning**: Some gaps detected but within tolerance
- ❌ **Critical**: Significant gaps in backup coverage

### Size Formatting
- Use human-readable sizes: "1.5 GB", "450 MB"
- Show growth as both absolute and percentage
- Include capacity projections when growth is detected

## Common User Requests

### "Are there any gaps in my backups?"
1. Get connectors → Get snapshot range (P30D, count=99) → Analyze gaps
2. Report each gap with start/end times
3. Suggest investigation steps for any gaps found

### "Are we meeting our RPO?"
1. Clarify RPO target (default: 24 hours)
2. Get snapshot range → Calculate RPO compliance
3. Report compliance percentage and any violations

### "How fast is our backup data growing?"
1. Get snapshot range (P30D or P90D) → Analyze size trend
2. Report growth rate and project future needs
3. Recommend capacity actions if growth is significant

### "Give me a full backup continuity report"
1. All connectors → Full analysis (gaps, RPO, size trends)
2. Comprehensive report with all sections
3. Prioritized recommendations

## Cross-Skill Investigation Workflows

### Gap Found → Job History Correlation

When a gap is detected, check what happened during that period:

```python
# 1. Gap detected from startTime to endTime
gap_start = "2026-02-05T02:00:00Z"
gap_connector = "2gfd9w-2l3knw-s50ffl"

# 2. Check job history during the gap
jobs = get_job_history(guid=gap_connector, duration="P14D")
# Look for failed jobs during the gap period

# 3. Check audit logs for config changes
audit_logs = get_audit_log_history(duration="P14D")
# Filter for events near gap_start
```

### Continuity Report → Health Check

Verify current state after finding historical gaps:

```python
# 1. Continuity analysis found gaps for a connector
connector_guid = "2gfd9w-2l3knw-s50ffl"

# 2. Check current health
health = get_connector_health(guid=connector_guid)
latest = get_latest_snapshot(guid=connector_guid)
active_jobs = get_active_jobs(guid=connector_guid)
```

### Size Growth → Compliance Audit

When data growth is significant, verify retention is adequate:

```python
# 1. Size trend shows 15%+ growth
connector = connectors[0]

# 2. Check retention policy
retention = connector.get('backup_retention')
# If retention is short and data is growing, flag capacity risk
```

## MCP Functions Used

- `get_snapshot_range(guid, startTime?, timespan?, reverse?, count?)` - Primary tool for snapshot analysis
- `get_latest_snapshot(guid)` - Current state check
- `get_cloud_connectors(connectorType="cloud")` - Connector discovery
- `get_connector_health(guid)` - Health context (cross-skill)
- `get_active_jobs(guid)` - Currently running jobs (cross-skill)
- `get_job_history(guid, duration)` - Failure correlation (cross-skill)

## Success Criteria

A successful snapshot analysis provides:

- ✅ Complete gap detection across the analysis period
- ✅ RPO compliance measurement against organizational targets
- ✅ Size trend analysis with growth projections
- ✅ Partial vs. complete snapshot breakdown
- ✅ Actionable recommendations for any issues found
- ✅ Clear, scannable report format

The user should know whether their backups are continuous, whether they meet RPO targets, and whether their storage needs are growing.
