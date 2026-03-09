# Restore Readiness Assessor — Example Outputs

This document provides example outputs for common restore readiness assessment
scenarios, demonstrating the expected formatting and content structure.

---

## Example 1: Fully Ready Account (Grade A)

All connectors healthy, backups fresh, restore history available with high
success rates. This is the ideal state.

### User Prompt

> "Are we ready to recover from a ransomware attack?"

### Response

## Restore Readiness Assessment

**Overall Readiness Grade: ✅ A (94.2/100)**

**Assessment Date:** 2025-01-15
**Connectors Evaluated:** 4
**Ready:** 4 | **At Risk:** 0 | **Not Ready:** 0

### Key Findings
- All 4 connectors are healthy and reachable
- All backups are within the 24-hour RPO target
- Restore testing completed for all connectors with 100% success rate
- Estimated RTO ranges from 2 minutes to 18 minutes across all connectors

---

### Microsoft 365 — Production
**Readiness Score:** ✅ 97.5/100 (A)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 100 | 25% | Connector is healthy and reachable |
| Freshness | 100 | 30% | Last backup 3.2h ago — within 24h target |
| Continuity | 100 | 20% | No significant gaps in 30 snapshots |
| Restore History | 90 | 25% | 100% success rate, 8 restores in 30 days |

### Entra ID
**Readiness Score:** ✅ 95.0/100 (A)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 100 | 25% | Connector is healthy and reachable |
| Freshness | 100 | 30% | Last backup 5.1h ago — within 24h target |
| Continuity | 100 | 20% | No significant gaps in 28 snapshots |
| Restore History | 80 | 25% | 100% success rate, 3 restores in 30 days |

### Google Workspace
**Readiness Score:** ✅ 92.5/100 (A)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 100 | 25% | Connector is healthy and reachable |
| Freshness | 100 | 30% | Last backup 8.7h ago — within 24h target |
| Continuity | 75 | 20% | Minor gaps detected (largest: 36.2h) |
| Restore History | 100 | 25% | 100% success rate, 12 restores in 30 days |

### Salesforce
**Readiness Score:** ✅ 92.0/100 (A)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 100 | 25% | Connector is healthy and reachable |
| Freshness | 100 | 30% | Last backup 2.0h ago — within 24h target |
| Continuity | 100 | 20% | No significant gaps in 30 snapshots |
| Restore History | 80 | 25% | 90% success rate (9/10 restores successful) |

---

### RPO Achievement

| Connector | Target RPO | Actual RPO | Status |
|-----------|-----------|------------|--------|
| Microsoft 365 | 24h | 3.2h | ✅ Achieved |
| Entra ID | 24h | 5.1h | ✅ Achieved |
| Google Workspace | 24h | 8.7h | ✅ Achieved |
| Salesforce | 24h | 2.0h | ✅ Achieved |

**RPO Summary:** 4/4 connectors meeting the 24-hour RPO target.

### RTO Estimation

| Connector | Median RTO | P95 RTO | Confidence | Based On |
|-----------|-----------|---------|------------|----------|
| Microsoft 365 | 2m 15s | 8m 30s | Medium | 8 restores |
| Entra ID | 1m 45s | 3m 10s | Medium | 3 restores |
| Google Workspace | 5m 20s | 18m 0s | High | 12 restores |
| Salesforce | 3m 30s | 12m 45s | High | 10 restores |

**RTO Summary:** All 4 connectors have measured RTO estimates. Median recovery
time across all connectors is under 6 minutes.

---

### Recommendations

| Priority | Category | Recommendation |
|----------|----------|----------------|
| 🟢 LOW | Maintenance | Schedule quarterly readiness reassessments to maintain grade |
| 🟢 LOW | Improvement | Investigate the minor backup gap on Google Workspace to prevent recurrence |

### Ransomware Recovery Assessment

Your organization is **well-prepared** for a ransomware recovery scenario:

