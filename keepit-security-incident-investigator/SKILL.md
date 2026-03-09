---
name: keepit-security-incident-investigator
description: Security incident investigation and threat detection for Keepit backup environments. Use when users ask about security incidents, suspicious activity, unauthorized access, failed login patterns, data exfiltration, or threat investigation. Triggers on keywords like "security incident", "suspicious activity", "unauthorized access", "failed logins", "threat investigation", "data exfiltration", "breach investigation".
---

# Keepit Security Incident Investigator

## Overview

The Security Incident Investigator skill provides comprehensive threat detection, evidence correlation, and incident severity scoring for Keepit backup environments. Designed for CISOs, Security Analysts, and SOC teams, this skill automates the investigation workflow by analyzing audit logs, correlating job activity, detecting attack patterns, and generating actionable investigation reports.

This skill transforms raw Keepit telemetry into structured security intelligence — identifying credential compromise, data exfiltration attempts, configuration tampering, and insider threat indicators across backup infrastructure.

### When to Use This Skill

- A user reports suspicious activity in their Keepit environment
- Security team needs to investigate failed login patterns or unauthorized access
- SOC analysts need to correlate audit events with backup job anomalies
- CISO requires an incident severity assessment with evidence timeline
- Compliance team needs forensic-grade investigation reports
- Proactive threat hunting across backup infrastructure

### Target Persona

- **CISO** — Executive-level incident summaries with business impact
- **Security Analyst** — Detailed evidence timelines with IOC identification
- **SOC Team** — Pattern detection results with severity scoring and triage guidance

---

## Core Workflow

### Step 1: Scope the Investigation

Define the investigation parameters before gathering evidence. Establish the time window, affected connectors, and incident type based on user input or detected indicators.

```python
# Define investigation scope
# Default to 7-day lookback for incident investigations
# Expand to 30 days if looking for slow-burn attack patterns
investigation_duration = "P7D"   # ISO 8601 duration for standard investigation
extended_duration = "P30D"       # Extended lookback for persistent threats

# Get account context
account_info = get_my_account_info()

# Retrieve all connectors to establish scope
connectors = get_cloud_connectors(connectorType="cloud")

# Determine incident type from user query:
# - "failed logins"       -> authentication_attack
# - "data export"         -> data_exfiltration
# - "config changes"      -> config_tampering
# - "suspicious activity" -> general_investigation
# - "ransomware"          -> ransomware_precursor
```

**Scoping guidelines:**
- Authentication attacks: Start with P7D, expand if brute force is slow
- Data exfiltration: Use P14D to capture preparation and execution phases
- Config tampering: Use P30D to detect gradual changes
- General investigation: Start P7D, expand based on initial findings
- Ransomware precursor: Use P30D for full kill-chain reconstruction

### Step 2: Gather Audit Log Evidence

Retrieve audit events using paginated calls. Collect all available events within the investigation window for comprehensive analysis.

```python
# Retrieve all audit events for the investigation window (single call, no pagination needed)
all_audit_events = get_audit_log_history(duration=investigation_duration)

# Categorize events by type for targeted analysis
# Audit log entries have: type, area (optional), action (optional), clientIP, wasAllowed, succeeded
# Use 'area' field and 'type'/'action' patterns to categorize
auth_events = [e for e in all_audit_events if e.get('area', '').lower() in ('user events', 'authentication')]
config_events = [e for e in all_audit_events if e.get('type', '') in ('POST', 'PUT', 'DELETE') and e.get('area', '').lower() in ('configuration', 'settings')]
job_events = [e for e in all_audit_events if e.get('area', '').lower() in ('job', 'restore', 'export')]
admin_events = [e for e in all_audit_events if e.get('area', '').lower() == 'administration']
```

**Evidence collection notes:**
- The API returns all events for the specified duration in a single call
- Preserve raw event data for forensic record
- Note any gaps in audit log coverage (may indicate log tampering)
- Record total event count per category for baseline comparison

### Step 3: Analyze Authentication Patterns

Detect credential compromise by analyzing failed-to-success authentication sequences, brute force indicators, and anomalous login patterns.

