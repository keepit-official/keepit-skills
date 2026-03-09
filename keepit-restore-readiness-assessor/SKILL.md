---
name: keepit-restore-readiness-assessor
description: Restore readiness and recovery capability assessment for Keepit backup environments. Use when users ask about disaster recovery readiness, restore capability, RPO/RTO analysis, ransomware recovery preparedness, or backup recoverability. Triggers on keywords like "restore readiness", "recovery capability", "RPO", "RTO", "disaster recovery", "ransomware readiness", "can we recover", "restore test", "recovery assessment".
---

# Keepit Restore Readiness Assessor

## Overview

The Restore Readiness Assessor provides a structured, evidence-based evaluation of an organization's ability to recover data from Keepit backups. It examines every protected connector across health, backup freshness, continuity, and restore history to produce a composite readiness grade (A through F) with actionable recommendations.

**Target Persona:** CIO / IT Director, CISO, Compliance Officer

**Primary Use Cases:**
- Disaster recovery readiness assessments before audits or board reviews
- RPO/RTO analysis against organizational targets
- Ransomware recovery preparedness evaluation
- NIS2/DORA compliance evidence generation for backup testing requirements
- Pre-migration or pre-change readiness validation
- Periodic backup health reporting for executive stakeholders

**Key Outputs:**
- Per-connector readiness scores with factor breakdowns
- Overall readiness grade (A-F) with weighted aggregate scoring
- RPO achievement analysis (actual vs. target recovery points)
- RTO estimation based on historical restore durations
- Coverage gap identification for unprotected or stale connectors
- Compliance evidence mapping to NIS2 Article 21 and DORA Article 12

## Core Workflow

### Step 1: Discover Protected Assets

Inventory all configured connectors to understand the backup estate.

```python
# Retrieve all cloud connectors in the account
connectors = get_cloud_connectors(connectorType="cloud")

# Build asset inventory with friendly names
type_map = {
    'o365-admin': 'Microsoft 365', 'azure-ad': 'Entra ID',
    'gsuite': 'Google Workspace', 'dynamics365': 'Dynamics 365',
    'sforce': 'Salesforce', 'powerbi': 'Power BI',
    'zendesk': 'Zendesk', 'okta': 'Okta',
    'docusign': 'DocuSign', 'bamboohr': 'BambooHR',
    'confluence': 'Confluence', 'jira': 'Jira', 'azure-do': 'Azure DevOps',
}

for connector in connectors:
    friendly_name = type_map.get(connector.get('type', ''), connector.get('type', 'Unknown'))
    # Record: guid, name, type, friendly_type
```

### Step 2: Assess Connector Health

Check whether each connector can reach its source system. Health is the foundation of restore readiness — if we cannot connect, we cannot verify recoverability.

```python
# For each connector, check health status
for connector in connectors:
    health = get_connector_health(guid=connector['guid'])
    # health returns: {"healthStatus": "healthy"|"unhealthy"|"critical"|"unknown"}
    # A connector with 'critical' or 'unhealthy' healthStatus may not be able to perform restores
```

### Step 3: Evaluate Backup Freshness

Determine how recent the latest backup is for each connector. This directly feeds into RPO achievement calculations.

```python
# For each connector, get the most recent snapshot
for connector in connectors:
    latest = get_latest_snapshot(guid=connector['guid'])
    # latest returns: {"tstamp": ..., "size": ..., "type": "p"|"c", "account": ...} or null
    # Calculate hours since last backup
    if latest and latest.get('tstamp'):
        last_backup = parse_iso_timestamp(latest['tstamp'])
        hours_since = (now - last_backup).total_seconds() / 3600
        # Compare against target RPO (default 24 hours)
```

### Step 4: Analyze Backup Continuity

Examine snapshot history over the past 30 days to identify gaps in the backup chain. Gaps weaken confidence in point-in-time recovery.

