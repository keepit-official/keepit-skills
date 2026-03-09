---
name: keepit-executive-backup-summary
description: Executive-level backup status and data protection summary for leadership reporting. Use when users ask for executive summaries, board reports, protection scores, business risk assessments, or CIO/CTO-level backup overviews. Triggers on keywords like "executive summary", "board report", "protection score", "business risk", "data protection overview", "leadership report", "CIO report".
---

# Keepit Executive Backup Summary Skill

## Overview

This skill generates executive-level data protection summaries designed for CIOs, IT Directors, Board members, and IT Managers. It translates raw backup telemetry into business-language reports with a composite **Protection Score (0-100)**, plain-English risk descriptions, recovery readiness estimates, and board-ready snippets.

The skill aggregates data from all protected connectors and computes a weighted score reflecting overall data protection posture. Reports avoid technical jargon and focus on business risk, compliance readiness, and actionable recommendations.

**Target Personas:** CIO, CTO, IT Director, IT Manager, Board of Directors, Compliance Officer

**Report Cadences Supported:** On-demand, weekly, monthly, quarterly, board meeting prep

---

## Core Workflow

### Step 1: Gather Account Context

Retrieve account-level information to establish organizational context.

```python
# Get account details for report header
account_info = get_my_account_info()

# Extract key fields — get_my_account_info returns flat structure
# Fields: id, enabled (bool), created, product, parent, subscribed (bool)
account_id = account_info.get('id', 'Unknown')
account_enabled = account_info.get('enabled', False)
account_subscribed = account_info.get('subscribed', False)
account_state = "Active" if account_enabled and account_subscribed else "Inactive"
```

This provides the account status and subscription context for the report header.

### Step 2: Inventory Protected Applications

Enumerate all cloud connectors and translate technical types to plain-English application names.

```python
# Get all protected cloud applications
connectors = get_cloud_connectors(connectorType="cloud")

# Map technical types to business-readable names
type_map = {
    'o365-admin': 'Microsoft 365',
    'azure-ad': 'Entra ID',
    'gsuite': 'Google Workspace',
    'dynamics365': 'Dynamics 365',
    'sforce': 'Salesforce',
    'powerbi': 'Power BI',
    'zendesk': 'Zendesk',
    'okta': 'Okta',
    'docusign': 'DocuSign',
    'bamboohr': 'BambooHR',
    'confluence': 'Confluence',
    'jira': 'Jira',
    'azure-do': 'Azure DevOps',
}

# Build coverage summary
app_names = []
for connector in connectors:
    raw_type = connector.get('type', 'unknown')
    friendly = type_map.get(raw_type, raw_type.replace('-', ' ').title())
    app_names.append(friendly)

# Generate plain-English sentence
# "3 SaaS applications protected: Microsoft 365, Entra ID, Salesforce"
summary = f"{len(app_names)} SaaS application{'s' if len(app_names) != 1 else ''} protected: {', '.join(app_names)}"
```

### Step 3: Assess Protection Health

Query connector health status for every protected application.

```python
# Collect health status for each connector
health_results = []
for connector in connectors:
    health = get_connector_health(guid=connector['guid'])
    health_results.append({
        'name': connector.get('name', 'Unknown'),
        'type': connector.get('type', 'unknown'),
        'guid': connector['guid'],
        'health': health.get('health', 'unknown'),
    })

# Classify health states
# get_connector_health returns {"healthStatus": "healthy"|"unhealthy"|"critical"|"unknown"}
# We stored the extracted string above, so h['health'] is e.g. "healthy"
healthy_count = sum(1 for h in health_results if h['health'] == 'healthy')
unhealthy_count = sum(1 for h in health_results if h['health'] in ('unhealthy', 'critical'))
unknown_count = len(health_results) - healthy_count - unhealthy_count
```

### Step 4: Evaluate Backup Freshness

Determine when each application was last backed up to assess data recency.