```python
# Extract authentication events and group by token
from collections import defaultdict

auth_by_token = defaultdict(list)
for event in auth_events:
    # Audit logs use 'token' (masked: first4***last4), not 'tokenName'
    token = event.get('token', 'unknown')
    auth_by_token[token].append(event)

# Detect failed -> success sequences (credential compromise indicator)
# Pattern: Multiple failures followed by success within short window
for token, events in auth_by_token.items():
    sorted_events = sorted(events, key=lambda e: e['time'])
    failure_streak = 0
    for event in sorted_events:
        # Audit logs use 'succeeded' (string/bool) and 'wasAllowed' (string/bool), not 'result'
        succeeded = str(event.get('succeeded', '')).lower() in ('true', '1', 'yes')
        if not succeeded:
            failure_streak += 1
        elif succeeded and failure_streak >= 3:
            # ALERT: Possible credential compromise
            # failure_streak failures followed by success
            record_finding(
                pattern="credential_compromise",
                token=token,
                failure_count=failure_streak,
                success_event=event
            )
            failure_streak = 0
        else:
            failure_streak = 0

# Brute force detection thresholds:
# - 5+ failures in 10 minutes  -> brute_force
# - 10+ failures in 1 hour     -> distributed_brute_force
# - 3+ failures then success   -> credential_compromise
# - Failures across 3+ tokens  -> credential_stuffing
```

### Step 4: Correlate with Job Activity

Cross-reference suspicious authentication or audit events with backup job history. Restore and export jobs near suspicious events are high-priority indicators.

```python
# For each connector, retrieve job history
all_jobs = []
for connector in connectors:
    try:
        jobs = get_job_history(
            guid=connector['guid'],
            duration=investigation_duration
        )
        for job in jobs:
            job['connector_name'] = connector.get('name', 'Unknown')
            job['connector_guid'] = connector['guid']
        all_jobs.extend(jobs)
    except Exception:
        # Record connector access failure — may itself be suspicious
        pass

# Flag high-risk job types near suspicious events
# Job type values: 'backup', 'restore', 'srestore', 'pstrestore', 'zipdownload'
high_risk_job_types = ['restore', 'srestore', 'pstrestore', 'zipdownload']
suspicious_jobs = [
    j for j in all_jobs
    if j.get('type') in high_risk_job_types
]

# Correlate: jobs occurring within 1 hour of suspicious auth events
for job in suspicious_jobs:
    job_time = parse_iso_timestamp(job['start'])
    for auth_finding in auth_findings:
        auth_time = parse_iso_timestamp(auth_finding['timestamp'])
        if abs((job_time - auth_time).total_seconds()) < 3600:
            # ALERT: High-risk job correlated with suspicious auth
            record_correlation(
                job=job,
                auth_finding=auth_finding,
                time_delta_seconds=abs((job_time - auth_time).total_seconds())
            )
```

### Step 5: Assess Connector Impact

Evaluate backup integrity for affected connectors. Compromised backups may indicate data destruction or tampering as part of a ransomware attack chain.

```python
# Check health and snapshot integrity for affected connectors
impact_assessment = []
for connector in affected_connectors:
    health = get_connector_health(guid=connector['guid'])
    snapshot = get_latest_snapshot(guid=connector['guid'])

    status = "unknown"
    # get_connector_health returns {"healthStatus": "healthy"|"unhealthy"|"critical"|"unknown"}
    # get_latest_snapshot returns {"tstamp": ..., "type": "p"|"c", "size": ..., "account": ...} or null
    health_state = health.get('health', 'unknown') if health else 'unknown'
    if health_state == 'healthy':
        if snapshot and snapshot.get('type') == 'c':
            status = "intact"        # Backup appears uncompromised
        else:
            status = "degraded"      # Backup may be incomplete
    else:
        status = "compromised"       # Backup health degraded — investigate

    impact_assessment.append({
        'connector': connector['name'],
        'guid': connector['guid'],
        'health_status': health_state,
        'last_snapshot': snapshot.get('tstamp', 'None') if snapshot else 'None',
        'assessment': status
    })

# Impact severity:
# - "compromised"  -> 🔴 Critical: backup integrity at risk
# - "degraded"     -> ⚠️ Warning: partial backup, investigate further
# - "intact"       -> ✅ Healthy: backup verified intact
# - "unknown"      -> ⚠️ Warning: unable to assess, manual check needed
```

### Step 6: Detect Attack Patterns

Run comprehensive attack pattern detection across all collected evidence. Each detector returns structured findings with confidence scores.

