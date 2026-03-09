# Retention Policy Auditor — Example Outputs

This document provides example outputs for common retention policy auditing scenarios. These templates demonstrate the expected formatting, structure, and level of detail for each type of analysis.

---

## Scenario 1: Compliant Setup

**Context:** An organization with 4 connectors, all with retention policies set, meeting GDPR and NIS2 requirements. The environment is well-configured and recently audited.

### User Request

> "Run a retention policy audit against GDPR and NIS2 for our environment."

### Example Response

---

## Retention Policy Audit Report

**Audit Date:** 2026-02-17
**Frameworks Assessed:** GDPR, NIS2
**Connectors Evaluated:** 4

---

### Policy Inventory

All 4 connectors have retention policies configured.

| Connector | Type | Retention | Days | Last Updated | Status |
|-----------|------|-----------|------|--------------|--------|
| Exchange Online | Microsoft 365 | P1Y | 365 | 2025-11-15 | ✅ Set |
| SharePoint Online | Microsoft 365 | P1Y | 365 | 2025-11-15 | ✅ Set |
| Teams | Microsoft 365 | P365D | 365 | 2025-11-15 | ✅ Set |
| Entra ID | Entra ID | P1Y | 365 | 2025-10-20 | ✅ Set |

**Summary:**
- Policies set: 4 of 4 (100%)
- Shortest retention: 365 days (1 year)
- Longest retention: 365 days (1 year)
- Retention is standardized across all connectors.

---

### Framework Compliance Matrix

| Connector | GDPR | NIS2 |
|-----------|------|------|
| Exchange Online | ✅ Documented (365 days) | ✅ Documented (365 days) |
| SharePoint Online | ✅ Documented (365 days) | ✅ Documented (365 days) |
| Teams | ✅ Documented (365 days) | ✅ Documented (365 days) |
| Entra ID | ✅ Documented (365 days) | ✅ Documented (365 days) |

**GDPR Assessment:**
- ✅ All connectors have documented retention policies as required by Art. 5(1)(e) and Art. 30.
- Retention periods are defined and consistent across the environment.

**NIS2 Assessment:**
- ✅ All connectors have documented backup policies as required by Article 21.
- Backup and recovery retention is explicitly configured.

---

### Recent Retention Changes (Last 90 Days)

| Date | User | Connector | Action | Old Value | New Value |
|------|------|-----------|--------|-----------|-----------|
| 2025-11-15 | admin@contoso.com | Exchange Online | Policy Updated | P180D (180d) | P1Y (365d) |
| 2025-11-15 | admin@contoso.com | SharePoint Online | Policy Updated | P180D (180d) | P1Y (365d) |
| 2025-11-15 | admin@contoso.com | Teams | Policy Set | Not set | P365D (365d) |
| 2025-10-20 | admin@contoso.com | Entra ID | Policy Updated | P90D (90d) | P1Y (365d) |

All changes were made by the same administrator during two sessions (Oct 20 and Nov 15), indicating a coordinated retention policy standardization effort.

---

### Enforcement Verification

| Connector | Policy | Oldest Snapshot | Expected Max | Status |
|-----------|--------|-----------------|--------------|--------|
| Exchange Online | 365 days | 362 days | 365 days | ✅ Properly enforced |
| SharePoint Online | 365 days | 358 days | 365 days | ✅ Properly enforced |
| Teams | 365 days | 93 days | 365 days | ✅ Within policy (newer connector) |
| Entra ID | 365 days | 361 days | 365 days | ✅ Properly enforced |

---

### Findings

No critical or high-priority findings.

### Recommendations

1. Continue quarterly retention audits to maintain compliance posture.
2. Document the retention policy rationale in your Records of Processing Activities (ROPA) for GDPR Art. 30 compliance.
3. Consider whether 365 days meets your organization's specific data recovery needs beyond regulatory minimums.

---

## Scenario 2: Non-Compliant Setup

**Context:** An organization with 5 connectors. Two connectors have no retention policy configured, and one connector's retention is below the HIPAA 6-year minimum. The organization is subject to GDPR, NIS2, and HIPAA.

### User Request

> "Check our retention compliance against GDPR, NIS2, and HIPAA."

