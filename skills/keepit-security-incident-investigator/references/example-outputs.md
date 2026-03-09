# Security Incident Investigator — Example Outputs

## Table of Contents

1. [Scenario 1: Credential Compromise Investigation](#scenario-1-credential-compromise-investigation)
2. [Scenario 2: Insider Threat Investigation](#scenario-2-insider-threat-investigation)
3. [Scenario 3: Ransomware Precursor Detection](#scenario-3-ransomware-precursor-detection)
4. [Scenario 4: Clean Investigation](#scenario-4-clean-investigation)
5. [Response Templates](#response-templates)

---

## Scenario 1: Credential Compromise Investigation

**Scenario:** An API token used for backup automation shows a pattern of repeated authentication failures followed by a successful login and an immediate data export. The SOC team suspects credential compromise.

**User Query:** "We're seeing failed login alerts for the backup service token. Can you investigate if the token was compromised?"

```markdown
## Security Investigation Report

**Investigation ID:** INV-2026-0214-001
**Severity:** ❌ Critical (Score: 87/100)
**Time Window:** 2026-02-07 to 2026-02-14
**Total Events Analyzed:** 1,247
**Patterns Detected:** 3 (Credential Compromise, Data Exfiltration, Off-Hours Anomaly)
**Investigation Completeness:** 100%

---

### Executive Summary

Investigation detected a **credential compromise** of the `api-token-backup-svc` API token.
The attack followed a classic pattern: brute-force authentication attempts at 02:10 UTC on
2026-02-14, followed by successful login at 02:14 UTC and immediate data export (2.3 GB)
from the Exchange Online connector. All activity occurred outside business hours, increasing
the severity classification.

**Immediate action required: Revoke the compromised token and verify exported data scope.**

---

### Evidence Timeline

| Time (UTC) | Source | Event | Actor | Severity | Details |
|------------|--------|-------|-------|----------|---------|
| 2026-02-14 02:10 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:11 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:11 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:12 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:12 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:14 | Audit | Auth Success | api-token-backup-svc | 🔴 | Success after 5 failures — credential compromise indicator |
| 2026-02-14 02:18 | Audit | Configuration | api-token-backup-svc | ⚠️ | Connector export settings accessed |
| 2026-02-14 02:22 | Job | Export Started | Exchange Online | 🔴 | Export job initiated via compromised token |
| 2026-02-14 02:35 | Job | Export Complete | Exchange Online | 🔴 | 2.3 GB data exported successfully |

---

### Attack Pattern Analysis

#### Pattern 1: Credential Compromise ❌

| Attribute | Value |
|-----------|-------|
| **Pattern Type** | credential_compromise |
| **Token** | api-token-backup-svc |
| **Failure Count** | 5 |
| **Time to Success** | 4 minutes |
| **Window** | 2026-02-14 02:10 — 02:14 UTC |
| **Confidence** | High |

The attacker made 5 failed authentication attempts over 4 minutes before
successfully authenticating. The rapid succession and eventual success
indicate the token credential was compromised, likely through credential
theft or brute force.

#### Pattern 2: Data Exfiltration 🔴

| Attribute | Value |
|-----------|-------|
| **Job Type** | Export |
| **Connector** | Exchange Online (abc-123) |
| **Data Volume** | 2.3 GB |
| **Time After Compromise** | 8 minutes |
| **Risk Factors** | off_hours_execution, auth_failure_correlation, high_failure_token |
| **Confidence** | High |

An export job was initiated just 8 minutes after the credential compromise,
targeting the Exchange Online connector. The export completed successfully,
extracting 2.3 GB of email backup data.

#### Pattern 3: Off-Hours Anomaly ⚠️

| Attribute | Value |
|-----------|-------|
| **Time Window** | 02:10 — 02:35 UTC |
| **Business Hours** | 08:00 — 18:00 UTC |
| **Anomaly Score** | 0.95 |

All attack activity occurred between 02:10 and 02:35 UTC, well outside
the established business hours of 08:00 to 18:00 UTC. Historical baseline
shows near-zero activity during this window.

---

### Indicators of Compromise (IOCs)

**Suspicious Tokens:**
- `api-token-backup-svc` — 5 failed auths → success, off-hours export (risk score: 65)

**Suspicious Activity Windows:**
- 2026-02-14 02:10 — 02:35 UTC — Brute force + export attack chain

**Affected Connectors:**
- Exchange Online (abc-123) — Export target, backup verified intact ✅

---

### Severity Assessment

| Factor | Points | Description |
|--------|--------|-------------|
| Credential Compromise | +30 | Failed → success authentication sequence |
| Data Exfiltration (High) | +40 | Export job with high-confidence risk factors |
| Off-Hours Anomalies | +12 | Activity outside established business hours |
| Multi-Pattern Correlation | x1.3 | Three distinct attack patterns detected |
| **Total** | **87/100** | **❌ Critical** |

---

### Recommendations (Priority Order)

1. **ACTIVATE INCIDENT RESPONSE** — containment required immediately
2. Immediately revoke the `api-token-backup-svc` API token
3. Review the exported data (2.3 GB from Exchange Online) to assess data exposure scope
4. Audit destination of exported data — check access logs for download activity
5. Enable multi-factor authentication for all API tokens if available
6. Generate a new backup service token with restricted permissions
7. Review all other tokens for similar compromise indicators
8. Notify security leadership and legal counsel
9. Preserve all audit logs for forensic record

---

### Backup Integrity Check

| Connector | Health | Last Snapshot | Assessment |
|-----------|--------|---------------|------------|
| Exchange Online | ✅ Healthy | 2026-02-14 06:00 UTC | Intact — backup not modified |
| SharePoint | ✅ Healthy | 2026-02-14 06:00 UTC | Intact — not targeted |
| Teams | ✅ Healthy | 2026-02-14 05:45 UTC | Intact — not targeted |

Backup data integrity remains intact. The attacker exported a copy but did not
modify or delete existing backups.
```

---

## Scenario 2: Insider Threat Investigation

**Scenario:** A departing employee with admin access makes off-hours configuration changes to backup retention policies and initiates large data exports from multiple connectors over several days.

**User Query:** "Can you investigate what the admin-token-jsmith account has been doing over the last 30 days? We think there might be insider activity."

```markdown
## Security Investigation Report

**Investigation ID:** INV-2026-0217-003
**Severity:** 🔴 High (Score: 72/100)
**Time Window:** 2026-01-18 to 2026-02-17
**Total Events Analyzed:** 3,891
**Patterns Detected:** 3 (Config Tampering, Data Exfiltration, Off-Hours Anomaly)
**Investigation Completeness:** 100%

---

### Executive Summary

Investigation of the `admin-token-jsmith` token reveals a **pattern consistent
with insider threat activity** over the past 30 days. The token was used to:

1. Reduce backup retention from 365 days to 30 days on two connectors (Feb 8)
2. Export data from Exchange Online (4.1 GB) and SharePoint (7.8 GB) over three sessions
3. All modifications and exports occurred outside business hours (22:00 — 01:00 UTC)

The combination of retention policy weakening and large data exports from a single
token outside normal hours is a strong insider threat indicator.

---

### Evidence Timeline

| Time (UTC) | Source | Event | Actor | Severity | Details |
|------------|--------|-------|-------|----------|---------|
| 2026-02-08 22:12 | Audit | Configuration | admin-token-jsmith | 🔴 | Retention policy changed: Exchange 365d → 30d |
| 2026-02-08 22:15 | Audit | Configuration | admin-token-jsmith | 🔴 | Retention policy changed: SharePoint 365d → 30d |
| 2026-02-10 23:05 | Job | Export Started | Exchange Online | 🔴 | Export initiated by admin-token-jsmith |
| 2026-02-10 23:42 | Job | Export Complete | Exchange Online | 🔴 | 4.1 GB exported |
| 2026-02-12 22:30 | Job | Export Started | SharePoint | 🔴 | Export initiated by admin-token-jsmith |
| 2026-02-12 23:18 | Job | Export Complete | SharePoint | 🔴 | 7.8 GB exported |
| 2026-02-14 00:05 | Job | Export Started | SharePoint | ⚠️ | Additional export — incremental data |
| 2026-02-14 00:22 | Job | Export Complete | SharePoint | ⚠️ | 1.2 GB exported |

---

### Attack Pattern Analysis

#### Pattern 1: Configuration Tampering 🔴

| Attribute | Value |
|-----------|-------|
| **Change Type** | retention_modification |
| **Connectors Affected** | Exchange Online, SharePoint |
| **Original Retention** | 365 days |
| **New Retention** | 30 days |
| **Token** | admin-token-jsmith |
| **Risk Factors** | retention_change, off_hours_change, destructive_operation |
| **Confidence** | High |

Retention policies were reduced from 365 days to 30 days on two critical
connectors. This change, if undetected, would result in automatic deletion
of 11 months of backup data within 30 days.

#### Pattern 2: Data Exfiltration 🔴

| Attribute | Value |
|-----------|-------|
| **Job Types** | Export (3 sessions) |
| **Connectors** | Exchange Online, SharePoint |
| **Total Data Volume** | 13.1 GB |
| **Time Span** | 4 days (Feb 10 — Feb 14) |
| **Risk Factors** | off_hours_execution, multi_session, high_volume |
| **Confidence** | High |

Three export sessions over four days extracted 13.1 GB of data from two
connectors. The staged approach (separate sessions, separate connectors)
suggests deliberate exfiltration rather than legitimate administrative activity.

#### Pattern 3: Off-Hours Anomaly ⚠️

| Attribute | Value |
|-----------|-------|
| **Activity Hours** | 22:00 — 01:00 UTC exclusively |
| **Business Hours** | 08:00 — 18:00 UTC |
| **Anomaly Score** | 0.92 |
| **Historical Baseline** | 0 events/hour during 22:00-01:00 window |

All configuration changes and export operations occurred between 22:00 and
01:00 UTC. The `admin-token-jsmith` token showed zero activity during normal
business hours throughout the investigation window, which is itself anomalous
for an active admin token.

---

### Indicators of Compromise (IOCs)

**Suspicious Tokens:**
- `admin-token-jsmith` — Off-hours only activity, retention changes, 13.1 GB exports (risk score: 55)

**Suspicious Activity Windows:**
- 2026-02-08 22:00 — 23:00 UTC — Retention policy tampering
- 2026-02-10 23:00 — 00:00 UTC — Exchange export session
- 2026-02-12 22:30 — 23:30 UTC — SharePoint export session 1
- 2026-02-14 00:00 — 01:00 UTC — SharePoint export session 2

**Affected Connectors:**
- Exchange Online (abc-123) — Retention modified, export target
- SharePoint (def-456) — Retention modified, export target

---

### Severity Assessment

| Factor | Points | Description |
|--------|--------|-------------|
| Config Tampering (retention) | +25 | Retention policies shortened on 2 connectors |
| Config Tampering (destructive) | +15 | Changes weaken data protection |
| Data Exfiltration (High) | +40 | 13.1 GB exported across 3 sessions |
| Off-Hours Anomalies | +12 | All activity outside business hours |
| Multi-Pattern Correlation | x1.3 | Three distinct patterns detected |
| **Total** | **72/100** | **🔴 High** |

---

### Recommendations (Priority Order)

1. **Investigate immediately** and escalate to security lead
2. Immediately revoke the `admin-token-jsmith` API token
3. Revert retention policies on Exchange Online and SharePoint to 365 days
4. Audit exported data destinations — determine if data left the organization
5. Review HR status of the token owner — correlate with employment changes
6. Verify backup integrity for affected connectors
7. Review all admin tokens for similar off-hours activity patterns
8. Implement alerts for retention policy changes
9. Consider restricting export operations to business hours only
```

---

## Scenario 3: Ransomware Precursor Detection

**Scenario:** Multiple connectors begin showing health degradation after a series of configuration changes. The pattern resembles ransomware preparation: disable backups, corrupt retention, then encrypt.

**User Query:** "Several of our connectors went unhealthy in the last 48 hours. Could this be a ransomware attack targeting our backups?"

```markdown
## Security Investigation Report

**Investigation ID:** INV-2026-0217-005
**Severity:** ❌ Critical (Score: 93/100)
**Time Window:** 2026-02-15 to 2026-02-17
**Total Events Analyzed:** 487
**Patterns Detected:** 4 (Config Tampering, Credential Compromise, Off-Hours Anomaly, Connector Degradation)
**Investigation Completeness:** 95% (1 connector health check failed)

---

### Executive Summary

Investigation reveals a **coordinated attack consistent with ransomware preparation**
targeting backup infrastructure. Over the past 48 hours:

1. The `api-token-integrations` token was compromised (brute force at 01:30 UTC Feb 15)
2. Using the compromised token, backup schedules were disabled on 4 connectors
3. Retention policies were reduced to minimum (1 day) on all affected connectors
4. Connector health degraded from Healthy to Critical on 3 of 4 connectors
5. No data export detected — attack appears focused on backup destruction

**This matches the pre-encryption phase of a ransomware kill chain. Immediate
containment is required.**

---

### Evidence Timeline

| Time (UTC) | Source | Event | Actor | Severity | Details |
|------------|--------|-------|-------|----------|---------|
| 2026-02-15 01:30 | Audit | Auth Failure x8 | api-token-integrations | ⚠️ | Rapid brute force attempt |
| 2026-02-15 01:33 | Audit | Auth Success | api-token-integrations | 🔴 | Success after 8 failures |
| 2026-02-15 01:35 | Audit | Configuration | api-token-integrations | 🔴 | Exchange: schedule disabled |
| 2026-02-15 01:36 | Audit | Configuration | api-token-integrations | 🔴 | SharePoint: schedule disabled |
| 2026-02-15 01:37 | Audit | Configuration | api-token-integrations | 🔴 | Teams: schedule disabled |
| 2026-02-15 01:38 | Audit | Configuration | api-token-integrations | 🔴 | OneDrive: schedule disabled |
| 2026-02-15 01:40 | Audit | Configuration | api-token-integrations | 🔴 | Exchange: retention → 1 day |
| 2026-02-15 01:41 | Audit | Configuration | api-token-integrations | 🔴 | SharePoint: retention → 1 day |
| 2026-02-15 01:42 | Audit | Configuration | api-token-integrations | 🔴 | Teams: retention → 1 day |
| 2026-02-15 01:43 | Audit | Configuration | api-token-integrations | 🔴 | OneDrive: retention → 1 day |
| 2026-02-16 06:00 | Health | Degradation | Exchange Online | ❌ | Health: Healthy → Unhealthy |
| 2026-02-16 06:00 | Health | Degradation | SharePoint | ❌ | Health: Healthy → Unhealthy |
| 2026-02-16 06:00 | Health | Degradation | Teams | ❌ | Health: Healthy → Critical |
| 2026-02-16 06:15 | Health | Assessment | OneDrive | ⚠️ | Assessment unavailable |

---

### Attack Pattern Analysis

#### Pattern 1: Credential Compromise (Brute Force) ❌

| Attribute | Value |
|-----------|-------|
| **Pattern Type** | brute_force |
| **Token** | api-token-integrations |
| **Failure Count** | 8 |
| **Time to Success** | 3 minutes |
| **Confidence** | High |

Rapid brute force attack against the integrations token. Eight failures in
3 minutes followed by successful authentication. The token was then used
immediately for destructive configuration changes.

#### Pattern 2: Configuration Tampering (Destructive) ❌

| Attribute | Value |
|-----------|-------|
| **Changes** | 8 configuration modifications in 8 minutes |
| **Connectors Affected** | Exchange, SharePoint, Teams, OneDrive (all 4) |
| **Actions** | Backup schedules disabled, retention set to 1 day |
| **Token** | api-token-integrations (compromised) |
| **Risk Factors** | destructive_operation, retention_change, schedule_change, near_auth_failure, off_hours_change |
| **Confidence** | High |

The attack systematically disabled backup schedules and reduced retention
to 1 day on every connector in the account. This is a textbook ransomware
preparation pattern: eliminate backup protection before encrypting production data.

#### Pattern 3: Connector Health Degradation ❌

| Connector | Before | After | Impact |
|-----------|--------|-------|--------|
| Exchange Online | ✅ Healthy | ❌ Unhealthy | Backups stopped, data at risk |
| SharePoint | ✅ Healthy | ❌ Unhealthy | Backups stopped, data at risk |
| Teams | ✅ Healthy | ❌ Critical | Backups stopped, snapshots expiring |
| OneDrive | ✅ Healthy | ⚠️ Unknown | Health check failed |

Three of four connectors degraded to Unhealthy/Critical within 24 hours of
the configuration changes. This confirms the attack achieved its objective
of disabling backup protection.

---

### Indicators of Compromise (IOCs)

**Suspicious Tokens:**
- `api-token-integrations` — Brute-forced, used for destructive config changes (risk score: 85)

**Suspicious Activity Windows:**
- 2026-02-15 01:30 — 01:43 UTC — Full attack chain (13 minutes)

**Affected Connectors:**
- Exchange Online (abc-123) — Schedule disabled, retention 1 day, health degraded ❌
- SharePoint (def-456) — Schedule disabled, retention 1 day, health degraded ❌
- Teams (ghi-789) — Schedule disabled, retention 1 day, health critical ❌
- OneDrive (jkl-012) — Schedule disabled, retention 1 day, status unknown ⚠️

---

### Severity Assessment

| Factor | Points | Description |
|--------|--------|-------------|
| Brute Force Attack | +20 | 8 failures → success in 3 minutes |
| Credential Compromise | +30 | Compromised token used for destruction |
| Config Tampering (destructive) | +30 | Schedules disabled, retention minimized |
| Config Tampering (retention) | +25 | Retention reduced to 1 day on 4 connectors |
| Off-Hours Anomalies | +10 | All activity at 01:30 UTC |
| Compromised Connectors | x1.2 | 3 connectors in degraded state |
| Multi-Pattern Correlation | x1.3 | 4 distinct attack patterns |
| **Total (capped)** | **93/100** | **❌ Critical** |

---

### Recommendations (Priority Order)

1. **ACTIVATE INCIDENT RESPONSE** — this is an active attack in progress
2. **Immediately revoke** the `api-token-integrations` token
3. **Re-enable backup schedules** on all 4 affected connectors NOW
4. **Restore retention policies** to original values (check pre-Feb-15 configuration)
5. **Verify existing snapshots** — determine if any data has already been purged
6. **Rotate all API tokens** — assume other tokens may also be compromised
7. **Monitor for encryption** — alert production IT team that ransomware execution may be imminent
8. **Isolate affected systems** if ransomware indicators appear in production
9. Notify security leadership, legal counsel, and cyber insurance provider
10. Preserve all audit logs and investigation artifacts for forensic analysis
11. Engage incident response firm if encryption is detected

---

### Ransomware Kill Chain Assessment

| Phase | Status | Evidence |
|-------|--------|----------|
| Reconnaissance | Unknown | No pre-attack scanning detected in audit logs |
| Initial Access | ✅ Confirmed | Brute force compromise of api-token-integrations |
| Persistence | Unknown | No additional tokens created (check manually) |
| Defense Evasion | ✅ Confirmed | Backup schedules disabled, retention minimized |
| Impact Preparation | ✅ Confirmed | 4/4 connectors affected, 3 degraded |
| Encryption/Destruction | ⚠️ Pending | Not yet detected — may be imminent |
```

---

## Scenario 4: Clean Investigation

**Scenario:** A security team runs a routine investigation after a compliance review. No suspicious patterns are detected. The environment appears healthy.

**User Query:** "Run a full security check on our Keepit environment. We need this for our quarterly security review."

```markdown
## Security Investigation Report

**Investigation ID:** INV-2026-0217-007
**Severity:** 🟢 Low (Score: 4/100)
**Time Window:** 2026-01-18 to 2026-02-17
**Total Events Analyzed:** 4,218
**Patterns Detected:** 0
**Investigation Completeness:** 100%

---

### Executive Summary

Comprehensive 30-day security investigation of the Keepit backup environment
found **no suspicious activity patterns**. All authentication events are
consistent with normal operational activity. No indicators of compromise
were detected.

Environment health is strong across all 6 connectors with regular backup
schedules maintaining current snapshots.

---

### Investigation Summary

#### Authentication Analysis ✅

| Metric | Value | Status |
|--------|-------|--------|
| Total auth events | 1,842 | Normal |
| Successful authentications | 1,836 (99.7%) | ✅ Healthy |
| Failed authentications | 6 (0.3%) | ✅ Normal rate |
| Unique tokens active | 4 | Expected |
| Brute force patterns | 0 | ✅ None detected |
| Credential compromise patterns | 0 | ✅ None detected |
| Credential stuffing patterns | 0 | ✅ None detected |

The 6 failed authentication events were isolated incidents (single failures,
no sequences) consistent with token rotation or transient network issues.

#### Job Activity Analysis ✅

| Metric | Value | Status |
|--------|-------|--------|
| Total jobs | 2,047 | Normal |
| Backup jobs | 2,038 (99.6%) | ✅ Expected |
| Restore jobs | 7 (0.3%) | ✅ Normal |
| Export jobs | 2 (0.1%) | ✅ Normal |
| Off-hours jobs | 12 (scheduled) | ✅ Expected — scheduled backups |

Two export jobs were initiated during business hours by the `admin-token-primary`
token, consistent with normal administrative data retrieval.

#### Configuration Changes ✅

| Metric | Value | Status |
|--------|-------|--------|
| Config change events | 14 | Normal |
| Retention changes | 0 | ✅ No modifications |
| Schedule changes | 2 | ✅ Reviewed — legitimate |
| Connector modifications | 1 | ✅ New connector added |

All configuration changes occurred during business hours by expected admin tokens.
Two schedule changes adjusted backup windows per IT team request (ticket ref INC-4521).

#### Connector Health ✅

| Connector | Health | Last Snapshot | Snapshot Age |
|-----------|--------|---------------|--------------|
| Exchange Online | ✅ Healthy | 2026-02-17 06:00 UTC | 4 hours |
| SharePoint | ✅ Healthy | 2026-02-17 06:00 UTC | 4 hours |
| Teams | ✅ Healthy | 2026-02-17 05:45 UTC | 4.25 hours |
| OneDrive | ✅ Healthy | 2026-02-17 06:15 UTC | 3.75 hours |
| Dynamics 365 | ✅ Healthy | 2026-02-17 04:00 UTC | 6 hours |
| Entra ID | ✅ Healthy | 2026-02-17 06:00 UTC | 4 hours |

All 6 connectors are healthy with current snapshots within expected backup windows.

---

### Behavioral Baseline

| Metric | Value |
|--------|-------|
| Business hours | 08:00 — 18:00 UTC |
| Peak activity hour | 10:00 UTC |
| Average daily events | 140.6 |
| Weekend activity ratio | 8.2% (automated jobs only) |
| Active tokens | admin-token-primary, api-token-backup-svc, api-token-monitoring, api-token-reporting |

Activity patterns are consistent and predictable. No anomalous deviations detected.

---

### Token Activity Summary ✅

| Token | Events | Failure Rate | Sensitive Ops | Hours Active | Risk |
|-------|--------|--------------|---------------|-------------|------|
| admin-token-primary | 892 | 0.2% | 16 (config) | 08-17 | 🟢 None |
| api-token-backup-svc | 2,614 | 0.1% | 0 | 00-23 (scheduled) | 🟢 None |
| api-token-monitoring | 498 | 0.4% | 0 | 08-18 | 🟢 None |
| api-token-reporting | 214 | 0.0% | 2 (export) | 09-16 | 🟢 None |

All tokens operate within expected parameters. No suspicious risk profiles detected.

---

### Severity Assessment

| Factor | Points | Description |
|--------|--------|-------------|
| Auth patterns | 0 | No suspicious sequences |
| Exfiltration indicators | 0 | No suspicious exports |
| Config tampering | 0 | No unauthorized changes |
| Off-hours anomalies | +4 | 4 minor off-hours events (automated, expected) |
| Suspicious tokens | 0 | No tokens flagged |
| **Total** | **4/100** | **🟢 Low** |

---

### Recommendations

1. Continue monitoring — no immediate action required
2. Consider implementing automated alerting for failed auth sequences (proactive measure)
3. Review API token permissions during next quarterly access review
4. Document this clean investigation result for compliance records

---

### Compliance Note

This investigation report covers the period 2026-01-18 to 2026-02-17 and can be
used as evidence for quarterly security review compliance. All data sources were
fully accessible and no evidence gaps exist.
```

---

## Response Templates

### Template 1: Quick Security Check

Use when users ask for a brief security status or "is everything okay?"

```markdown
## Quick Security Status

**Account:** {account_name}
**Checked:** {timestamp}
**Status:** {severity_icon} {severity_label}

### Summary
- **Authentication:** {auth_status_icon} {total_auth_events} events, {failure_rate}% failure rate
- **Configuration:** {config_status_icon} {config_changes} changes in last 7 days
- **Jobs:** {job_status_icon} {total_jobs} jobs, {export_count} exports
- **Connectors:** {connector_status_icon} {healthy_count}/{total_count} healthy

{if_findings}
### Findings
{finding_list}
{/if_findings}

{if_clean}
No suspicious activity detected. Environment appears healthy.
{/if_clean}
```

### Template 2: Full Investigation Report

Use for comprehensive investigations. Structure:

```markdown
## Security Investigation Report

**Investigation ID:** INV-{date}-{seq}
**Severity:** {severity_icon} {severity_label} (Score: {score}/100)
**Time Window:** {start_date} to {end_date}
**Total Events Analyzed:** {event_count}
**Patterns Detected:** {pattern_count} ({pattern_list})
**Investigation Completeness:** {completeness}%

---

### Executive Summary
{2-3 sentence summary of findings and recommended action}

---

### Evidence Timeline
{chronological event table}

---

### Attack Pattern Analysis
{per-pattern detailed analysis}

---

### Indicators of Compromise (IOCs)
{tokens, time windows, connectors}

---

### Severity Assessment
{scoring breakdown table}

---

### Recommendations (Priority Order)
{numbered action items}

---

### Backup Integrity Check
{connector health table}
```

### Template 3: IOC Summary

Use when users ask specifically about indicators of compromise.

```markdown
## Indicator of Compromise (IOC) Summary

**Investigation:** {investigation_id}
**Generated:** {timestamp}
**Total IOCs:** {ioc_count}

### Suspicious Tokens ({token_count})

| Token | Risk Score | Indicators | First Seen | Last Active |
|-------|-----------|------------|------------|-------------|
| {token_name} | {score}/100 | {indicator_list} | {first_seen} | {last_active} |

### Suspicious Time Windows ({window_count})

| Window (UTC) | Duration | Activity Type | Confidence |
|-------------|----------|---------------|------------|
| {start} — {end} | {duration} | {activity} | {confidence} |

### Affected Connectors ({connector_count})

| Connector | GUID | Impact | Health | Recommendation |
|-----------|------|--------|--------|----------------|
| {name} | {guid} | {impact} | {health_icon} | {recommendation} |

### Recommended Actions
{prioritized action list based on IOC severity}
```

### Template 4: Comparison with Previous Investigation

Use when users ask to compare current state against a previous investigation.

```markdown
## Security Status Comparison

**Current Investigation:** {current_id} ({current_date})
**Previous Investigation:** {previous_id} ({previous_date})

### Trend Summary

| Metric | Previous | Current | Trend |
|--------|----------|---------|-------|
| Severity Score | {prev_score} | {curr_score} | {trend_icon} |
| Auth Failures | {prev_failures} | {curr_failures} | {trend_icon} |
| Config Changes | {prev_changes} | {curr_changes} | {trend_icon} |
| Suspicious Tokens | {prev_tokens} | {curr_tokens} | {trend_icon} |
| Healthy Connectors | {prev_healthy} | {curr_healthy} | {trend_icon} |

### Key Changes
{bulleted list of significant differences}

### Resolved Issues
{issues from previous investigation no longer present}

### New Findings
{issues not present in previous investigation}
```
