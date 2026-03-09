---
name: keepit-job-history-analyzer
description: Comprehensive Keepit backup job history analyzer for investigating failures, performance patterns, and operational trends. Use when users ask to analyze backup jobs, investigate failures, check job history, review backup performance, calculate success rates, or examine job patterns over time. Triggers on keywords like "job history", "backup failures", "analyze jobs", "performance trends", "success rate", "why did backup fail".
---

# Keepit Backup Job History Analyzer

## Overview

This skill provides deep analysis of Keepit backup and restore job history. It investigates job patterns, identifies failures, calculates performance metrics, and provides actionable insights for troubleshooting and optimization.

**Primary Use Cases:**
- Failure investigation and root cause analysis
- Performance trend analysis
- Success rate calculations and SLA verification
- Capacity planning and backup window optimization
- Recurring issue identification
- Historical performance reporting

**Keywords**: job history, backup failures, restore operations, performance analysis, success rate, job patterns, failure trends, backup jobs, job investigation

## Core Workflow

### Step 1: Determine Analysis Scope

First, clarify what needs to be analyzed:

**Time Range Options:**
- Last 24 hours (P1D)
- Last week (P7D)
- Last 30 days (P30D)
- Custom period (user-specified)

**Connector Selection:**
- Specific connector by name or GUID
- All connectors (comprehensive analysis)
- Connector type (e.g., all Microsoft 365 connectors)

**Analysis Focus:**
- General overview (all jobs)
- Failures only (troubleshooting)
- Performance metrics (optimization)
- Specific job type (backup vs. restore)

### Step 2: Retrieve Connector Information

Get connector details for context:

```python
# Get list of connectors
connectors = get_cloud_connectors(connectorType="cloud")

# If user specified a connector name, match it
# If "all connectors" requested, prepare to analyze each
# Store connector metadata for reporting context
```

**Important Details to Capture:**
- Connector GUID (required for job history query)
- Connector name (for readable reports)
- Connector type (context for analysis)
- Creation date (to understand data availability)

### Step 3: Check Active Jobs (Real-Time Context)

Before analyzing history, check what's running right now:

```python
for connector in selected_connectors:
    active_jobs = get_active_jobs(guid=connector['guid'])

    # Same schema as job history. Shows currently running jobs with:
    # - type: job type (backup, restore, etc.)
    # - progress: decimal "0.0" to "1.0"
    # - started: when execution began
    # - description: job description
    #
    # Include in report: "1 job currently running (45% complete)"
    # This prevents reporting "no recent backups" when one is in progress
```

**Why this matters:** Job history only shows completed (succeeded or failed) jobs. Without checking active jobs, the analysis might report concerning metrics while a backup is actively running and about to succeed.

### Step 4: Retrieve Job History

Query job history for each connector in scope:

```python
# For each connector to analyze
for connector in selected_connectors:
    job_history = get_job_history(
        guid=connector['guid'],
        duration="P7D"  # ISO 8601 duration format
    )
    
    # Job data fields from API:
    # - type: job type (e.g., "backup", "restore")
    # - active: boolean (true = currently running)
    # - start: ISO timestamp (job creation/queue time)
    # - started: ISO timestamp (actual execution start)
    # - failed: ISO timestamp or null (failure time; null = not failed)
    # - progress: decimal string "0.0" to "1.0"
    # - description: string with job metadata
    # - execsummary: XML string with execution details
    #
    # Status is inferred (no explicit status field):
    #   failed has a timestamp → job failed
    #   active == true → job is running
    #   failed is null AND active is false → job succeeded
```

**ISO 8601 Duration Format:**
- P1D = 1 day
- P7D = 7 days
- P30D = 30 days
- PT24H = 24 hours
- P1M = 1 month

**Note**: The `duration` parameter is optional. If not provided, a default lookback period will be used.

### Step 5: Analyze Job Data

Perform comprehensive analysis on collected job history:

#### A. Success/Failure Metrics