- **Data Protection:** All 4 SaaS applications are backed up with fresh data
- **Recovery Capability:** Restore operations have been tested and verified for all connectors
- **Recovery Time:** Based on historical data, full recovery can be expected within 18 minutes (P95) for any single application
- **Recovery Point:** Maximum data loss would be approximately 8.7 hours (Google Workspace) — well within the 24-hour target

---

## Example 2: Partially Ready (Grade C)

Mixed state: some connectors healthy but one stale, one has no restore history.
Common in organizations that have set up backups but have not validated recovery.

### User Prompt

> "Give me a restore readiness report for our upcoming audit."

### Response

## Restore Readiness Assessment

**Overall Readiness Grade: ⚠️ C (73.1/100)**

**Assessment Date:** 2025-01-15
**Connectors Evaluated:** 3
**Ready:** 1 | **At Risk:** 2 | **Not Ready:** 0

### Key Findings
- 1 of 3 connectors is fully ready for recovery
- Dynamics 365 has not been backed up in over 3 days — RPO breached
- Google Workspace has never had a restore test — recovery capability unverified
- Compliance evidence is incomplete for NIS2 and DORA requirements

---

### Microsoft 365 — Production
**Readiness Score:** ✅ 92.5/100 (A)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 100 | 25% | Connector is healthy and reachable |
| Freshness | 100 | 30% | Last backup 6.3h ago — within 24h target |
| Continuity | 100 | 20% | No significant gaps in 30 snapshots |
| Restore History | 80 | 25% | 100% success rate, 5 restores in 30 days |

### Google Workspace
**Readiness Score:** ⚠️ 70.0/100 (C)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 100 | 25% | Connector is healthy and reachable |
| Freshness | 100 | 30% | Last backup 11.5h ago — within 24h target |
| Continuity | 75 | 20% | Minor gaps detected (largest: 38.0h) |
| Restore History | 40 | 25% | No restore history — recovery capability unverified |

### Dynamics 365
**Readiness Score:** ❌ 56.8/100 (F)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 60 | 25% | Connector has warnings — may affect restores |
| Freshness | 25 | 30% | Last backup 78.0h ago — significantly stale |
| Continuity | 50 | 20% | Moderate gaps detected (largest: 78.0h, 2 gaps) |
| Restore History | 80 | 25% | 100% success rate, 4 restores in 30 days |

---

### RPO Achievement

| Connector | Target RPO | Actual RPO | Status |
|-----------|-----------|------------|--------|
| Microsoft 365 | 24h | 6.3h | ✅ Achieved |
| Google Workspace | 24h | 11.5h | ✅ Achieved |
| Dynamics 365 | 24h | 78.0h | ❌ Breached (gap: 54.0h) |

**RPO Summary:** 2/3 connectors meeting the 24-hour RPO target. Dynamics 365
has a 54-hour RPO gap requiring immediate attention.

### RTO Estimation

| Connector | Median RTO | P95 RTO | Confidence | Based On |
|-----------|-----------|---------|------------|----------|
| Microsoft 365 | 3m 10s | 9m 45s | Medium | 5 restores |
| Google Workspace | N/A | N/A | None | 0 restores |
| Dynamics 365 | 4m 50s | 11m 20s | Medium | 4 restores |

**RTO Summary:** 2 of 3 connectors have measured RTO estimates. Google Workspace
RTO is unknown — no restore tests have been performed.

---

### Coverage Gaps

| Connector | Type | Issue | Severity |
|-----------|------|-------|----------|
| Dynamics 365 | Dynamics 365 | Last backup is 78h (3 days) old — stale | 🔴 HIGH |

### Recommendations

| Priority | Category | Recommendation |
|----------|----------|----------------|
| 🔴 HIGH | RPO | RPO breached for Dynamics 365 — trigger immediate backup and investigate schedule |
| 🔴 HIGH | Health | Investigate health warnings for Dynamics 365 |
| 🟡 MEDIUM | Restore Testing | Perform a test restore for Google Workspace to validate recovery capability |
| 🟡 MEDIUM | Improvement | Address identified gaps within 30 days to improve readiness grade |

### Compliance Evidence