```python
# For each connector, retrieve snapshot history
for connector in connectors:
    snapshots = get_snapshot_range(guid=connector['guid'], timespan="P30D", count=99)
    # Analyze the snapshot timeline:
    # - Count total snapshots in the period
    # - Identify largest gap between consecutive snapshots
    # - Calculate average interval between snapshots
    # - Flag any gaps exceeding 2x the average interval
```

### Step 5: Review Restore History

Examine past restore operations to understand actual recovery capability. Filter job history for restore-type jobs and calculate success rates and durations.

```python
# For each connector, get job history and filter for restores
for connector in connectors:
    jobs = get_job_history(guid=connector['guid'], duration="P30D")
    # Filter for restore job types
    restore_jobs = [
        j for j in jobs
        if j.get('type', '').lower() in ('restore', 'srestore', 'pstrestore')
    ]
    # For each restore job, determine status:
    # - job.get('active') -> currently running
    # - job.get('failed') -> failed
    # - else -> successful
    #
    # Calculate: success_rate, avg_duration, median_duration, p95_duration
    # These feed directly into RTO estimation
```

### Step 6: Check Active Operations

Verify whether any backup or restore operations are currently in progress. Active restores demonstrate operational readiness; active backups may affect restore performance.

```python
# For each connector, check for active jobs
for connector in connectors:
    active = get_active_jobs(guid=connector['guid'])
    # Record any active backup or restore operations
    # Active restores are a positive signal for readiness
    # Note: concurrent operations may affect RTO estimates
```

### Step 7: Calculate Per-Connector Readiness

Combine all factors into a composite readiness score for each connector.

```python
# Readiness score components (0-100 per factor):
# - Health status:      25% weight — is the connector reachable?
# - Backup freshness:   30% weight — how recent is the latest backup?
# - Backup continuity:  20% weight — are there gaps in the backup chain?
# - Restore history:    25% weight — have restores been tested and succeeded?

# Health scoring:
#   healthy -> 100, unhealthy -> 60, critical -> 20, unknown -> 40

# Freshness scoring:
#   < 24h -> 100, 24-48h -> 75, 48-72h -> 50, 72-168h -> 25, > 168h -> 0

# Continuity scoring:
#   no gaps -> 100, minor gaps (< 2x avg) -> 75, moderate gaps -> 50, severe gaps -> 25

# Restore history scoring:
#   100% success + recent restore -> 100
#   > 90% success -> 80
#   > 70% success -> 60
#   No restore history -> 40 (unknown capability)
#   < 70% success -> 20
```

### Step 8: Calculate Overall Readiness Grade

Aggregate per-connector scores into an overall readiness grade.

```python
# Overall readiness = weighted average of all connector scores
# Grade thresholds:
#   A (90-100): Fully ready — all connectors healthy, fresh, tested
#   B (80-89):  Ready — minor improvements recommended
#   C (70-79):  Partially ready — some gaps need attention
#   D (60-69):  At risk — significant gaps in recovery capability
#   F (< 60):   Not ready — critical issues require immediate action

# Weight connectors by importance (can be customized):
# All connectors weighted equally by default
# Microsoft 365 and Google Workspace may carry higher weight in practice
```

### Step 9: Generate Readiness Report

Produce a structured assessment with all findings, recommendations, and compliance evidence.

```python
# Final report structure:
# 1. Executive Summary — overall grade, key findings
# 2. Per-Connector Detail — score breakdown per connector
# 3. RPO Analysis — actual vs. target for each connector
# 4. RTO Estimation — based on historical restore durations
# 5. Coverage Gaps — connectors with no protection
# 6. Recommendations — prioritized action items
# 7. Compliance Evidence — NIS2/DORA mapping
```

## Output Formatting Guidelines

### Executive Summary Format

Present the overall readiness grade prominently with supporting context:

