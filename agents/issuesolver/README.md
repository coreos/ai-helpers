# IssueSolver10000

An autonomous agent for GitHub issue triage, evaluation, and implementation.

## Overview

Triages GitHub issues, creates solution plans in Obsidian, and implements fixes in isolated git worktrees.

**Workflow**: Evaluation → Planning (with human approval) → Implementation

## Prerequisites

- **Git** with worktree support (2.5.0+)
- **Obsidian** with Local REST API plugin installed
- **GitHub Personal Access Token** with `repo` scope

## Required MCP Tools

Install via [Docker MCP Toolkit](https://github.com/docker/mcp) or [ToolHive](https://toolhive.com/):

1. **GitHub MCP Server** - For fetching issues and repository access
2. **Obsidian MCP Server** - For creating solution plans (requires Obsidian Local REST API plugin)
3. **Fetch MCP Server** - For retrieving documentation (usually included by default)

## Usage

Start Claude in your repository root, then:

```
@agent-issuesolver <github-issue-url>
```

**Agent workflow:**
1. Evaluates the issue
2. Creates solution plan in Obsidian
3. Waits for your approval
4. Implements in new worktree (after approval)

**To implement existing plan:**
```
Implement solution for issue #123 from my Obsidian vault
```

## Support

- **Repository**: https://github.com/openshift-eng/ai-helpers
- **MCP Setup**: [Docker MCP Toolkit](https://github.com/docker/mcp) | [ToolHive](https://toolhive.com/)