#### NIS2 Article 21 — Business continuity and disaster recovery

**Status:** ⚠️ Partial Compliance

**Evidence:**
- Backup coverage: 3 connector(s) configured and monitored
- Overall readiness grade: C (73.1/100)
- Restore testing: 5 restores recorded for Microsoft 365 (100% success)
- Restore testing: 4 restores recorded for Dynamics 365 (100% success)

**Gaps:**
- Readiness grade below B — improvements needed for full compliance
- No restore tests recorded for Google Workspace — Article 21 requires regular
  testing of business continuity and disaster recovery measures

#### DORA Article 12 — Backup policies and procedures

**Status:** ⚠️ Partial Compliance

**Evidence:**
- RPO documented and measured: 2/3 targets met
- RTO estimated from historical data for 2 connector(s)

**Gaps:**
- Restore success rate measurement incomplete (Google Workspace has no data)
- No documented RTO for Google Workspace

---

## Example 3: Not Ready (Grade F)

Critical state: unhealthy connectors, missing backups, no restore history.
Requires immediate remediation.

### User Prompt

> "How confident are we in our backups?"

### Response

## Restore Readiness Assessment

**Overall Readiness Grade: ❌ F (38.5/100)**

**Assessment Date:** 2025-01-15
**Connectors Evaluated:** 3
**Ready:** 0 | **At Risk:** 1 | **Not Ready:** 2

### Key Findings
- **No connectors are fully ready** for recovery operations
- Salesforce connector is in error state — restores may fail
- Zendesk has no backups at all — data is completely unprotected
- No restore tests have been performed on any connector in the past 30 days
- Estimated data at risk: all Zendesk data, plus Salesforce data older than 12 days

---

### Microsoft 365 — Production
**Readiness Score:** ❌ 53.8/100 (F)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 100 | 25% | Connector is healthy and reachable |
| Freshness | 25 | 30% | Last backup 96.0h ago — significantly stale |
| Continuity | 25 | 20% | Severe gaps detected (largest: 96.0h, 3 gaps) |
| Restore History | 40 | 25% | No restore history — recovery capability unverified |

### Salesforce
**Readiness Score:** ❌ 37.0/100 (F)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 20 | 25% | Connector in error state — restores likely impacted |
| Freshness | 0 | 30% | Last backup 288.0h ago — critically stale |
| Continuity | 25 | 20% | Severe gaps detected (largest: 288.0h, 5 gaps) |
| Restore History | 40 | 25% | No restore history — recovery capability unverified |

### Zendesk
**Readiness Score:** ❌ 24.8/100 (F)

| Factor | Score | Weight | Details |
|--------|-------|--------|---------|
| Health | 60 | 25% | Connector has warnings — may affect restores |
| Freshness | 0 | 30% | No backups found — data is unprotected |
| Continuity | 0 | 20% | No snapshots — continuity cannot be assessed |
| Restore History | 40 | 25% | No restore history — recovery capability unverified |

---

### RPO Achievement

| Connector | Target RPO | Actual RPO | Status |
|-----------|-----------|------------|--------|
| Microsoft 365 | 24h | 96.0h | ❌ Breached (gap: 72.0h) |
| Salesforce | 24h | 288.0h | ❌ Breached (gap: 264.0h) |
| Zendesk | 24h | N/A | ❌ No data — cannot calculate |

**RPO Summary:** 0/3 connectors meeting the 24-hour RPO target. All connectors
have breached or cannot be measured.

### RTO Estimation

| Connector | Median RTO | P95 RTO | Confidence | Based On |
|-----------|-----------|---------|------------|----------|
| Microsoft 365 | N/A | N/A | None | 0 restores |
| Salesforce | N/A | N/A | None | 0 restores |
| Zendesk | N/A | N/A | None | 0 restores |

**RTO Summary:** RTO is completely unknown for all connectors. No restore
operations have been performed. Recovery time cannot be estimated.

---

### Coverage Gaps

