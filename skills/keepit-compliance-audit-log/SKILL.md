---
name: keepit-compliance-audit-log
description: Comprehensive compliance audit log extractor and formatter for regulatory reporting and security investigations. Use when users ask to extract audit logs, generate compliance reports, create audit trails, investigate security events, document user actions, or prepare for regulatory audits. Supports GDPR, HIPAA, ISO 27001, NIS2, SOC 2, and other frameworks. Triggers on keywords like "audit log", "compliance report", "security investigation", "regulatory audit", "audit trail", "user activity", "GDPR report", "access log".
---

# Keepit Compliance Audit Log Extractor & Formatter

## Overview

This skill provides comprehensive audit log extraction, analysis, and formatting for compliance and security purposes. It retrieves Keepit audit logs, categorizes events, and formats them according to various regulatory frameworks for audits, investigations, and documentation.

**Primary Use Cases:**
- Regulatory compliance reporting (GDPR, HIPAA, ISO 27001, NIS2, SOC 2)
- Security incident investigation
- User activity auditing
- Access control verification
- Configuration change tracking
- Data protection documentation
- Internal audit support
- Forensic analysis

**Keywords**: audit log, compliance report, security investigation, regulatory audit, audit trail, user activity, GDPR, HIPAA, ISO 27001, access log, event log, security audit

## Data Boundaries

**This skill can only provide audit log evidence from the Keepit API.** A complete compliance report requires additional organizational context that must be supplied by the user's compliance team.

### What This Skill Provides (from Keepit API)

- Audit log events: who did what, when, from where
- Event categorization and risk assessment
- Temporal patterns and anomaly detection
- Framework-specific event mapping (GDPR articles, HIPAA sections, etc.)
- Pagination across the full audit log dataset

### What the Organization Must Provide

- **Organizational context:** Company name, DPO contact, legal entity details
- **Legal basis:** Why data is being processed (consent, legitimate interest, etc.)
- **Encryption details:** What encryption is used for data at rest and in transit
- **Training records:** Staff data protection training evidence
- **Policy documents:** Data protection policies, incident response plans
- **Data subject request records:** DSARs handled outside the Keepit platform
- **Risk assessments:** Organizational risk analysis and treatment plans

### Report Template Markers

When generating compliance reports, clearly distinguish data sources:

- Sections populated from API data should be labeled as such
- Sections requiring organizational input should use placeholder markers like `[ORGANIZATION TO PROVIDE: ...]`
- Never fabricate organizational context (encryption specs, DPO names, legal basis, training records)

### Pre-Audit Preparation Checklist

Before running a compliance report, the organization should gather:

1. **Compliance framework** and specific requirements (e.g., GDPR Articles 5, 15, 30, 32, 33)
2. **Audit period** and any specific focus areas
3. **Organizational details** for the report header (entity name, controller, processor)
4. **Data processing records** (Article 30 registers, if GDPR)
5. **Incident response documentation** for the period
6. **Previous audit findings** and remediation status

## Core Workflow

### Step 1: Define Audit Scope

First, clarify the audit requirements:

**Time Period:**
- Last 24 hours (P1D)
- Last week (P7D)
- Last 30 days (P30D)
- Last quarter (P90D)
- Custom period (ISO 8601 duration)
- Specific date range

**Compliance Framework:**
- GDPR (EU data protection)
- HIPAA (US healthcare)
- ISO 27001 (Information security)
- NIS2 (EU network/information security)
- SOC 2 (Service organization controls)
- General (non-specific framework)

**Analysis Focus:**
- All events (comprehensive audit)
- User actions (access and modifications)
- Configuration changes (system modifications)
- Security events (authentication, authorization)
- Data access (who accessed what)
- Administrative actions (privileged operations)

**Output Format:**
- Executive summary
- Detailed event listing
- Categorized by event type
- Timeline visualization
- Formatted for specific framework

### Step 2: Retrieve Audit Logs

Query audit log history for the specified period:

```python
# Get audit log history — single call returns all events in the period
audit_logs = get_audit_log_history(duration="P30D")
```

**Note:** The API returns all events for the specified duration in a single call. No pagination is needed.