```python
# Get most recent snapshot for each connector
recency_data = []
for connector in connectors:
    latest = get_latest_snapshot(guid=connector['guid'])
    recency_data.append({
        'name': connector.get('name', 'Unknown'),
        'type': connector.get('type', 'unknown'),
        'guid': connector['guid'],
        'latest_snapshot': latest,
    })

# Flag stale backups (>24h for daily, >48h for concern, >72h for critical)
# get_latest_snapshot returns {"tstamp": ..., "size": ..., "type": "p"|"c", "account": ...} or null
now = datetime.now(timezone.utc)
for item in recency_data:
    snapshot_data = item['latest_snapshot'] if item['latest_snapshot'] else None
    snapshot_time = parse_iso_timestamp(snapshot_data.get('tstamp', '')) if snapshot_data else None
    if snapshot_time:
        hours_ago = (now - snapshot_time).total_seconds() / 3600
        item['hours_since_backup'] = hours_ago
        if hours_ago <= 24:
            item['freshness'] = 'current'       # ✅
        elif hours_ago <= 48:
            item['freshness'] = 'acceptable'     # ⚠️
        else:
            item['freshness'] = 'stale'          # ❌
```

### Step 5: Analyze Backup Continuity

Assess RPO compliance by examining snapshot regularity over the past 30 days.

```python
# Get snapshot history for RPO analysis
rpo_results = []
for connector in connectors:
    snapshots = get_snapshot_range(guid=connector['guid'], timespan="P30D", count=99)
    rpo_results.append({
        'name': connector.get('name', 'Unknown'),
        'guid': connector['guid'],
        'snapshots': snapshots,
    })

# Calculate RPO compliance percentage
# Expected: at least 1 snapshot per day = 30 snapshots in 30 days
total_expected = 0
total_actual = 0
for result in rpo_results:
    snapshot_list = result['snapshots'] if isinstance(result['snapshots'], list) else []
    expected_count = 30  # daily backups over 30 days
    actual_count = min(len(snapshot_list), expected_count)
    total_expected += expected_count
    total_actual += actual_count

rpo_compliance = (total_actual / total_expected * 100) if total_expected > 0 else 0
```

### Step 6: Review Operational Performance

Evaluate job success rates over the past 7 days for reliability assessment.

```python
# Get job history for each connector
job_results = []
for connector in connectors:
    jobs = get_job_history(guid=connector['guid'], duration="P7D")
    job_results.append({
        'name': connector.get('name', 'Unknown'),
        'guid': connector['guid'],
        'jobs': jobs,
    })

# Calculate overall success rate
# Note: Jobs have NO explicit status field. Infer status from `active` and `failed`:
#   - failed has a timestamp → job failed
#   - active is true → job is currently running
#   - failed is null/absent AND active is false → job succeeded
total_jobs = 0
successful_jobs = 0
for result in job_results:
    job_list = result['jobs'] if isinstance(result['jobs'], list) else []
    for job in job_list:
        total_jobs += 1
        is_failed = bool(job.get('failed'))
        is_active = bool(job.get('active'))
        if not is_failed and not is_active:
            successful_jobs += 1

success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
```

### Step 7: Check Real-Time Status

Verify any currently running backup operations.

```python
# Check for active jobs across all connectors
active_operations = []
for connector in connectors:
    active = get_active_jobs(guid=connector['guid'])
    if active:
        active_list = active if isinstance(active, list) else [active]
        for job in active_list:
            active_operations.append({
                'connector_name': connector.get('name', 'Unknown'),
                'job': job,
            })

# Note in report if backups are currently running
running_count = len(active_operations)
```

### Step 8: Summarize Recent Changes

Pull audit log for configuration change awareness.

```python
# Get recent audit activity
audit_logs = get_audit_log_history(duration="P30D")

# Count and categorize changes
change_count = len(audit_logs) if isinstance(audit_logs, list) else 0

# Flag security-relevant changes
security_changes = []
for log in (audit_logs if isinstance(audit_logs, list) else []):
    action = log.get('action', '').lower()
    if any(keyword in action for keyword in ['delete', 'remove', 'disable', 'password', 'permission', 'role']):
        security_changes.append(log)
```

### Step 9: Compute Protection Score

Calculate the weighted composite Protection Score (0-100).

```python
# Protection Score weights
# - Connector Health: 30%
# - Backup Recency: 25%
# - RPO Compliance: 25%
# - Job Success Rate: 20%

health_score = calculate_health_score(health_results)       # 0-100
recency_score = calculate_recency_score(recency_data)       # 0-100
rpo_score = min(rpo_compliance, 100)                         # 0-100
job_score = min(success_rate, 100)                           # 0-100

protection_score = (
    health_score * 0.30 +
    recency_score * 0.25 +
    rpo_score * 0.25 +
    job_score * 0.20
)

# Map to letter grade
# A: 90-100, B: 80-89, C: 70-79, D: 60-69, F: <60
grade = score_to_grade(protection_score)
color = score_to_color(protection_score)
```

