# Contributing

Contributions are welcome — bug fixes, skill improvements, and new skills all appreciated.

## Ways to contribute

- **Bug reports** — something outputting wrong results, a skill failing to run, a broken link
- **Skill improvements** — better instructions, updated scoring logic, improved example outputs
- **New skills** — coverage for a scenario not yet addressed

## Getting started

1. Fork the repository
2. Create a branch (`git checkout -b my-fix`)
3. Make your changes in `skills/<skill-name>/`
4. Open a pull request with a clear description of what changed and why

## Skill structure

Each skill lives in `skills/<skill-name>/` and contains:

```
skills/keepit-example/
├── SKILL.md                  # AI instruction set — the core of the skill
├── LICENSE.txt
├── references/
│   └── example-outputs.md   # Sample reports for consistent formatting
└── scripts/
    └── example_utils.py     # Reference scoring/analysis logic
```

When editing a skill, the most impactful changes are usually to `SKILL.md` — the instructions the AI follows.

## Guidelines

- Keep skill instructions accurate against the [Keepit MCP Server](https://github.com/keepit-official/keepit-mcp) API
- Test against a live Keepit environment where possible
- Example outputs should reflect realistic data, not ideal-case scenarios

## License

By contributing, you agree your changes will be licensed under the [MIT License](LICENSE).
