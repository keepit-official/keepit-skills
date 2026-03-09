# Example Outputs and Response Patterns

This reference provides concrete examples of health check outputs for various scenarios.

## Table of Contents

1. [Healthy Account Example](#healthy-account-example)
2. [Account with Warnings Example](#account-with-warnings-example)
3. [Critical Issues Example](#critical-issues-example)
4. [New Account Validation Example](#new-account-validation-example)
5. [Response Templates](#response-templates)

---

## Healthy Account Example

**Scenario:** Mature account, all systems operational

### Report Output

```markdown
# Keepit Account Health Report
Generated: October 22, 2025 at 14:35 UTC

## ✅ Executive Summary
- **Account Status:** Active & Subscribed
- **Total Connectors:** 3 cloud connectors
- **Overall Health:** Healthy
- **Critical Issues:** 0
- **Warnings:** 0

## Account Details
- **Account ID:** z7ge93-18gjkb-3qsl9m
- **Created:** August 4, 2023 (2 years ago)
- **Product:** xnols1-3rcnim-53zoep
- **Subscription:** Active

## Connector Status

| Connector Name | Type | Health | Last Backup | Retention | Age |
|---------------|------|--------|-------------|-----------|-----|
| Microsoft 365 Backup | o365-admin | ✅ Healthy | 2 hours ago | ✅ 1 year | 3 months |
| Entra ID Backup(1) | azure-ad | ✅ Healthy | 3 hours ago | ✅ 1 year | 3 months |
| Entra ID Backup(2) | azure-ad | ✅ Healthy | 1 hour ago | ✅ 90 days | 1 month |

## Analysis

### 🟢 All Systems Operational
- All connectors report healthy status
- All backups completed within the last 4 hours
- All retention policies configured
- No configuration issues identified

### Backup Coverage
- **Microsoft 365:** Full tenant backup active
- **Entra ID:** Dual backup configuration (redundancy in place)

## Recommendations

✅ **No immediate actions required**

**Maintenance suggestions:**
- Continue monitoring daily backup completion
- Review backup retention policies quarterly
- Consider scheduling monthly compliance reports

---

**Next Steps:**
- Schedule next health check for next week
- Set up automated weekly summary reports
```

---

## Account with Warnings Example

**Scenario:** Account operational but with minor issues needing attention

### Report Output

```markdown
# Keepit Account Health Report
Generated: October 22, 2025 at 14:35 UTC

## ⚠️ Executive Summary
- **Account Status:** Active & Subscribed
- **Total Connectors:** 3 cloud connectors
- **Overall Health:** Operational with Warnings
- **Critical Issues:** 0
- **Warnings:** 2

## Account Details
- **Account ID:** z7ge93-18gjkb-3qsl9m
- **Created:** August 4, 2023
- **Subscription:** Active

## Connector Status

| Connector Name | Type | Health | Last Backup | Retention | Age |
|---------------|------|--------|-------------|-----------|-----|
| Microsoft 365 Backup | o365-admin | ✅ Healthy | 4 hours ago | ✅ 1 year | 3 months |
| Entra ID Backup(1) | azure-ad | ⚠️ Unhealthy | 2 days ago | ✅ 1 year | 3 months |
| Entra ID Backup(2) | azure-ad | ✅ Healthy | 1 hour ago | ❌ Not set | 1 month |

## Issues Requiring Attention

### 🟡 Warning: Stale Backup Detected
**Connector:** Entra ID Backup(1)
- **Last backup:** 2 days ago (48+ hours)
- **Expected:** Daily backups
- **Impact:** Recovery point gap of 2 days

**Recommended actions:**
1. Check connector configuration in Keepit UI
2. Review recent job history for failures
3. Verify Azure AD permissions are still valid
4. Consider manual backup trigger to close gap

### 🟡 Warning: Health Status Reported as Unhealthy
**Connector:** Entra ID Backup(1)
- **Health status:** Unhealthy
- **Potential causes:** Permission changes, API throttling, temporary connectivity issues

**Recommended actions:**
1. Review connector health details in Keepit dashboard
2. Check for recent Azure AD configuration changes
3. Verify service account permissions
4. Monitor next scheduled backup

## Health Summary

### ✅ Healthy Systems (2/3)
- Microsoft 365 Backup: Operating normally
- Entra ID Backup(2): Operating normally

### ⚠️ Systems Needing Attention (1/3)
- Entra ID Backup(1): Stale backup + unhealthy health status

## Recommendations

**Immediate actions (within 24 hours):**
1. Investigate Entra ID Backup(1) connector status
2. Review and resolve health warnings
3. Trigger manual backup if needed
4. Verify Azure AD permissions

**Follow-up actions:**
- Monitor Entra ID Backup(1) for next 3 days
- Schedule detailed job history analysis if issues persist
- Consider audit log review for this connector

---

**Next Steps:**
- Address warnings within 24 hours
- Run health check again after remediation
- Set up alerting for backup delays
```

---

## Critical Issues Example

**Scenario:** Account with critical problems requiring immediate attention

### Report Output

```markdown
# Keepit Account Health Report
Generated: October 22, 2025 at 14:35 UTC

## 🔴 Executive Summary - CRITICAL ISSUES DETECTED
- **Account Status:** Active & Subscribed
- **Total Connectors:** 3 cloud connectors
- **Overall Health:** DEGRADED - Immediate attention required
- **Critical Issues:** 2
- **Warnings:** 1

## 🚨 Critical Issues

### 🔴 CRITICAL: No Backup Data Available
**Connector:** Entra ID Backup(2)
- **Status:** Connector created but never backed up
- **Created:** 1 month ago (September 30, 2025)
- **Last backup:** NEVER
- **Impact:** NO data protection for this connector

**IMMEDIATE ACTIONS REQUIRED:**
1. ⚠️ Verify connector configuration in Keepit UI
2. ⚠️ Check Azure AD connection permissions
3. ⚠️ Trigger manual backup immediately
4. ⚠️ Contact Keepit support if issue persists

### 🔴 CRITICAL: Backup Severely Stale
**Connector:** Microsoft 365 Backup
- **Last backup:** 8 days ago
- **Expected:** Daily backups
- **Impact:** 8-day recovery point gap

**IMMEDIATE ACTIONS REQUIRED:**
1. ⚠️ Check connector health in Keepit UI
2. ⚠️ Review job history for pattern of failures
3. ⚠️ Verify Microsoft 365 permissions
4. ⚠️ Escalate to Keepit support immediately

## Connector Status

| Connector Name | Type | Health | Last Backup | Retention | Age | Priority |
|---------------|------|--------|-------------|-----------|-----|----------|
| Microsoft 365 Backup | o365-admin | ❌ Critical | 8 days ago | ✅ 1 year | 3 months | 🔴 HIGH |
| Entra ID Backup(1) | azure-ad | ⚠️ Unhealthy | 2 days ago | ✅ 1 year | 3 months | 🟡 MEDIUM |
| Entra ID Backup(2) | azure-ad | ❌ Critical | NEVER | ❌ Not set | 1 month | 🔴 HIGH |

## Impact Assessment

### Data Protection Status
- **Protected:** 1 of 3 connectors (33%)
- **At Risk:** 2 of 3 connectors (67%)
- **Total exposure:** 10 days of potential data loss

### Business Risk
- Microsoft 365 backup failure exposes email, documents, SharePoint
- Entra ID Backup(2) has ZERO protection since creation
- Current state violates backup best practices and likely SLAs

## Immediate Action Plan

**Within 1 hour:**
1. Log into Keepit dashboard immediately
2. Check active jobs and error messages
3. Verify all connector permissions
4. Trigger manual backups for all connectors
5. Open support ticket with Keepit

**Within 4 hours:**
1. Review detailed job history for all failed connectors
2. Check audit logs for permission or configuration changes
3. Implement temporary monitoring
4. Escalate to management if issues persist

**Within 24 hours:**
1. Root cause analysis for all failures
2. Implement corrective measures
3. Verify all backups resume successfully
4. Document incident for compliance records

## Recommendations

⚠️ **URGENT:** This backup configuration is NOT providing adequate data protection. Immediate remediation is critical.

**Support contacts:**
- Keepit Support: [Include support contact info]
- Internal IT escalation: [Include internal contacts]

---

**Status:** CRITICAL - Immediate intervention required
**Follow-up:** Recheck status in 4 hours after remediation attempts
```

---

## New Account Validation Example

**Scenario:** Recently created account, validating initial setup

### Report Output

```markdown
# Keepit Account Setup Validation
Generated: October 22, 2025 at 14:35 UTC

## ✅ Account Activation Confirmed

**Welcome to Keepit!** Your account is properly configured and operational.

## Account Details
- **Account ID:** z7ge93-18gjkb-3qsl9m
- **Created:** October 20, 2025 (2 days ago)
- **Status:** ✅ Enabled & Subscribed
- **Product:** xnols1-3rcnim-53zoep

## Initial Configuration Status

### Connectors Configured: 3

| Connector Name | Type | Status | First Backup | Setup Status |
|---------------|------|--------|--------------|--------------|
| Microsoft 365 Backup | o365-admin | ✅ Active | 1 day ago | Complete |
| Entra ID Backup(1) | azure-ad | ✅ Active | 1 day ago | Complete |
| Entra ID Backup(2) | azure-ad | ⏳ Pending | Not yet run | In Progress |

## Setup Progress

### ✅ Completed Steps
- [x] Account created and activated
- [x] Subscription confirmed
- [x] Microsoft 365 connector configured
- [x] First Entra ID connector configured
- [x] Initial backups running
- [x] Backup data being captured

### ⏳ In Progress
- [ ] Entra ID Backup(2) - Awaiting first backup
  - **Status:** Connector created, initial backup scheduled
  - **Expected:** First backup within 24 hours
  - **Action:** No action needed, monitor progress

### 📋 Recommended Next Steps

**Within 24 hours:**
1. ✅ Verify Entra ID Backup(2) completes first backup
2. ✅ Review backup coverage meets requirements
3. ✅ Configure backup retention policies (if not done)
4. ✅ Set up administrative notifications

**Within 1 week:**
1. Configure additional connectors if needed (Salesforce, Google Workspace, etc.)
2. Review and document backup policies
3. Set up compliance reporting schedules
4. Train additional administrators

**Within 1 month:**
1. Perform first restore test
2. Generate compliance documentation
3. Review backup storage consumption
4. Schedule regular health checks

## Validation Checklist

- ✅ Account properly enabled
- ✅ Subscription active
- ✅ At least one connector operational
- ✅ Initial backups successful
- ⏳ All connectors completing first backup cycle
- 📋 Retention policies (configure if needed)
- 📋 Alerting (configure if needed)

## Everything Looks Good!

Your Keepit backup environment is set up correctly. The initial connectors are running, and your data protection is active.

**Recommended frequency for health checks:**
- Daily: First week (monitor initial backups)
- Weekly: First month (ensure stability)
- Monthly: Ongoing operations

---

**Next Health Check:** October 29, 2025 (1 week from now)
```

---

## Response Templates

### Quick Status Template

```markdown
## Keepit Quick Status

**Account:** ✅ Active | **Connectors:** {count} | **Health:** {status}

{brief_table}

{issue_summary_if_any}
```

### Executive Summary Template

```markdown
## Executive Summary

Your Keepit backup environment has:
- {total_connectors} configured connectors
- {healthy_count} healthy connectors ({percentage}%)
- {warning_count} warnings requiring attention
- {critical_count} critical issues needing immediate action

{one_sentence_recommendation}
```

### Connector Detail Template

```markdown
### {Connector Name}

- **Type:** {connector_type}
- **Health:** {status_icon} {status_text}
- **Last Backup:** {relative_time} ({iso_timestamp})
- **Age:** {time_since_creation}

{analysis_if_issues}
```

### Issue Action Template

```markdown
### {Issue Level}: {Issue Title}

**Affected:** {connector_name}
**Impact:** {brief_impact_description}
**Detected:** {when_detected}

**Recommended actions:**
1. {action_step_1}
2. {action_step_2}
3. {action_step_3}

**Priority:** {High/Medium/Low}
**Timeline:** {immediate/24hrs/this_week}
```

---

## Tone and Language Guidelines

### For Healthy Accounts
- Positive and encouraging
- Brief and efficient
- Include proactive suggestions
- "Everything looks good!" tone

### For Accounts with Warnings
- Calm but clear about issues
- Actionable and specific
- Prioritize recommendations
- "Let's address these items" tone

### For Critical Issues
- Urgent but not panicked
- Very specific about actions needed
- Clear timelines
- Include escalation paths
- "Immediate attention required" tone

### For New Accounts
- Welcoming and supportive
- Educational about next steps
- Validating and encouraging
- "Great start, here's what's next" tone

---

## Integration with Other Skills

When issues are detected, suggest relevant follow-up skills:

**For backup failures:**
→ "Would you like me to analyze the job history for this connector in detail?"
→ Triggers: Backup Job History Analyzer skill

**For gaps in snapshots:**
→ "I can check for gaps in your backup continuity if you'd like."
→ Triggers: Snapshot Gap & Continuity Analyzer skill

**For compliance needs:**
→ "Would you like me to generate a compliance audit report?"
→ Triggers: Compliance Audit Log Extractor skill

**For weekly reporting:**
→ "I can create a weekly summary report if you'd like regular updates."
→ Triggers: Weekly Backup Operations Summary skill