### Step 10: Generate Executive Report

Compile all data into a business-language executive report.

```python
# Build report sections:
# 1. Protection Score banner (score, grade, color, trend)
# 2. Coverage Summary (plain-English app list)
# 3. Risk Items (business-language, not technical)
# 4. Recovery Readiness (RPO/RTO estimates)
# 5. Board Snippet (3-5 sentences)
# 6. Recommendations

# Example risk item translation:
# Technical: "connector azure-ad health: unhealthy"
# Business:  "Entra ID backup service is experiencing issues - identity data recovery may be delayed"

board_snippet = generate_board_snippet({
    'score': protection_score,
    'grade': grade,
    'app_count': len(connectors),
    'risk_count': len(risk_items),
    'success_rate': success_rate,
    'rpo_compliance': rpo_compliance,
})
```

---

## Output Formatting Guidelines

### Report Header

```
# Data Protection Executive Summary
**Account:** {account_name}
**Report Date:** {date}
**Reporting Period:** {period}
```

### Protection Score Banner

```
## Protection Score: {score}/100 ({grade})
{color_icon} Overall data protection posture is {posture_description}.
```

Score presentation:
- **90-100 (A):** ✅ "Excellent" — Green
- **80-89 (B):** ✅ "Good" — Green
- **70-79 (C):** ⚠️ "Adequate" — Yellow
- **60-69 (D):** ⚠️ "Needs Improvement" — Yellow
- **Below 60 (F):** ❌ "Critical Attention Required" — Red

### Coverage Summary Section

```
## Application Coverage
{total_apps} SaaS applications are currently protected by Keepit:

| Application | Status | Last Backup |
|---|---|---|
| Microsoft 365 | ✅ Healthy | 2 hours ago |
| Entra ID | ✅ Healthy | 4 hours ago |
| Salesforce | ⚠️ Degraded | 26 hours ago |
```

### Risk Items Section

Present risks in business language, not technical terms:

```
## Risk Items

### 🔴 High Priority
- **Salesforce backup service is degraded** — Sales data recovery capability may be limited. Last successful backup was 26 hours ago.
  - *Business Impact:* If Salesforce data is lost, the most recent 26 hours of customer records cannot be recovered.
  - *Recommended Action:* IT team should investigate within 4 hours.

### 🟡 Medium Priority
- **3 configuration changes detected this month** — Review recommended to ensure changes align with data protection policy.

### 🟢 Low Priority
- None at this time.
```

### Recovery Readiness Section

```
## Recovery Readiness
- **Recovery Point Objective (RPO):** Estimated {rpo_hours} hours of potential data loss in a recovery scenario
- **Recovery Time Objective (RTO):** Estimated {rto_estimate} for full restoration
- **Readiness Level:** {readiness_level}
```

### Board Snippet Section

```
## Board Summary
> {3-5 sentence plain-English summary suitable for board deck inclusion}
```

### Trend Indicator

```
## Trend
{trend_icon} Protection posture is **{direction}** compared to the previous period ({delta}).
```

### Recommendations Section

```
## Recommendations
1. {Prioritized recommendation in business language}
2. {Next recommendation}
3. {Next recommendation}
```

---

## Advanced Features

### Protection Score Composition

The Protection Score is a weighted composite that balances four dimensions:

| Component | Weight | Measures |
|---|---|---|
| Connector Health | 30% | Are backup services operational? |
| Backup Recency | 25% | How fresh is the most recent backup? |
| RPO Compliance | 25% | Are backups running on schedule? |
| Job Success Rate | 20% | Are backup jobs completing without errors? |

**Scoring logic per component:**

```python
# Health Score (30% weight)
# healthy = 100, unhealthy = 50, critical/unknown = 0
# Average across all connectors

# Recency Score (25% weight)
# <12h = 100, 12-24h = 80, 24-48h = 50, 48-72h = 25, >72h = 0
# Average across all connectors

# RPO Compliance (25% weight)
# (actual_snapshots / expected_snapshots) * 100
# Capped at 100

# Job Success Rate (20% weight)
# (successful_jobs / total_jobs) * 100
# Capped at 100
```

### Trend Analysis

When historical score data is available, the skill computes trend:

