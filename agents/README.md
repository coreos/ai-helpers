# Agents

This directory contains Claude Code agent definitions (`.md` files) that provide specialized instructions and behavior for specific development tasks.

## Directory Structure

```
agents/
├── README.md           # This file
└── {agent-name}/
    ├── agent.md        # Agent definition (instructions for Claude)
    └── README.md       # User documentation
```

## Creating a New Agent

1. **Create directory**: `mkdir -p agents/{agent-name}`
2. **Create `agent.md`**: Write agent instructions (what the AI should do)
3. **Create `README.md`**: Document usage, prerequisites, and required MCP tools
4. **Test**: Load with `@agent-{agent-name}` and verify behavior

## Required Documentation

Each agent's `README.md` must include:
- **Overview**: What the agent does
- **Prerequisites**: Required tools and credentials
- **Required MCP Tools**: List MCP servers needed (use [Docker MCP Toolkit](https://github.com/docker/mcp) or [ToolHive](https://toolhive.com/) for installation)
- **Usage**: How to invoke the agent
- **Examples**: Real usage scenarios

## Loading Agents

```bash
# In Claude Code, mention the agent
@agent-issuesolver <github-issue-url>

# Agent instructions are now active for this conversation
```

## Available Agents

See subdirectories for specific agents:
- **issuesolver**: GitHub issue triage, planning, and implementation

## Support

- **Repository**: https://github.com/openshift-eng/ai-helpers
- **MCP Tools**: [Docker MCP Toolkit](https://github.com/docker/mcp) | [ToolHive](https://toolhive.com/)