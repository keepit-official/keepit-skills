# Job History Analysis Examples and Patterns

This reference provides concrete examples of job history analysis outputs for various scenarios.

## Table of Contents

1. [Troubleshooting Analysis Example](#troubleshooting-analysis-example)
2. [Performance Analysis Example](#performance-analysis-example)
3. [SLA Verification Example](#sla-verification-example)
4. [Comprehensive Monthly Report Example](#comprehensive-monthly-report-example)
5. [Pattern Recognition Examples](#pattern-recognition-examples)
6. [Response Templates](#response-templates)

---

## Troubleshooting Analysis Example

**Scenario:** User reports recent backup failures, needs to understand what's happening

**User Query:** "Why did my Microsoft 365 backup fail yesterday?"

### Analysis Output

```markdown
# Backup Failure Analysis
**Connector:** Microsoft 365 Backup  
**Time Period:** Last 7 days (October 15-22, 2025)  
**Generated:** October 22, 2025 at 15:30 UTC

## 🔴 Critical Finding

**3 consecutive backup failures detected** in the last 24 hours

### Failure Summary

| Date/Time | Status | Duration | Error |
|-----------|--------|----------|-------|
| Oct 22, 02:15 UTC | ❌ Failed | 2m 14s | Authentication token expired |
| Oct 21, 02:15 UTC | ❌ Failed | 2m 08s | Authentication token expired |
| Oct 20, 02:15 UTC | ❌ Failed | 2m 11s | Authentication token expired |

## 📊 Pattern Analysis

### Key Findings

1. **Consistent Failure Time**
   - All failures occur at exactly 02:15 UTC
   - This is during your scheduled backup window
   
2. **Consistent Error Message**
   - "Authentication token expired" appears in all 3 failures
   - Indicates authentication/authorization issue
   
3. **Short Duration Before Failure**
   - Jobs fail quickly (~2 minutes)
   - Failure happens during initial authentication phase
   - No actual data transfer occurring

4. **No Successful Jobs Since**
   - Last successful backup: October 19, 2025 at 02:13 UTC
   - You currently have a **3-day backup gap**

## 🎯 Root Cause

**Likely cause:** Microsoft 365 authentication token has expired

**Why this happens:**
- OAuth tokens have expiration periods (typically 90 days)
- Token was likely issued around July 22, 2025
- Token expired around October 19-20, 2025
- Keepit cannot authenticate to Microsoft 365 without valid token

**Why it fails at 02:15 UTC specifically:**
- This is your scheduled backup time
- Job starts, attempts authentication
- Expired token rejected by Microsoft
- Job fails immediately

## ✅ Recommended Actions

### Immediate (Within 1 hour)

1. **Re-authenticate the Microsoft 365 connector**
   - Log into Keepit dashboard
   - Navigate to Connectors → Microsoft 365 Backup
   - Click "Re-authorize" or "Refresh Connection"
   - Complete Microsoft 365 authentication flow
   
2. **Trigger manual backup**
   - After re-authenticating, start a manual backup
   - Verify it completes successfully
   - This will close the 3-day backup gap

### Short-term (Within 24 hours)

3. **Verify automatic backups resume**
   - Wait for next scheduled backup (tomorrow at 02:15 UTC)
   - Check that it completes successfully
   - Monitor for next 3 days to confirm stability

4. **Set up proactive monitoring**
   - Enable Keepit email notifications for failures
   - Consider setting calendar reminder for 80 days from now
   - This prevents future token expiration surprises

### Long-term (Ongoing)

5. **Regular health checks**
   - Run weekly health checks using the Account Health skill
   - Catches issues before they become critical
   - Identifies patterns early

## 📈 Historical Context

### 7-Day Statistics

- **Total Jobs:** 7 attempted
- **Successful:** 4 (57% success rate) ⚠️
- **Failed:** 3 (43% failure rate)
- **Average Duration:** 8m 45s (when successful)

### Before This Issue

Prior to October 20, your Microsoft 365 backups had:
- **100% success rate** for previous 30 days
- **Average duration:** 12 minutes
- **No authentication issues**

**This confirms** the issue started suddenly on October 20, consistent with token expiration.

## 🔍 Verification Steps

After re-authenticating, verify:

1. ✅ Manual backup completes successfully
2. ✅ Job duration returns to normal (~12 minutes)
3. ✅ No error messages in job log
4. ✅ Next scheduled backup completes
5. ✅ Backup gap is closed

---

**Severity:** 🔴 High - Active backup gap  
**Confidence:** High - Clear authentication pattern  
**Expected resolution time:** 15 minutes  
**Follow-up:** Check status in 24 hours
```

---

## Performance Analysis Example

**Scenario:** User wants to understand backup performance trends for capacity planning

**User Query:** "Analyze backup performance for the last 30 days"

### Analysis Output

```markdown
# Backup Performance Analysis
**Scope:** All cloud connectors  
**Time Period:** Last 30 days (September 22 - October 22, 2025)  
**Generated:** October 22, 2025 at 15:30 UTC

## 📊 Executive Summary

**Overall Status:** 🟢 Good performance with optimization opportunities

**Key Metrics:**
- Total jobs analyzed: 842 jobs across 3 connectors
- Overall success rate: 94.3% ✅
- Average job duration: 14m 32s
- Performance trend: Gradually increasing (+8% vs. last month)

**Primary Recommendation:** Schedule optimization to improve backup window utilization

---

## 📈 Aggregate Statistics

| Metric | Value | Trend | Status |
|--------|-------|-------|--------|
| Total Jobs | 842 | ➡️ Stable | - |
| Successful | 794 | ⬆️ +2% | ✅ |
| Failed | 48 | ⬇️ -15% | 🟢 |
| Success Rate | 94.3% | ⬆️ +1.2% | ✅ |
| Avg Duration | 14m 32s | ⬆️ +8% | ⚠️ |
| Total Time | 204.1 hours | ⬆️ +12% | ⚠️ |

### Success Rate Trend

```
Week 1 (Sep 22-28): 92.5% ████████████████████░░
Week 2 (Sep 29-Oct 5): 93.8% █████████████████████░
Week 3 (Oct 6-12):     95.1% ██████████████████████
Week 4 (Oct 13-19):    94.9% ██████████████████████
Week 5 (Oct 20-22):    94.0% █████████████████████░
```

**Analysis:** Success rate improved steadily through Week 3, slight dip in Week 5 (within normal variance).

---

## 🔍 Per-Connector Performance

### Microsoft 365 Backup

**Job Statistics:**
- Total Jobs: 420 (50% of all jobs)
- Success Rate: 97.1% ✅ Excellent
- Avg Duration: 18m 45s
- Duration Trend: +12% increase

**Performance Profile:**
- Consistently runs daily at 02:15 UTC
- Longest jobs: 28-32 minutes (weekends)
- Shortest jobs: 12-14 minutes (weekdays)
- **Observation:** Weekend jobs 60% longer (likely due to data accumulation)

**Recommendations:**
- ✅ Performance is good
- Consider splitting large weekend backups
- Monitor for continued duration growth

---

### Entra ID Backup(1)

**Job Statistics:**
- Total Jobs: 248 (29% of all jobs)
- Success Rate: 91.5% 🟡 Acceptable
- Avg Duration: 8m 12s
- Duration Trend: +3% (stable)

**Performance Profile:**
- Runs daily at 03:00 UTC
- Very consistent duration (7-9 minutes)
- 21 failures in period (8.5% failure rate)

**Issues Identified:**
- Recurring failure pattern on Mondays
- Error: "API rate limit exceeded"
- **Hypothesis:** Monday morning peak usage conflicts with backup

**Recommendations:**
- ⚠️ Adjust schedule to avoid Monday 03:00 UTC
- Consider moving to 01:00 UTC or 05:00 UTC
- Monitor API rate limit metrics

---

### Entra ID Backup(2)

**Job Statistics:**
- Total Jobs: 174 (21% of all jobs)
- Success Rate: 93.1% 🟢 Good
- Avg Duration: 12m 18s
- Duration Trend: +15% increase ⚠️

**Performance Profile:**
- Runs daily at 04:30 UTC
- Duration increasing steadily
- Started at 10m avg, now 12m avg

**Growth Analysis:**
- +2 minutes average over 30 days
- Linear growth pattern
- Projected to reach 15 minutes in 60 days

**Recommendations:**
- 🟡 Monitor continued growth
- Review for data accumulation
- Plan for backup window expansion
- Current window still sufficient

---

## 💡 Insights and Patterns

### Duration Growth Analysis

**Overall trend:** Job durations increasing 8% month-over-month

**Breakdown by connector:**
- Microsoft 365: +12% (fastest growth)
- Entra ID(2): +15% (concerning trend)
- Entra ID(1): +3% (stable)

**Likely causes:**
1. **Data growth** - Normal business data accumulation
2. **User growth** - More users/mailboxes/objects to backup
3. **Feature adoption** - More M365 services in use

**Impact assessment:**
- **Current:** Backup windows still adequate
- **30 days:** Will approach window limits
- **60 days:** May need schedule adjustment
- **90 days:** Window expansion required

### Schedule Efficiency

**Current backup schedule:**
```
02:00 - 03:00 UTC: Microsoft 365 (peaks at 32 min on weekends)
03:00 - 04:00 UTC: Entra ID(1) (typically 8 min)
04:30 - 05:30 UTC: Entra ID(2) (typically 12 min)
```

**Window utilization:**
- Microsoft 365: 50-90% (varies by day)
- Entra ID(1): 13% (underutilized)
- Entra ID(2): 20% (good)

**Optimization opportunities:**
- Entra ID connectors could run in parallel
- Would free up 1 hour of backup window
- Creates capacity for future growth

### Failure Pattern Analysis

**48 total failures across 30 days:**

**By connector:**
- Entra ID(1): 21 failures (44%)
- Microsoft 365: 12 failures (25%)
- Entra ID(2): 15 failures (31%)

**By error type:**
- API rate limit (28 occurrences) - 58%
- Network timeout (12 occurrences) - 25%
- Authentication (8 occurrences) - 17%

**By day of week:**
- Monday: 18 failures (38%)
- Tuesday-Friday: 24 failures (50%)
- Weekend: 6 failures (12%)

**Key insight:** Monday morning has 3x more failures than average, suggesting peak usage conflicts.

---

## 🎯 Recommendations

### Immediate Actions

1. **Adjust Entra ID(1) schedule**
   - Move from Monday 03:00 UTC to 01:00 UTC
   - Avoids peak API usage period
   - Should reduce 70% of current failures

2. **Enable parallel execution**
   - Run both Entra ID backups simultaneously
   - Reduces overall backup window by 1 hour
   - Creates capacity headroom

### Short-term (30 days)

3. **Implement duration monitoring**
   - Set alerts for jobs exceeding 20 minutes
   - Track month-over-month growth
   - Identify optimization opportunities

4. **Review Microsoft 365 weekend backups**
   - Investigate why weekend jobs take 60% longer
   - Consider incremental backup strategy
   - May reduce backup window usage

### Long-term (60-90 days)

5. **Capacity planning**
   - Current growth rate: 8% per month
   - At this rate, backup windows saturate in 4-5 months
   - Plan schedule expansion or optimization

6. **Performance baseline**
   - Document current "normal" durations
   - Set alerting thresholds (e.g., 25% above baseline)
   - Enables proactive issue detection

---

## 📋 Next Steps

1. **Immediate:** Adjust Entra ID(1) schedule (ETA: 15 minutes)
2. **This week:** Monitor for improvement in Monday failures
3. **In 30 days:** Run follow-up performance analysis
4. **In 60 days:** Review duration growth trends
5. **Ongoing:** Weekly health checks using Account Health skill

---

**Analysis Confidence:** High  
**Data Completeness:** 100% (all jobs captured)  
**Recommended Review Frequency:** Monthly  
**Next Analysis Due:** November 22, 2025
```

---

## SLA Verification Example

**Scenario:** User needs to verify backup operations meet SLA requirements

**User Query:** "Are we meeting our 95% success rate SLA?"

### Analysis Output

```markdown
# SLA Compliance Report
**Period:** Last 30 days (September 22 - October 22, 2025)  
**SLA Target:** 95% success rate  
**Generated:** October 22, 2025 at 15:30 UTC

## ✅ SLA Compliance Status: PASS (with concerns)

**Overall Success Rate:** 94.3%  
**SLA Target:** 95.0%  
**Variance:** -0.7% (within acceptable margin)

While technically below target, the 0.7% variance is within measurement error and recent trend is positive.

---

## 📊 Compliance Metrics

### Overall Performance

| Metric | Target | Actual | Status | Variance |
|--------|--------|--------|--------|----------|
| Success Rate | ≥95% | 94.3% | ⚠️ Near | -0.7% |
| Total Jobs | - | 842 | - | - |
| Successful | - | 794 | ✅ | - |
| Failed | ≤5% | 48 (5.7%) | ⚠️ Near | +0.7% |

### Weekly Breakdown

| Week | Jobs | Success Rate | SLA Status | Trend |
|------|------|--------------|------------|-------|
| Week 1 (Sep 22-28) | 168 | 92.5% | ❌ Below | - |
| Week 2 (Sep 29-Oct 5) | 175 | 93.8% | ❌ Below | ⬆️ Improving |
| Week 3 (Oct 6-12) | 171 | 95.1% | ✅ Pass | ⬆️ Improving |
| Week 4 (Oct 13-19) | 178 | 94.9% | ⚠️ Near | ➡️ Stable |
| Week 5 (Oct 20-22) | 150 | 94.0% | ❌ Below | ⬇️ Slight dip |

**Trend Analysis:** Performance improved significantly from Week 1 to Week 3, achieving SLA compliance. Weeks 4-5 show slight decline but remain close to target.

---

## 🔍 Per-Connector SLA Performance

### Microsoft 365 Backup ✅

**Success Rate:** 97.1% (Target: 95%)  
**Status:** ✅ **EXCEEDS SLA**

- Consistently above target
- Excellent reliability
- No SLA concerns

### Entra ID Backup(1) ⚠️

**Success Rate:** 91.5% (Target: 95%)  
**Status:** ❌ **BELOW SLA** (-3.5%)

- Primary SLA concern
- Recurring Monday failures
- API rate limit issues
- **Action required**

### Entra ID Backup(2) 🟢

**Success Rate:** 93.1% (Target: 95%)  
**Status:** ⚠️ **NEAR TARGET** (-1.9%)

- Close to compliance
- Improving trend
- Minor optimization needed

---

## ⚠️ SLA Risk Factors

### High Risk

**1. Entra ID Backup(1) - Monday Failures**
- **Impact:** -3.5% against SLA
- **Frequency:** 18 Monday failures in 30 days
- **Root cause:** API rate limiting during peak usage
- **Resolution:** Schedule adjustment required

### Medium Risk

**2. Performance Degradation**
- **Impact:** Could affect future reliability
- **Observation:** 8% increase in job duration
- **Concern:** May lead to job failures if windows exceeded
- **Resolution:** Capacity planning and optimization

### Low Risk

**3. Entra ID Backup(2) - Minor gap**
- **Impact:** -1.9% against SLA
- **Trend:** Improving
- **Resolution:** Continue monitoring

---

## 💡 SLA Improvement Plan

### Target: Achieve consistent 96%+ success rate

**Immediate Actions (Impact: +2.5%)**

1. **Fix Entra ID(1) Monday failures**
   - Reschedule to avoid API peak
   - Expected improvement: +2.1%
   - Timeline: This week

2. **Implement failure alerting**
   - Catch issues faster
   - Reduce failure duration
   - Expected improvement: +0.4%
   - Timeline: This week

**Projected New Success Rate:** 96.8% ✅

### Short-term Actions (30 days)

3. **Optimize Entra ID(2) performance**
   - Review configuration
   - Adjust retry logic
   - Expected improvement: +0.5%

4. **Preventive monitoring**
   - Weekly health checks
   - Proactive issue detection
   - Prevents degradation

### Long-term Actions (60-90 days)

5. **Capacity management**
   - Prevent future capacity-related failures
   - Maintain performance as data grows

6. **Continuous improvement**
   - Monthly SLA reviews
   - Trend analysis
   - Benchmark against targets

---

## 📈 Forecast

### If no action taken:
- **Next 30 days:** 93.5% (below SLA)
- **Confidence:** Medium
- **Risk:** SLA breach

### If recommendations implemented:
- **Next 30 days:** 96.5% (above SLA)
- **Confidence:** High
- **Risk:** Low

---

## 📋 Compliance Documentation

### For Audit Purposes

**SLA Period:** September 22 - October 22, 2025  
**Target Metric:** 95% success rate for backup jobs  
**Actual Performance:** 94.3% overall success rate  
**Compliance Status:** Near target (-0.7%)  
**Trend:** Improving (92.5% → 95.1% → 94.9%)  
**Action Plan:** In place, targeting 96%+ within 30 days

### Supporting Evidence

- Total jobs executed: 842
- Successful completions: 794
- Documented failures: 48
- Root cause analysis: Complete
- Remediation plan: Defined
- Expected resolution: 7 days

---

**Overall Assessment:** While current performance is slightly below the 95% SLA target, the trend is positive and corrective actions are in progress. With the Monday failure issue resolved, compliance is expected within 1-2 weeks.

**Next SLA Review:** November 22, 2025 (30 days)  
**Recommended Review Frequency:** Monthly
```

---

## Comprehensive Monthly Report Example

**Scenario:** Executive management needs monthly operational review

**User Query:** "Generate a comprehensive backup operations report for October"

### Analysis Output

```markdown
# Keepit Backup Operations Report
**Period:** October 2025 (October 1-31)  
**Prepared for:** Executive Management  
**Generated:** November 1, 2025

---

## Executive Summary

### Overall Status: 🟢 Operations Healthy

**Key Highlights:**
- ✅ 95.2% success rate across all backup operations
- ✅ Zero data loss incidents
- ✅ All SLA targets met
- ⚠️ One authentication incident (resolved within 4 hours)
- 📈 8% increase in backup volume month-over-month

**Bottom Line:** Backup operations performed well in October with one minor incident that was quickly resolved. System capacity is adequate for current needs, with planning underway for Q1 2026 growth.

---

## 📊 Operations at a Glance

| Metric | October | September | Change |
|--------|---------|-----------|--------|
| Total Jobs | 1,156 | 1,083 | +6.7% ⬆️ |
| Successful | 1,100 | 1,019 | +7.9% ⬆️ |
| Failed | 56 | 64 | -12.5% ⬇️ |
| Success Rate | 95.2% | 94.1% | +1.1% ⬆️ |
| Avg Duration | 14m 28s | 13m 42s | +5.6% ⬆️ |

### Success Rate Trend (Last 6 Months)

```
May:     93.2% ███████████████████░
Jun:     93.8% ████████████████████
Jul:     94.5% ████████████████████
Aug:     94.1% ████████████████████
Sep:     94.1% ████████████████████
Oct:     95.2% █████████████████████
```

**Analysis:** Steady improvement trend with October showing best performance in 6 months.

---

## 🎯 SLA Performance

### Primary SLAs

| SLA Metric | Target | Actual | Status |
|------------|--------|--------|--------|
| Success Rate | ≥95% | 95.2% | ✅ Pass |
| RPO (Recovery Point) | 24 hours | 18 hours avg | ✅ Pass |
| Backup Completion | Before 8AM UTC | 6:45AM avg | ✅ Pass |

**Compliance:** All SLA targets met or exceeded in October.

---

## 📈 System Performance

### Backup Operations

**Total Operations:** 1,156 jobs  
**Daily Average:** 37 jobs  
**Peak Day:** October 23 (42 jobs)  
**Quietest Day:** October 15 (32 jobs)

### Performance Metrics

**Job Duration:**
- Minimum: 4m 12s
- Maximum: 34m 56s
- Average: 14m 28s
- Median: 13m 15s

### Capacity Utilization

**Backup Windows:**
- Primary window (02:00-06:00 UTC): 68% utilized
- Secondary window (12:00-14:00 UTC): 45% utilized
- Available capacity: Good (32% headroom in primary window)

---

## 🔍 Incidents and Issues

### Incident Summary

**Total Incidents:** 1  
**Severity:**
- Critical: 0
- High: 1 (authentication failure)
- Medium: 0
- Low: 0

### Incident Details

**Incident #1: Microsoft 365 Authentication Expiration**

- **Date:** October 20-22, 2025
- **Duration:** 72 hours (detected and resolved within 4 hours of detection)
- **Impact:** Microsoft 365 backups failed for 3 consecutive days
- **Root Cause:** OAuth token expired after 90-day lifecycle
- **Resolution:** Connector re-authenticated, manual backup triggered
- **Data Impact:** None - restoration from October 19 available
- **Prevention:** Calendar reminders set for future token renewals

**Lessons Learned:**
- Implemented proactive token expiration monitoring
- Added alerting 7 days before token expiration
- Documented re-authentication procedure

---

## 💼 Operations by Connector

### Microsoft 365 Backup

**Jobs:** 527 | **Success Rate:** 97.4% ✅ | **Avg Duration:** 19m 12s

- **Strengths:** Excellent reliability outside of authentication incident
- **Concerns:** Duration increasing 12% month-over-month
- **Action:** Monitor for continued growth

### Entra ID Backup(1)

**Jobs:** 372 | **Success Rate:** 93.8% 🟡 | **Avg Duration:** 8m 45s

- **Strengths:** Consistent, predictable performance
- **Concerns:** Monday morning failures (API rate limiting)
- **Action:** Schedule adjusted to 01:00 UTC (implemented Oct 28)

### Entra ID Backup(2)

**Jobs:** 257 | **Success Rate:** 94.5% 🟢 | **Avg Duration:** 12m 42s

- **Strengths:** Good reliability, stable duration
- **Concerns:** Gradual duration increase
- **Action:** Continue monitoring

---

## 💡 Insights and Trends

### Growth Patterns

**Data Growth:**
- +9.1% month-over-month
- On track with projected annual growth (15%)
- Capacity planning remains adequate

**Performance Trends:**
- Success rate improving (↑1.1%)
- Duration increasing (↑5.6%) but within acceptable range
- Failure rate decreasing (↓12.5%)

### Operational Improvements

**Implemented in October:**
1. ✅ Proactive health monitoring (weekly checks)
2. ✅ Enhanced failure alerting
3. ✅ Token expiration tracking
4. ✅ Schedule optimization for Entra ID connectors

**Results:**
- Faster incident detection (avg 2 hours vs. 6 hours previously)
- Reduced failure rate
- Improved SLA compliance

---

## 🎯 Q4 Objectives Progress

| Objective | Target | Status | Progress |
|-----------|--------|--------|----------|
| Achieve 95% success rate | 95% | ✅ On track | 95.2% |
| Reduce MTTR | <4 hours | ✅ Met | 2.8 hours avg |
| Zero data loss | 0 incidents | ✅ Met | 0 incidents |
| Implement automation | 3 tools | 🟡 In progress | 2 of 3 complete |

---

## 📋 Recommendations

### Immediate (November)

1. **Continue monitoring token expirations**
   - Next token renewal due: January 18, 2026
   - Set reminder for January 11, 2026

2. **Validate schedule optimization results**
   - Monitor Entra ID(1) Monday performance
   - Expect 70% reduction in Monday failures

### Short-term (Q4 2025)

3. **Capacity planning review**
   - Current growth sustainable through Q1 2026
   - Review again in December for Q2 planning

4. **Documentation update**
   - Complete runbooks for common incidents
   - Update escalation procedures

### Long-term (Q1 2026)

5. **Backup strategy review**
   - Evaluate incremental vs. full backup mix
   - Consider parallel execution for capacity optimization

6. **Disaster recovery testing**
   - Schedule quarterly restore test
   - Validate RTO/RPO targets

---

## 📅 Looking Ahead (November)

**Planned Activities:**
1. Quarterly restore validation test (Nov 15)
2. Q4 performance review (Nov 30)
3. 2026 capacity planning kickoff (Nov 20)
4. Team training on new monitoring tools (Nov 10)

**Expected Improvements:**
- Success rate target: 96%+
- Reduced Monday failures (schedule optimization)
- Faster incident response (new alerting)

**Risks to Monitor:**
- Continued duration growth
- Holiday period schedule changes
- Year-end data surge

---

## Appendices

### A. Methodology
- Data source: Keepit job history API
- Analysis period: October 1-31, 2025 (23:59 UTC)
- Jobs analyzed: 1,156 total operations
- Exclusions: Test jobs, cancelled jobs

### B. Definitions
- **Success Rate:** (Successful jobs / Total jobs) × 100
- **RPO:** Maximum acceptable data loss (measured in hours)
- **MTTR:** Mean Time To Repair/Restore (incident detection to resolution)
- **SLA Compliance:** Actual performance vs. defined target

### C. Contact Information
- **Operations Team:** ops@company.com
- **Keepit Support:** support@keepit.com
- **Escalation:** CTO (critical incidents only)

---

**Report Prepared By:** Backup Operations Team  
**Next Report:** December 1, 2025  
**Questions?** Contact ops@company.com
```

---

## Pattern Recognition Examples

### Authentication Pattern

```markdown
**Pattern Detected:** Recurring authentication failures

**Signature:**
- Error message contains "authentication", "token", or "authorization"
- Failures occur at consistent time each day
- Short job duration (typically <5 minutes before failure)
- Affects only specific connector(s), not all

**Common Causes:**
1. OAuth token expiration (90-day lifecycle)
2. Password change on service account
3. MFA requirement added to account
4. Permission changes on source system

**Diagnostic Questions:**
- When did failures start? (helps pinpoint trigger event)
- Does manual authentication resolve it? (confirms auth issue)
- Have any account changes occurred? (identifies root cause)

**Resolution Path:**
1. Re-authenticate connector
2. Verify permissions still granted
3. Check for MFA or conditional access policies
4. Trigger test backup to confirm resolution
```

### Performance Degradation Pattern

```markdown
**Pattern Detected:** Gradual job duration increase

**Signature:**
- Job duration increases steadily over weeks/months
- Success rate remains high
- No specific error messages
- Affects all or most jobs for a connector

**Common Causes:**
1. Data growth (normal business operations)
2. User/mailbox expansion
3. Increased object count in source system
4. Network performance degradation
5. Backend storage approaching capacity

**Diagnostic Questions:**
- What's the rate of increase? (helps forecast)
- Is data volume growing proportionally? (confirms normal growth)
- Are there duration spikes or steady increase? (sudden vs. gradual)

**Resolution Path:**
1. Review data growth metrics in source system
2. Evaluate backup window capacity
3. Consider optimization strategies (incremental, parallel)
4. Plan for capacity expansion if needed
5. Set monitoring thresholds for alerting
```

### API Rate Limiting Pattern

```markdown
**Pattern Detected:** API rate limit failures

**Signature:**
- Error message contains "rate limit", "throttling", or "429"
- Failures cluster at specific times
- Often affects multiple connectors simultaneously
- Higher failure rate on specific days (often Monday)

**Common Causes:**
1. Source system API limits
2. Concurrent operations hitting same API
3. Peak business hours conflicting with backup
4. Insufficient API quotas/licensing

**Diagnostic Questions:**
- What time do failures occur? (identifies conflict window)
- Do failures correlate with business activity? (confirms usage conflict)
- Are multiple jobs running simultaneously? (identifies concurrency issue)

**Resolution Path:**
1. Identify peak API usage times in source system
2. Reschedule backups to off-peak hours
3. Implement staggered job execution
4. Request higher API quotas if needed
5. Consider throttling backup operations
```

### Weekend/Holiday Pattern

```markdown
**Pattern Detected:** Day-of-week performance variations

**Signature:**
- Consistent pattern based on calendar day
- Different duration or failure rates on weekends
- Holiday correlation
- Predictable, recurring pattern

**Common Causes:**
1. Data accumulation over weekend (longer jobs on Monday)
2. Maintenance windows on specific days
3. Reduced data changes on weekends (faster jobs)
4. Business process timing (month-end, quarter-end)

**Diagnostic Questions:**
- Is the pattern consistent week-to-week? (confirms calendar correlation)
- Does data volume vary by day? (explains duration differences)
- Are there scheduled maintenance windows? (identifies external factors)

**Resolution Path:**
1. Analyze data volume by day of week
2. Adjust backup strategy for high-volume days
3. Consider split jobs for heavy periods
4. Account for patterns in capacity planning
5. Set day-specific performance expectations
```

---

## Response Templates

### Template 1: Simple Failure Explanation

```markdown
## Backup Failure Analysis

**Connector:** [Connector Name]  
**Time Period:** [Period]  
**Failures Found:** [Count]

### What Happened

[1-2 sentence plain English explanation]

### Why It Happened

[Bullet points explaining root cause]

### How to Fix It

[Numbered steps with specific actions]

### What to Expect

[Timeline and expected outcome]

---
**Severity:** [Low/Medium/High/Critical]  
**Action Required:** [Yes/No - if yes, when]  
**Follow-up:** [When to check back]
```

### Template 2: Performance Summary

```markdown
## Performance Summary

**Period:** [Timeframe]  
**Connectors Analyzed:** [Count/Names]

### Quick Stats

- Total Jobs: [number]
- Success Rate: [percentage] [icon]
- Avg Duration: [time]
- Trend: [improving/stable/degrading]

### Key Findings

[3-5 bullet points with most important insights]

### Recommendation

[One clear primary action]

---
**Overall Status:** [icon + brief assessment]
```

### Template 3: Pattern Alert

```markdown
## ⚠️ Pattern Detected

**Pattern Type:** [Authentication/Performance/Rate Limit/etc.]

**Observed:** [Brief description of pattern]

**Impact:** [What this means for backups]

**Recommended Action:** [Specific next step]

**Confidence:** [Low/Medium/High] - [Brief justification]

---
**Learn more:** [Link to detailed analysis if available]
```

### Template 4: Trend Report

```markdown
## Trend Analysis

**Metric:** [What's being tracked]  
**Period:** [Timeframe]  
**Direction:** [⬆️/⬇️/➡️] [Percentage change]

### Visualization

[Text-based chart or trend description]

### Analysis

[What this trend means]

### Projection

[Where this is heading if continues]

### Action Needed

[Whether intervention is required]
```

---

## Usage Guidelines for Examples

### When to Use Each Example Type

**Troubleshooting Example:**
- User reports specific failure
- Recent issue needs investigation
- Root cause analysis required
- Immediate action needed

**Performance Example:**
- Regular operational review
- Optimization investigation
- Capacity planning
- No specific issue, just analysis

**SLA Verification Example:**
- Compliance reporting needed
- Management review
- Audit preparation
- Target verification

**Comprehensive Report Example:**
- Executive briefing
- Monthly/quarterly review
- Complete operational overview
- Multiple stakeholder audiences

### Adapting Examples

**For simpler requests:**
- Use only Executive Summary and Key Findings
- Skip detailed per-connector breakdown
- Provide brief recommendations
- Link to full analysis if needed

**For deeper investigation:**
- Include all sections
- Add raw data references
- Provide multiple hypotheses
- Suggest follow-up analysis

**For technical audiences:**
- Include more detailed metrics
- Reference specific error codes
- Provide technical recommendations
- Less executive summary, more data

**For management audiences:**
- Lead with business impact
- Focus on trends and SLA
- Clear recommendations
- Minimal technical detail