```python
# The audit log contains these fields:
# Required:
# - time: ISO 8601 timestamp (when event occurred)
# - token: string (masked user identifier, first4***last4)
# - clientIP: string (sanitized IP address)
# - type: string (event type, e.g., "POST", "DELETE", "GET")
# - wasAllowed: boolean (whether the action was permitted)
# - succeeded: boolean (whether the action completed successfully)
# - metadata: array of parameter objects
#
# Optional:
# - action: string (specific action performed)
# - area: string (event category, e.g., "User events")
# - account: string (account GUID)
# - company: string (company name)
# - device: string (device identifier)
```

**ISO 8601 Duration Examples:**
- PT1H = 1 hour
- P1D = 1 day
- P7D = 7 days
- P30D = 30 days
- P90D = 90 days (quarter)
- P1Y = 1 year

**Note:** The `duration` parameter is required and specifies how far back to retrieve logs.

### Step 3: Parse and Categorize Events

Organize audit log events into meaningful categories:

#### Metadata Extraction

Each audit log event includes a `metadata` array of `{ parameter: { key, value } }` objects that provide structured context about the event. Always extract and use metadata for richer analysis:

```python
from audit_utils import extract_metadata

for event in audit_logs:
    meta = extract_metadata(event)
    # meta is a flat dict, e.g.:
    # { "connector_guid": "2gfd9w-2l3knw-s50ffl",
    #   "old_value": "P90D",
    #   "new_value": "P365D",
    #   "target_user": "user@company.com" }
    #
    # Metadata varies per event. Common keys may include:
    # - Resource identifiers (which connector, account, user)
    # - Configuration change details (old value → new value)
    # - Request parameters and context
```

**Display metadata in event details** when showing detailed event entries:

```markdown
**2025-10-22T14:35Z** | admin@co.com | Modified retention | ✅ Succeeded
- Connector: Microsoft 365 Backup (2gfd9w-2l3knw-s50ffl)
- Changed from: P90D → P365D
- *Source: metadata fields*
```

#### Event Categories

> **Note:** Event categories are inferred from the `action` string (optional), `area` field (optional), `method` (HTTP method), `allowed`/`succeeded` booleans, and `metadata` values. The API does not provide a category field directly.

**Authentication Events:**
- Login attempts (successful/failed)
- Logout events
- Password changes
- MFA activities
- Session management
- Token generation/revocation

**Authorization Events:**
- Permission grants/revocations
- Role assignments/changes
- Access denials
- Privilege escalations

**Data Access Events:**
- Backup data viewed
- Restore operations performed
- Search queries executed
- Export operations
- Download activities

**Configuration Events:**
- Connector created/modified/deleted
- Policy changes (retention, backup)
- Schedule modifications
- Settings updates
- Integration configurations

**Administrative Events:**
- User account management
- Organization settings
- Subscription changes
- API key management
- Audit log access (meta-audit)

**Security Events:**
- Failed authentication attempts
- Suspicious activities
- Access violations
- Rate limit hits
- Anomalous behaviors

### Step 4: Apply Compliance Framework

Format events according to regulatory requirements:

#### GDPR (General Data Protection Regulation)

**Focus areas:**
- Data subject access (who accessed personal data)
- Data processing activities (backup, restore, export)
- Data retention compliance
- Right to erasure tracking
- Data breach documentation
- Cross-border data transfers

**Required fields:**
- Timestamp (when)
- User identity (who)
- Action performed (what)
- Data category affected (personal data)
- Legal basis (consent, legitimate interest)
- Purpose of processing

**GDPR-specific elements:**
- Article 30 processing record
- Article 32 security measures
- Article 33 breach notification timeline
- Article 15 access request trail

#### HIPAA (Health Insurance Portability and Accountability Act)

**Focus areas:**
- PHI (Protected Health Information) access
- Administrative safeguards
- Physical safeguards (not applicable to SaaS)
- Technical safeguards (access controls)
- Breach notification requirements

**Required fields:**
- Date and time of access
- User accessing PHI
- Patient/data subject (if tracked)
- Type of access (view, modify, export)
- Access authorization
- Audit trail integrity

**HIPAA-specific elements:**
- § 164.308 administrative controls
- § 164.312 technical safeguards
- § 164.414 accounting of disclosures
- Minimum necessary rule compliance

