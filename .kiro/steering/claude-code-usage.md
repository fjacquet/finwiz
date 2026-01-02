# Claude Code Usage Guide

*Based on guidance from Patrick Ellis and Anand Tyagi (2025).*

## Context is King

The most important factor for agent performance. Methods to provide context:

| Method                  | Purpose                                             |
| ----------------------- | --------------------------------------------------- |
| **CLAUDE.md**           | Main context file - becomes part of every prompt    |
| **Subfolder CLAUDE.md** | Hierarchical context - Claude fetches relevant ones |
| **`/add-dir`**          | Add entire directories to context                   |
| **`/memory`**           | Add memories to CLAUDE.md easily                    |
| **Sub-agents**          | Use to summarize and keep context manageable        |
| **MCPs**                | Context7, GitHub, Playwright for live data          |

## When to Use Claude Code vs IDE Tools

**Use Claude Code for:**

- Multi-step processes and complex tasks
- Starting new projects
- Exploring/ramping up on codebases
- Refactoring large files
- Generating files requiring info from many sources
- Generating tests with feedback loops

**Use IDE tools (Cursor, etc.) for:**

- Specific problems in specific files/lines
- One-step tasks
- Fine-grained control over edits

## Essential Commands

| Command    | Use Case                              |
| ---------- | ------------------------------------- |
| `/model`   | Switch between Sonnet 4 and Opus 4    |
| `/add-dir` | Add directory context                 |
| `/memory`  | Add memories to CLAUDE.md             |
| `/plan`    | Enter planning mode for complex tasks |
| `/clear`   | Clear context between different tasks |

## Sub-agents and Planning

- **Planning Mode**: Use before complex tasks to think through execution steps
- **Sub-agents**: Spawn for specific sub-tasks; summarize large contexts
- Keep everything in model context; use sub-agents to summarize when needed

## Multi-Agent Workflows

**Git Worktrees for Parallel Development:**

```bash
git worktree add <PATH> <BRANCH-NAME>
git worktree list
```

This enables running multiple Claude Code instances on different branches simultaneously.

## The Agent Loop

```
Get Task → Add to Task List → Do Task → Reflect on Output → Output
```

Each "Do Task" step involves tool calls: reading files, searching, executing commands, or MCP calls.

## Key Principles

1. **Use Claude as an independent agent** - a "super sidekick"
2. **Plan before executing** - use plan mode or external plan files
3. **Maximize context** - CLAUDE.md, commands, MCPs
4. **Delegate confidently** to sub-agents
5. **Think of prompts and specs as source code**

## Resources

- [Mastering Claude Code in 30 minutes](https://www.youtube.com/watch?v=6eBSHbLKuN0)
- [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Claude Code Commands Directory](https://claudecodecommands.directory)