### Example Response

---

## Retention Policy Audit Report

**Audit Date:** 2026-02-17
**Frameworks Assessed:** GDPR, NIS2, HIPAA
**Connectors Evaluated:** 5

---

### Policy Inventory

:red_circle: **2 of 5 connectors are missing retention policies — this is a critical compliance finding.**

| Connector | Type | Retention | Days | Last Updated | Status |
|-----------|------|-----------|------|--------------|--------|
| Exchange Online | Microsoft 365 | P1Y | 365 | 2025-09-10 | ✅ Set |
| SharePoint Online | Microsoft 365 | P1Y | 365 | 2025-09-10 | ✅ Set |
| Google Drive | Google Workspace | — | 0 | — | ❌ Not Set |
| Salesforce | Salesforce | P90D | 90 | 2025-08-01 | ⚠️ Set (short) |
| Dynamics 365 | Dynamics 365 | — | 0 | — | ❌ Not Set |

**Summary:**
- Policies set: 3 of 5 (60%)
- Policies missing: 2 of 5 (40%)
- Shortest retention (among set): 90 days
- Longest retention: 365 days
- :red_circle: Google Drive and Dynamics 365 have no retention policies.
- ⚠️ Salesforce has only 90-day retention.

---

### Framework Compliance Matrix

| Connector | GDPR | NIS2 | HIPAA |
|-----------|------|------|-------|
| Exchange Online | ✅ Documented (365d) | ✅ Documented (365d) | ❌ 365d < 2190d |
| SharePoint Online | ✅ Documented (365d) | ✅ Documented (365d) | ❌ 365d < 2190d |
| Google Drive | ❌ No policy | ❌ No policy | ❌ No policy |
| Salesforce | ✅ Documented (90d) | ✅ Documented (90d) | ❌ 90d < 2190d |
| Dynamics 365 | ❌ No policy | ❌ No policy | ❌ No policy |

**GDPR Assessment:**
- ❌ 2 connectors (Google Drive, Dynamics 365) have no documented retention policy.
- Non-compliance with Art. 5(1)(e) storage limitation and Art. 30 records requirement.

**NIS2 Assessment:**
- ❌ 2 connectors lack documented backup policies as required by Article 21.

**HIPAA Assessment:**
- ❌ No connectors meet the 6-year (2190-day) minimum retention requirement.
- Exchange and SharePoint are 1825 days short (365d vs. 2190d required).
- Salesforce is 2100 days short (90d vs. 2190d required).
- Google Drive and Dynamics 365 have no policy at all.

---

### Findings

| Priority | Icon | Category | Connector | Description |
|----------|------|----------|-----------|-------------|
| High | :red_circle: | Missing Policy | Google Drive | Google Workspace connector has no retention policy configured |
| High | :red_circle: | Missing Policy | Dynamics 365 | Dynamics 365 connector has no retention policy configured |
| High | ❌ | HIPAA Non-Compliance | Exchange Online | 365 days is 1825 days below HIPAA minimum of 2190 days |
| High | ❌ | HIPAA Non-Compliance | SharePoint Online | 365 days is 1825 days below HIPAA minimum of 2190 days |
| High | ❌ | HIPAA Non-Compliance | Salesforce | 90 days is 2100 days below HIPAA minimum of 2190 days |
| Medium | ⚠️ | Configuration Warning | Salesforce | Unusually short retention (90 days) |

---

### Recommendations

1. **CRITICAL:** Configure retention policies on Google Drive and Dynamics 365 connectors immediately to achieve baseline GDPR and NIS2 compliance.
2. **CRITICAL:** Increase retention to a minimum of P6Y (2190 days / 6 years) on all connectors storing HIPAA-covered data to meet 45 CFR 164.530(j) requirements.
3. Review whether Salesforce's 90-day retention meets business continuity needs — this is unusually short for a CRM system.
4. Standardize retention periods across similar connector types to simplify compliance management.
5. Schedule a follow-up audit within 30 days to verify remediation.

---

## Scenario 3: Policy Change Investigation

**Context:** A compliance officer noticed that retention settings were recently changed and wants to understand who changed them, when, and what the before/after values were.

### User Request

