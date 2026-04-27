---
name: pipeline-jira
description: Create JIRA issues for CI pipeline failures - COS project conventions and subtask structure
---

# Pipeline JIRA

JIRA CLI commands and COS project conventions for tracking CI pipeline failures.

> Related: `pipeline-failures`

## JIRA CLI Commands

### Listing Issues

```bash
# List issues with JQL query
jira issue list --project COS --type Task -q "summary ~ 'Pipeline Monitoring'" --plain

# List open issues
jira issue list --project COS --status "Open" --plain

# List issues by component
jira issue list --project COS --component RHCOS --plain
```

### Creating Issues

```bash
# Create a sub-task
jira issue create --type Sub-task --parent <PARENT-KEY> --project COS \
  --summary "<job> #<build-number> - <stream> <brief-description>" \
  --label <label> \
  --body "<detailed-markdown-description>" --no-input

# Create a task
jira issue create --type Task --project COS \
  --summary "<summary>" \
  --body "<description>" --no-input
```

### Managing Issues

```bash
# Add a comment (comment text is a positional argument, NOT --body flag)
jira issue comment add <ISSUE-KEY> "<comment-text>"

# Multi-line comment
jira issue comment add <ISSUE-KEY> $'Line one\n\nLine two'

# View issue details
jira issue view <ISSUE-KEY>

# Transition issue status
jira issue move <ISSUE-KEY> "In Progress"
```

> ⚠️ **Important:** `jira issue comment add` takes the comment as a **positional argument**, not a `--body` flag. The `--body` flag is only for `jira issue create`.

## COS Project Conventions

### Project: COS

The COS project is used for CoreOS-related issues.

### Pipeline Monitoring Tasks

Weekly Pipeline Monitoring tasks track CI failures.

**Naming convention:** `Pipeline monitoring - Sprint NNN - Ws YYYYMMDD`
- `Ws` = Week starting (Monday)
- One task per week

**Find current week's monitoring task:**

```bash
# Calculate Monday of current week
DOW=$(date +%u)
if [ "$DOW" -eq 1 ]; then
  MONDAY=$(date +%Y%m%d)
else
  MONDAY=$(date -d "last monday" +%Y%m%d)
fi

# Find this week's monitoring task
PARENT=$(jira issue list --project COS --type Task \
  -q "summary ~ 'Pipeline monitoring' AND summary ~ '$MONDAY'" \
  --plain --no-headers | head -1 | awk '{print $2}')
```

## Deduplication

Load **`pipeline-dedup`** skill for three-pass deduplication logic (exact match, similar failure, semantic analysis) before creating subtasks.

## Sub-task Structure

Each build failure should be its own sub-task (including retries that failed).

**Summary format:**
```
<job> #<build-number> - <stream> [arch] <brief-description>
```

**Important:** Always use the **full Jenkins stream** (e.g., `4.22-9.8` not `4.22`). The stream value comes from the Jenkins build parameters (`STREAM` or `RELEASE`). For `build-arch`, include the architecture after the stream.

**Examples:**
- `build #3456 - rhel-9.6 kernel regression in selinux test`
- `build-arch #1234 - c9s s390x compose failure - repo timeout`
- `build-node-image #4216 - 4.20-9.6 TLS handshake timeout`
- `release #789 - rhel-9.8 extensions-container build failed`

### Sub-task Body Structure

```markdown
## Build Details
- **Job**: <job-name>
- **Build**: #<build-number>
- **Stream**: <stream>
- **Architecture**: <arch>
- **Timestamp**: <timestamp>
- **Duration**: <duration>
- **Jenkins URL**: <url>

## Root Cause Analysis
- **Classification**: <infrastructure | flake | test_regression | package_change | registry_auth | tooling | unknown>
- **Confidence**: <low | medium | high>

<detailed explanation of what caused the failure, including reasoning>

## Evidence

### Log Excerpt
```
<key error lines from console log>
```

### Patterns Observed
- <pattern 1>
- <pattern 2>

## Upstream Links
<!-- Include any relevant links discovered during investigation -->
- **Related Issues**: <GitHub/GitLab issue URLs>
- **Related PRs**: <PR URLs>
- **Related Commits**: <commit URLs if change was identified>
- **Package Build**: <Brew build URL if package change>
- **Test Source**: <link to test code in upstream repo>

## Resolution
- **Status**: <resolved/unresolved/retry-pending>
- **Retry Build**: #<retry-build-number> (if applicable)
- **Fix PR**: <link> (if applicable)
```

## Labels

| Label | When to Use |
|-------|-------------|
| `flake-infrastructure` | Transient infrastructure issues (repo timeouts, GitHub 500, network) |
| `flake-test` | Flaky test failures (passed on rerun) |
| `bug` | Actual bugs requiring code fixes |

## Issue Linking

For CVE tracking, link OCPBUG issues to RHEL vulnerability issues:

```bash
# Links are created via API, type: "Blocks"
# OCPBUG blocks RHEL (outward)
# RHEL is blocked by OCPBUG (inward)
```
