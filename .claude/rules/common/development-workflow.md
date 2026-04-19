# Development Workflow

> This file extends [common/git-workflow.md](./git-workflow.md) with the full feature development process that happens before git operations.

The Feature Implementation Workflow describes the development pipeline: research, planning, TDD, code review, and then committing to git.

## Feature Implementation Workflow

0. **Research & Reuse** _(mandatory before any new implementation)_
   - **GitHub code search first:** Run `gh search repos` and `gh search code` to find existing implementations, templates, and patterns before writing anything new.
   - **Exa MCP for research:** Use `exa-web-search` MCP during the planning phase for broader research, data ingestion, and discovering prior art.
   - **Check package registries:** Search npm, PyPI, crates.io, and other registries before writing utility code. Prefer battle-tested libraries over hand-rolled solutions.
   - **Search for adaptable implementations:** Look for open-source projects that solve 80%+ of the problem and can be forked, ported, or wrapped.
   - Prefer adopting or porting a proven approach over writing net-new code when it meets the requirement.

1. **Plan First**
   - Use **planner** agent to create implementation plan
   - Generate planning docs before coding: PRD, architecture, system_design, tech_doc, task_list
   - Identify dependencies and risks
   - Break down into phases

2. **TDD Approach**
   - Use **tdd-guide** agent
   - Write tests first (RED)
   - Implement to pass tests (GREEN)
   - Refactor (IMPROVE)
   - Verify 80%+ coverage

3. **Code Review**
   - Use **code-reviewer** agent immediately after writing code
   - Address CRITICAL and HIGH issues
   - Fix MEDIUM issues when possible

4. **Commit & Push**
   - Detailed commit messages
   - Follow conventional commits format
   - See [git-workflow.md](./git-workflow.md) for commit message format and PR process

---

## Rules Installation

This repository contains a layered set of coding standards under the `rules/` directory. Install them into `~/.claude/rules/` so Claude Code automatically applies them to every project.

### Structure

```
rules/
  common/      ← language-agnostic principles (always install)
  typescript/  ← TypeScript / JavaScript specific
  python/      ← Python specific
  golang/      ← Go specific
  swift/       ← Swift specific
```

### How to install

**Option A – tell Claude Code directly (recommended):**

Just say in the Claude Code chat:
> "幫我安裝 typescript 和 python 的規範" （or whichever languages your project uses）

Claude Code will run the copy commands for you.

**Option B – run the install script:**

```bash
# Install common + one or more language rule sets
./install.sh typescript
./install.sh python golang
```

**Option C – copy manually:**

```bash
# Common rules are required for all projects
cp -r rules/common ~/.claude/rules/common

# Add only the languages your project uses
cp -r rules/typescript ~/.claude/rules/typescript
cp -r rules/python     ~/.claude/rules/python
cp -r rules/golang     ~/.claude/rules/golang
cp -r rules/swift      ~/.claude/rules/swift
```

> ⚠️ Always copy **entire directories** with `cp -r`. Never flatten files into one directory — language-specific files share the same filenames as common files and will overwrite them.

### When Claude Code reads these rules

Claude Code loads `~/.claude/rules/**/*.md` at startup. Files with a `paths:` frontmatter (e.g. `paths: ["**/*.ts"]`) are applied only when Claude edits matching files. Common rules apply to every file.

### Language selection guide

| Your stack | Install |
|---|---|
| Node.js / React / Next.js | `common` + `typescript` |
| Python / Django / FastAPI | `common` + `python` |
| Go | `common` + `golang` |
| iOS / macOS | `common` + `swift` |
| Full-stack (e.g. Next.js + Python API) | `common` + `typescript` + `python` |