> "Who changed our retention policies recently? I need to see the full change history."

### Example Response

---

## Retention Change Investigation

**Investigation Period:** Last 90 days (2025-11-19 to 2026-02-17)
**Data Sources:** Audit logs + connector `retention_updated` field

---

### Change Timeline

| # | Date | Time (UTC) | User | Connector | Action | Previous | New | Source |
|---|------|------------|------|-----------|--------|----------|-----|--------|
| 1 | 2026-02-10 | 09:15:22 | j.smith@corp.com | Salesforce | Policy Updated | P1Y (365d) | P90D (90d) | Audit log |
| 2 | 2026-01-20 | 14:42:08 | admin@corp.com | Exchange Online | Policy Updated | P180D (180d) | P1Y (365d) | Audit log |
| 3 | 2026-01-20 | 14:43:15 | admin@corp.com | SharePoint Online | Policy Updated | P180D (180d) | P1Y (365d) | Audit log |
| 4 | 2026-01-20 | 14:44:02 | admin@corp.com | Teams | Policy Set | Not set | P1Y (365d) | Audit log |
| 5 | 2025-12-05 | — | — | Google Drive | Retention updated | — | P6M (180d) | Connector field |

---

### Analysis

**Change #1 — Salesforce retention reduced (Feb 10)**
- :red_circle: **High concern:** Retention was reduced from 365 days to 90 days.
- Changed by: j.smith@corp.com
- Reducing retention may cause compliance issues if this connector stores regulated data.
- **Action needed:** Verify that j.smith@corp.com was authorized to make this change and that the reduction was approved through your change management process.

**Changes #2-4 — Microsoft 365 retention standardized (Jan 20)**
- ✅ Retention was increased across all Microsoft 365 connectors to 1 year.
- Changed by: admin@corp.com in a single session (3 changes within 2 minutes).
- Teams connector had no previous policy — this is a positive remediation.

**Change #5 — Google Drive retention set (Dec 5)**
- ✅ Retention policy was configured on Google Drive.
- ⚠️ No matching audit log event found — the change may have occurred via API or before the audit log retention window.
- Source is the connector's `retention_updated` field only.

---

### Connector Retention Status After Changes

| Connector | Current Retention | Last Changed | Changed By |
|-----------|-------------------|--------------|------------|
| Exchange Online | P1Y (365 days) | 2026-01-20 | admin@corp.com |
| SharePoint Online | P1Y (365 days) | 2026-01-20 | admin@corp.com |
| Teams | P1Y (365 days) | 2026-01-20 | admin@corp.com |
| Salesforce | P90D (90 days) | 2026-02-10 | j.smith@corp.com |
| Google Drive | P6M (180 days) | 2025-12-05 | Unknown |

---

### Recommendations

1. **Investigate Salesforce retention reduction:** Confirm j.smith@corp.com had authorization to reduce retention from 365 to 90 days. If Salesforce stores regulated data, this may need to be reversed.
2. **Identify Google Drive change actor:** The `retention_updated` field shows a December 5 change but no audit log event was found. Use the Audit Event Analyzer skill with a broader time range to investigate.
3. **Implement change control:** Consider requiring approval workflows for retention policy modifications, especially reductions.

---

## Scenario 4: Response Templates

### Template A: Quick Retention Check

For users asking "show me our retention policies" or "how long is data kept":

---

## Retention Policy Summary

| Connector | Type | Retention Period | Status |
|-----------|------|-----------------|--------|
| Exchange Online | Microsoft 365 | 1 year (365 days) | ✅ Set |
| SharePoint Online | Microsoft 365 | 1 year (365 days) | ✅ Set |
| Teams | Microsoft 365 | 1 year (365 days) | ✅ Set |
| Entra ID | Entra ID | 1 year (365 days) | ✅ Set |
| Salesforce | Salesforce | 90 days | ✅ Set |

All 5 connectors have retention policies configured. The shortest retention is 90 days (Salesforce) and the longest is 365 days (Microsoft 365 connectors).

---

### Template B: Full Audit Report

For users asking "run a full retention compliance audit":

---

## Retention Compliance Audit

