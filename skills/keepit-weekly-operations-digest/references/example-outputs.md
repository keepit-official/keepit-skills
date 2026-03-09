# Weekly Operations Digest - Example Outputs

This document contains example outputs for the Keepit Weekly Operations Digest
skill across different scenarios. Each scenario includes the full digest report
with all sections. These examples serve as reference templates for consistent
formatting and tone.

---

## Scenario 1: Clean Week

All connectors healthy. No failures. High success rate. No gaps. Minimal
configuration changes. This is the ideal state.

**User prompt:** "Give me the weekly backup report"

```markdown
## 📊 Weekly Operations Digest
**Period:** Feb 10 – Feb 17, 2026
**Account:** Contoso Corp (Active)
**Generated:** Feb 17, 2026 at 08:15 UTC

---

### Week at a Glance
| Metric                | Value       |
|-----------------------|-------------|
| Total Jobs            | 156         |
| Success Rate          | 100.0%      |
| Failed Jobs           | 0           |
| Connectors            | 6           |
| Healthy Connectors    | 6 ✅        |
| Backup Gaps           | 0 ✅        |
| Config Changes        | 1           |
| Action Items          | 0           |

✅ **All systems operating normally.** No failures, no gaps, no action items.

---

### Connector Status
| Connector              | Type              | Health | Last Backup | Jobs | Failures | Rate   |
|------------------------|-------------------|--------|-------------|------|----------|--------|
| M365 Production        | Microsoft 365     | ✅     | 2h ago      | 42   | 0        | 100.0% |
| M365 Archive           | Microsoft 365     | ✅     | 3h ago      | 28   | 0        | 100.0% |
| Entra ID Prod          | Entra ID          | ✅     | 4h ago      | 21   | 0        | 100.0% |
| Google Workspace       | Google Workspace  | ✅     | 1h ago      | 35   | 0        | 100.0% |
| Salesforce CRM         | Salesforce        | ✅     | 5h ago      | 14   | 0        | 100.0% |
| Zendesk Support        | Zendesk           | ✅     | 6h ago      | 16   | 0        | 100.0% |

---

### Failures & Issues

No failures recorded this week.

---

### Configuration Changes
| When            | Who          | Action                              |
|-----------------|--------------|-------------------------------------|
| Feb 14 09:30    | admin@corp   | Updated retention policy on M365 Archive |

No high-severity configuration changes detected.

---

### Backup Continuity

✅ **No gaps detected.** All connectors maintained consistent backup schedules
throughout the reporting period.

---

### Action Items

No action items this week. All systems are operating as expected.

---

### Trend (vs. Previous Week)
| Metric         | This Week | Last Week | Delta  |
|----------------|-----------|-----------|--------|
| Success Rate   | 100.0%    | 99.3%     | +0.7%  |
| Failed Jobs    | 0         | 1         | -1     |
| Total Jobs     | 156       | 152       | +4     |
| Backup Gaps    | 0         | 0         | —      |

✅ Operations are stable. Slight improvement in success rate.
```

---

## Scenario 2: Problematic Week

Multiple connectors with failures. Backup gaps detected. Several configuration
changes. Critical health status on one connector. This represents a week that
requires immediate attention.

**User prompt:** "Monday morning status report"