#### ISO 27001 (Information Security Management)

**Focus areas:**
- Information security events
- Access control effectiveness
- Change management
- Incident management
- System monitoring
- Policy compliance

**Required fields:**
- Event classification (security level)
- Asset affected (information asset)
- Control reference (ISO control)
- Risk assessment linkage
- Corrective actions

**ISO 27001-specific elements:**
- Annex A controls mapping
- Risk treatment plan evidence
- Security incident log
- Change control records
- Access review documentation

#### NIS2 (Network and Information Security Directive)

**Focus areas:**
- Cybersecurity incidents
- Vulnerability management
- Supply chain security
- Incident notification timeline
- Security measures effectiveness

**Required fields:**
- Incident severity
- Affected services
- Notification timeline
- Containment measures
- Recovery actions

**NIS2-specific elements:**
- Article 23 incident reporting
- Essential vs. important entities
- Cross-border incident notification
- Supply chain risk management

#### SOC 2 (Service Organization Control 2)

**Focus areas:**
- Trust Services Criteria
- Security principle
- Availability principle
- Processing integrity
- Confidentiality
- Privacy

**Required fields:**
- Control testing evidence
- Segregation of duties
- Change management approval
- Monitoring and review
- Exception handling

**SOC 2-specific elements:**
- Control objectives mapping
- Common Criteria alignment
- Additional Criteria if applicable
- Type I vs. Type II evidence

### Step 5: Filter and Enrich Events

Enhance audit log data with additional context:

#### Filtering Options

**By token (masked user identifier):**
- Specific token pattern
- External vs. internal users (inferred from token format)

**By action:**
- Read operations
- Write operations
- Delete operations
- Administrative actions
- High-risk activities

**By resource:**
- Specific connector
- Backup data
- Configuration settings
- User accounts
- API endpoints

**By result:**
- Successful operations
- Failed operations
- Denied access
- Errors and exceptions

**By risk level:**
- High-risk events (privilege escalation, bulk export)
- Medium-risk events (config changes)
- Low-risk events (routine access)
- Informational events

#### Event Enrichment

**Add context:**
- Event significance explanation
- Compliance requirement mapping
- Risk level assessment
- Related events correlation
- Anomaly indicators

**User context:**
- Token-based user identification (note: tokens are masked)
- Previous activity patterns (by matching token values)
- Source IP address (from clientIP field; geo lookup possible but not provided by API)

**Timeline context:**
- Event sequence
- Duration between events
- Clustering identification
- Pattern recognition

### Step 6: Generate Compliance Report

Create formatted report based on framework and audience:

#### Report Structure

**1. Executive Summary**
- Audit period covered
- Framework/standard compliance
- Total events analyzed
- Key findings summary
- Compliance status
- Recommendations

**2. Audit Methodology**
- Scope definition
- Data sources
- Time period
- Filtering criteria
- Analysis approach
- Limitations

**3. Event Summary Statistics**
- Total events by category
- User activity breakdown
- Action type distribution
- Success vs. failure rates
- Geographic distribution
- Temporal patterns

**4. Detailed Event Log**
- Chronological or categorized listing
- Full event details
- Compliance annotations
- Risk assessments
- Supporting evidence

**5. Findings and Observations**
- Security concerns
- Policy violations
- Anomalous activities
- Access pattern analysis
- Configuration changes
- Administrative actions

**6. Compliance Assessment**
- Framework requirement mapping
- Control effectiveness
- Gaps identified
- Evidence of compliance
- Areas needing improvement

**7. Recommendations**
- Immediate actions
- Policy updates
- Process improvements
- Technical controls
- Monitoring enhancements

**8. Appendices**
- Full event listings
- User directories
- Technical details
- Glossary of terms
- Reference materials

### Step 7: Format for Intended Audience

Adapt report style to reader:

#### For Auditors (External/Internal)

**Emphasis:**
- Evidence completeness
- Control testing results
- Exception documentation
- Remediation tracking
- Attestation readiness

**Format:**
- Formal language
- Detailed methodology
- Complete event logs
- Control mappings
- Supporting documentation

#### For Management (Executive)

**Emphasis:**
- Compliance status
- Risk summary
- Business impact
- Resource requirements
- Strategic recommendations

