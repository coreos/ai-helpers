# Jenkins Analyzer Plugin

Analyze Jenkins build failures, compare with last known good builds, and generate summaries with root cause findings.

## Features

- **`/analyze-failures`** command: Analyze recent Jenkins failures with deep root cause investigation
- **`failure-analyzer`** agent: Autonomous analysis when you discuss build failures
- **Stream filtering**: Focus on specific streams (c9s, rhel-9.8, rhel-9.4, etc.)
- **Log comparison**: Compare failed builds with last known good builds
- **Component tracking**: Identify version changes in coreos-assembler, rpm-ostree, kernel
- **GitHub integration**: Automatically investigate upstream commits that may have caused failures

## Prerequisites

1. `.env` file in your working directory with Jenkins credentials:
   ```
   JENKINS_URL=https://your-jenkins-server.com
   JENKINS_USER=your-username
   JENKINS_API_TOKEN=your-api-token
   ```

2. `podman` installed and able to pull `quay.io/cverna/coreos-agent-tools`

3. `gh` (GitHub CLI) installed and authenticated for commit analysis

4. `jq` installed for JSON parsing

## Usage

### Command

```bash
# Query all default jobs and let user choose which failure to investigate
/analyze-failures

# Analyze failures from a specific job
/analyze-failures build

# Analyze failures for a specific stream
/analyze-failures build --stream c9s
/analyze-failures build --stream rhel-9.8

# Analyze last 3 failures
/analyze-failures build -n 3
```

### Agent

The agent triggers when you explicitly ask about Jenkins failures:
- "Can you analyze the recent Jenkins failures?"
- "Why are the builds failing?"
- "Check the last 3 build failures for build-node-image"
- "What's the last good build for c9s?"

## Analysis Workflow

The plugin follows this investigation workflow:

1. **List failures** - Find recent failed builds, optionally filtered by stream
2. **Get build details** - Retrieve build parameters, trigger cause, duration
3. **Find last known good** - Locate the most recent successful build for the same stream
4. **Compare logs** - Download and compare console logs between good and bad builds
5. **Track component versions** - Compare coreos-assembler, rpm-ostree, kernel versions
6. **Investigate changes** - Use GitHub CLI to analyze commits between versions
7. **Generate report** - Summarize findings with root cause and recommendations

## Output

The analysis provides:
- Overview of failures analyzed
- Failed build details with error summary
- Last known good build comparison
- Component version changes (cosa, rpm-ostree, kernel)
- Root cause analysis with evidence (commit SHAs, diffs)
- Actionable recommendations with links to relevant PRs/issues

## Jenkins CLI Commands

The plugin uses `jenkins.py` which provides these command groups:

```bash
# Jobs management
jenkins.py jobs list [--folder] [--filter]
jenkins.py jobs info <job>
jenkins.py jobs build <job> [-p KEY=VALUE]
jenkins.py jobs abort <job> <build>

# Builds management
jenkins.py builds list <job> [--status] [-n] [-d]
jenkins.py builds info <job> <build>
jenkins.py builds log <job> <build> [-o file]
jenkins.py builds artifacts <job> <build>

# Queue management
jenkins.py queue list
jenkins.py queue cancel <id>

# Nodes management
jenkins.py nodes list
jenkins.py nodes info <node>

# Backwards compatibility
jenkins.py failures <job> [-n] [-d]
```

All commands support `--pretty` for formatted JSON output.

## Installation

Copy to your Claude Code plugins directory or use `--plugin-dir`:

```bash
claude --plugin-dir /path/to/jenkins-analyzer
```