| Connector | Type | Issue | Severity |
|-----------|------|-------|----------|
| Zendesk | Zendesk | No backups exist — data is completely unprotected | 🔴 CRITICAL |
| Salesforce | Salesforce | Last backup is 288h (12 days) old — critically stale | 🔴 CRITICAL |
| Microsoft 365 | Microsoft 365 | Last backup is 96h (4 days) old — stale | 🔴 HIGH |

### Recommendations

| Priority | Category | Recommendation |
|----------|----------|----------------|
| 🔴 HIGH | Critical | Immediate action required — readiness grade is below acceptable threshold |
| 🔴 HIGH | Coverage Gap | Initiate an immediate backup for Zendesk |
| 🔴 HIGH | Coverage Gap | Investigate why backups have stopped and trigger an immediate backup for Salesforce |
| 🔴 HIGH | Health | Resolve connector health errors for Salesforce |
| 🔴 HIGH | RPO | RPO breached for Microsoft 365 — trigger immediate backup and investigate schedule |
| 🔴 HIGH | RPO | RPO breached for Salesforce — trigger immediate backup and investigate schedule |
| 🟡 MEDIUM | Restore Testing | Perform a test restore for Microsoft 365 to validate recovery capability |
| 🟡 MEDIUM | Restore Testing | Perform a test restore for Salesforce to validate recovery capability |
| 🟡 MEDIUM | Restore Testing | Perform a test restore for Zendesk to validate recovery capability |

### Confidence Assessment

Your organization's backup confidence level is **critically low**:

- **Data Protection:** 1 of 3 applications has no backups at all; the other 2
  have severely stale backups
- **Recovery Capability:** Completely untested — no restore operations have ever
  been performed
- **Recovery Time:** Unknown — without restore history, RTO cannot be estimated
- **Recovery Point:** At best, you could recover Microsoft 365 data from 4 days
  ago; Salesforce from 12 days ago; Zendesk data cannot be recovered at all

**Immediate actions required:**
1. Resolve the Salesforce connector error state
2. Initiate backups for Zendesk and Salesforce immediately
3. Trigger a fresh backup for Microsoft 365
4. Perform test restores for all connectors once backups complete

---

## Response Templates

### Template 1: Quick Readiness Check

For users who ask "quick check" or "how are we doing" — abbreviated format.

```
## Quick Readiness Check

**Overall Grade: [icon] [grade] ([score]/100)**
**Date:** [date] | **Connectors:** [count]

### Status Summary
| Connector | Type | Score | RPO | Last Restore |
|-----------|------|-------|-----|-------------|
| [name] | [type] | [icon] [score] | [actual]h / [target]h | [date or Never] |

### Top Issues
1. [icon] [Most critical issue]
2. [icon] [Second issue]
3. [icon] [Third issue]

### Next Steps
- [Most important action]
- [Second action]
```

### Template 2: Full Assessment Report

For users who ask for a "full report" or "detailed assessment" — comprehensive
format as shown in Examples 1-3 above.

Structure:
1. Executive Summary (grade, date, key findings)
2. Per-Connector Detail (readiness score table per connector)
3. RPO Achievement (table of actual vs target)
4. RTO Estimation (table of median/P95/confidence)
5. Coverage Gaps (if any)
6. Recommendations (prioritized table)
7. Compliance Evidence (if requested or relevant)

### Template 3: Compliance Evidence Summary

For audit-focused users — compliance-first format.

```
## Backup & Recovery Compliance Evidence

**Assessment Date:** [date]
**Overall Readiness:** [icon] Grade [grade] ([score]/100)

---

### NIS2 Article 21 — Business Continuity & Disaster Recovery

**Compliance Status:** [status]

**Evidence Provided:**
- [bullet list of evidence items]

**Gaps Identified:**
- [bullet list of gaps, or "None" if compliant]

---

### DORA Article 12 — Backup Policies & Restoration

**Compliance Status:** [status]

**Evidence Provided:**
- [bullet list of evidence items]

**Gaps Identified:**
- [bullet list of gaps, or "None" if compliant]

---

### Supporting Data

#### Backup Coverage
| Connector | Type | Last Backup | RPO Status |
|-----------|------|-------------|------------|
| [name] | [type] | [timestamp] | [icon] [status] |

#### Restore Testing Evidence
| Connector | Restores (30d) | Success Rate | Last Test |
|-----------|---------------|-------------|-----------|
| [name] | [count] | [rate]% | [date] |

#### Recovery Time Evidence
| Connector | Median RTO | P95 RTO | Confidence |
|-----------|-----------|---------|------------|
| [name] | [median] | [p95] | [level] |

---

### Recommendations for Compliance Remediation
| Priority | Requirement | Gap | Remediation |
|----------|-----------|-----|-------------|
| [icon] | [NIS2/DORA ref] | [gap description] | [action] |
```