```python
# Run all pattern detectors
auth_attacks = detect_auth_attack_pattern(auth_events)
exfil_indicators = detect_data_exfiltration_pattern(all_audit_events, all_jobs)
config_tampering = detect_config_tampering(config_events, connectors)
off_hours_anomalies = detect_off_hours_anomalies(all_audit_events, baseline)
suspicious_tokens = identify_suspicious_tokens(all_audit_events)

# Aggregate all findings
all_findings = {
    'auth_attacks': auth_attacks,
    'exfiltration_indicators': exfil_indicators,
    'config_tampering': config_tampering,
    'off_hours_anomalies': off_hours_anomalies,
    'suspicious_tokens': suspicious_tokens,
    'affected_connectors': impact_assessment,
    'total_events_analyzed': len(all_audit_events),
    'investigation_window': investigation_duration
}
```

**Attack pattern categories:**

| Pattern | Indicators | Severity Boost |
|---------|-----------|---------------|
| Brute Force | 5+ failures in 10 min | +20 |
| Credential Compromise | Failed -> success sequence | +30 |
| Credential Stuffing | Failures across multiple tokens | +25 |
| Data Exfiltration | Export/restore after suspicious auth | +40 |
| Config Tampering | Retention/settings changes | +25 |
| Off-Hours Access | Activity outside business hours | +15 |
| Privilege Escalation | Admin operations from new tokens | +35 |

### Step 7: Score Incident Severity

Calculate a composite severity score from all findings. The score determines incident classification and recommended response urgency.

```python
# Composite severity scoring
severity_result = score_incident_severity(all_findings)

# Scoring methodology:
# Base score starts at 0
# Each finding adds points based on pattern type and confidence
# Multipliers applied for:
#   - Multiple pattern types detected (1.5x)
#   - Off-hours timing (1.3x)
#   - Data export/restore involved (1.5x)
#   - Multiple connectors affected (1.2x per additional connector)

# Severity thresholds:
# 0-19   -> 🟢 Low       — Monitor, no immediate action
# 20-49  -> 🟡 Medium    — Investigate within 24 hours
# 50-79  -> 🔴 High      — Investigate immediately, notify security lead
# 80-100 -> ❌ Critical   — Activate incident response, containment required

# severity_result contains:
# {
#     'severity': 'critical',
#     'score': 87,
#     'icon': '❌',
#     'factors': ['credential_compromise', 'data_exfiltration', 'off_hours'],
#     'recommendations': [
#         'Immediately revoke compromised API tokens',
#         'Verify backup integrity for affected connectors',
#         'Review export/restore job outputs for data loss',
#         'Enable enhanced audit logging',
#         'Notify security leadership and legal'
#     ]
# }
```

### Step 8: Generate Investigation Report

Compile all findings into a structured investigation report with timeline, evidence, severity assessment, and actionable recommendations.

```python
# Report structure:
# 1. Investigation Summary (severity, scope, time window)
# 2. Evidence Timeline (chronological events with annotations)
# 3. Attack Pattern Analysis (detected patterns with evidence)
# 4. Affected Assets (connectors, tokens, data scope)
# 5. IOC Summary (indicators of compromise)
# 6. Severity Assessment (score breakdown)
# 7. Recommendations (prioritized response actions)
# 8. Next Steps (follow-up investigation tasks)

ioc_summary = generate_ioc_summary(all_findings)
timeline = reconstruct_incident_timeline(all_audit_events, all_jobs, impact_assessment)
```

---

## Output Formatting Guidelines

### Investigation Summary Header

```
## Security Investigation Report

**Investigation ID:** INV-2026-0217-001
**Severity:** ❌ Critical (Score: 87/100)
**Time Window:** 2026-02-10 to 2026-02-17
**Total Events Analyzed:** 1,247
**Patterns Detected:** 3 (Credential Compromise, Data Exfiltration, Off-Hours Anomaly)
```

### Evidence Timeline Format

```
### Evidence Timeline

| Time (UTC) | Source | Event | Actor | Severity | Details |
|------------|--------|-------|-------|----------|---------|
| 2026-02-14 02:14 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:15 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:15 | Audit | Auth Failure | api-token-backup-svc | ⚠️ | Failed authentication attempt |
| 2026-02-14 02:16 | Audit | Auth Success | api-token-backup-svc | 🔴 | Success after 3 failures |
| 2026-02-14 02:22 | Job | Export Started | api-token-backup-svc | 🔴 | Exchange connector export |
| 2026-02-14 02:35 | Job | Export Complete | api-token-backup-svc | 🔴 | 2.3 GB exported |
```

### Severity Badge Format

- ❌ **Critical** (80-100) — Immediate incident response required
- 🔴 **High** (50-79) — Investigate immediately, escalate
- 🟡 **Medium** (20-49) — Investigate within 24 hours
- 🟢 **Low** (0-19) — Monitor, document for baseline

