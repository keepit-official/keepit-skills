# Executive Backup Summary — Example Outputs

This document contains reference examples of the Keepit Executive Backup Summary skill output across different scenarios. Use these as formatting templates and quality benchmarks.

---

## Table of Contents

1. [Board-Ready Quarterly Summary — All Healthy (Score 96/A)](#1-board-ready-quarterly-summary--all-healthy-score-96a)
2. [Monthly Executive Report with One Issue (Score 78/C)](#2-monthly-executive-report-with-one-issue-score-78c)
3. [Risk Escalation Report — Critical Issues (Score 45/F)](#3-risk-escalation-report--critical-issues-score-45f)
4. [Response Templates](#4-response-templates)

---

## 1. Board-Ready Quarterly Summary — All Healthy (Score 96/A)

**Scenario:** All three connectors (Microsoft 365, Entra ID, Salesforce) are healthy, backups are fresh, RPO compliance is high, and job success rate is excellent. This is the ideal state.

**User prompt:** "Give me a board-ready summary of our backup status for Q4."

```markdown
# Data Protection Executive Summary
**Account:** Acme Corporation
**Report Date:** December 31, 2025
**Reporting Period:** Q4 2025 (October 1 – December 31)

---

## Protection Score: 96/100 (A)
✅ Overall data protection posture is **Excellent**.

| Component | Score | Weight |
|---|---|---|
| Connector Health | 100/100 | 30% |
| Backup Recency | 93/100 | 25% |
| RPO Compliance | 97/100 | 25% |
| Job Success Rate | 99/100 | 20% |

---

## Application Coverage
3 SaaS applications are currently protected by Keepit:

| Application | Status | Last Backup |
|---|---|---|
| Microsoft 365 | ✅ Healthy | 2 hours ago |
| Entra ID | ✅ Healthy | 4 hours ago |
| Salesforce | ✅ Healthy | 6 hours ago |

All critical cloud applications are covered. No gaps in application-level protection have been identified.

---

## Risk Items

### 🔴 High Priority
- None at this time.

### 🟡 Medium Priority
- None at this time.

### 🟢 Low Priority
- None at this time.

No material risks to data recoverability have been identified this quarter.

---

## Recovery Readiness
- **Recovery Point Objective (RPO):** Estimated 6 hours of potential data loss in a worst-case recovery scenario
- **Recovery Time Objective (RTO):** Under 4 hours for full restoration of all protected applications
- **Readiness Level:** ✅ Excellent

In a disaster scenario, all three protected applications could be restored to within the last 6 hours of data, with full restoration completed in under 4 hours.

---

## Trend
📈 Protection posture is **improved** compared to the previous quarter (+3 points).

The improvement is driven by increased backup frequency for Salesforce, which reduced average RPO from 18 hours to 6 hours.

---

## Board Summary
> Our data protection posture is rated A (96/100), indicating excellent coverage across all critical SaaS applications. Keepit is actively protecting 3 cloud applications including Microsoft 365, Entra ID, and Salesforce with a 99.2% backup success rate. No material risks to data recoverability have been identified this period. Estimated recovery time in a disaster scenario is under 4 hours.

---

## Recommendations
1. **Continue current backup schedules** — All applications are well within target RPO and RTO thresholds.
2. **Evaluate additional application coverage** — Consider extending Keepit protection to any newly adopted SaaS platforms (e.g., Power BI, Zendesk) to maintain comprehensive coverage.
3. **Schedule next quarterly review** — Maintain the quarterly executive review cadence to ensure continued visibility into data protection posture.

---

## Operational Summary
- **Total backup jobs (Q4):** 276
- **Successful:** 274 (99.3%)
- **Failed:** 2 (0.7%)
- **Configuration changes this quarter:** 4 (all reviewed, no concerns)
- **Active jobs at report time:** 1 (Microsoft 365 incremental backup in progress)
```

---

## 2. Monthly Executive Report with One Issue (Score 78/C)

**Scenario:** Microsoft 365 and Entra ID are healthy, but Salesforce connector is degraded with a stale backup (last backup was 26 hours ago). Overall job success rate is slightly below target.

**User prompt:** "Generate a monthly executive report on our data protection status."

```markdown
# Data Protection Executive Summary
**Account:** Acme Corporation
**Report Date:** January 31, 2026
**Reporting Period:** January 2026

---

## Protection Score: 78/100 (C)
⚠️ Overall data protection posture is **Adequate**.

| Component | Score | Weight |
|---|---|---|
| Connector Health | 83/100 | 30% |
| Backup Recency | 60/100 | 25% |
| RPO Compliance | 82/100 | 25% |
| Job Success Rate | 88/100 | 20% |

The score has decreased from last month's 92/A, primarily due to degraded Salesforce backup performance.

---

## Application Coverage
3 SaaS applications are currently protected by Keepit:

| Application | Status | Last Backup |
|---|---|---|
| Microsoft 365 | ✅ Healthy | 3 hours ago |
| Entra ID | ✅ Healthy | 5 hours ago |
| Salesforce | ⚠️ Degraded | 26 hours ago |

Two of three applications are fully operational. Salesforce backup service requires attention.

---

## Risk Items

### 🔴 High Priority
- **Salesforce has not been backed up recently** — Salesforce has not been backed up in 26 hours. If Salesforce data is lost, the most recent 26 hours of customer records, opportunities, and pipeline data cannot be recovered.
  - *Business Impact:* Sales team data entered in the last 26 hours is not yet protected. In a data loss event, this information would need to be manually re-entered.
  - *Recommended Action:* IT team should investigate the Salesforce backup service within 4 hours and trigger a manual backup if needed.

### 🟡 Medium Priority
- **Salesforce backup service is experiencing issues** — The Salesforce backup connector is operating in a degraded state. Data recovery for Salesforce may be delayed or incomplete until the issue is resolved.
  - *Business Impact:* If a Salesforce restore is needed, it may take longer than expected or may not include the most recent data.
  - *Recommended Action:* IT team should investigate the Salesforce backup service within 4 hours.

- **Backup job reliability is slightly below target** — 12% of backup jobs failed this month across all applications. While Microsoft 365 and Entra ID maintained high reliability, Salesforce accounted for the majority of failures.
  - *Business Impact:* Recurring failures increase the risk of data protection gaps.
  - *Recommended Action:* IT team should review Salesforce backup job logs and resolve recurring failures.

### 🟢 Low Priority
- **5 configuration changes detected this month** — Review recommended to ensure changes align with data protection policy.

---

## Recovery Readiness
- **Recovery Point Objective (RPO):** Estimated 26 hours of potential data loss for Salesforce; 5 hours for all other applications
- **Recovery Time Objective (RTO):** Approximately 6 hours for full restoration of all protected applications
- **Readiness Level:** ⚠️ Fair

Recovery readiness is fair. Microsoft 365 and Entra ID can be restored quickly with minimal data loss. However, Salesforce recovery would result in up to 26 hours of data loss until the backup service is restored.

---

## Trend
📉 Protection posture is **degraded** compared to the previous month (-14 points).

The decline is driven by the Salesforce backup service degradation. Prior to this issue, the protection posture was tracking at 92/A.

---

## Board Summary
> Our data protection posture is rated C (78/100), indicating adequate but reduced coverage across our SaaS applications. Keepit is actively protecting 3 cloud applications including Microsoft 365, Entra ID, and Salesforce with an 88% backup success rate. One risk item requires attention: Salesforce backup service is experiencing issues and the most recent backup is 26 hours old. The IT team has been notified and is investigating. Estimated recovery time in a disaster scenario is approximately 6 hours.

---

## Recommendations
1. **Investigate Salesforce backup degradation immediately** — The Salesforce connector has been degraded for over 24 hours. IT team should prioritize restoring normal backup operations and trigger a manual backup once the service is healthy.
2. **Review Salesforce job failure logs** — Identify the root cause of increased job failures to prevent recurrence.
3. **Establish alerting threshold** — Configure alerts for any connector that has not completed a backup within 12 hours to enable faster response.
4. **Schedule follow-up review in 1 week** — Verify that Salesforce backup service has been restored and protection score has returned to target levels.

---

## Operational Summary
- **Total backup jobs (January):** 89
- **Successful:** 78 (87.6%)
- **Failed:** 11 (12.4%)
- **Salesforce failures:** 9 of 11 total failures
- **Configuration changes this month:** 5 (review recommended)
- **Active jobs at report time:** 0
```

---

## 3. Risk Escalation Report — Critical Issues (Score 45/F)

**Scenario:** Entra ID connector is unhealthy (no backups in 4 days), Salesforce is degraded with stale backups, Microsoft 365 has low job success rate. Multiple critical risks require immediate executive attention.

**User prompt:** "Our backups seem to be having problems. Give me an executive risk report."

```markdown
# Data Protection Executive Summary — RISK ESCALATION
**Account:** Acme Corporation
**Report Date:** February 15, 2026
**Reporting Period:** Last 7 Days
**Escalation Level:** Critical

---

## Protection Score: 45/100 (F)
❌ Overall data protection posture requires **Critical Attention**.

| Component | Score | Weight |
|---|---|---|
| Connector Health | 50/100 | 30% |
| Backup Recency | 25/100 | 25% |
| RPO Compliance | 52/100 | 25% |
| Job Success Rate | 60/100 | 20% |

**This score represents a significant decline from the prior period (78/C). Immediate action is required.**

---

## Application Coverage
3 SaaS applications are protected by Keepit, but all three are experiencing issues:

| Application | Status | Last Backup |
|---|---|---|
| Microsoft 365 | ⚠️ Degraded | 18 hours ago |
| Entra ID | ❌ Unhealthy | 96 hours ago (4 days) |
| Salesforce | ⚠️ Degraded | 52 hours ago |

No applications are operating normally. Data protection coverage is materially impaired.

---

## Risk Items

### 🔴 High Priority

1. **Entra ID backup service is down** — The Entra ID (identity management) backup service has been unavailable for 4 days. Identity data, user accounts, group memberships, and access policies are not being backed up.
   - *Business Impact:* If Entra ID data is lost or corrupted, user accounts, access permissions, and security policies cannot be recovered. This could prevent employees from accessing all cloud applications. The last recoverable state is 4 days old.
   - *Recommended Action:* IT team must investigate the Entra ID backup service immediately. This is the highest priority item due to the cascading impact on all cloud access.

2. **Salesforce has not been backed up in over 48 hours** — The Salesforce backup is 52 hours stale. Two full business days of customer data, opportunities, and sales pipeline information are unprotected.
   - *Business Impact:* If Salesforce data is lost, 52 hours of customer interactions, deals, and pipeline updates cannot be recovered. Revenue-impacting data is at risk.
   - *Recommended Action:* IT team should investigate the Salesforce backup service within 4 hours and trigger a manual backup once connectivity is restored.

3. **Microsoft 365 backup reliability is critically low** — Only 60% of Microsoft 365 backup jobs succeeded in the past 7 days. 40% of backup attempts have failed.
   - *Business Impact:* Email, documents, and collaboration data in Microsoft 365 may have gaps in backup coverage. Some data created in the past week may not be recoverable.
   - *Recommended Action:* IT team should review Microsoft 365 backup job logs immediately to identify and resolve the failure pattern.

### 🟡 Medium Priority

4. **Backup schedule compliance is significantly below target** — Only 52% of expected backups were completed across all applications in the past 30 days. The target is 95%.
   - *Business Impact:* Significant data protection gaps exist across the reporting period. Multiple time windows have no backup points available for recovery.
   - *Recommended Action:* After resolving the individual connector issues above, IT team should perform a full schedule audit to verify all backup windows are properly configured.

5. **8 configuration changes detected in the past 30 days** — An unusually high number of configuration changes were detected. Review is recommended to determine if any changes contributed to the current issues.
   - *Business Impact:* Configuration changes may have inadvertently caused or contributed to backup failures.
   - *Recommended Action:* IT team should review the audit log for the past 30 days and correlate changes with the onset of backup failures.

### 🟢 Low Priority
- None. All items are medium or high priority.

---

## Recovery Readiness
- **Recovery Point Objective (RPO):** Estimated 96 hours (4 days) of potential data loss for Entra ID; 52 hours for Salesforce; 18 hours for Microsoft 365
- **Recovery Time Objective (RTO):** Approximately 1.5 days for full restoration of all protected applications (assuming backup services are first restored to health)
- **Readiness Level:** ❌ Poor

Recovery readiness is poor. In a disaster scenario today:
- **Entra ID** could only be restored to a state from 4 days ago — all identity changes, new accounts, and permission updates since then would be lost.
- **Salesforce** could only be restored to a state from 52 hours ago — two business days of customer data would be lost.
- **Microsoft 365** could be restored to approximately 18 hours ago, but some data may be missing due to intermittent backup failures.

---

## Trend
📉 Protection posture is **degraded** compared to the previous period (-33 points).

This is a sharp decline from the prior period's score of 78/C. The deterioration accelerated over the past 4 days, correlating with the Entra ID backup service failure.

---

## Board Summary
> Our data protection posture is rated F (45/100), indicating critical attention is required across our SaaS backup infrastructure. Keepit protects 3 cloud applications — Microsoft 365, Entra ID, and Salesforce — but all three are currently experiencing issues, with Entra ID backup unavailable for 4 days. 3 high-priority risk items have been identified; the IT team has been notified and remediation is in progress. Protection posture has declined by 33 points since the last reporting period; corrective actions are underway.

---

## Recommendations
1. **IMMEDIATE: Restore Entra ID backup service** — This is the highest priority. Entra ID impacts all cloud application access. The IT team should escalate to Keepit support if the issue cannot be resolved internally within 2 hours.
2. **IMMEDIATE: Investigate Salesforce backup degradation** — Restore normal backup operations and trigger a manual backup to close the 52-hour data gap.
3. **URGENT: Diagnose Microsoft 365 backup failures** — Review job logs for the past 7 days to identify the failure pattern. 40% failure rate indicates a systemic issue, not transient errors.
4. **Review recent configuration changes** — Correlate the 8 configuration changes from the past 30 days with the timeline of backup failures to determine if a change caused the issues.
5. **Schedule daily status check** — Until all connectors are restored to healthy status, conduct daily backup status reviews rather than waiting for the next scheduled report.
6. **Post-incident review** — Once all services are restored, conduct a root cause analysis and implement preventive measures to avoid recurrence.

---

## Operational Summary
- **Total backup jobs (past 7 days):** 42
- **Successful:** 25 (59.5%)
- **Failed:** 17 (40.5%)
- **Entra ID:** 0 successful / 7 attempted (0% success)
- **Salesforce:** 8 successful / 14 attempted (57.1% success)
- **Microsoft 365:** 17 successful / 21 attempted (81.0% success)
- **Configuration changes (past 30 days):** 8 (review required)
- **Active jobs at report time:** 0 (no backups currently running)

---

## Escalation Contacts
This report has been flagged for escalation due to Protection Score below 60. Recommended distribution:
- IT Director / CIO (immediate)
- Security team (Entra ID impact assessment)
- Sales operations (Salesforce data gap awareness)
- Keepit support (service restoration assistance)
```

---

## 4. Response Templates

### Board Snippet Template

Use this template when the user specifically asks for a board-ready snippet or a brief summary for executive presentation.

```markdown
> Our data protection posture is rated {grade} ({score}/100), indicating
> {posture} coverage across {qualifier} SaaS applications. Keepit is actively
> protecting {app_count} cloud application(s) including {app_names} with a
> {success_rate}% backup success rate. {risk_sentence} {recovery_sentence}
> {trend_sentence}
```

**Variable definitions:**

| Variable | Description | Example |
|---|---|---|
| `{grade}` | Letter grade A-F | A |
| `{score}` | Numeric score 0-100 | 96 |
| `{posture}` | Posture description | excellent |
| `{qualifier}` | "all critical" if score >= 80, "our" otherwise | all critical |
| `{app_count}` | Number of protected apps | 3 |
| `{app_names}` | Comma-separated app names | Microsoft 365, Entra ID, Salesforce |
| `{success_rate}` | Job success percentage | 99.2 |
| `{risk_sentence}` | Risk summary or confidence statement | No material risks identified. |
| `{recovery_sentence}` | RTO summary | Estimated recovery time is under 4 hours. |
| `{trend_sentence}` | Trend summary (optional) | Protection has improved by 3 points. |

---

### Executive Summary Header Template

```markdown
# Data Protection Executive Summary
**Account:** {account_name}
**Report Date:** {report_date}
**Reporting Period:** {period_description}
```

For risk escalation reports, add:
```markdown
**Escalation Level:** Critical
```

---

### Protection Score Section Template

```markdown
## Protection Score: {score}/100 ({grade})
{icon} Overall data protection posture is **{posture}**.

| Component | Score | Weight |
|---|---|---|
| Connector Health | {health_score}/100 | 30% |
| Backup Recency | {recency_score}/100 | 25% |
| RPO Compliance | {rpo_score}/100 | 25% |
| Job Success Rate | {job_score}/100 | 20% |
```

**Icon mapping:**
- Score 90-100: ✅
- Score 70-89: ⚠️
- Score below 70: ❌

---

### Application Coverage Table Template

```markdown
## Application Coverage
{app_count} SaaS application(s) are currently protected by Keepit:

| Application | Status | Last Backup |
|---|---|---|
| {app_name} | {status_icon} {status_text} | {last_backup_relative} |
```

**Status mapping:**
- Healthy: `✅ Healthy`
- Degraded: `⚠️ Degraded`
- Unhealthy: `❌ Unhealthy`
- Unknown: `⚠️ Unknown`

**Last Backup formatting:**
- Under 1 hour: "X minutes ago"
- 1-24 hours: "X hours ago"
- 24-48 hours: "X hours ago" (flag as concern)
- Over 48 hours: "X hours ago (X days)" (flag as critical)

---

### Risk Item Template

```markdown
### {priority_icon} {priority_level} Priority

- **{title}** — {description}
  - *Business Impact:* {business_impact}
  - *Recommended Action:* {recommended_action}
```

**Priority icons:**
- High: 🔴
- Medium: 🟡
- Low: 🟢

**Writing style guidelines for risk items:**
- Use plain English, no technical jargon
- Lead with the application name in the title
- Describe impact in terms of data loss, recovery delay, or business disruption
- Make recommendations actionable with clear ownership ("IT team should...")
- Include time expectations ("within 4 hours", "immediately")

---

### Recovery Readiness Template

```markdown
## Recovery Readiness
- **Recovery Point Objective (RPO):** Estimated {rpo_hours} hours of potential data loss in a recovery scenario
- **Recovery Time Objective (RTO):** {rto_estimate} for full restoration
- **Readiness Level:** {readiness_icon} {readiness_level}

{readiness_description}
```

**Readiness levels:**
- Excellent (✅): RPO <= 12h, RTO <= 4h
- Good (✅): RPO <= 24h, RTO <= 8h
- Fair (⚠️): RPO <= 48h, RTO <= 24h
- Poor (❌): RPO > 48h or RTO > 24h

---

### Trend Section Template

```markdown
## Trend
{trend_icon} Protection posture is **{direction}** compared to the previous period ({delta_description}).

{trend_explanation}
```

**Trend icons:**
- Improved (delta > +2): 📈
- Stable (delta -2 to +2): ➡️
- Degraded (delta < -2): 📉

---

### Recommendations Section Template

```markdown
## Recommendations
1. **{urgency}: {recommendation_title}** — {recommendation_detail}
2. **{recommendation_title}** — {recommendation_detail}
3. **{recommendation_title}** — {recommendation_detail}
```

**Urgency prefixes (use only when score < 70):**
- Score < 50: "IMMEDIATE"
- Score 50-60: "URGENT"
- Score 60-70: No prefix needed

**Recommendation writing guidelines:**
- Maximum 5 recommendations
- Order by priority and impact
- Each recommendation should be actionable with clear ownership
- Include time expectations where relevant
- For healthy environments, focus on maintenance and expansion
- For degraded environments, focus on remediation and prevention

---

### Operational Summary Template

```markdown
## Operational Summary
- **Total backup jobs ({period}):** {total_jobs}
- **Successful:** {success_count} ({success_pct}%)
- **Failed:** {failure_count} ({failure_pct}%)
- **Configuration changes ({period}):** {change_count}
- **Active jobs at report time:** {active_count}
```

For risk escalation reports, add per-connector breakdown:
```markdown
- **{app_name}:** {success} successful / {total} attempted ({pct}% success)
```

---

### Empty State Template

When no connectors are found:

```markdown
# Data Protection Executive Summary
**Account:** {account_name}
**Report Date:** {report_date}

## Protection Score: 0/100 (F)
❌ No SaaS applications are currently protected by Keepit.

## Application Coverage
No cloud connectors have been configured. Data protection is not active.

## Recommendations
1. **IMMEDIATE: Configure cloud application connectors** — No SaaS applications are currently being backed up. Contact your Keepit administrator or partner to begin onboarding Microsoft 365, Google Workspace, Salesforce, or other critical cloud applications.
2. **Identify critical data sources** — Inventory all SaaS applications in use across the organization and prioritize them for backup coverage based on business criticality.
3. **Establish backup policy** — Define target RPO and RTO for each application to guide connector configuration and backup scheduling.

## Board Summary
> No SaaS applications are currently protected by Keepit backup. Data created in cloud applications such as Microsoft 365, Google Workspace, and Salesforce is not being backed up and cannot be recovered in the event of data loss. Immediate action is recommended to configure data protection for critical business applications.
```