```python
# Calculate for each connector (status inferred from API fields):
# - failed has a timestamp → failed job
# - active == true → running
# - failed is null AND active is false → succeeded
- Total jobs executed
- Successful jobs count (failed is null, not active)
- Failed jobs count (failed has a timestamp)
- Running jobs count (active == true)
- Success rate percentage
- Failure rate percentage
```

#### B. Failure Analysis

```python
# For failed jobs (failed has a timestamp), identify:
- Common patterns in job descriptions and execution summaries (XML)
- Time of day patterns (morning vs. evening failures)
- Day of week patterns
- Recurring issues parsed from description and execsummary fields
- Connectors with highest failure rates
- First occurrence vs. recurring failures

# Parse execsummary XML for detailed error data:
from analysis_utils import parse_execsummary

for job in failed_jobs:
    parsed = parse_execsummary(job.get('execsummary'))
    # parsed['errors'] — list of error message strings from XML
    # parsed['exit_reason'] — why the job terminated
    # parsed['warnings'] — warning messages
    # parsed['details'] — other key-value pairs from the XML
    # parsed['parse_error'] — set if XML was malformed
```

**Execsummary Analysis:** The `execsummary` field is an XML string containing error messages, exit reasons, and completion details. Use `parse_execsummary()` to extract structured data from it. This provides richer error categorization than the `description` field alone — including specific error codes, exit reasons, and warnings that help distinguish between authentication failures, permission issues, API errors, and data-level problems.

#### C. Performance Analysis

```python
# Job duration analysis (using started and completion timestamps):
- Average job duration (completion time - started)
- Minimum and maximum durations
- Duration trends over time
- Jobs exceeding expected duration
- Performance degradation patterns
```

#### D. Temporal Patterns

```python
# Identify patterns:
- Job frequency (how often jobs run)
- Time distribution (when jobs execute)
- Job clustering (multiple jobs at same time)
- Gap detection (missing expected jobs)
```

#### E. Job Type Distribution

```python
# Categorize by job type:
- Backup job statistics
- Restore job statistics
- Other job types (validation, migration, etc.)
- Type-specific success rates
```

### Step 6: Generate Insights and Recommendations

Based on analysis, generate actionable insights:

#### Pattern Recognition
- Identify recurring failures (same error multiple times)
- Detect performance degradation trends
- Spot unusual activity (sudden failure spike)
- Recognize schedule conflicts

#### Root Cause Hypotheses
- Permission/authentication issues (certain error patterns)
- Resource constraints (duration increases)
- Configuration problems (consistent failures)
- External dependencies (time-correlated failures)

#### Recommendations
- Immediate actions for critical issues
- Schedule optimizations
- Configuration adjustments
- Monitoring improvements

### Step 7: Format Report

Create clear, actionable report with appropriate level of detail:

**Executive Summary Section:**
- Overall success rate
- Total jobs analyzed
- Time period covered
- Critical findings count
- Primary recommendation

**Detailed Findings Section:**
- Per-connector statistics
- Failure breakdown with examples
- Performance metrics and trends
- Pattern identification

**Action Items Section:**
- Prioritized recommendations
- Specific steps to resolve issues
- Timeline for actions
- Follow-up suggestions

## Output Formatting Guidelines

### Report Structure

Use clear hierarchy and progressive disclosure:

```markdown
# Backup Job History Analysis Report
[Time period] | [Connector(s)] | Generated: [timestamp]

## 📊 Executive Summary
[High-level metrics and key findings]

## 📈 Overall Statistics
[Aggregate metrics across all analyzed jobs]

## 🔍 Detailed Analysis by Connector
[Per-connector breakdown]

## ⚠️ Issues and Failures
[Failure analysis with patterns]

## 💡 Insights and Recommendations
[Actionable findings]

## 📋 Next Steps
[Recommended actions]
```

### Statistics Presentation

**Use tables for metrics:**

