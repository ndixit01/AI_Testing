# CLAUDE.md — AI Assistant Guide for AI_Testing

This file provides essential context for AI assistants (Claude Code and similar tools)
working in this repository. Update this file as the project evolves.

---

## Repository Overview

**Repository:** `ndixit01/AI_Testing`
**Purpose:** A repository for AI-driven testing, experimentation, and automation workflows.
**Status:** Newly initialized — this file serves as the foundational guide.

---

## Repository Structure

This is a new repository. As files and directories are added, document them here:

```
AI_Testing/
├── CLAUDE.md          # This file — AI assistant guide
└── (project files added over time)
```

Update this tree whenever significant structural changes are made.

---

## Development Branch Conventions

- All AI-assisted development branches must be prefixed with `claude/`
- Branch names follow the pattern: `claude/<task-slug>-<session-id>`
- Example: `claude/claude-md-mm51pjqdvpmxzhpv-Lwlm5`
- Never push directly to `main` without a pull request review
- Always push with: `git push -u origin <branch-name>`

---

## Git Workflow

1. **Branch** off `main` (or the specified feature branch) using the naming convention above
2. **Develop** your changes with clear, focused commits
3. **Commit** with descriptive messages (see commit message guidelines below)
4. **Push** to the remote branch: `git push -u origin <branch-name>`
5. **Open a PR** — never merge directly to `main`

### Commit Message Guidelines

- Use the imperative mood: "Add feature" not "Added feature"
- Keep the subject line under 72 characters
- Separate subject from body with a blank line when extra context is needed
- Reference issue numbers when applicable: `Fixes #123`
- Include the Claude Code session URL at the end of the body

**Format:**
```
<type>: <short summary>

<optional body explaining why, not just what>

<optional session URL>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

---

## Code Conventions

Since no language or framework is established yet, conventions will be added here
as the project takes shape. When adding new languages/frameworks, document:

- **Language version** (e.g., Python 3.12, Node 20)
- **Formatter** (e.g., `black`, `prettier`)
- **Linter** (e.g., `ruff`, `eslint`)
- **Test runner** (e.g., `pytest`, `jest`)
- **Package manager** (e.g., `pip`/`uv`, `npm`/`pnpm`)
- **How to run tests** (command + expected output)
- **How to run linting** (command)

### General Principles

- Prefer explicit over implicit
- Avoid over-engineering: only build what is needed now
- Keep functions small and single-purpose
- Write tests alongside new functionality
- Do not leave dead code or commented-out blocks without explanation

---

## Testing Conventions

Document test structure here as tests are added:

- Test files should be co-located with source files or placed in a `tests/` directory
- Test functions must have descriptive names that explain what is being tested
- Prefer deterministic tests — avoid relying on external network calls or time-sensitive logic
- CI must pass before merging

---

## Environment Setup

Document setup steps here as the project evolves. Typical things to capture:

```bash
# Clone the repository
git clone <repo-url>
cd AI_Testing

# Install dependencies (add actual command once stack is chosen)
# e.g.: pip install -r requirements.txt
#       npm install

# Run tests (add actual command once test framework is chosen)
# e.g.: pytest
#       npm test

# Run linting (add actual command once linter is chosen)
# e.g.: ruff check .
#       npm run lint
```

---

## AI Assistant Instructions

### General Guidelines

- **Read before editing.** Always read the relevant files before making changes.
- **Minimal changes.** Only modify what is directly required by the task.
- **Do not add unrequested features**, refactors, comments, or docstrings.
- **Do not create files** unless absolutely necessary.
- **Do not hardcode secrets** or credentials anywhere in the codebase.
- **Avoid backwards-compatibility shims** — change the code directly.
- **Prefer editing existing files** over creating new ones.

### Security

- Never introduce command injection, XSS, SQL injection, or other OWASP Top 10 vulnerabilities.
- Do not commit secrets, API keys, or credentials.
- Add `.env` and similar files to `.gitignore`.
- Only validate input at system boundaries (user input, external APIs).

### When You Are Unsure

- If a requirement is ambiguous, ask for clarification before implementing.
- If you encounter an obstacle, do not brute-force through it — investigate or ask.
- If unexpected files or state exist, investigate before deleting or overwriting.

### Risky Actions Requiring Explicit User Confirmation

Always confirm with the user before:

- Deleting files or branches
- Force-pushing (`--force`)
- Resetting commits (`git reset --hard`)
- Modifying CI/CD pipeline files
- Pushing to `main` or any protected branch
- Dropping database tables or running destructive migrations
- Sending messages or posting to external services

---

## CI/CD

Document CI/CD pipelines here once configured. Typical things to capture:

- CI provider (GitHub Actions, CircleCI, etc.)
- Workflow file location (e.g., `.github/workflows/`)
- What CI checks run (lint, test, build)
- How to trigger CI manually
- Required checks before merging a PR

---

## Dependency Management

Document dependency management practices once a language/framework is chosen:

- List package managers and their lock files
- Explain how to add/remove dependencies
- Note any version pinning policies

---

## Changelog

| Date       | Author         | Change                                      |
|------------|----------------|---------------------------------------------|
| 2026-02-27 | Claude Code    | Initial CLAUDE.md created for new repository |

---

*This CLAUDE.md should be kept up to date as the repository grows. When adding
a new language, framework, tool, or workflow, update the relevant section above.*