**Format:**
- Executive summary first
- High-level metrics
- Visual dashboards
- Minimal technical detail
- Action-oriented

#### For Security Team (Technical)

**Emphasis:**
- Security events detail
- Threat indicators
- Anomaly analysis
- Technical recommendations
- Investigation support

**Format:**
- Technical language
- Detailed event analysis
- IOC identification
- Forensic timeline
- Remediation steps

#### For Compliance Officer

**Emphasis:**
- Regulatory adherence
- Policy compliance
- Documentation completeness
- Evidence management
- Audit trail integrity

**Format:**
- Framework-aligned
- Control verification
- Gap analysis
- Remediation tracking
- Certification support

## Output Formatting Guidelines

### Event Entry Format

**Standard Event Entry:**
```markdown
**[time]** | **[token]** | **[action]** | **[area]** | **wasAllowed: [bool]** / **succeeded: [bool]**

Details:
- IP Address: [clientIP]
- Type: [type]
- Area: [area]

Compliance Notes:
- Framework Requirement: [Specific requirement]
- Risk Level: [Low/Medium/High]
- Review Required: [Yes/No]
```

**Example:**
```markdown
**2025-10-22T14:35:00Z** | **admin@company.com** | **Modified backup retention** | **Microsoft 365 Connector** | **Success**

Details:
- IP Address: 203.0.113.42
- Changed retention from 7 years to 10 years
- Reason: GDPR compliance update

Compliance Notes:
- Framework Requirement: GDPR Article 5(1)(e) - Storage limitation
- Risk Level: Medium (affects data retention compliance)
- Review Required: Yes (verify business justification documented)
```

### Table Format for Event Summaries

```markdown
| Time | Token (User) | Action | Area | Allowed | Succeeded | Risk |
|------|-------------|--------|------|---------|-----------|------|
| 2025-10-22 14:35 UTC | adm...@company.com | Modified retention | Configuration | ✅ Yes | ✅ Yes | 🟡 Medium |
| 2025-10-22 14:30 UTC | usr...@company.com | Accessed backup | Data access | ✅ Yes | ✅ Yes | 🟢 Low |
| 2025-10-22 14:25 UTC | ext...@partner.com | Login attempt | User events | ❌ No | ❌ No | 🔴 High |
```

### Categorized Event Format

```markdown
## Authentication Events (24 events)

### Successful Logins (22)
- 2025-10-22 09:15 UTC: admin@company.com from 203.0.113.42
- 2025-10-22 10:30 UTC: user@company.com from 198.51.100.15
[...]

### Failed Login Attempts (2) ⚠️
- 2025-10-22 14:25 UTC: external@partner.com from 192.0.2.100
  - Reason: Invalid credentials
  - Action taken: Account locked after 3 attempts
  - Compliance note: NIST 800-53 AC-7 enforcement
```

### Timeline Visualization (Text-based)

```markdown
## Event Timeline (October 22, 2025)

00:00 ─────────────────────────────────── 24:00
      │    │    │         │    │      │
      │    │    │         │    │      └─ 18:00: Backup completion (routine)
      │    │    │         │    └──────── 14:35: Config change (admin)
      │    │    │         └────────────── 14:25: Failed login ⚠️
      │    │    └─────────────────────── 10:30: Data access (user)
      │    └───────────────────────────── 09:15: Admin login
      └─────────────────────────────────── 02:00: Backup job start

🔴 High Risk   🟡 Medium Risk   🟢 Low Risk   ⚪ Informational
```

### Risk Assessment Matrix

```markdown
## Risk Assessment Summary

| Risk Level | Count | % of Total | Examples |
|------------|-------|------------|----------|
| 🔴 High | 3 | 2.1% | Failed external access, Bulk export, Privilege escalation |
| 🟡 Medium | 18 | 12.5% | Config changes, Retention modifications, Role changes |
| 🟢 Low | 98 | 68.1% | Routine backups, Normal data access, Read operations |
| ⚪ Info | 25 | 17.4% | Login success, Logout, System events |

**Total Events:** 144
```

### Compliance Framework Mapping