```markdown
## 📊 Weekly Operations Digest
**Period:** Feb 10 – Feb 17, 2026
**Account:** Acme Industries (Active)
**Generated:** Feb 17, 2026 at 07:00 UTC

---

### Week at a Glance
| Metric                | Value       |
|-----------------------|-------------|
| Total Jobs            | 198         |
| Success Rate          | 87.4%       |
| Failed Jobs           | 25          |
| Connectors            | 10          |
| Healthy Connectors    | 6 ✅        |
| Warning Connectors    | 2 ⚠️        |
| Critical Connectors   | 2 ❌        |
| Backup Gaps           | 3 ⚠️        |
| Config Changes        | 7           |
| Action Items          | 6           |

❌ **Attention required.** Multiple failures and backup gaps detected.
Two connectors are in critical state.

---

### Connector Status
| Connector              | Type              | Health | Last Backup | Jobs | Failures | Rate   |
|------------------------|-------------------|--------|-------------|------|----------|--------|
| Salesforce CRM         | Salesforce        | ❌     | 52h ago     | 18   | 9        | 50.0%  |
| Dynamics 365 Prod      | Dynamics 365      | ❌     | 74h ago     | 14   | 8        | 42.9%  |
| Zendesk Support        | Zendesk           | ⚠️     | 28h ago     | 16   | 3        | 81.3%  |
| Power BI Reports       | Power BI          | ⚠️     | 30h ago     | 10   | 2        | 80.0%  |
| M365 Production        | Microsoft 365     | ✅     | 1h ago      | 42   | 1        | 97.6%  |
| M365 Archive           | Microsoft 365     | ✅     | 2h ago      | 28   | 1        | 96.4%  |
| Entra ID Prod          | Entra ID          | ✅     | 3h ago      | 21   | 0        | 100.0% |
| Google Workspace       | Google Workspace  | ✅     | 1h ago      | 35   | 1        | 97.1%  |
| Okta Identity          | Okta              | ✅     | 4h ago      | 7    | 0        | 100.0% |
| Confluence Wiki        | Confluence        | ✅     | 5h ago      | 7    | 0        | 100.0% |

---

### Failures & Issues

🔴 **Authentication Failures** (12 occurrences)
   Connectors: Salesforce CRM, Dynamics 365 Prod
   First seen: Feb 11 03:00 | Last seen: Feb 16 21:00
   Pattern: OAuth token refresh failure — credentials may have expired or
   been revoked. Both connectors use the same service account.

🔴 **API Rate Limit Exceeded** (5 occurrences)
   Connectors: Zendesk Support, Power BI Reports
   First seen: Feb 12 14:00 | Last seen: Feb 15 09:00
   Pattern: Upstream API returned 429 Too Many Requests. Jobs were not
   automatically retried.

🟡 **Transient Network Errors** (3 occurrences)
   Connectors: M365 Production, M365 Archive, Google Workspace
   First seen: Feb 13 02:15 | Last seen: Feb 13 02:45
   Pattern: Connection timeout during nightly backup window. All three
   jobs succeeded on automatic retry within 30 minutes.

---

### Configuration Changes
| When            | Who             | Action                                      |
|-----------------|-----------------|---------------------------------------------|
| Feb 10 08:00    | admin@acme      | Created connector "Power BI Reports"        |
| Feb 10 08:15    | admin@acme      | Configured retention policy for Power BI    |
| Feb 12 11:30    | svc-backup      | Modified Salesforce connector settings      |
| Feb 13 09:00    | admin@acme      | Updated Zendesk API key                     |
| Feb 14 16:00    | admin@acme      | Changed Dynamics 365 backup schedule        |
| Feb 15 10:00    | svc-backup      | Modified M365 Production retention rules    |
| Feb 16 14:00    | admin@acme      | Re-authorized Salesforce OAuth token        |

⚠️ **Note:** The Salesforce OAuth re-authorization on Feb 16 may resolve the
ongoing authentication failures. Monitor over the next 24 hours.

---

### Backup Continuity

⚠️ **3 gaps detected**

- **Salesforce CRM**: 52-hour gap (Feb 14 22:00 → Feb 17 02:00)
  Likely cause: Persistent authentication failures prevented all backup
  attempts during this window.

- **Dynamics 365 Prod**: 74-hour gap (Feb 13 18:00 → Feb 16 20:00)
  Likely cause: Authentication failure combined with schedule change on
  Feb 14 may have caused extended outage.

- **Power BI Reports**: 38-hour gap (Feb 11 10:00 → Feb 13 00:00)
  Likely cause: Newly created connector; initial backups may have taken
  time to configure and start.

---

### Action Items

1. 🔴 **Verify Salesforce re-authorization** — OAuth token was refreshed on Feb 16;
   confirm backups are now completing successfully. If not, re-authorize from the
   Keepit admin console.
   *Connector: Salesforce CRM*

2. 🔴 **Resolve Dynamics 365 authentication** — 74-hour backup gap and ongoing
   failures. Re-authorize the service account and verify API permissions.
   *Connector: Dynamics 365 Prod*

3. 🔴 **Investigate Dynamics 365 data coverage** — 74-hour gap may mean missing
   data. Trigger a full backup and verify data completeness.
   *Connector: Dynamics 365 Prod*

4. 🟡 **Address API rate limiting** — Zendesk and Power BI are hitting rate limits.
   Consider adjusting backup schedules to off-peak hours or reducing concurrency.
   *Connectors: Zendesk Support, Power BI Reports*

5. 🟡 **Verify Power BI initial setup** — Connector created Feb 10; confirm that
   the initial backup completed fully and that the schedule is correct.
   *Connector: Power BI Reports*

6. 🟢 **Review transient network errors** — Three connectors saw brief timeouts
   on Feb 13 around 02:00 UTC. Likely a network blip; all retried successfully.
   Monitor for recurrence.
   *Connectors: M365 Production, M365 Archive, Google Workspace*

---

### Trend (vs. Previous Week)
| Metric         | This Week | Last Week | Delta   |
|----------------|-----------|-----------|---------|
| Success Rate   | 87.4%     | 98.1%     | -10.7%  |
| Failed Jobs    | 25        | 3         | +22     |
| Total Jobs     | 198       | 186       | +12     |
| Backup Gaps    | 3         | 0         | +3      |

❌ **Significant decline.** Success rate dropped over 10 percentage points.
Authentication issues across Salesforce and Dynamics 365 account for the
majority of failures.
```