| Metric | Value | Status |
|--------|-------|--------|
| Total Jobs | 156 | - |
| Successful | 142 | ✅ 91% |
| Failed | 12 | ⚠️ 8% |
| Running | 2 | ⏳ 1% |

**Use charts description for trends:**
- "Success rate increased from 85% to 91% over the period"
- "Average job duration: 12 minutes (down from 15 minutes last week)"

### Failure Presentation

**Group by pattern, not chronologically:**

```markdown
### 🔴 Authentication Failures (8 occurrences)
**Pattern**: Consistent failures at 2:00 AM UTC
**Connectors affected**: Microsoft 365 Backup, SharePoint Backup
**First occurrence**: October 15, 2025
**Last occurrence**: October 22, 2025
**Likely cause**: Token expiration during maintenance window
**Recommendation**: Refresh authentication tokens or adjust backup schedule
```

### Time Formatting

Be consistent and human-readable:
- "Analyzed: Last 7 days (October 15-22, 2025)"
- "Job completed in 14 minutes 32 seconds"
- "Average duration: 12m 15s"
- "Failed 3 days ago (October 19, 2025 at 14:30 UTC)"

### Success Rate Visualization

Use clear indicators:
- ✅ **Excellent**: 95-100% success rate
- 🟢 **Good**: 90-94% success rate
- 🟡 **Acceptable**: 85-89% success rate
- ⚠️ **Concerning**: 75-84% success rate
- 🔴 **Critical**: Below 75% success rate

## Analysis Strategies

### For Troubleshooting Failures

**Focus on:**
1. Most recent failures first
2. Recurring vs. one-time failures
3. Error message patterns
4. Temporal correlations
5. Configuration changes timeline

**Questions to answer:**
- What failed and when?
- Is this a new issue or recurring?
- Which connectors are affected?
- What error messages appear?
- Are there common characteristics?

### For Performance Analysis

**Focus on:**
1. Job duration trends over time
2. Comparison against baseline
3. Resource utilization patterns
4. Schedule efficiency
5. Backup window utilization

**Questions to answer:**
- How long do jobs typically take?
- Are durations increasing?
- When do jobs run?
- Are backup windows sufficient?
- Where can we optimize?

### For SLA Verification

**Focus on:**
1. Success rate calculations
2. Meeting RPO/RTO targets
3. Backup frequency compliance
4. Failure impact assessment
5. Service level metrics

**Questions to answer:**
- Are we meeting SLA targets?
- What's our actual vs. target success rate?
- Are backups completing on schedule?
- What's the impact of failures?
- Where are we at risk?

### For Capacity Planning

**Focus on:**
1. Job count trends
2. Duration growth patterns
3. Schedule density
4. Resource saturation indicators
5. Future projection

**Questions to answer:**
- How many jobs run daily?
- Is job duration increasing?
- Is the schedule getting crowded?
- When will we hit capacity?
- What expansion is needed?

## Advanced Analysis Techniques

### Failure Pattern Recognition

**Look for these patterns:**

**Time-based patterns:**
- Failures always at specific time (scheduled task conflict)
- Failures on specific days (weekly maintenance)
- Failures during business hours vs. off-hours
- Seasonal patterns (month-end, quarter-end)

**Connector-based patterns:**
- Only one connector failing (connector-specific issue)
- All connectors failing simultaneously (system-wide issue)
- Cascading failures (one triggers others)
- Type-specific failures (all Microsoft 365 connectors)

**Error message patterns:**
- Same error repeatedly (persistent issue)
- Error evolution (problem getting worse)
- Multiple different errors (systemic problem)
- Intermittent specific error (network/timing issue)

### Performance Trend Analysis

**Calculate and report:**

```python
# Week-over-week comparison
current_week_avg_duration = calculate_average_duration(current_week_jobs)
previous_week_avg_duration = calculate_average_duration(previous_week_jobs)
percent_change = ((current - previous) / previous) * 100

# Report: "Job duration increased 15% week-over-week"
```