### Template 4: Ransomware Recovery Readiness

For users specifically asking about ransomware scenarios.

```
## Ransomware Recovery Readiness

**Overall Preparedness: [icon] [grade]**

### Can We Recover?
[Yes/Partially/No] — [brief explanation based on data]

### Recovery Coverage
| Application | Protected | Freshness | Tested | Ready |
|------------|-----------|-----------|--------|-------|
| [name] | [Yes/No] | [hours]h ago | [Yes/No] | [icon] |

### Estimated Recovery Timeline
| Application | Expected RTO | Confidence |
|------------|-------------|------------|
| [name] | [duration] | [level] |

### Maximum Data Loss (RPO)
| Application | Data at Risk | RPO Status |
|------------|-------------|------------|
| [name] | Up to [hours]h | [icon] [status] |

### Gaps in Ransomware Preparedness
1. [icon] [gap description]
2. [icon] [gap description]

### Recommended Actions
1. [icon] [action with priority]
2. [icon] [action with priority]
```

---

## Formatting Notes

### Grade Display

Always display the grade with its icon, letter, and numeric score:
- ✅ A (94.2/100) — Fully ready
- ✅ B (83.5/100) — Ready
- ⚠️ C (73.1/100) — Partially ready
- ❌ D (62.0/100) — At risk
- ❌ F (38.5/100) — Not ready

### RPO Status Display

- ✅ Achieved — actual RPO is within target
- ⚠️ At Risk — actual RPO is between 1x and 1.5x target
- ❌ Breached — actual RPO exceeds 1.5x target

### RTO Confidence Display

- **High** — based on 10+ restore operations
- **Medium** — based on 3-9 restore operations
- **Low** — based on 1-2 restore operations
- **None** — no restore history available

### Recommendation Priority Display

- 🔴 **HIGH** — Must address before next audit or recovery event
- 🟡 **MEDIUM** — Address within 30 days
- 🟢 **LOW** — Best practice improvement

### Compliance Status Display

- ✅ **Compliant** — all requirements met with evidence
- ⚠️ **Partial** — some requirements met, gaps identified
- ❌ **Non-Compliant** — critical requirements not met

---

## Edge Cases

### No Connectors Configured

```
## Restore Readiness Assessment

**Overall Readiness Grade: ❌ F (0/100)**

No connectors are configured in this Keepit account. There is no backup
coverage and no data can be recovered.

**Immediate Action Required:**
- Configure backup connectors for all critical SaaS applications
- Start with Microsoft 365 and Google Workspace if applicable
- Schedule restore tests after initial backups complete
```

### Single Connector Account

Format as a focused assessment for that one connector rather than a
multi-connector comparison. Omit the summary table and go directly to the
detailed breakdown.

### All Data Unavailable

If MCP calls fail for all connectors:

```
## Restore Readiness Assessment

**Overall Readiness Grade: ❌ Unable to Assess**

The assessment could not be completed due to data retrieval errors for all
connectors. This may indicate:
- API connectivity issues
- Permission problems
- Service outage

**Recommendation:** Retry the assessment. If the problem persists, check
Keepit service status and API permissions.
```

### Mixed Connector Types

When an account has many different SaaS types, group the per-connector detail
by type category (Productivity, CRM, Identity, etc.) for easier reading.
The summary tables should still include all connectors.