---

## Scenario 3: Mixed Week

Some issues occurred mid-week but were partially resolved. Improvement trend
visible toward the end of the week. One connector still needs attention.

**User prompt:** "What happened with our backups this week?"

```markdown
## 📊 Weekly Operations Digest
**Period:** Feb 10 – Feb 17, 2026
**Account:** Northwind Corp (Active)
**Generated:** Feb 17, 2026 at 09:00 UTC

---

### Week at a Glance
| Metric                | Value       |
|-----------------------|-------------|
| Total Jobs            | 112         |
| Success Rate          | 94.6%       |
| Failed Jobs           | 6           |
| Connectors            | 7           |
| Healthy Connectors    | 6 ✅        |
| Warning Connectors    | 1 ⚠️        |
| Backup Gaps           | 1 ⚠️        |
| Config Changes        | 4           |
| Action Items          | 3           |

⚠️ **Mostly stable with one area of concern.** Six failures occurred
mid-week, concentrated on a single connector. Five of six issues have
been resolved; one connector remains in warning state.

---

### Connector Status
| Connector              | Type              | Health | Last Backup | Jobs | Failures | Rate   |
|------------------------|-------------------|--------|-------------|------|----------|--------|
| Salesforce CRM         | Salesforce        | ⚠️     | 8h ago      | 14   | 5        | 64.3%  |
| M365 Production        | Microsoft 365     | ✅     | 1h ago      | 28   | 0        | 100.0% |
| M365 Archive           | Microsoft 365     | ✅     | 2h ago      | 21   | 0        | 100.0% |
| Entra ID Prod          | Entra ID          | ✅     | 3h ago      | 14   | 0        | 100.0% |
| Google Workspace       | Google Workspace  | ✅     | 1h ago      | 21   | 0        | 100.0% |
| Jira Projects          | Jira              | ✅     | 4h ago      | 7    | 1        | 85.7%  |
| Azure DevOps           | Azure DevOps      | ✅     | 5h ago      | 7    | 0        | 100.0% |

---

### Failures & Issues

🔴 **Salesforce API Errors** (5 occurrences)
   Connector: Salesforce CRM
   First seen: Feb 12 06:00 | Last seen: Feb 14 18:00
   Pattern: Salesforce API returned 503 Service Unavailable during
   scheduled backup windows. Salesforce status page confirmed a partial
   outage Feb 12–14. Backups resumed successfully on Feb 15.

🟢 **Jira Timeout** (1 occurrence)
   Connector: Jira Projects
   Seen: Feb 13 03:00
   Pattern: Single timeout during nightly backup. Job succeeded on
   the next scheduled run. No further occurrences.

---

### Configuration Changes
| When            | Who             | Action                                  |
|-----------------|-----------------|------------------------------------------|
| Feb 11 10:00    | admin@nw        | Added new Jira project to backup scope   |
| Feb 13 08:30    | admin@nw        | Modified Salesforce backup schedule      |
| Feb 14 14:00    | admin@nw        | Adjusted Salesforce retry settings       |
| Feb 15 09:00    | admin@nw        | Restored Salesforce original schedule    |

The Salesforce schedule changes on Feb 13–15 were in response to the
upstream outage. The schedule was restored after the outage resolved.

---

### Backup Continuity

⚠️ **1 gap detected**

- **Salesforce CRM**: 42-hour gap (Feb 12 06:00 → Feb 13 24:00)
  Cause: Salesforce upstream outage (confirmed via Salesforce Status).
  Backups resumed Feb 14 and have been completing since, though the
  connector remains in warning state pending a full clean run.

---

### Action Items

1. 🟡 **Monitor Salesforce CRM recovery** — Backups resumed on Feb 15 but
   the connector is still in warning state. Verify that the next 2–3 scheduled
   runs complete without error to confirm full recovery.
   *Connector: Salesforce CRM*

2. 🟡 **Verify Salesforce data coverage** — The 42-hour gap may mean some
   incremental changes were not captured. Consider triggering a full backup
   to ensure completeness.
   *Connector: Salesforce CRM*

3. 🟢 **Review Jira backup stability** — Single timeout on Feb 13. No action
   needed unless it recurs. Informational only.
   *Connector: Jira Projects*

---

### Trend (vs. Previous Week)
| Metric         | This Week | Last Week | Delta  |
|----------------|-----------|-----------|--------|
| Success Rate   | 94.6%     | 99.1%     | -4.5%  |
| Failed Jobs    | 6         | 1         | +5     |
| Total Jobs     | 112       | 108       | +4     |
| Backup Gaps    | 1         | 0         | +1     |

⚠️ **Slight decline** due to the Salesforce upstream outage. Excluding the
Salesforce connector, the remaining environment maintained 99.0% success rate.
Expect metrics to recover next week if Salesforce stabilizes.

---

### Mid-Week Recovery Timeline

For context, here is how the Salesforce issue progressed:

| Date   | Event                                                |
|--------|------------------------------------------------------|
| Feb 12 | Salesforce API outage begins; backup jobs start failing |
| Feb 13 | Admin adjusts backup schedule to retry more frequently |
| Feb 14 | Admin adjusts retry settings; Salesforce still intermittent |
| Feb 15 | Salesforce outage resolves; backups resume successfully |
| Feb 15 | Admin restores original backup schedule              |
| Feb 16 | Two consecutive successful backups confirmed         |
| Feb 17 | Connector remains in warning state pending third clean run |
```

