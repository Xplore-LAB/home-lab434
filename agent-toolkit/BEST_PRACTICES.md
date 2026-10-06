# BEST_PRACTICES.md - Agent File Workflow Rules

## 1. Canonical Folder Map
- `scaffold/` = templates and project skeletons
- `research/` = analysis, surveys, and notes
- `memory/` = daily logs and experience
- `utils/` = reusable code
- `scripts/` = automation

## 2. Naming Rules
✅ Use: `2026-10-06-mimo-survey.md`
✅ Use: `run_experiments.py`
❌ Never use: `final-final-v2.md`
❌ Never use: `temp/`, `tmp/`, `new folder/`

## 3. Find-Before-Create Rule
Before creating any file:
1. Search for existing candidates by topic/slug
2. If likely file exists, update it instead of creating new one
3. If uncertain, ask one disambiguation question with exact paths

## 4. Duplicate Prevention
- Choose one canonical file
- Move superseded files to archive/
- Add note: "superseded by [path]"

## 5. Completion Proof
For every write task, report:
- Exact path written
- Whether file was created vs updated
- 1-line summary of changes

## 6. Safety Rules
- Never write outside allowed directories
- Never delete without confirmation
- Never auto-modify permissions
- Always validate paths with realpath()