**Identify:**
- Sudden spikes (configuration change or issue)
- Gradual increases (data growth, need optimization)
- Improvements (successful optimization)
- Cyclical patterns (predictable variations)

### Root Cause Correlation

**Cross-reference with:**
- Configuration changes (when were connectors modified?)
- Known incidents (correlate with other issues)
- Maintenance windows (scheduled changes)
- External factors (source system changes)

## Error Handling and Edge Cases

### No Job History Available

If job history is empty:
```markdown
⚠️ **No job history found** for [connector name]

**Possible reasons:**
- Connector recently created (no jobs yet)
- Time range too narrow (no jobs in period)
- Connector not yet activated
- Permissions issue (unable to retrieve history)

**Recommended actions:**
1. Verify connector is active and configured
2. Expand time range if needed
3. Check connector creation date
4. Verify API permissions
```

### Incomplete Job Data

If jobs have missing fields:
- Note the limitation in the report
- Work with available data
- Flag data quality issues
- Continue analysis with what's available

### Very Large Result Sets

If job history is extensive (100+ jobs):
- Summarize overall statistics
- Focus on recent failures
- Provide aggregated metrics
- Offer to drill into specific time periods

### Conflicting Data

If data seems inconsistent:
- Report the observation
- Present both views
- Suggest verification
- Continue with most conservative interpretation

## Integration with Other Skills

### Cross-Skill Investigation Workflows

#### Failures Found → Audit Log Correlation

When job history reveals failures, check audit logs for config changes that may have caused them:

```python
# 1. Job history shows failures starting at a specific time
first_failure_time = "2026-02-10T02:15:00Z"

# 2. Pull audit logs around that time window
audit_logs = get_audit_log_history(duration="P7D")
# Filter for events near first_failure_time
# Look for: config changes, permission changes, retention updates

# 3. Correlate: "Config change at 14:00 UTC → backup failure at 14:15 UTC"
```

#### Performance Degradation → Snapshot Size Trends

When job durations are increasing, check if backup data is growing:

```python
# 1. Job history shows increasing durations
connector_guid = "2gfd9w-2l3knw-s50ffl"

# 2. Get snapshot size trend for the same period
snapshots = get_snapshot_range(guid=connector_guid, timespan="P30D", count=99)
# Use analyze_snapshot_size_trend(snapshots) to check data growth

# 3. Compare: "Duration +15% while data size +12% → growth is the likely cause"
```

#### Recurring Failures → Health Check Validation

When the same failure keeps recurring, verify current connector state:

```python
# 1. Job history shows recurring failures
connector_guid = "2gfd9w-2l3knw-s50ffl"

# 2. Check current health
health = get_connector_health(guid=connector_guid)

# 3. Check if a job is running right now
active = get_active_jobs(guid=connector_guid)

# 4. Get latest successful snapshot to assess actual protection status
latest = get_latest_snapshot(guid=connector_guid)
```

### Complementary Skills

**Trigger Health Check skill when:**
- Current connector status needed
- Real-time health differs from historical
- Latest snapshot information required

**Suggest Snapshot Gap & Continuity Analyzer when:**
- Gap patterns detected in job history
- Backup continuity questions arise
- RPO validation needed

**Suggest Audit Log Extractor when:**
- Configuration change timeline needed
- User action correlation required
- Compliance documentation needed

## Common User Requests and Responses

### "Why did my backup fail?"

**Process:**
1. Get connector identification (name or GUID)
2. Retrieve recent job history (P1D or P7D)
3. Filter for failed jobs
4. Analyze most recent failures
5. Identify error patterns
6. Provide specific diagnosis

**Response includes:**
- Specific failure details
- Error messages
- Time of failure
- Frequency (one-time vs. recurring)
- Likely cause
- Recommended fix

### "How often do my backups fail?"

**Process:**
1. Determine time period (default P30D)
2. Get job history for all connectors
3. Calculate success/failure rates
4. Identify trends
5. Compare against benchmarks