---

## Scenario 4: Response Templates

Reusable templates for common digest sections.

### Template: Week at a Glance

```markdown
## 📊 Weekly Operations Digest
**Period:** {start_date} – {end_date}
**Account:** {account_name} ({account_state})
**Generated:** {generated_at}

---

### Week at a Glance
| Metric                | Value             |
|-----------------------|-------------------|
| Total Jobs            | {total_jobs}      |
| Success Rate          | {success_rate}%   |
| Failed Jobs           | {failed_jobs}     |
| Connectors            | {total_connectors}|
| Healthy Connectors    | {healthy} ✅      |
| Backup Gaps           | {gaps} {gap_icon} |
| Config Changes        | {audit_count}     |
| Action Items          | {action_count}    |

{overall_status_icon} **{overall_status_message}**
```

### Template: Connector Status Table

```markdown
### Connector Status
| Connector | Type | Health | Last Backup | Jobs | Failures | Rate |
|-----------|------|--------|-------------|------|----------|------|
{for each connector, sorted by status (issues first):}
| {name} | {type} | {health_icon} | {last_backup_ago} | {total_jobs} | {failed_jobs} | {success_rate}% |
{end for}
```

### Template: Failures Section

```markdown
### Failures & Issues

{if no failures:}
No failures recorded this week.

{else, for each failure pattern grouped by severity:}
{severity_icon} **{pattern_title}** ({count} occurrence(s))
   Connector(s): {connectors_affected}
   First seen: {first_seen} | Last seen: {last_seen}
   Pattern: {pattern_description}
{end for}
```

### Template: Configuration Changes

```markdown
### Configuration Changes
| When | Who | Action |
|------|-----|--------|
{for each audit event:}
| {timestamp} | {who} | {summary} |
{end for}

{if no changes:}
No configuration changes detected this week.

{if high-severity changes exist:}
⚠️ **Note:** {context about the significant change and its potential impact}
```

### Template: Backup Continuity

```markdown
### Backup Continuity

{if no gaps:}
✅ **No gaps detected.** All connectors maintained consistent backup schedules
throughout the reporting period.

{else:}
⚠️ **{gap_count} gap(s) detected**

{for each gap, sorted by duration descending:}
- **{connector_name}**: {gap_hours}-hour gap ({gap_start} → {gap_end})
  {likely_cause_description}
{end for}
```

### Template: Action Items

```markdown
### Action Items

{if no action items:}
No action items this week. All systems are operating as expected.

{else, numbered list sorted by priority:}
{n}. {priority_icon} **{title}** — {description}
   *Connector: {connector_name}*

{end for}
```