```markdown
## GDPR Compliance Mapping

| GDPR Article | Requirement | Evidence | Status |
|--------------|-------------|----------|--------|
| Art. 5(1)(a) | Lawfulness, fairness, transparency | Access logs showing lawful processing | ✅ Met |
| Art. 5(1)(e) | Storage limitation | Retention policy logs | ✅ Met |
| Art. 15 | Right of access | Data subject access logs | ✅ Met |
| Art. 17 | Right to erasure | Deletion request logs | ⚠️ Review |
| Art. 30 | Records of processing | Complete audit trail | ✅ Met |
| Art. 32 | Security of processing | Security event logs | ✅ Met |
| Art. 33 | Breach notification | Incident response logs | ✅ Met |

**Overall Compliance Status:** Compliant (1 item under review)
```

## Advanced Analysis Techniques

### Pattern Recognition

#### Identify Anomalous Behavior

**Time-based anomalies:**
- Access during unusual hours (outside business hours)
- Activity on weekends/holidays
- Rapid succession of actions
- Extended session durations

**User-based anomalies:**
- Actions inconsistent with role
- Access to unusual resources
- Geographic impossibilities (location hopping)
- Sudden spike in activity

**Resource-based anomalies:**
- Unusual data export volumes
- Multiple failed access attempts
- Privilege escalation attempts
- Concurrent access from multiple locations

#### Detect Security Incidents

**Potential indicators:**
- Multiple failed authentication attempts
- Successful login after failures (potential breach)
- Unusual data access patterns
- Bulk operations outside normal business
- Configuration changes by unauthorized users
- Access from suspicious IP addresses/countries

### Correlation Analysis

#### Event Correlation

```python
# Example correlation patterns

# Pattern 1: Suspicious access sequence
1. Failed login attempts (multiple)
2. Successful login (finally succeeded)
3. Bulk data export (immediate suspicious action)
4. Logout (quick exit)

# Pattern 2: Privilege escalation
1. Normal user login
2. Role change to administrator
3. Configuration modifications
4. Role change back to normal

# Pattern 3: Data breach indicators
1. After-hours access
2. Multiple connector access
3. Large restore operations
4. Data export to external destination
```

### User Behavior Analytics

**Establish baselines:**
- Typical login times
- Normal access patterns
- Average session duration
- Usual resources accessed
- Standard action frequencies

**Detect deviations:**
- Significant variance from baseline
- New behaviors not previously seen
- Behaviors inconsistent with role
- Impossible travel scenarios

## Compliance Framework Templates

### GDPR Audit Report Template

```markdown
# GDPR Compliance Audit Report

**Organization:** [ORGANIZATION TO PROVIDE: Company name]
**Data Controller:** [ORGANIZATION TO PROVIDE: Controller name and contact]
**Data Processor:** Keepit ApS (Backup Service Provider)
**Audit Period:** [Start Date] to [End Date]
**Report Date:** [Report Date]
**Auditor:** [ORGANIZATION TO PROVIDE: Auditor name]

## Executive Summary

[FROM KEEPIT API: Event counts, risk levels, compliance mapping]
[ORGANIZATION TO PROVIDE: Overall compliance assessment context]

## Article 30: Records of Processing Activities

### Processing Activities Identified

1. **Backup Processing** (evidence from Keepit audit logs)
   - Purpose: [ORGANIZATION TO PROVIDE: Business justification]
   - Legal Basis: [ORGANIZATION TO PROVIDE: e.g., Legitimate interest Art. 6(1)(f)]
   - Data Categories: [ORGANIZATION TO PROVIDE]
   - Data Subjects: [ORGANIZATION TO PROVIDE]
   - Recipients: [ORGANIZATION TO PROVIDE]
   - Retention Period: [FROM KEEPIT API: connector backup_retention values]
   - Security Measures: [ORGANIZATION TO PROVIDE: encryption, access controls]

## Article 32: Security of Processing

### Technical Measures Evidence

[FROM KEEPIT API: Authentication events, access control events, security events]
[ORGANIZATION TO PROVIDE: Encryption details, network security measures]

## Article 15: Right of Access

### Data Subject Access Requests

[ORGANIZATION TO PROVIDE: DSAR records — Keepit API does not track DSARs]

## Article 33: Personal Data Breaches

### Breach Incidents

[FROM KEEPIT API: Security anomalies and failed access attempts detected]
[ORGANIZATION TO PROVIDE: Breach notification records, DPA communications]

## Recommendations

[List any compliance improvements needed based on API findings]
```