```
## Restore Readiness Assessment

**Overall Readiness Grade: [icon] [grade] ([score]/100)**

**Assessment Date:** [date]
**Connectors Evaluated:** [count]
**Ready:** [ready_count] | **At Risk:** [at_risk_count] | **Not Ready:** [not_ready_count]

### Key Findings
- [Top-level finding 1]
- [Top-level finding 2]
- [Top-level finding 3]
```

### Per-Connector Detail Format

```
### [Connector Name] — [Friendly Type]
**Readiness Score:** [icon] [score]/100 ([grade])

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | [score] | 25% | [status description] |
| Freshness | [score] | 30% | Last backup: [time ago] |
| Continuity | [score] | 20% | [gap description] |
| Restore History | [score] | 25% | [restore stats] |
```

### RPO/RTO Analysis Format

```
### RPO Achievement

| Connector | Target RPO | Actual RPO | Status |
|-----------|-----------|------------|--------|
| [name] | [target]h | [actual]h | [icon] [Achieved/Missed] |

### RTO Estimation

| Connector | Median RTO | P95 RTO | Confidence | Based On |
|-----------|-----------|---------|------------|----------|
| [name] | [median] | [p95] | [level] | [n] restores |
```

### Grade Icons

- ✅ Grade A or B — Ready or fully ready
- ⚠️ Grade C — Partially ready, improvements recommended
- ❌ Grade D or F — At risk or not ready
- 🔴 High priority gap or critical issue
- 🟡 Medium priority — should be addressed
- 🟢 Low priority or informational

### Priority Indicators for Recommendations

- 🔴 **HIGH** — Must address before next audit or recovery event
- 🟡 **MEDIUM** — Address within 30 days
- 🟢 **LOW** — Best practice improvement

## Advanced Features

### RPO Achievement Analysis

Compare actual backup freshness against organizational RPO targets. Default target is 24 hours but can be adjusted per connector or per data class.

```python
# RPO calculation for each connector:
# actual_rpo_hours = hours since last successful backup
# target_rpo_hours = organizational target (default 24h)
# achieved = actual_rpo_hours <= target_rpo_hours
# gap_hours = max(0, actual_rpo_hours - target_rpo_hours)

# RPO status mapping:
# actual <= target        -> ✅ "RPO Achieved"
# actual <= target * 1.5  -> ⚠️ "RPO At Risk"
# actual > target * 1.5   -> ❌ "RPO Breached"
```

### RTO Estimation from Historical Restores

Estimate recovery time objectives based on actual restore job durations.

```python
# Filter job history for restore types: restore, srestore, pstrestore
# Extract duration for each completed (non-active) restore job
# Calculate:
#   median_duration — typical restore time
#   p95_duration    — worst-case realistic restore time
#   confidence      — based on sample size (high: 10+, medium: 3-9, low: 1-2, none: 0)

# If no restore history exists:
#   Report "No restore history — RTO unknown"
#   Flag as a gap requiring restore testing
```

### Backup Continuity Analysis

Detect gaps in the backup chain that could affect point-in-time recovery.

```python
# Sort snapshots by timestamp
# Calculate intervals between consecutive snapshots
# Identify gaps exceeding 2x the median interval
# Rate continuity:
#   No gaps detected     -> score 100
#   Minor gaps (< 2x)    -> score 75
#   Moderate gaps (2-4x)  -> score 50
#   Severe gaps (> 4x)    -> score 25
#   No snapshots at all   -> score 0
```

### NIS2/DORA Compliance Evidence

Map readiness findings to specific regulatory requirements.

```python
# NIS2 Article 21 — Backup and disaster recovery requirements:
# - Evidence: backup frequency, retention, restore testing
# - Gap: no restore tests in 90 days -> compliance risk

# DORA Article 12 — ICT backup and restoration:
# - Evidence: RPO/RTO documentation, restore success rates
# - Gap: no documented RTO -> compliance risk
# - Gap: restore success rate < 95% -> compliance risk
```

## Error Handling

### Connector Access Errors