### IOC Summary Format

```
### Indicators of Compromise (IOCs)

**Suspicious Tokens:**
- `api-token-backup-svc` — 12 failed auths, off-hours activity, export operations
- `admin-token-legacy` — Config changes during investigation window

**Suspicious Activity Windows:**
- 2026-02-14 02:00-03:00 UTC — Concentrated failed auth + export
- 2026-02-15 23:30-00:15 UTC — Off-hours config changes

**Affected Connectors:**
- Exchange Online (guid: abc-123) — Export target, backup intact ✅
- SharePoint (guid: def-456) — Config modified, backup degraded ⚠️
```

---

## Advanced Features

### Multi-Phase Attack Detection

The skill detects multi-phase attacks by correlating events across time:

1. **Reconnaissance Phase** — Unusual list/enumerate API calls, multiple connector queries
2. **Initial Access** — Authentication failures transitioning to success
3. **Lateral Movement** — Single token accessing multiple connectors in sequence
4. **Exfiltration** — Export/restore/download operations from compromised session
5. **Cover Tracks** — Configuration changes, log gaps, retention modifications

```python
# Multi-phase detection chains events by token and temporal proximity
# Phase detection windows:
# - Recon -> Access:    0-24 hours
# - Access -> Movement: 0-4 hours
# - Movement -> Exfil:  0-2 hours
# - Exfil -> Cover:     0-12 hours
```

### Behavioral Baseline Comparison

The skill establishes normal activity baselines to detect anomalies:

```python
# Generate baseline from historical audit events
baseline = generate_off_hours_baseline(all_audit_events)
# baseline = {
#     'hourly_distribution': {0: 2, 1: 0, ..., 9: 45, 10: 67, ...},
#     'business_hours': (8, 18),       # Detected business hours range
#     'peak_hour': 14,                  # Most active hour
#     'avg_daily_events': 127,          # Average events per day
#     'weekend_activity_ratio': 0.12    # Weekend vs weekday ratio
# }

# Flag events deviating from baseline
anomalies = detect_off_hours_anomalies(all_audit_events, baseline)
```

### Token Risk Profiling

Each API token receives a risk profile based on activity patterns:

```python
# Token risk factors:
# - failure_rate > 20%           -> +15 risk points
# - off_hours_ratio > 50%        -> +20 risk points
# - sensitive_ops (export/config) -> +25 risk points
# - multi_connector_access        -> +10 risk points
# - new_token (first seen < 7d)  -> +10 risk points
```

---

## Error Handling

### API Failures During Investigation

```python
# Always wrap API calls in try/except to preserve partial results
try:
    audit_logs = get_audit_log_history(duration="P7D")
except Exception as e:
    # Record the failure — API inaccessibility may itself be an IOC
    investigation_errors.append({
        'api': 'get_audit_log_history',
        'error': str(e),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'impact': 'Audit log evidence unavailable — investigation incomplete'
    })
    audit_logs = []
```

### Incomplete Evidence Handling

- If audit logs are unavailable, note the gap and proceed with available job data
- If connector health checks fail, mark connector as "assessment unavailable"
- If job history is missing, flag as potential evidence gap
- Always report investigation completeness percentage in the final report

### Common Error Scenarios

| Error | Impact | Mitigation |
|-------|--------|------------|
| Audit API timeout | Missing events | Retry with smaller page size, note gap |
| Connector unreachable | No health data | Mark as "unknown", flag for manual check |
| Job history empty | Missing correlation | Note absence, rely on audit logs only |
| Token expired | Partial data | Report auth failure, recommend token renewal |

---

## Best Practices

### Investigation Best Practices

1. **Preserve evidence** — Never modify audit logs or job history during investigation
2. **Start broad, narrow down** — Begin with full time window, then focus on anomalies
3. **Correlate across sources** — Always cross-reference audit logs with job history
4. **Document assumptions** — State what the investigation does and does not cover
5. **Recommend containment** — Prioritize stopping active threats over root cause analysis
6. **Chain of custody** — Note all data sources and retrieval timestamps
7. **False positive awareness** — Legitimate admin activity can trigger patterns; context matters

### Severity Calibration

- Do not over-classify. A single failed login is not a security incident
- Multiple pattern types detected together significantly increase severity
- Off-hours activity alone is 🟡 Medium unless combined with other indicators
- Any data exfiltration indicator is automatically 🔴 High minimum
- Config tampering targeting retention policies is automatically 🔴 High minimum