### HIPAA Audit Report Template

```markdown
# HIPAA Compliance Audit Report

**Covered Entity:** [ORGANIZATION TO PROVIDE: Entity name]
**Audit Period:** [Start Date] to [End Date]
**Report Date:** [Report Date]
**Auditor:** [ORGANIZATION TO PROVIDE: Auditor name]

## Executive Summary

[FROM KEEPIT API: Event counts, access patterns, security events]
[ORGANIZATION TO PROVIDE: Overall HIPAA compliance assessment]

## § 164.308 Administrative Safeguards

### (a)(1)(i) Security Management Process

[FROM KEEPIT API: Security events, anomaly detection results]

### (a)(2) Assigned Security Responsibility

[ORGANIZATION TO PROVIDE: Security officer designation — not tracked in Keepit]

### (a)(3) Workforce Security

[FROM KEEPIT API: User access logs]
[ORGANIZATION TO PROVIDE: Training records, sanctions policy]

### (a)(4) Information Access Management

[FROM KEEPIT API: Access control events, permission changes]

## § 164.312 Technical Safeguards

### (a)(1) Access Control

[FROM KEEPIT API: Authentication logs, session events]

### (d) Person or Entity Authentication

[FROM KEEPIT API: Authentication events, MFA indicators]

## § 164.414 Accounting of Disclosures

### Disclosure Log

[ORGANIZATION TO PROVIDE: PHI disclosure records — not tracked in Keepit audit logs]

## Findings

[FROM KEEPIT API: Security concerns identified from audit log analysis]

## Recommendations

[Corrective actions needed based on API findings and organizational context]
```

### ISO 27001 Audit Report Template

```markdown
# ISO 27001 Compliance Audit Report

**Organization:** [Company Name]
**ISMS Scope:** [Scope definition]
**Audit Period:** [Start Date] to [End Date]
**Report Date:** [Report Date]
**Lead Auditor:** [Auditor Name]

## Executive Summary

[Overview of ISMS effectiveness]

## Annex A Control Assessment

### A.9 Access Control

#### A.9.2.1 User Registration and De-registration

[Evidence from user management logs]

#### A.9.2.2 User Access Provisioning

[Evidence from access grant/revoke logs]

#### A.9.4.1 Information Access Restriction

[Evidence from access denial logs]

### A.12 Operations Security

#### A.12.4.1 Event Logging

[Evidence of comprehensive logging]

#### A.12.4.2 Protection of Log Information

[Evidence of log integrity measures]

#### A.12.4.3 Administrator and Operator Logs

[Evidence of privileged activity logging]

### A.18 Compliance

#### A.18.1.1 Identification of Applicable Legislation

[Compliance framework mapping]

## Non-conformities

[List any control failures]

## Opportunities for Improvement

[Suggestions for enhancement]
```

## Cross-Skill Investigation Workflows

### Config Change → Health Impact Check

When audit logs reveal a configuration change, verify its impact on connector health:

```python
# 1. Audit log shows config change for a connector
affected_guid = "2gfd9w-2l3knw-s50ffl"
change_time = "2026-02-10T14:00:00Z"

# 2. Check connector health after the change
health = get_connector_health(guid=affected_guid)

# 3. Get job history to see if backups still work
jobs = get_job_history(guid=affected_guid, duration="P7D")
# Filter for jobs after change_time — are they succeeding or failing?

# 4. Get latest snapshot to confirm data protection
latest = get_latest_snapshot(guid=affected_guid)
```

### Security Event → Comprehensive Investigation

When audit logs show suspicious activity, cross-reference with other data:

```python
# 1. Audit logs detect suspicious failed auth pattern
suspicious_token = "adm...@company.com"

# 2. Check account health — has anything been tampered with?
account_info = get_my_account_info()
connectors = get_cloud_connectors(connectorType="cloud")

# 3. For each connector, verify health and recent snapshots
for connector in connectors:
    health = get_connector_health(guid=connector['guid'])
    latest = get_latest_snapshot(guid=connector['guid'])
    # Flag any connectors that became unhealthy around the suspicious event time
```