### Template: Week-over-Week Trend

```markdown
### Trend (vs. Previous Week)
| Metric         | This Week    | Last Week    | Delta    |
|----------------|-------------|--------------|----------|
| Success Rate   | {current}%  | {previous}%  | {delta}% |
| Failed Jobs    | {current}   | {previous}   | {delta}  |
| Total Jobs     | {current}   | {previous}   | {delta}  |
| Backup Gaps    | {current}   | {previous}   | {delta}  |

{trend_icon} **{trend_description}**
```

### Template: Executive Summary (Short Form)

For IT Managers who want a concise overview:

```markdown
## 📊 Weekly Backup Summary — {period}

**Status:** {overall_status_icon} {overall_status_word}
**Success Rate:** {success_rate}% ({total_jobs} jobs)
**Connectors:** {healthy}/{total} healthy

{if action items exist:}
### Needs Attention
{for each high/medium priority action item:}
- {priority_icon} {title} ({connector})
{end for}

{else:}
All systems nominal. No action required.
```

### Template: Single-Connector Weekly Report

For when the user requests a digest for a specific connector:

```markdown
## 📊 Weekly Report: {connector_name}
**Type:** {connector_type}
**Period:** {start_date} – {end_date}

### Status
| Metric          | Value               |
|-----------------|---------------------|
| Health          | {health_icon} {health_status} |
| Last Backup     | {last_backup_ago}   |
| Jobs This Week  | {total_jobs}        |
| Successful      | {successful_jobs}   |
| Failed          | {failed_jobs}       |
| Success Rate    | {success_rate}%     |
| Backup Gaps     | {gap_count}         |

{if failures:}
### Failures
{for each failure:}
- **{timestamp}**: {description}
{end for}

{if gaps:}
### Backup Gaps
{for each gap:}
- {gap_hours}-hour gap ({gap_start} → {gap_end})
{end for}

{if action items:}
### Recommended Actions
{for each action:}
- {priority_icon} {title}: {description}
{end for}
```

### Template: Data Collection Error Section

When some connectors fail to return data:

```markdown
### Data Collection Notes

⚠️ The following connectors could not be fully queried during digest
generation. Their metrics are excluded from the totals above.

| Connector          | Issue                         |
|-------------------|-------------------------------|
{for each error:}
| {connector_name}  | {operation}: {error_message}  |
{end for}

These connectors should be investigated separately.
```

---

## Formatting Notes

### Overall Status Logic

The overall status message at the top of the digest follows these rules:

| Condition                          | Icon | Message                                   |
|-----------------------------------|------|-------------------------------------------|
| 100% success, 0 gaps, all healthy | ✅   | All systems operating normally.           |
| >95% success, 0 critical          | ✅   | Operations healthy with minor issues.     |
| 90-95% success OR warnings exist  | ⚠️   | Mostly stable with areas of concern.      |
| <90% success OR critical exists   | ❌   | Attention required. Multiple issues found.|
| <80% success AND gaps detected    | ❌   | Critical issues detected. Immediate action needed. |

### Connector Table Sort Order

Connectors in the status table are always sorted with issues first:
1. ❌ Critical / failing connectors
2. ⚠️ Warning / degraded connectors
3. ✅ Healthy connectors

Within each group, sort alphabetically by connector name.

### Action Item Priority Rules

| Condition                               | Priority | Icon |
|-----------------------------------------|----------|------|
| Connector in critical state             | High     | 🔴   |
| Failure pattern with 3+ occurrences     | High     | 🔴   |
| Backup gap > 72 hours                   | High     | 🔴   |
| No backups ever (stale = never)         | High     | 🔴   |
| Backup gap 36–72 hours                  | Medium   | 🟡   |
| Warning health status                   | Medium   | 🟡   |
| Failure pattern with 2 occurrences      | Medium   | 🟡   |
| API rate limit issues                   | Medium   | 🟡   |
| Single transient failure (auto-retried) | Low      | 🟢   |
| Informational config change             | Low      | 🟢   |
| New connector to verify                 | Low      | 🟢   |

### Trend Direction Icons

| Direction  | Icon | Threshold                            |
|-----------|------|--------------------------------------|
| Improving | ✅   | Rate delta > +1pp AND failures down  |
| Stable    | —    | Rate delta within +/- 1pp            |
| Declining | ❌   | Rate delta < -1pp OR failures up > 2 |