```python
# If get_connector_health() fails:
#   Record health as 'unknown', score health factor at 40
#   Continue assessment — do not abort for a single connector

# If get_latest_snapshot() returns None:
#   Record freshness as 'no data', score freshness at 0
#   Flag as a critical coverage gap
```

### Empty or Missing Data

```python
# No connectors found:
#   Report: "No connectors configured — backup estate is empty"
#   Overall grade: F

# No snapshots for a connector:
#   RPO: "Cannot calculate — no backups exist"
#   Continuity: score 0
#   Flag as 🔴 HIGH priority gap

# No restore history:
#   RTO: "Unknown — no restore operations recorded"
#   Restore history score: 40 (unknown capability, not necessarily failed)
#   Recommend: "Perform a test restore to validate recovery capability"
```

### Graceful Degradation

```python
# If any MCP call fails, log the error and continue with available data
# Partial assessments are still valuable
# Always indicate which data was unavailable in the report
# Never block the entire assessment for a single connector failure
```

## Best Practices

1. **Always assess ALL connectors** — do not skip connectors even if the user asks about a specific one. Context matters; a single healthy connector means little if others are failing.

2. **Default RPO target is 24 hours** — adjust if the user specifies a different target. Financial services often target 4-8 hours; critical systems may target 1 hour.

3. **Weight restore history heavily** — having backups is necessary but not sufficient. Only tested restores prove recoverability. Flag connectors with zero restore history prominently.

4. **Present the grade first, details second** — executives want the headline before the analysis. Lead with the overall grade and key findings.

5. **Include recommendations with every assessment** — even a Grade A assessment should include maintenance recommendations. Always provide the "next best action."

6. **Time context matters** — a Grade B assessment taken 6 months ago may be Grade D today. Include the assessment timestamp and recommend reassessment frequency.

7. **Distinguish between "not tested" and "failed"** — a connector with no restore history is not the same as one with failed restores. Score accordingly (40 vs 20).

8. **Use compliance framing for executive audiences** — map findings to NIS2/DORA when the user mentions compliance, audit, or regulation.

9. **Calculate confidence levels for RTO estimates** — more historical restore data means higher confidence. Flag low-confidence estimates clearly.

10. **Prioritize recommendations** — use 🔴/🟡/🟢 priority levels so stakeholders know where to focus first.

## Common User Requests

### "Are we ready to recover from a ransomware attack?"

Full readiness assessment with emphasis on:
- All connectors healthy and accessible
- Recent backups exist (RPO analysis)
- Restore capability proven (restore history)
- No single points of failure
- Compliance evidence for incident response

### "What is our RPO and RTO?"

Focused RPO/RTO analysis:
- RPO: actual backup freshness per connector vs. target
- RTO: estimated from historical restore durations
- Identify connectors where RPO/RTO is unknown (no data)

### "Give me a restore readiness report for our audit"

Compliance-focused assessment:
- Overall readiness grade with evidence
- Per-connector detail with scores
- NIS2/DORA compliance mapping
- Gap analysis with remediation recommendations
- Formatted for audit documentation

### "Can we recover our Microsoft 365 data?"

Connector-specific assessment:
- Filter for o365-admin type connectors
- Full readiness analysis for those connectors
- Still mention other connectors briefly for context

### "How confident are we in our backups?"

Confidence-focused assessment:
- Emphasis on restore history and success rates
- RTO confidence levels based on sample sizes
- Coverage gap analysis
- Recommendations for improving confidence through testing

### "Run a quick readiness check"

Abbreviated assessment:
- Overall grade and score
- Top 3 issues requiring attention
- Quick RPO/RTO summary
- Skip detailed per-connector breakdown unless requested

## Cross-Skill Investigation Workflows

### From Backup Health Dashboard

When the backup health dashboard identifies unhealthy connectors:
1. Feed unhealthy connector list into readiness assessment
2. Calculate impact on overall readiness grade
3. Provide recovery-focused recommendations

### From Anomaly Detection