**Date:** 2026-02-17 | **Connectors:** 6 | **Frameworks:** GDPR, NIS2, HIPAA

### Executive Summary

- **Policy coverage:** 5 of 6 connectors (83%) have retention policies
- :red_circle: **1 connector** has no retention policy (Dynamics 365)
- ❌ **0 of 6 connectors** meet HIPAA 6-year minimum
- ✅ **5 of 6 connectors** meet GDPR documentation requirements
- ✅ **5 of 6 connectors** meet NIS2 backup policy requirements
- **2 retention changes** detected in the last 90 days

### Critical Findings

1. :red_circle: **Dynamics 365** has no retention policy — non-compliant with all frameworks
2. ❌ **All connectors** below HIPAA 6-year minimum (highest is 365 days)
3. ⚠️ **Salesforce** has unusually short retention of 90 days

### Policy Inventory

| Connector | Type | Retention | Days | Last Updated | Status |
|-----------|------|-----------|------|--------------|--------|
| Exchange Online | Microsoft 365 | P1Y | 365 | 2025-11-15 | ✅ Set |
| SharePoint Online | Microsoft 365 | P1Y | 365 | 2025-11-15 | ✅ Set |
| Teams | Microsoft 365 | P365D | 365 | 2025-11-15 | ✅ Set |
| Entra ID | Entra ID | P1Y | 365 | 2025-10-20 | ✅ Set |
| Salesforce | Salesforce | P90D | 90 | 2025-08-01 | ⚠️ Set |
| Dynamics 365 | Dynamics 365 | — | 0 | — | ❌ Not set |

### Compliance Matrix

| Connector | GDPR | NIS2 | HIPAA |
|-----------|------|------|-------|
| Exchange Online | ✅ | ✅ | ❌ 365d < 2190d |
| SharePoint Online | ✅ | ✅ | ❌ 365d < 2190d |
| Teams | ✅ | ✅ | ❌ 365d < 2190d |
| Entra ID | ✅ | ✅ | ❌ 365d < 2190d |
| Salesforce | ✅ | ✅ | ❌ 90d < 2190d |
| Dynamics 365 | ❌ | ❌ | ❌ No policy |

### Recent Changes

| Date | User | Connector | Old | New |
|------|------|-----------|-----|-----|
| 2025-11-15 | admin@corp.com | Teams | Not set | P365D (365d) |
| 2025-11-15 | admin@corp.com | Exchange | P180D | P1Y (365d) |

### Enforcement Verification

| Connector | Policy | Oldest Snapshot | Status |
|-----------|--------|-----------------|--------|
| Exchange Online | 365d | 362d | ✅ Enforced |
| SharePoint Online | 365d | 359d | ✅ Enforced |
| Teams | 365d | 93d | ✅ Within policy |
| Entra ID | 365d | 364d | ✅ Enforced |
| Salesforce | 90d | 88d | ✅ Enforced |
| Dynamics 365 | — | — | ❌ No policy to verify |

### Recommendations

1. **CRITICAL:** Configure a retention policy on Dynamics 365 immediately.
2. **CRITICAL:** If HIPAA applies, increase all retention to P6Y (2190 days minimum).
3. Review Salesforce 90-day retention with business stakeholders.
4. Document retention rationale in your ROPA for GDPR Art. 30.
5. Schedule next audit for Q2 2026.

---

### Template C: Compliance Matrix (Single Framework)

For users asking "are we HIPAA compliant on retention?":

---

## HIPAA Retention Compliance Check

**Requirement:** Minimum 6-year (2190-day) retention for covered records (45 CFR 164.530(j))

| Connector | Type | Current Retention | HIPAA Status | Shortfall |
|-----------|------|-------------------|--------------|-----------|
| Exchange Online | Microsoft 365 | 365 days | ❌ Non-compliant | 1825 days short |
| SharePoint Online | Microsoft 365 | 365 days | ❌ Non-compliant | 1825 days short |
| Teams | Microsoft 365 | 365 days | ❌ Non-compliant | 1825 days short |
| Entra ID | Entra ID | 365 days | ❌ Non-compliant | 1825 days short |
| Salesforce | Salesforce | 90 days | ❌ Non-compliant | 2100 days short |