### Compliance Audit → Complete Evidence Package

When preparing a full compliance report, gather evidence from all skills:

```python
# 1. Audit logs for the compliance period
audit_logs = get_audit_log_history(duration="P90D")
# Returns all events for the period in a single call

# 2. Account and connector health as of report date
account = get_my_account_info()
connectors = get_cloud_connectors(connectorType="cloud")

# 3. Backup continuity evidence per connector
for connector in connectors:
    snapshots = get_snapshot_range(guid=connector['guid'], timespan="P90D", count=99)
    # Proves continuous data protection throughout the audit period

# 4. Job history for reliability evidence
for connector in connectors:
    jobs = get_job_history(guid=connector['guid'], duration="P90D")
    # Calculate success rates as compliance evidence
```

## Integration with Investigations

### Security Incident Investigation

**When audit logs support incident response:**

1. **Establish Timeline**
   - First indication of compromise
   - Progression of attacker actions
   - Duration of unauthorized access
   - Containment and resolution

2. **Identify Affected Resources**
   - Systems accessed
   - Data viewed or exfiltrated
   - Configuration changes made
   - Users impacted

3. **Determine Attribution**
   - User accounts involved
   - IP addresses and locations
   - Access methods
   - Privilege levels used

4. **Assess Impact**
   - Scope of data exposure
   - Regulatory notification requirements
   - Business disruption
   - Recovery actions needed

5. **Document Evidence**
   - Preserve audit logs
   - Create incident timeline
   - Support forensic analysis
   - Enable legal proceedings if needed

### Forensic Analysis Support

**Audit logs as forensic evidence:**

- **Chain of custody:** Document log retrieval and handling
- **Integrity verification:** Ensure logs haven't been tampered
- **Completeness:** Demonstrate continuous logging
- **Time synchronization:** Verify timestamp accuracy
- **Attribution:** Link events to specific users/systems
- **Correlation:** Connect related events across systems

## Error Handling and Edge Cases

### Insufficient Data

If audit log data is limited or incomplete:

```markdown
⚠️ **Data Completeness Notice**

**Issue:** Audit log data is incomplete for the requested period.

**Details:**
- Requested period: [Date range]
- Available data: [Available range]
- Gap identified: [Gap details]

**Possible reasons:**
- Audit logging recently enabled
- Log retention period exceeded
- Data archival in progress
- System configuration change

**Recommendations:**
1. Adjust audit period to available data range
2. Check Keepit settings for audit log retention
3. Contact Keepit support if data should be available
4. Document the limitation in compliance report

**Impact on compliance:**
[Describe how this affects compliance reporting]
```

### No Events in Period

If no audit events found:

```markdown
ℹ️ **No Audit Events Found**

**Period analyzed:** [Date range]
**Framework:** [Framework]

**Interpretation:**
- System may have been inactive during this period
- Filters may be too restrictive
- This may be normal for low-activity periods

**Verification steps:**
1. Confirm Keepit account was active during period
2. Check if any users were accessing the system
3. Verify audit logging is enabled
4. Review filter criteria

**For compliance purposes:**
Document this as evidence of no activity requiring audit trail during this period.
```

### Suspicious Activity Detected

If anomalies are identified:

```markdown
🔴 **SECURITY ALERT: Suspicious Activity Detected**

**Alert Level:** [High/Critical]
**Detection Time:** [Timestamp]
**Event Count:** [Number]

**Suspicious Pattern Identified:**
[Description of the suspicious behavior]

**Affected Resources:**
- [List of resources]

**Recommended Immediate Actions:**
1. Review detailed event listing below
2. Verify if activity was authorized
3. Contact affected users if needed
4. Escalate to security team
5. Preserve evidence for investigation
6. Consider temporary access restrictions

**Events Detail:**
[Detailed listing of suspicious events]

**Next Steps:**
- Conduct full security investigation
- Document findings
- Implement corrective controls
- Update monitoring rules
```

## Best Practices

### Regular Audit Log Review

**Frequency recommendations:**

- **Daily:** For high-security environments
  - Review authentication failures
  - Check administrative actions
  - Monitor high-risk operations

- **Weekly:** For standard environments
  - Review all administrative changes
  - Check user access patterns
  - Verify policy compliance