When anomaly detection flags unusual backup patterns:
1. Assess whether the anomaly affects restore readiness
2. Check if the affected connector's backups are still recoverable
3. Evaluate RPO impact of the anomaly

### From Compliance Reporting

When compliance reporting needs backup testing evidence:
1. Generate readiness report with compliance framing
2. Map restore test results to NIS2/DORA requirements
3. Identify compliance gaps requiring remediation

### From Job Analytics

When job analytics reveals restore job failures:
1. Incorporate failure data into readiness scoring
2. Calculate impact on RTO confidence
3. Recommend corrective actions for failed restores

## Skill Integration Points

| Trigger From | Data Needed | Readiness Action |
|-------------|-------------|-----------------|
| Backup Health Dashboard | Unhealthy connector list | Assess recovery impact of health issues |
| Anomaly Detection | Anomalous backup patterns | Evaluate RPO/RTO impact |
| Compliance Reporting | Audit requirements | Generate compliance evidence |
| Job Analytics | Restore job failures | Update RTO confidence and scoring |
| Storage Analytics | Capacity warnings | Assess impact on backup continuity |

## Technical Notes

### MCP Functions Used

| Function | Purpose | Parameters |
|----------|---------|------------|
| `get_cloud_connectors(connectorType="cloud")` | Inventory all protected assets | None |
| `get_connector_health(guid)` | Check connector reachability | `guid`: connector GUID |
| `get_latest_snapshot(guid)` | Get most recent backup | `guid`: connector GUID |
| `get_snapshot_range(guid, timespan, count)` | Get snapshot history | `guid`, `timespan`: ISO 8601 duration, `count`: max results |
| `get_job_history(guid, duration)` | Get job history including restores | `guid`, `duration`: ISO 8601 duration |
| `get_active_jobs(guid)` | Check for running operations | `guid`: connector GUID |

### Time Calculations

```python
# RPO calculation:
# actual_rpo = now - latest_snapshot_timestamp (in hours)
# rpo_achieved = actual_rpo <= target_rpo

# RTO calculation (from restore job history):
# For each completed restore job:
#   duration = job_end - job_start (in seconds)
# median_rto = median(all_durations)
# p95_rto = percentile_95(all_durations)

# Backup interval calculation:
# Sort snapshots by timestamp
# intervals = [snap[i+1].timestamp - snap[i].timestamp for i in range(len-1)]
# avg_interval = mean(intervals)
# gap_threshold = 2 * median(intervals)
```

### Error Resilience

```python
# Every MCP call is wrapped in try/except
# Individual connector failures do not block the overall assessment
# Missing data is scored conservatively (not zero, but below passing)
# The report always indicates data availability per connector
# Partial assessments include a "Data Completeness" indicator
```

### Scoring Weights

```python
# Per-connector readiness score:
HEALTH_WEIGHT = 0.25      # Can we reach the source?
FRESHNESS_WEIGHT = 0.30   # How recent is the backup?
CONTINUITY_WEIGHT = 0.20  # Any gaps in the chain?
RESTORE_WEIGHT = 0.25     # Have restores been tested?

# Overall readiness:
# Simple weighted average of all connector scores
# All connectors weighted equally by default
```

## Success Metrics

A successful readiness assessment should:

1. **Cover all connectors** — every configured connector is evaluated
2. **Provide a clear grade** — A-F with numeric score, immediately understandable
3. **Quantify RPO/RTO** — actual numbers, not just qualitative statements
4. **Identify specific gaps** — named connectors, specific issues, not generic warnings
5. **Prioritize actions** — 🔴/🟡/🟢 so stakeholders know what to fix first
6. **Include compliance mapping** — when the audience is compliance-aware
7. **State confidence levels** — especially for RTO estimates based on limited data
8. **Recommend next steps** — every assessment ends with actionable recommendations
9. **Complete in a single pass** — all MCP calls made efficiently, no redundant queries
10. **Be reproducible** — same data should produce the same grade and recommendations
