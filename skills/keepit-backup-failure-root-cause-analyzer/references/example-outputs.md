# Keepit Backup Failure Root Cause Analyzer — Example Outputs

## Table of Contents

1. [Scenario 1: Auth Token Expiry Investigation](#scenario-1-auth-token-expiry-investigation)
2. [Scenario 2: Config-Change-Induced Failure](#scenario-2-config-change-induced-failure)
3. [Scenario 3: Recurring Monday Morning Failure](#scenario-3-recurring-monday-morning-failure)
4. [Scenario 4: First-Time Connectivity Failure](#scenario-4-first-time-connectivity-failure)
5. [Response Templates](#response-templates)
   - [Quick Diagnosis Template](#quick-diagnosis-template)
   - [Full RCA Report Template](#full-rca-report-template)
   - [Verification Checklist Template](#verification-checklist-template)

---

## Scenario 1: Auth Token Expiry Investigation

**User prompt:** "Why did my Exchange Online backup fail this morning?"

**Context:** The Exchange Online connector's 8:00 AM backup failed. The execsummary XML contains a token expiry error. The connector health is currently unhealthy. No recent config changes.

### Expected Output

```markdown
# Backup Failure Root Cause Analysis

**Connector:** Exchange Online (Microsoft 365)
**Failure Time:** 2025-01-15T08:00:12Z
**Investigation Time:** 2025-01-15T10:35:00Z
**Status:** ❌ Unhealthy

---

## Root Cause Summary

| Field | Value |
|-------|-------|
| Root Cause | Authentication Token Expired |
| Confidence | High |
| Recurrence | First occurrence |
| Backup Gap | 26.6 hours |
| Risk Level | 🟡 Medium |
| Active Recovery | No |

## Root Cause Details

**Classification:** `auth_expired` (High confidence)

The backup failed because the OAuth refresh token for the Microsoft 365
connector has expired. The job execution summary reports:

> **Error:** Token expired for Microsoft Graph API
> **Exit Reason:** Authentication failure - 401 Unauthorized

This is the first occurrence of this error for this connector. No
configuration changes were detected in the 24 hours preceding the failure.

### Evidence

- Error message explicitly references expired token
- HTTP 401 Unauthorized response from Microsoft Graph API
- Connector health status changed to "unhealthy" at failure time
- No config changes or audit events correlated with the failure

## Data Risk Assessment

| Metric | Value |
|--------|-------|
| Last Successful Backup | 2025-01-14T08:00:00Z |
| Backup Gap | 26.6 hours (1.1 days) |
| Risk Level | 🟡 Medium |
| Normal Backup Interval | ~24.0 hours |

Data created or modified in the past 26.6 hours is unprotected.
Prioritize remediation to avoid the gap growing further.

## Event Timeline

| Time | Event | Relevance |
|------|-------|-----------|
| 2025-01-14T08:00:00Z | Last successful backup | ✅ Baseline |
| 2025-01-15T08:00:12Z | Backup job failed (401) | ❌ Target failure |
| 2025-01-15T08:00:15Z | Connector health → unhealthy | ⚠️ State change |

## Resolution Steps

### 🔴 Step 1: Re-authorize the Exchange Online connector
Navigate to the Keepit admin console, select the Exchange Online connector,
and initiate re-authorization. This will refresh the OAuth tokens used for
backup access to the Microsoft 365 environment.

### 🔴 Step 2: Verify credential validity
Confirm that the service account credentials are still valid in the
Microsoft 365 admin center. Check for:
- Recent password resets
- MFA policy changes
- Conditional access policy updates
- Azure AD application consent status

### 🔴 Step 3: Trigger a manual backup
After re-authorization, run a manual backup job to verify that
authentication is working correctly and the backup gap begins closing.

### 🟡 Step 4: Set up token expiry monitoring
Configure alerts for upcoming token expirations to prevent future
auth-related failures. Review the token renewal schedule and set
a reminder 7 days before the next expected expiry.

## Post-Fix Verification Checklist

- [ ] **Connector re-authorization successful**
  - **How:** Check connector status in Keepit admin console shows 'Authorized'
  - **Expected:** Connector status is healthy with valid credentials

- [ ] **Manual backup completes successfully**
  - **How:** Trigger a manual backup and monitor job status until completion
  - **Expected:** Job completes without auth errors; no 'failed' timestamp

- [ ] **Next scheduled backup succeeds**
  - **How:** Wait for the next scheduled backup window and check job history
  - **Expected:** Scheduled backup completes successfully

- [ ] **Token expiry alert configured**
  - **How:** Verify monitoring/alert configuration for credential expiration
  - **Expected:** Alert rules exist and will fire before next token expiry
```

---

## Scenario 2: Config-Change-Induced Failure

**User prompt:** "Our SharePoint backup started failing after someone changed the retention policy. Can you investigate?"

**Context:** SharePoint Online connector failed 2 hours after a retention policy update. Audit log shows the change. The failure has occurred twice since the change.

### Expected Output

```markdown
# Backup Failure Root Cause Analysis

**Connector:** SharePoint Online (Microsoft 365)
**Failure Time:** 2025-02-10T14:22:08Z
**Investigation Time:** 2025-02-10T16:45:00Z
**Status:** ❌ Unhealthy

---

## Root Cause Summary

| Field | Value |
|-------|-------|
| Root Cause | Configuration Change |
| Confidence | High |
| Recurrence | Recurring (2 occurrences) |
| Backup Gap | 30.7 hours |
| Risk Level | 🟡 Medium |
| Active Recovery | No |

## Root Cause Details

**Classification:** `config_change` (High confidence)

The backup failure is directly correlated with a retention policy change
made 2.0 hours before the first failure. Audit log analysis confirms:

> **Audit Event (2025-02-10T12:15:00Z):** Retention policy updated on
> connector "SharePoint Online" by admin@contoso.com
>
> **First Failure (2025-02-10T14:22:08Z):** 2.0 hours after policy change
>
> **Second Failure (2025-02-11T02:22:00Z):** Scheduled retry also failed

### Configuration Change Attribution

| Field | Value |
|-------|-------|
| Change Detected | ⚠️ Yes — Retention policy update |
| Changed By | admin@contoso.com |
| Change Time | 2025-02-10T12:15:00Z |
| Time Before Failure | 2.0 hours |
| Causal Confidence | High |

### Evidence

- Retention policy updated 2.0 hours before first failure
- Connector `retention_updated` field confirms: 2025-02-10T12:15:00Z
- Audit log entry: "Retention policy updated on SharePoint Online"
- Error message references retention configuration conflict
- No other changes or events detected in the correlation window

## Data Risk Assessment

| Metric | Value |
|--------|-------|
| Last Successful Backup | 2025-02-10T08:00:00Z |
| Backup Gap | 30.7 hours (1.3 days) |
| Risk Level | 🟡 Medium |
| Normal Backup Interval | ~24.0 hours |

Data created or modified in the past 30.7 hours is unprotected.
Prioritize remediation to avoid the gap growing further.

## Event Timeline

| Time | Event | Relevance |
|------|-------|-----------|
| 2025-02-10T08:00:00Z | Last successful backup | ✅ Baseline |
| 2025-02-10T12:15:00Z | Retention policy updated by admin@contoso.com | 🔴 Likely cause |
| 2025-02-10T14:22:08Z | Backup job failed | ❌ Target failure |
| 2025-02-11T02:22:00Z | Scheduled retry failed | ❌ Recurring failure |

## Resolution Steps

### 🔴 Step 1: Review the retention policy change
Examine the audit log entry from 2025-02-10T12:15:00Z. The retention policy
was updated by admin@contoso.com on the SharePoint Online connector.
Compare the new policy with the previous settings to identify the conflict.

### 🔴 Step 2: Revert the retention policy change
Revert the retention policy to its previous configuration. Document the
change and the revert for the change management record. Contact
admin@contoso.com to discuss the intended change and find a compatible
configuration.

### 🔴 Step 3: Test with corrected configuration
Run a manual backup with the corrected configuration to confirm the
issue is resolved and the backup can complete successfully.

### 🟡 Step 4: Implement change control process
Establish or reinforce a change management process that requires review
and approval before modifying backup configurations. This prevents
unintended disruption from ad-hoc changes.

### 🔴 Step 5: Escalate recurring failure pattern
This failure has occurred 2 times since the configuration change. If the
retention policy revert does not resolve the issue, escalate to Keepit
support with the audit trail and error details.

## Post-Fix Verification Checklist

- [ ] **Configuration reverted or corrected**
  - **How:** Compare current config against last known good configuration
  - **Expected:** Configuration matches the pre-change state

- [ ] **Manual backup completes successfully**
  - **How:** Trigger a manual backup and monitor to completion
  - **Expected:** Job completes without configuration errors

- [ ] **Audit log confirms the correction**
  - **How:** Review audit log for the corrective config change entry
  - **Expected:** Audit log shows revert with appropriate timestamp

- [ ] **Next two scheduled backups succeed**
  - **How:** Monitor the next two backup cycles
  - **Expected:** Both complete without errors, confirming stable resolution
```

---

## Scenario 3: Recurring Monday Morning Failure

**User prompt:** "Our Google Workspace backup keeps failing on Monday mornings. This has been happening for 3 weeks now."

**Context:** Google Workspace connector fails every Monday at 06:00 AM with rate limit errors. Backups succeed on other days. 6 failures over 3 weeks (Mon+Tue retries). API rate limiting during peak hours.

### Expected Output

```markdown
# Backup Failure Root Cause Analysis

**Connector:** Google Workspace (Gmail + Drive)
**Failure Time:** 2025-03-03T06:01:44Z (most recent)
**Investigation Time:** 2025-03-03T09:15:00Z
**Status:** ⚠️ Warning (intermittent failures)

---

## Root Cause Summary

| Field | Value |
|-------|-------|
| Root Cause | API Rate Limiting |
| Confidence | High |
| Recurrence | Chronic (6 occurrences over 3 weeks) |
| Backup Gap | 51.3 hours (worst case) |
| Risk Level | 🟡 Medium |
| Active Recovery | Yes — retry in progress |

## Root Cause Details

**Classification:** `api_limit` (High confidence)

The Google Workspace connector consistently fails on Monday mornings due
to API rate limiting from Google's servers. The backup schedule overlaps
with peak usage hours when Google enforces stricter rate limits.

> **Error:** API rate limit exceeded — 429 Too Many Requests
> **Exit Reason:** Throttled by Google API — retry limit reached
> **Warning:** Request quota 80% consumed before job termination

### Failure Pattern Analysis

| Date | Day | Time | Result |
|------|-----|------|--------|
| 2025-02-17 | Monday | 06:00 | ❌ Failed (429) |
| 2025-02-18 | Tuesday | 06:00 | ❌ Failed (retry, 429) |
| 2025-02-19 | Wednesday | 06:00 | ✅ Success |
| 2025-02-24 | Monday | 06:00 | ❌ Failed (429) |
| 2025-02-25 | Tuesday | 06:00 | ❌ Failed (retry, 429) |
| 2025-02-26 | Wednesday | 06:00 | ✅ Success |
| 2025-03-03 | Monday | 06:00 | ❌ Failed (429) |
| 2025-03-03 | Monday | 09:00 | ⏳ Retry in progress |

**Pattern:** Failures cluster on Monday mornings at 06:00, with Tuesday
retries also failing. Wednesday backups succeed, suggesting the rate
limit issue is timing-related, not configuration-related.

### Recurrence Classification

| Field | Value |
|-------|-------|
| Classification | Chronic |
| Total Occurrences | 6 |
| First Seen | 2025-02-17T06:01:12Z |
| Pattern | Every Monday 06:00 + Tuesday retry |
| Weeks Affected | 3 consecutive |

### Evidence

- 6 failures with HTTP 429 response codes
- All failures occur Monday 06:00-06:05 window
- Tuesday retries also hit rate limits
- Wednesday and later backups succeed
- No config changes or auth issues detected
- Google API quota dashboard shows spikes on Mondays

## Data Risk Assessment

| Metric | Value |
|--------|-------|
| Last Successful Backup | 2025-02-26T06:00:00Z (Wednesday) |
| Current Backup Gap | 51.3 hours (worst case before Wed recovery) |
| Risk Level | 🟡 Medium |
| Normal Backup Interval | ~24.0 hours |
| Typical Recovery | Wednesday backup succeeds |

While the Monday and Tuesday gaps are concerning, the pattern shows
reliable Wednesday recovery. Ongoing risk is moderate but should be
addressed to ensure Monday protection.

## Event Timeline (Last Cycle)

| Time | Event | Relevance |
|------|-------|-----------|
| 2025-02-26T06:00:00Z | Wednesday backup succeeded | ✅ Last good backup |
| 2025-03-03T06:01:44Z | Monday backup failed (429) | ❌ Rate limited |
| 2025-03-03T09:00:00Z | Retry job started | ⏳ In progress |

## Resolution Steps

### 🔴 Step 1: Reschedule Monday backup to off-peak hours
Move the Monday backup window from 06:00 to 22:00 (Sunday night) or
02:00 (Monday early morning) to avoid peak Google API usage hours.
This is the most effective single change to resolve the pattern.

### 🔴 Step 2: Stagger backup jobs across connectors
If multiple connectors are scheduled at 06:00, spread them across
different time windows. Avoid running Google Workspace backup
concurrently with other Google-dependent connectors.

### 🟡 Step 3: Reduce parallel operation count
Configure the Google Workspace connector to use fewer parallel API
connections. This reduces throughput but stays within rate limits
during peak periods.

### 🟡 Step 4: Review Google API quota allocation
Check the Google Admin Console for API quota settings. If the
organization has access to increased quotas, request a higher
allocation for the backup service account.

### 🟢 Step 5: Contact Google for rate limit increase
If backup volume legitimately requires higher throughput during peak
hours, contact Google Cloud support to request a rate limit increase
for the service account used by Keepit.

### 🔴 Step 6: Escalate chronic failure pattern
This failure has occurred 6 times over 3 consecutive weeks. Create a
tracking ticket and schedule a review of the backup architecture to
prevent ongoing Monday gaps.

## Post-Fix Verification Checklist

- [ ] **Backup schedule updated**
  - **How:** Confirm the new schedule in Keepit admin console
  - **Expected:** Monday backup window moved to off-peak hours

- [ ] **Next Monday backup succeeds**
  - **How:** Monitor the next Monday backup cycle after schedule change
  - **Expected:** Job completes without 429 rate limit errors

- [ ] **Sustained success over 3 Mondays**
  - **How:** Track Monday backup results for 3 consecutive weeks
  - **Expected:** Zero rate limit failures on Mondays

- [ ] **Backup gap eliminated**
  - **How:** Verify no gaps > 24h in snapshot history
  - **Expected:** Consistent daily snapshots with no Monday/Tuesday gaps
```

---

## Scenario 4: First-Time Connectivity Failure

**User prompt:** "Our Salesforce backup failed and I've never seen this error before."

**Context:** Salesforce connector experienced a first-time connectivity failure. Connector health is unhealthy. No prior similar failures. No config changes detected.

### Expected Output

```markdown
# Backup Failure Root Cause Analysis

**Connector:** Salesforce (CRM)
**Failure Time:** 2025-01-20T03:15:33Z
**Investigation Time:** 2025-01-20T08:00:00Z
**Status:** ❌ Unhealthy

---

## Root Cause Summary

| Field | Value |
|-------|-------|
| Root Cause | Connectivity Failure |
| Confidence | High |
| Recurrence | First occurrence |
| Backup Gap | 28.7 hours |
| Risk Level | 🟡 Medium |
| Active Recovery | No |

## Root Cause Details

**Classification:** `connectivity` (High confidence)

The Salesforce connector failed due to a network connectivity issue
preventing the backup service from reaching the Salesforce API endpoint.
This is the first occurrence of this type of failure for this connector.

> **Error:** Connection timeout after 120s — login.salesforce.com
> **Exit Reason:** Connection refused — unable to establish SSL handshake
> **Warning:** DNS resolution succeeded but TCP connection timed out

### Evidence

- Connection timeout error to Salesforce API endpoint
- SSL handshake failure indicates network-layer issue
- DNS resolution succeeded (not a DNS problem)
- No auth errors — credentials are likely still valid
- No config changes detected in the past 24 hours
- First occurrence — no historical pattern

## Data Risk Assessment

| Metric | Value |
|--------|-------|
| Last Successful Backup | 2025-01-19T03:15:00Z |
| Backup Gap | 28.7 hours (1.2 days) |
| Risk Level | 🟡 Medium |
| Normal Backup Interval | ~24.0 hours |

Data created or modified in Salesforce during the past 28.7 hours is
unprotected. Given this is a first-time failure, the gap is likely
to be resolved quickly once connectivity is restored.

## Correlation Analysis

| Check | Result |
|-------|--------|
| Config changes (24h window) | ✅ None detected |
| Auth events (24h window) | ✅ None detected |
| Other connector failures | ✅ None — isolated to Salesforce |
| Salesforce status page | ⚠️ Check status.salesforce.com |

No audit events were found correlated with this failure, suggesting
the cause is external (network infrastructure or Salesforce service).

## Event Timeline

| Time | Event | Relevance |
|------|-------|-----------|
| 2025-01-19T03:15:00Z | Last successful backup | ✅ Baseline |
| 2025-01-20T03:15:33Z | Backup failed — connection timeout | ❌ Target failure |
| 2025-01-20T03:15:35Z | Connector health → unhealthy | ⚠️ State change |

## Resolution Steps

### 🔴 Step 1: Verify network connectivity
Check that the Keepit service can reach login.salesforce.com and the
Salesforce API endpoints. Test DNS resolution, TCP connectivity on
port 443, and SSL/TLS handshake.

### 🔴 Step 2: Check Salesforce service status
Visit https://status.salesforce.com to verify whether Salesforce is
experiencing an outage or maintenance window. Check for any incidents
affecting the API or login services.

### 🔴 Step 3: Review firewall and proxy rules
Confirm that no recent firewall, proxy, or network changes are blocking
the connection to Salesforce. Check for:
- IP allowlist changes
- SSL inspection certificate issues
- Proxy authentication requirements
- Outbound port 443 access

### 🟡 Step 4: Retry the backup
If the connectivity issue was transient (e.g., Salesforce maintenance
window), trigger a manual backup to verify connectivity is restored.
Monitor the job until completion.

### 🟡 Step 5: Set up connectivity monitoring
Configure network monitoring for the Salesforce API endpoint to receive
early warning of future connectivity issues before they impact backups.

## Post-Fix Verification Checklist

- [ ] **Network connectivity restored**
  - **How:** Test connectivity to login.salesforce.com on port 443
  - **Expected:** TCP connection and SSL handshake succeed

- [ ] **Manual backup completes successfully**
  - **How:** Trigger a manual backup and monitor to completion
  - **Expected:** Job completes without connectivity errors

- [ ] **Connector health shows healthy**
  - **How:** Check connector health status in Keepit admin console
  - **Expected:** Health status is 'healthy' or 'connected'

- [ ] **Next scheduled backup succeeds**
  - **How:** Wait for the next scheduled backup window
  - **Expected:** Automated backup completes without errors
```

---

## Response Templates

### Quick Diagnosis Template

For simple, single-cause failures where the user needs a fast answer.

```markdown
## Quick Diagnosis

**Connector:** {connector_name}
**Failed:** {failure_time}
**Root Cause:** {failure_type} ({confidence} confidence)

**What happened:**
{one_sentence_description}

**Error:**
> {primary_error_message}

**Fix:**
{primary_resolution_step}

**Verify:**
Run a manual backup after applying the fix. Check that the job completes
without errors and the connector health returns to healthy.

**Backup Gap:** {gap_description} — Risk: {risk_icon} {risk_level}
```

**Example filled in:**

```markdown
## Quick Diagnosis

**Connector:** Exchange Online
**Failed:** 2025-01-15T08:00:12Z
**Root Cause:** auth_expired (High confidence)

**What happened:**
The OAuth token for the Microsoft 365 connector expired, causing a 401
authentication error.

**Error:**
> Token expired for Microsoft Graph API — 401 Unauthorized

**Fix:**
Re-authorize the Exchange Online connector in the Keepit admin console
to refresh the OAuth token.

**Verify:**
Run a manual backup after re-authorization. Check that the job completes
without errors and the connector health returns to healthy.

**Backup Gap:** 26.6 hours — Risk: 🟡 Medium
```

### Full RCA Report Template

For formal root cause analysis documentation.

```markdown
# Root Cause Analysis Report

## Incident Summary

| Field | Value |
|-------|-------|
| Incident ID | RCA-{YYYY}-{NNN} |
| Connector | {connector_name} ({connector_type}) |
| Failure Time | {failure_timestamp} |
| Detection Time | {detection_timestamp} |
| Resolution Time | {resolution_timestamp} |
| Time to Detect | {ttd} |
| Time to Resolve | {ttr} |
| Impact | {risk_level} — {gap_description} backup gap |

## Root Cause

**Classification:** {failure_type}
**Confidence:** {confidence}
**Recurrence:** {recurrence_classification} ({occurrence_count} occurrences)

{detailed_root_cause_description}

## Evidence

{numbered_list_of_evidence_items}

## Timeline

| Time | Event | Actor | Impact |
|------|-------|-------|--------|
| {events_in_chronological_order} |

## Correlated Changes

{config_changes_and_audit_events_if_any}

## Data Impact

| Metric | Value |
|--------|-------|
| Backup Gap | {gap_hours}h ({gap_description}) |
| Risk Level | {risk_icon} {risk_level} |
| Data at Risk | {data_at_risk_description} |
| Last Good Backup | {last_good_backup} |

## Resolution

### Steps Taken
{numbered_resolution_steps_with_details}

### Outcome
{description_of_resolution_outcome}

## Preventive Measures

{recommendations_to_prevent_recurrence}

## Verification

{completed_verification_checklist}
```

### Verification Checklist Template

Standalone verification checklist for post-fix validation.

```markdown
## Post-Fix Verification Checklist

**Connector:** {connector_name}
**Issue:** {failure_type} — {short_description}
**Fixed:** {fix_timestamp}
**Verified By:** {admin_name}

### Immediate Checks

- [ ] **Connector health is healthy**
  - **How:** Admin console → Connectors → {connector_name} → Status
  - **Expected:** Status shows "Healthy" or "Connected"
  - **Actual:** _______________

- [ ] **Manual backup succeeds**
  - **How:** Trigger manual backup, monitor until completion
  - **Expected:** Job completes with no errors, no 'failed' timestamp
  - **Actual:** _______________

### 24-Hour Checks

- [ ] **Next scheduled backup succeeds**
  - **How:** Check job history after next scheduled backup window
  - **Expected:** Automated backup completes successfully
  - **Actual:** _______________

- [ ] **Backup gap closing**
  - **How:** Check latest snapshot timestamp
  - **Expected:** New snapshot created within expected interval
  - **Actual:** _______________

### 72-Hour Checks

- [ ] **No recurrence of failure**
  - **How:** Review job history for the past 72 hours
  - **Expected:** Zero failures with the same error pattern
  - **Actual:** _______________

- [ ] **Connector consistently healthy**
  - **How:** Check connector health history over 72 hours
  - **Expected:** Health status remained "Healthy" throughout
  - **Actual:** _______________

### Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Backup Admin | _______________ | _______________ | _______________ |
| IT Manager | _______________ | _______________ | _______________ |
```

---

## Notes on Output Formatting

### Icon Usage

| Icon | Meaning | When to Use |
|------|---------|-------------|
| ✅ | Healthy / Good / Passed | Successful backups, passed checks, healthy status |
| ⚠️ | Warning / Degraded | Intermittent issues, warnings, partial failures |
| ❌ | Critical / Failed | Backup failures, unhealthy connectors, critical risk |
| 🔴 | High Priority | Steps requiring immediate action |
| 🟡 | Medium Priority | Steps to address within 24 hours |
| 🟢 | Low Priority | Steps for next maintenance window |
| ⏳ | In Progress | Active retry jobs, pending operations |

### Risk Level Thresholds

| Gap Duration | Risk Level | Icon | Recommended Response Time |
|-------------|------------|------|--------------------------|
| < 24 hours | Low | 🟢 | Standard (next business day) |
| 24-72 hours | Medium | 🟡 | Prioritized (within 24 hours) |
| 72-168 hours | High | 🔴 | Urgent (within 4 hours) |
| > 168 hours | Critical | ❌ | Emergency (immediate) |

### Confidence Level Criteria

| Confidence | Criteria | Typical Scenarios |
|-----------|---------|-------------------|
| High | 3+ matching indicators, clear error messages | Auth expired, explicit 429, connection timeout |
| Medium | 2 matching indicators, some ambiguity | Config change correlation, partial error messages |
| Low | 1 indicator or no clear match | Unknown errors, missing execsummary data |

### Recurrence Thresholds

| Count | Classification | Recommended Action |
|-------|---------------|-------------------|
| 1 | First | Investigate and resolve |
| 2-4 | Recurring | Establish pattern, prioritize fix, create ticket |
| 5+ | Chronic | Escalate to management, schedule dedicated investigation |