- **Monthly:** For comprehensive audits
  - Full compliance framework review
  - Trend analysis
  - Management reporting
  - Documentation updates

- **Quarterly:** For regulatory reporting
  - Formal compliance assessment
  - External audit preparation
  - Policy effectiveness review
  - Risk assessment updates

### Audit Log Retention

**Recommended retention periods:**

- **GDPR:** Minimum 1 year, recommended 2-3 years
- **HIPAA:** Minimum 6 years
- **ISO 27001:** Based on risk assessment, typically 1-3 years
- **NIS2:** Minimum 5 years for incident logs
- **SOC 2:** Type II requires 12+ months

**Storage considerations:**
- Ensure logs are immutable (cannot be altered)
- Maintain offline backups
- Document retention policy
- Implement automatic archival
- Plan for regulatory changes

### Documentation Standards

**Every audit report should include:**

1. **Clear scope definition**
   - What was audited
   - Time period covered
   - Framework/standard applied
   - Limitations or exclusions

2. **Methodology description**
   - Data sources used
   - Analysis approach
   - Tools employed
   - Validation methods

3. **Findings documentation**
   - Observations with evidence
   - Risk assessments
   - Compliance status
   - Gap analysis

4. **Recommendations**
   - Prioritized actions
   - Implementation guidance
   - Resource requirements
   - Timeline suggestions

5. **Attestation**
   - Who performed audit
   - When completed
   - Independence statement
   - Quality assurance

## Common Use Cases and Examples

### Use Case 1: Quarterly GDPR Compliance Report

**Request:** "Generate GDPR compliance report for Q3 2025"

**Process:**
1. Retrieve logs for P90D (July-September 2025)
2. Filter for GDPR-relevant events
3. Map to GDPR articles
4. Assess compliance status
5. Generate formatted report

**Output includes:**
- Article 30 processing records
- Article 32 security measures evidence
- Data subject request handling
- Breach notification compliance
- Recommendations for improvement

### Use Case 2: Failed Login Investigation

**Request:** "Investigate failed login attempts this week"

**Process:**
1. Retrieve logs for P7D
2. Filter for authentication failures
3. Analyze patterns (brute force, credential stuffing)
4. Identify source IPs and accounts
5. Assess security risk
6. Recommend actions

**Output includes:**
- Failed attempt timeline
- IP address analysis
- Account targeting patterns
- Risk assessment
- Remediation steps

### Use Case 3: User Activity Audit

**Request:** "Show me all actions by admin@company.com last month"

**Process:**
1. Retrieve logs for P30D
2. Filter by specific user
3. Categorize actions
4. Assess appropriateness
5. Document findings

**Output includes:**
- Chronological action log
- Resource access summary
- Privilege usage
- Policy compliance check
- Observations

### Use Case 4: Configuration Change Review

**Request:** "List all configuration changes made this year"

**Process:**
1. Retrieve logs for P365D
2. Filter for config modification events
3. Categorize by change type
4. Identify change makers
5. Assess change management compliance

**Output includes:**
- Change log with details
- Authorization verification
- Impact assessment
- Change control compliance
- Recommendations

### Use Case 5: Pre-Audit Preparation

**Request:** "Prepare audit package for ISO 27001 certification"

**Process:**
1. Retrieve comprehensive logs (P365D or more)
2. Map to ISO 27001 Annex A controls
3. Generate evidence documentation
4. Identify gaps
5. Create audit-ready package

**Output includes:**
- Control-by-control evidence
- Gap analysis
- Remediation plan
- Supporting documentation
- Certification readiness assessment

## Success Criteria

A successful compliance audit log report provides:

✅ **Complete event coverage** for the requested period  
✅ **Clear categorization** of events by type and risk  
✅ **Framework alignment** with specific regulatory requirements  
✅ **Evidence documentation** suitable for auditors  
✅ **Actionable insights** for compliance improvement  
✅ **Professional formatting** appropriate for stakeholders  
✅ **Audit trail integrity** with timestamps and attribution  
✅ **Risk assessment** for events and patterns  
✅ **Recommendations** for remediation and prevention  

The output should enable compliance officers and auditors to quickly assess adherence to regulatory requirements and identify any concerns needing attention.
