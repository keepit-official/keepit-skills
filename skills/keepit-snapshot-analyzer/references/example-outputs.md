# Snapshot Analysis Examples and Patterns

This reference provides concrete examples of snapshot continuity analysis outputs for various scenarios.

## Table of Contents

1. [Healthy Continuity Example](#healthy-continuity-example)
2. [Gap Detection Example](#gap-detection-example)
3. [RPO Compliance Report Example](#rpo-compliance-report-example)
4. [Capacity Planning Example](#capacity-planning-example)
5. [Response Templates](#response-templates)

---

## Healthy Continuity Example

**Scenario:** Quarterly continuity verification — all backups on track

**User Query:** "Verify backup continuity for all connectors"

### Analysis Output

```markdown
# Backup Continuity Analysis Report
**Scope:** All cloud connectors
**Time Period:** Last 30 days (January 18 - February 17, 2026)
**Generated:** February 17, 2026 at 10:00 UTC

## ✅ Executive Summary

- **Connectors analyzed:** 3
- **Total snapshots:** 89 across 30 days
- **Overall continuity:** ✅ Good — no significant gaps
- **RPO compliance:** 100% (target: 24h)
- **Size trend:** Growing (+4.2% over 30 days)

## Continuity Analysis

### Per-Connector Summary

| Connector | Snapshots | Max Gap | Avg Interval | P/C Ratio | Continuity |
|-----------|-----------|---------|--------------|-----------|------------|
| Microsoft 365 Backup | 30 | 24.5h | 24.0h | 0p / 30c | ✅ Good |
| Entra ID Backup(1) | 30 | 24.3h | 24.0h | 0p / 30c | ✅ Good |
| Entra ID Backup(2) | 29 | 25.1h | 24.8h | 1p / 28c | ✅ Good |

### Gaps Detected

No gaps exceeding 1.5x the expected 24-hour interval were found.

## RPO Compliance

**Target RPO:** 24 hours

| Connector | Worst Gap | Compliance | Violations |
|-----------|-----------|------------|------------|
| Microsoft 365 Backup | 24.5h | 100% | 0 |
| Entra ID Backup(1) | 24.3h | 100% | 0 |
| Entra ID Backup(2) | 25.1h | 96.6% | 1 (25.1h — within tolerance) |

**Overall RPO compliance: ✅ Compliant**

## Size Trend Analysis

| Connector | First Size | Latest Size | Growth | Trend |
|-----------|-----------|-------------|--------|-------|
| Microsoft 365 Backup | 2.1 GB | 2.2 GB | +4.8% | 📈 Growing |
| Entra ID Backup(1) | 450 MB | 462 MB | +2.7% | ➡️ Stable |
| Entra ID Backup(2) | 380 MB | 395 MB | +3.9% | 📈 Growing |

### 90-Day Capacity Projection

| Connector | Current | Projected (90d) | Daily Growth |
|-----------|---------|-----------------|-------------|
| Microsoft 365 Backup | 2.2 GB | 2.5 GB | +3.3 MB/day |
| Entra ID Backup(1) | 462 MB | 498 MB | +0.4 MB/day |
| Entra ID Backup(2) | 395 MB | 431 MB | +0.4 MB/day |

## Recommendations

✅ **No immediate actions required**

**Maintenance suggestions:**
- Continue monitoring — next review in 30 days
- Current storage growth is sustainable
- All RPO targets are being met
```

---

## Gap Detection Example

**Scenario:** User suspects missed backups, needs investigation

**User Query:** "Check if there are any gaps in my Microsoft 365 backups"

### Analysis Output

```markdown
# Backup Gap Analysis
**Connector:** Microsoft 365 Backup
**Time Period:** Last 30 days (January 18 - February 17, 2026)
**Generated:** February 17, 2026 at 10:00 UTC

## ⚠️ Gap Detected

**Continuity Status:** Warning — 1 gap found exceeding expected interval

### Gap Details

| # | Gap Start | Gap End | Duration | Expected |
|---|-----------|---------|----------|----------|
| 1 | Feb 8, 02:15 UTC | Feb 10, 02:18 UTC | **48.1 hours** | 24 hours |

### Snapshot Timeline (February 5-12)

```
Feb 5  ──●──────────────────────────────── 02:15 ✅ Complete (2.15 GB)
Feb 6  ──●──────────────────────────────── 02:14 ✅ Complete (2.16 GB)
Feb 7  ──●──────────────────────────────── 02:16 ✅ Complete (2.16 GB)
Feb 8  ──●──────────────────────────────── 02:15 ✅ Complete (2.17 GB)
Feb 9  ──────────────────────────────────── ❌ NO SNAPSHOT
Feb 10 ──●──────────────────────────────── 02:18 ✅ Complete (2.18 GB)
Feb 11 ──●──────────────────────────────── 02:15 ✅ Complete (2.18 GB)
Feb 12 ──●──────────────────────────────── 02:14 ✅ Complete (2.19 GB)
```

### Overall Statistics

- **Total snapshots:** 29 (expected: 30)
- **Max gap:** 48.1 hours
- **Avg interval:** 24.8 hours
- **Partial/Complete:** 0p / 29c
- **Continuity status:** ⚠️ Warning

## Impact Assessment

- **Data at risk:** 1 day of data (February 9) was not backed up on schedule
- **Recovery point:** If a restore were needed for Feb 9, the most recent snapshot would be from Feb 8 (up to 48h of data loss)
- **Current state:** Backups have resumed normally since Feb 10

## Recommended Investigation

1. **Check job history** for February 9 — was a backup attempted and failed?
   ```
   → Use Job History Analyzer to run: get_job_history(guid, duration="P14D")
   → Look for failed jobs on February 9
   ```

2. **Check audit logs** for February 8-9 — were any config changes made?
   ```
   → Use Compliance Audit Log to run: get_audit_log_history(duration="P14D")
   → Filter for configuration events around Feb 8-9
   ```

3. **Verify current health** — is the connector healthy now?
   ```
   → Use Account Health to run: get_connector_health(guid)
   ```

---

**Severity:** ⚠️ Medium — gap is historical, backups have resumed
**Action Required:** Investigate root cause to prevent recurrence
```

---

## RPO Compliance Report Example

**Scenario:** Compliance officer needs RPO verification for audit evidence

**User Query:** "Generate RPO compliance report for the last quarter"

### Analysis Output

```markdown
# RPO Compliance Report
**Scope:** All cloud connectors
**Time Period:** Last 90 days (November 19, 2025 - February 17, 2026)
**RPO Target:** 24 hours
**Generated:** February 17, 2026 at 10:00 UTC

## Executive Summary

**Overall RPO Compliance: ⚠️ 97.8% (target: 100%)**

3 RPO violations detected across 2 connectors during the 90-day period.
All violations were within 2x the RPO target (no gap exceeded 48 hours).

## Per-Connector Compliance

| Connector | Intervals | Compliant | Violations | Compliance % | Worst Gap |
|-----------|-----------|-----------|------------|-------------|-----------|
| Microsoft 365 Backup | 89 | 88 | 1 | 98.9% | 48.1h |
| Entra ID Backup(1) | 88 | 86 | 2 | 97.7% | 36.4h |
| Entra ID Backup(2) | 87 | 87 | 0 | 100% | 24.8h |

## Violation Details

### Violation 1: Microsoft 365 Backup
- **When:** February 8-10, 2026
- **Gap:** 48.1 hours (exceeded RPO by 24.1 hours)
- **Root cause:** [Requires investigation — correlate with job history]
- **Data impact:** 1 day of unprotected data

### Violation 2: Entra ID Backup(1)
- **When:** December 25-26, 2025
- **Gap:** 36.4 hours (exceeded RPO by 12.4 hours)
- **Root cause:** Holiday period — likely scheduled maintenance window
- **Data impact:** Minimal (low activity period)

### Violation 3: Entra ID Backup(1)
- **When:** January 15-16, 2026
- **Gap:** 28.2 hours (exceeded RPO by 4.2 hours)
- **Root cause:** [Requires investigation]
- **Data impact:** 4 hours of additional exposure

## Compliance Evidence

### For Auditors

- **Measurement method:** Consecutive snapshot interval analysis
- **Data source:** Keepit `get_snapshot_range` API
- **Period covered:** 90 days (265 total intervals measured)
- **RPO target:** 24 hours per organizational policy
- **Result:** 97.8% compliance (259/265 intervals within target)

### Trend Analysis

```
Nov 2025: 98.5% compliance (1 violation)
Dec 2025: 96.6% compliance (1 violation)
Jan 2026: 96.7% compliance (1 violation)
Feb 2026: 98.0% compliance (0 violations to date)
```

**Trend:** Stable with isolated incidents. No systemic degradation.

## Recommendations

1. **Investigate the 3 RPO violations** to determine root causes
2. **Set up alerting** when a backup hasn't completed within 20 hours (80% of RPO)
3. **Document accepted exceptions** (e.g., holiday maintenance windows)
4. **Target:** 99%+ RPO compliance for next quarter

---

**Report suitable for:** External audit evidence, compliance documentation
**Next review:** May 2026 (quarterly)
```

---

## Capacity Planning Example

**Scenario:** IT planning needs storage growth forecast

**User Query:** "How fast is our backup data growing? Will we need more storage?"

### Analysis Output

```markdown
# Backup Storage Trend & Capacity Forecast
**Scope:** All cloud connectors
**Analysis Period:** Last 90 days
**Projection:** 90 days ahead
**Generated:** February 17, 2026 at 10:00 UTC

## 📊 Executive Summary

**Total current backup size:** 3.1 GB across 3 connectors
**90-day growth:** +8.5% (+243 MB)
**Projected size (90 days):** 3.4 GB
**Growth rate:** ~2.7 MB/day

**Assessment:** Growth is moderate and sustainable. No immediate capacity concerns.

## Per-Connector Trends

### Microsoft 365 Backup (Largest — 71% of total)

| Metric | Value |
|--------|-------|
| Current size | 2.2 GB |
| 90 days ago | 1.95 GB |
| Growth | +250 MB (+12.8%) |
| Daily growth | +2.8 MB/day |
| 90-day projection | 2.45 GB |

**Assessment:** Steady growth driven by email and document accumulation. Expected pattern.

### Entra ID Backup(1) (15% of total)

| Metric | Value |
|--------|-------|
| Current size | 462 MB |
| 90 days ago | 445 MB |
| Growth | +17 MB (+3.8%) |
| Daily growth | +0.2 MB/day |
| 90-day projection | 480 MB |

**Assessment:** Minimal growth. Directory data grows slowly.

### Entra ID Backup(2) (13% of total)

| Metric | Value |
|--------|-------|
| Current size | 395 MB |
| 90 days ago | 368 MB |
| Growth | +27 MB (+7.3%) |
| Daily growth | +0.3 MB/day |
| 90-day projection | 422 MB |

**Assessment:** Moderate growth, consistent with user onboarding.

## Capacity Projection

```
Today:      3.1 GB  ████████████████████████████████
+30 days:   3.2 GB  █████████████████████████████████
+60 days:   3.3 GB  ██████████████████████████████████
+90 days:   3.4 GB  ███████████████████████████████████
+180 days:  3.6 GB  ████████████████████████████████████
+365 days:  4.1 GB  ████████████████████████████████████████
```

**Confidence:** Medium (based on 90 days of data)

## Recommendations

✅ **No capacity action needed** for the next 6 months

**Planning suggestions:**
- Review again in 90 days
- Microsoft 365 drives most growth — monitor if M365 usage increases
- If new connectors are added, factor them into capacity estimates
- Current growth rate: ~1 GB/year total
```

---

## Response Templates

### Template 1: Quick Continuity Check

```markdown
## Backup Continuity Check

**Connector:** [Name] | **Period:** [Timeframe] | **Status:** [icon] [status]

| Snapshots | Max Gap | Avg Interval | Partial/Complete |
|-----------|---------|--------------|------------------|
| [count]   | [hours] | [hours]      | [Xp / Yc]       |

[One-sentence summary]
[Action if needed]
```

### Template 2: RPO Status

```markdown
## RPO Compliance: [icon] [percentage]%

**Target:** [X] hours | **Worst gap:** [Y] hours | **Violations:** [N]

[Brief assessment and action if needed]
```

### Template 3: Size Trend Summary

```markdown
## Storage Trend

**Current:** [size] | **Growth:** [percentage]% over [period] | **Trend:** [icon] [direction]
**Projection ([N] days):** [projected size] (+[growth])

[Assessment and recommendation]
```