**Response includes:**
- Overall success rate percentage
- Per-connector success rates
- Trend analysis (improving/degrading)
- Comparison to targets
- Areas of concern

### "Analyze job performance for the last month"

**Process:**
1. Query job history with duration="P30D"
2. Calculate performance metrics
3. Identify trends and patterns
4. Generate comprehensive report

**Response includes:**
- Average job duration
- Duration trends
- Performance comparison
- Optimization opportunities
- Capacity insights

### "Show me all failed jobs this week"

**Process:**
1. Query job history for P7D
2. Filter for failed status
3. Sort by date (most recent first)
4. Group by connector or error type
5. Present in scannable format

**Response includes:**
- Failed job listing
- Grouped by pattern
- Error details
- Affected connectors
- Recommended actions

### "Are we meeting our backup SLA?"

**Process:**
1. Determine SLA targets (ask if not specified)
2. Calculate actual metrics
3. Compare against targets
4. Identify gaps or risks

**Response includes:**
- Target vs. actual comparison
- SLA compliance status
- Areas at risk
- Trend analysis
- Recommendations for improvement

## Technical Implementation Notes

### Time Range Calculations

Convert user-friendly requests to ISO 8601:

```python
user_request_to_duration = {
    "today": "P1D",
    "yesterday": "P1D",  # adjust query time
    "last 24 hours": "PT24H",
    "last week": "P7D",
    "last 2 weeks": "P14D",
    "last month": "P30D",
    "last 30 days": "P30D",
    "last quarter": "P90D",
}
```

### Job Status Classification

Status is inferred from API fields (there is no explicit `status` field):
- **Success**: `failed` is null and `active` is false (job completed without failure)
- **Failed**: `failed` has a timestamp (job failed at that time)
- **Running**: `active` is true (job currently in progress)
- **Pending**: `started` is null but `scheduled` or `dispatched` is present
- **Unknown**: Cannot be determined from available fields

### Duration Calculations

Use the `started` and `failed` timestamps from the API:
```python
from datetime import datetime

def calculate_duration(started, failed):
    """Calculate job duration from API timestamps.
    For successful jobs, the succeeded timestamp may be present.
    For failed jobs, use the failed timestamp."""
    start = datetime.fromisoformat(started)
    end = datetime.fromisoformat(failed)
    duration = end - start
    return duration
```

### Performance Metrics

Key metrics to calculate:
- **Mean duration**: Average of all job durations
- **Median duration**: Middle value (less affected by outliers)
- **P95 duration**: 95th percentile (SLA metric)
- **Min/Max duration**: Range boundaries
- **Standard deviation**: Variability measure

## Best Practices

### Analysis Scope

**Start focused, expand as needed:**
1. Begin with specific connector if issue reported
2. Expand to related connectors if pattern emerges
3. Include all connectors for comprehensive view
4. Use appropriate time range (recent for troubleshooting, longer for trends)

### Data Presentation

**Progressive detail levels:**
1. Executive summary (one paragraph)
2. High-level statistics (table)
3. Detailed findings (by connector/pattern)
4. Raw data references (if needed)

### Recommendations

**Make them actionable:**
- Specific (not vague suggestions)
- Prioritized (what to do first)
- Feasible (realistic actions)
- Measurable (can verify completion)
- Time-bound (when to act)

### Follow-up

**Always suggest next steps:**
- Immediate actions
- Monitoring requirements
- Follow-up analysis timing
- Related skills to use
- Escalation path if needed

## Success Criteria

A successful job history analysis provides:

✅ **Clear understanding** of what happened
✅ **Quantitative metrics** (success rates, durations)
✅ **Pattern identification** (recurring issues)
✅ **Root cause insights** (why problems occur)
✅ **Actionable recommendations** (what to do)
✅ **Appropriate detail level** (not too much, not too little)
✅ **Professional presentation** (scannable, clear)

The user should be able to:
- Understand their backup job performance
- Identify any problems quickly
- Know exactly what to do next
- Make informed decisions about their backup strategy