```python
# Trend calculation
delta = current_score - previous_score
if delta > 2:
    direction = 'improved'     # ✅
    icon = '📈'
elif delta < -2:
    direction = 'degraded'     # ❌
    icon = '📉'
else:
    direction = 'stable'       # ➡️
    icon = '➡️'
```

### Risk Translation

Technical alerts are translated to business-language descriptions:

| Technical Issue | Business Translation |
|---|---|
| Connector health: unhealthy | "{App} backup service is down — data recovery is unavailable" |
| Connector health: degraded | "{App} backup service is experiencing issues — recovery may be delayed" |
| Backup age > 48 hours | "{App} has not been backed up in {hours} hours — recent data may not be recoverable" |
| Job failure rate > 20% | "{App} backup reliability is below target — {rate}% of recent backups failed" |
| RPO compliance < 80% | "Backup schedule compliance is at {pct}% — data protection gaps exist" |

### Board Snippet Generation

The board snippet condenses the full report into 3-5 sentences:

```python
# Template structure:
# Sentence 1: Overall score and posture
# Sentence 2: Coverage breadth
# Sentence 3: Key risk (if any) OR confidence statement
# Sentence 4: Recovery readiness (if space)
# Sentence 5: Recommendation or trend (if space)

# Example output:
# "Our data protection posture is rated A (96/100), indicating excellent coverage
#  across all critical SaaS applications. Keepit is actively protecting 3 cloud
#  applications including Microsoft 365, Entra ID, and Salesforce with a 99.2%
#  backup success rate. No material risks to data recoverability have been
#  identified this period. Estimated recovery time in a disaster scenario is
#  under 4 hours."
```

---

## Error Handling

### MCP Call Failures

```python
# If a connector health check fails, degrade gracefully
try:
    health = get_connector_health(guid=connector['guid'])
except Exception:
    health = {'healthStatus': 'unknown'}
    # Flag as risk item: "Unable to verify {App} backup health"
```

### Missing or Incomplete Data

- If no connectors are found, report "No protected applications found" and recommend onboarding
- If latest snapshot returns empty, flag the connector as "No backup data available"
- If job history is empty, note "No job history available for the reporting period"
- If audit logs fail, omit the section and note "Audit data unavailable"

### Score Calculation Edge Cases

- If all connectors fail health checks: score the health component at 0
- If no snapshots exist: score recency at 0 and RPO compliance at 0
- If no jobs ran: exclude job success rate and redistribute weight proportionally
- Minimum possible score: 0 (all systems failing, no data)

---

## Best Practices

1. **Always use plain English** — The audience is executive leadership, not backup administrators
2. **Lead with the Protection Score** — Executives want a single number first, details second
3. **Translate every technical term** — "connector" becomes "backup service", "snapshot" becomes "backup", "RPO" includes a plain explanation
4. **Prioritize risks by business impact** — Order by data loss potential, not technical severity
5. **Include the Board Snippet** — Always generate the 3-5 sentence summary even if not requested
6. **Show trend when possible** — Executives want to know direction, not just current state
7. **Keep recommendations actionable** — "IT team should investigate Salesforce backup within 4 hours" not "Check connector health"
8. **Limit to top 3-5 risks** — Executives do not need exhaustive issue lists
9. **Use consistent color coding** — Green/Yellow/Red maps to A-B/C-D/F grades
10. **Date every report** — Include generation timestamp and reporting period

---

## Common User Requests

### "Give me an executive summary of our backups"
Full workflow Steps 1-10. Produce the complete executive report with Protection Score, coverage summary, risk items, recovery readiness, board snippet, and recommendations.

### "What's our protection score?"
Steps 1-6 and 9. Calculate and present the Protection Score with grade, component breakdown, and brief risk summary.

### "I need a board report on data protection"
Full workflow Steps 1-10, emphasis on the Board Snippet section. Format for copy-paste into presentation software. Omit deep technical details.

### "Are our backups at risk?"
Steps 2-6, focus on risk identification. Present risk items in business language with impact descriptions and recommended actions.

### "How quickly can we recover our data?"
Steps 4-6, focus on recovery readiness. Present RPO and RTO estimates with plain-English explanations.

### "Compare this month to last month"
Steps 1-9 for current period, then compare against prior period scores if available. Present trend indicator and delta analysis.

### "What SaaS applications are we protecting?"
Step 2 only. Present the coverage summary with human-readable application names and health status.

### "Generate a monthly IT report"
Full workflow Steps 1-10, formatted as a monthly report with period header, month-over-month trend, and recommendations for the coming month.