### Report Quality

- Always include the raw event count and investigation window
- Provide specific timestamps, not just date ranges
- Name affected tokens and connectors explicitly
- Include both what was found AND what was checked and found clean
- End with actionable, prioritized recommendations

---

## Common User Requests

### "Check for suspicious activity in the last week"

Run a general investigation with P7D window. Analyze all pattern types. Report findings or confirm clean status.

### "Investigate failed login attempts"

Focus on authentication events. Group by token, detect brute force patterns. Report failure rates, timing, and any subsequent success events.

### "Has anyone exported data recently?"

Query job history for Export/Restore/ZipDownload types. Cross-reference with audit events to verify authorization. Flag any exports associated with suspicious auth patterns.

### "Check if our backup configs have been tampered with"

Analyze configuration change events. Compare current connector settings against recent changes. Flag changes to retention policies, schedules, or connector parameters.

### "We think an API token was compromised — investigate"

Targeted investigation on specific token. Pull all audit events for that token. Analyze timing, operations, failure rates. Check for export/restore activity. Assess scope of potential compromise.

### "Run a full security assessment"

Comprehensive investigation across all pattern types. Extended P30D window. Full severity scoring with all detectors enabled. Generate complete investigation report with IOC summary.

---

## Cross-Skill Investigation Workflows

### Security + Compliance Audit

Combine security findings with compliance audit trail:
1. Security skill detects suspicious auth pattern
2. Compliance skill provides full audit trail for affected tokens
3. Together: complete forensic picture for regulators

### Security + Account Health

Correlate security indicators with infrastructure health:
1. Security skill detects config tampering indicators
2. Account health skill confirms connector degradation timeline
3. Together: determine if health issues are attack-caused or operational

### Security + Backup Verification

Validate backup integrity after security incident:
1. Security skill identifies affected connectors and time window
2. Backup verification skill checks snapshot completeness and consistency
3. Together: confirm whether backup data was compromised or preserved

---

## Skill Integration Points

### Input from Other Skills

- **Account Health** provides connector status context for impact assessment
- **Compliance Audit** provides extended audit trails for deep investigation
- **Backup Verification** provides snapshot integrity data

### Output to Other Skills

- **IOC List** — Suspicious tokens and time windows for targeted audit queries
- **Affected Connectors** — Connector GUIDs for health verification
- **Severity Score** — Investigation urgency for prioritization dashboards

---

## Technical Notes

### MCP Functions Used

| Function | Purpose | Typical Parameters |
|----------|---------|-------------------|
| `get_my_account_info()` | Account context | None |
| `get_audit_log_history(duration)` | Audit evidence | duration="P7D" |
| `get_cloud_connectors(connectorType="cloud")` | Connector inventory | None |
| `get_job_history(guid, duration)` | Job activity | guid=connector_guid, duration="P7D" |
| `get_connector_health(guid)` | Connector health | guid=connector_guid |
| `get_latest_snapshot(guid)` | Snapshot integrity | guid=connector_guid |

### Time Calculations

```python
# Investigation windows (ISO 8601 durations)
# P1D  = 1 day   — quick recent-activity check
# P7D  = 7 days  — standard incident investigation
# P14D = 14 days — extended investigation (exfiltration)
# P30D = 30 days — deep investigation (persistent threats, config drift)

# Temporal correlation windows
# 600 seconds  (10 min) — brute force detection window
# 3600 seconds (1 hour) — auth-to-job correlation window
# 14400 seconds (4 hours) — lateral movement detection window
# 86400 seconds (24 hours) — multi-phase attack chain window
```

### Error Resilience

The investigation proceeds with partial data whenever possible:
- Audit log failures: Proceed with job history and connector health
- Job history failures: Proceed with audit logs only, note reduced confidence
- Connector health failures: Mark as "unknown", continue with available data
- All findings include a `confidence` field: "high", "medium", "low"
- Final report includes an `investigation_completeness` percentage

---

## Success Metrics

A successful security investigation produces:

1. **Clear severity classification** — Critical/High/Medium/Low with numeric score
2. **Evidence-backed findings** — Every pattern detection linked to specific events
3. **Complete timeline** — Chronological reconstruction of incident events
4. **IOC identification** — Suspicious tokens, time windows, and affected assets
5. **Actionable recommendations** — Prioritized response steps
6. **Investigation completeness** — Percentage of data sources successfully analyzed
7. **False positive acknowledgment** — Context for findings that may be benign
