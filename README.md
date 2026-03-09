# Keepit AI Skills

AI skills for analyzing and monitoring your Keepit backup environment through natural language. Built for use with the [Keepit MCP Server](https://github.com/keepit-official/keepit-mcp) and any MCP-compatible AI client.

---

> [!IMPORTANT]
> **Experimental project — not an official Keepit product.**
>
> This repository was created as an initiative to explore what's possible when AI meets backup operations. It is not an official Keepit engineering release, has not gone through formal software development review, and may have gaps, inaccuracies, or compatibility issues as the MCP Server and AI clients evolve.
>
> That said, the skills are built on real Keepit API data and have been tested against live environments. They work well for most scenarios — just go in with realistic expectations and treat the output as a starting point for investigation, not a ground truth.
>
> Bug reports, feedback, and contributions are very welcome.

---

## What This Is

Each skill is a packaged set of instructions that turns your AI assistant into a Keepit expert for a specific task. Skills tell the AI *how* to approach a problem — which data to gather, how to analyze it, what patterns to look for, and how to present findings.

Skills are distributed as `.skill` files (ZIP archives) containing:

- **`SKILL.md`** — The core instruction set the AI follows
- **Python utilities** — Reference implementations for scoring and analysis logic
- **Example outputs** — Sample reports so the AI produces consistent, well-structured results

Every skill is open source. Browse the skill directories above to inspect exactly what each skill instructs the AI to do.

## Prerequisites

All skills require the **Keepit MCP Server** to be running and connected to your AI client. The MCP Server provides secure, read-only access to your Keepit backup data via the Keepit API.

- [Keepit MCP Server](https://github.com/keepit-official/keepit-mcp) — setup guide, configuration, and API credentials
- Your Keepit API credentials (region, access ID, access key)

## Available Skills

### Operations & Monitoring

| Skill | Folder | What It Does |
|-------|--------|-------------|
| **Account Health Reporter** | [`keepit-account-health`](keepit-account-health/) | Checks overall environment health — account status, connector configuration, backup freshness, and health scores across all protected applications. |
| **Job History Analyzer** | [`keepit-job-history-analyzer`](keepit-job-history-analyzer/) | Analyzes backup job success/failure rates, identifies failure patterns, examines performance trends, and checks SLA compliance over configurable time periods. |
| **Weekly Operations Digest** | [`keepit-weekly-operations-digest`](keepit-weekly-operations-digest/) | Generates a structured weekly summary of all backup activity — job metrics, failures, configuration changes, continuity gaps, and prioritized action items. |

### Investigation & Troubleshooting

| Skill | Folder | What It Does |
|-------|--------|-------------|
| **Backup Failure Root Cause Analyzer** | [`keepit-backup-failure-root-cause-analyzer`](keepit-backup-failure-root-cause-analyzer/) | Investigates why a backup failed by correlating job errors with audit log changes, health status, and snapshot gaps. Classifies failure type and provides resolution steps. |
| **Snapshot Gap & Continuity Analyzer** | [`keepit-snapshot-analyzer`](keepit-snapshot-analyzer/) | Detects gaps in backup coverage, measures RPO compliance, and projects storage growth trends. |

### Security & Compliance

| Skill | Folder | What It Does |
|-------|--------|-------------|
| **Security Incident Investigator** | [`keepit-security-incident-investigator`](keepit-security-incident-investigator/) | Reconstructs security incident timelines from audit logs, detects attack patterns (credential compromise, data exfiltration, config tampering), and scores incident severity. |
| **Compliance Audit Log Extractor** | [`keepit-compliance-audit-log`](keepit-compliance-audit-log/) | Formats audit trails for regulatory frameworks — GDPR, HIPAA, ISO 27001, NIS2, SOC 2. Prepares evidence packages for external audits. |
| **Retention Policy Auditor** | [`keepit-retention-policy-auditor`](keepit-retention-policy-auditor/) | Validates that retention policies comply with regulatory requirements (GDPR, NIS2, DORA, HIPAA, SOX), tracks policy changes, and verifies actual enforcement. |

### Executive & Strategic

| Skill | Folder | What It Does |
|-------|--------|-------------|
| **Executive Backup Summary** | [`keepit-executive-backup-summary`](keepit-executive-backup-summary/) | Translates backup data into business language with a Protection Score (0–100), plain-English risk descriptions, and a board-ready summary. Designed for CIO/CTO reporting. |
| **Restore Readiness Assessor** | [`keepit-restore-readiness-assessor`](keepit-restore-readiness-assessor/) | Evaluates whether you could actually recover your data right now. Produces an A–F readiness grade based on health, backup freshness, continuity, and historical restore performance. |

## Getting Started

### Step 1: Set Up the Keepit MCP Server

Follow the [Keepit MCP Server setup guide](https://github.com/keepit-official/keepit-mcp) to connect your AI client to your Keepit account. The MCP Server binary (`.mcpb`) is distributed via [GitHub Releases](https://github.com/keepit-official/keepit-mcp/releases) — download the latest release and follow the setup instructions there.

### Step 2: Install Skills

Download the `.skill` files from the [Releases](https://github.com/keepit-official/keepit-skills/releases) page and add them to your AI client.

**Claude Desktop**
1. Open Settings → Skills
2. Add the `.skill` files you want to use

**Claude Code (CLI)**
```
claude skill install keepit-account-health.skill
```

**Cursor / VS Code / AnythingLLM / Jan**
1. Connect the Keepit MCP Server (see the MCP Server repo for client-specific configuration)
2. Add the skill's `SKILL.md` file to your project directory or workspace context — the AI will pick it up as instructions

### Step 3: Start Asking Questions

Once installed, just ask naturally:

- *"Check the health of my Keepit backups"*
- *"Why did my Salesforce backup fail yesterday?"*
- *"Generate a GDPR compliance report for Q4"*
- *"Give me an executive summary for the board"*
- *"Are we ready to recover from a ransomware attack?"*
- *"Show me what happened this week"*

## Supported AI Clients

| Client | Support | Notes |
|--------|---------|-------|
| **Claude Desktop** | Full | Skills install directly as `.skill` files |
| **Claude Code (CLI)** | Full | Skills install via the `/skill` command |
| **Cursor** | Full | Connect MCP server via Settings → MCP; add `SKILL.md` as project context |
| **VS Code (Copilot)** | Full | Configure via `.vscode/mcp.json`; requires Copilot Agent Mode |
| **AnythingLLM** | Full | Good for offline/air-gapped setups with local models |
| **Jan** | Full | Configure via Settings → Advanced Settings → MCP Servers |
| **LM Studio** | Partial | MCP support varies by version; test with your setup |
| **ChatGPT Desktop** | Limited | Stdio-based MCP servers often fail to connect; not recommended |

## Security & Data Access

All skills operate through the Keepit MCP Server, which provides:

- **Read-only access** — Skills query backup metadata only. They cannot modify configurations, initiate restores, or access backup content.
- **Your credentials, your control** — The MCP Server authenticates with your Keepit API credentials, stored locally on your machine. No data passes through third parties beyond the AI provider processing your queries.
- **No persistent storage** — Skills don't store or cache your data. Each analysis runs fresh from live API calls.

## FAQ

**Can skills modify my Keepit configuration?**
No. All data access is read-only.

**Do I need all 10 skills?**
No. Install only the ones relevant to your role. A Backup Admin might use Account Health, Root Cause Analyzer, and Weekly Digest. A Compliance Officer might only need Compliance Audit Log and Retention Policy Auditor.

**Can I customize a skill?**
Yes. Each skill's source lives in this repository — edit `SKILL.md` or the utility scripts directly, then repackage the folder as a ZIP renamed to `.skill`. For example, you could adjust scoring thresholds, add your organization's RPO targets, or customize report formatting.

**Why aren't `.skill` files included in the repository?**
They are build artifacts generated from the source in this repo. Storing binaries in version control bloats the history every time they change. The canonical way to get them is via the [Releases](https://github.com/keepit-official/keepit-skills/releases) page.

**The output looks wrong or incomplete — what should I do?**
Given the experimental nature of this project, this can happen. Please [open an issue](https://github.com/keepit-official/keepit-skills/issues) with details about what you asked, which skill was used, and what the output looked like. Contributions to improve the skill instructions are also welcome via pull request.

**Which Keepit plans support this?**
The MCP Server requires Keepit API access. Check with your Keepit account representative for API availability on your plan.

## License

MIT License — Copyright (c) 2025 Keepit A/S. See [LICENSE](LICENSE) for details.
