# FILE-MAP.md - Workspace Directory Convention

## Root: /home/lab434/.openclaw/workspace/agent-toolkit/

| Directory | Purpose |
|-----------|---------|
| `scaffold/` | Project templates and scaffolding |
| `research/` | Research notes and literature reviews |
| `memory/` | Daily logs and experience notes |
| `utils/` | Shared utilities and helpers |
| `hooks/` | Policy enforcement hooks |
| `templates/` | Reusable templates |
| `scripts/` | Automation scripts |
| `config/` | Configuration files |

## Rules

1. **Never use /tmp/** for persistent work - use `scratch/` instead
2. **No loose files at root** - everything has a home
3. **Find before create** - search existing files before creating new ones
4. **DATE-prefix for temporal files** - YYYY-MM-DD-topic-slug.md
5. **Lowercase with hyphens** - no spaces, no camelCase

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Temporal | YYYY-MM-DD-topic-slug.md | 2026-10-06-mimo-survey.md |
| Project | project-name/ | mimo-v2.6-experiments/ |
| Script | verb-noun.py | run_experiments.py |
| Config | config-name.yml | experiment-config.yml |