---

## Cross-Skill Investigation Workflows

### Executive Summary -> Backup Failure Root Cause Analysis
When the executive summary reveals a low job success rate or specific connector failures, hand off to the **Backup Failure Root Cause Analyzer** skill for deep-dive diagnostics:
- "The executive summary shows Salesforce backup reliability at 72%. Use the root cause analyzer to investigate the failures."

### Executive Summary -> Account Health Check
When the Protection Score is below 70 or multiple connectors show issues, recommend a detailed **Account Health** assessment:
- "Our Protection Score is 65/D. Run a full account health check to identify all underlying issues."

### Executive Summary -> Compliance Audit Log
When audit log changes are flagged in the executive summary, hand off to the **Compliance Audit Log** skill for detailed change analysis:
- "The executive report noted 12 configuration changes this month. Run a compliance audit to review all changes."

### Executive Summary -> Snapshot Analyzer
When backup recency or RPO compliance scores are low, hand off to the **Snapshot Analyzer** for granular snapshot analysis:
- "RPO compliance is at 68%. Use the snapshot analyzer to identify which connectors have gaps."

### Executive Summary -> Job History Analyzer
When job success rates are below target, hand off to the **Job History Analyzer** for detailed job performance review:
- "Job success rate is 85%. Analyze the job history to find patterns in the failures."

---

## Skill Integration Points

| Skill | Integration Trigger | Data Passed |
|---|---|---|
| Account Health | Protection Score < 70 | Score, failing connectors |
| Backup Failure Root Cause | Job success rate < 90% | Connector GUIDs, failure counts |
| Compliance Audit Log | Security changes detected | Audit log entries, change count |
| Snapshot Analyzer | RPO compliance < 85% | Connector GUIDs, snapshot gaps |
| Job History Analyzer | Job success rate < 95% | Connector GUIDs, time period |
| Weekly Operations Digest | Scheduled reporting | Current Protection Score, trends |

---

## Technical Notes

### MCP Functions Used

| Function | Purpose | Call Pattern |
|---|---|---|
| `get_my_account_info()` | Account context for report header | Once per report |
| `get_cloud_connectors(connectorType="cloud")` | Enumerate protected applications | Once per report |
| `get_connector_health(guid)` | Health status per application | Once per connector |
| `get_latest_snapshot(guid)` | Backup recency per application | Once per connector |
| `get_snapshot_range(guid, timespan, count)` | RPO compliance analysis | Once per connector, `timespan="P30D"`, `count=99` |
| `get_job_history(guid, duration)` | Job success rate | Once per connector, `duration="P7D"` |
| `get_active_jobs(guid)` | Real-time operation status | Once per connector |
| `get_audit_log_history(duration)` | Configuration change awareness | Once per report, `duration="P30D"` |

### Time Calculations

```python
# Backup freshness (hours since last backup)
hours_since = (now - snapshot_timestamp).total_seconds() / 3600

# RPO compliance (percentage of expected backups achieved)
rpo_pct = (actual_snapshots / expected_snapshots) * 100

# Job success rate (percentage of jobs completed successfully)
success_pct = (successful_jobs / total_jobs) * 100

# Trend delta (current score minus previous score)
delta = current_score - previous_score
```

### Error Resilience

The executive report must always render, even with partial data:

```python
# Priority order for graceful degradation:
# 1. Protection Score (always compute, even if components are partial)
# 2. Coverage Summary (always show, mark unknown health as ⚠️)
# 3. Risk Items (always show, include data-gathering failures as risks)
# 4. Board Snippet (always generate from available data)
# 5. Recovery Readiness (omit if no snapshot data)
# 6. Trend (omit if no historical comparison available)
```

---

## Success Metrics

A well-generated executive backup summary should:

1. **Be understood by a non-technical executive in under 2 minutes**
2. **Lead with the Protection Score** — single number, letter grade, color
3. **List all protected applications** in plain English
4. **Identify top 3-5 risks** in business-impact language
5. **Include a board-ready snippet** of 3-5 sentences
6. **Provide actionable recommendations** with clear ownership and timelines
7. **Show trend direction** when historical data is available
8. **Complete in under 30 seconds** of MCP call execution time
9. **Degrade gracefully** — always produce a report, even with partial data
10. **Avoid all technical jargon** — no GUIDs, connector types, or API terms in the output