**Result:** ❌ **0 of 5 connectors meet HIPAA retention requirements.**

All connectors need retention increased to a minimum of P6Y (2190 days). The largest shortfall is on Salesforce, which is 2100 days below the minimum.

**Recommended action:** Set `backup_retention` to `P6Y` on all connectors that store Protected Health Information (PHI). If only specific connectors handle PHI, apply P6Y to those and document which connectors are in scope for HIPAA.

---

### Template D: Connectors Without Policies

For users asking "which connectors don't have retention policies?":

---

## Connectors Missing Retention Policies

:red_circle: **2 connectors have no retention policy configured:**

| # | Connector | Type | GUID | Status |
|---|-----------|------|------|--------|
| 1 | Google Drive | Google Workspace | `a1b2c3d4-...` | ❌ No retention policy |
| 2 | Dynamics 365 | Dynamics 365 | `e5f6g7h8-...` | ❌ No retention policy |

**Why this matters:**
- Without an explicit retention policy, data retention behavior is undefined.
- This is a compliance violation under GDPR (Art. 5(1)(e) — storage limitation), NIS2 (Article 21 — documented backup policy), and any framework requiring documented retention.
- Over-retention of personal data without a documented purpose may violate the data minimization principle.

**Recommended action:**
1. Determine the appropriate retention period for each connector based on the data it protects and applicable regulations.
2. Configure `backup_retention` on both connectors (e.g., `P1Y` for 1 year, `P6Y` for HIPAA, `P7Y` for SOX).
3. Document the retention rationale for audit purposes.
4. Re-run this audit to confirm compliance.

---

### Template E: Over-Retention Warning

For enforcement verification that detects data kept beyond policy:

---

## Over-Retention Warning

⚠️ **1 connector has data retained beyond its stated policy:**

| Connector | Policy | Oldest Snapshot | Over By | Concern |
|-----------|--------|-----------------|---------|---------|
| SharePoint Online | 365 days | 412 days | 47 days | GDPR data minimization |

**Details:**
- SharePoint Online has a 365-day retention policy, but the oldest snapshot is 412 days old — 47 days beyond the stated policy.
- Under GDPR Art. 5(1)(e), personal data should be kept no longer than necessary for the purposes for which it is processed.
- This may indicate a delay in the retention enforcement mechanism or a recent policy change that has not yet been fully applied.

**Recommended action:**
1. Check if the retention policy was recently reduced (which would explain snapshots from before the change still existing).
2. Verify that the Keepit retention enforcement job is running correctly.
3. If the over-retention is intentional (e.g., legal hold), document the justification.
4. Monitor this connector in the next audit cycle to confirm resolution.

---

### Template F: Multi-Framework Comparison

For users asking "compare our retention against NIS2 and DORA":

---

## NIS2 and DORA Retention Assessment

### NIS2 (Article 21 — Cybersecurity Risk Management Measures)
**Requirement:** Organizations must implement documented backup and recovery policies as part of their cybersecurity risk management.

| Connector | Retention Policy | NIS2 Status |
|-----------|-----------------|-------------|
| Exchange Online | P1Y (365 days) | ✅ Backup policy documented |
| SharePoint Online | P1Y (365 days) | ✅ Backup policy documented |
| Google Drive | Not set | ❌ No backup policy documented |

### DORA (Article 12 — ICT-Related Incident Management)
**Requirement:** Financial entities must include data retention in their ICT resilience testing framework and business continuity plans.

| Connector | Retention Policy | DORA Status |
|-----------|-----------------|-------------|
| Exchange Online | P1Y (365 days) | ✅ Retention defined in resilience plan |
| SharePoint Online | P1Y (365 days) | ✅ Retention defined in resilience plan |
| Google Drive | Not set | ❌ No retention in resilience plan |

### Combined Assessment

- ✅ 2 of 3 connectors meet both NIS2 and DORA documentation requirements.
- ❌ Google Drive lacks any retention policy, failing both frameworks.
- **Note:** Both NIS2 and DORA require that retention be part of broader documented policies (backup policy for NIS2, resilience plan for DORA). Simply having a technical retention setting is necessary but not sufficient — ensure the retention rationale is documented in your organizational policies.
