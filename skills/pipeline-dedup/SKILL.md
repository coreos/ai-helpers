---
name: pipeline-dedup
description: Deduplication logic for CI pipeline failures - check Jira for existing tracking with semantic analysis
---

# Pipeline Deduplication

Check if a failure is already tracked in Jira before investigating or creating issues.

## Prerequisites

Load **`pipeline-jira`** skill first to get the current week's parent task (`$PARENT`).

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `JOB` | Yes | Jenkins job name (build, build-arch, build-node-image) |
| `BUILD` | Yes | Build number |
| `STREAM` | Yes | Jenkins stream parameter |
| `ARCH` | For build-arch | Architecture (aarch64, s390x, ppc64le, x86_64) |

## Deduplication Workflow

### Pass 1: Exact Build Match

Check if this exact build already has a subtask:

```bash
jira issue list --parent $PARENT \
  -q "summary ~ '$JOB #$BUILD'" --plain --no-headers
```

**If found → Return `EXACT_MATCH: <JIRA-KEY>`**

---

### Pass 2: Similar Failure Check (Same Job + Stream + Arch)

Check for open subtasks with same job, stream, and architecture:

```bash
# For build-arch (include architecture in search)
jira issue list --parent $PARENT -s~Closed \
  -q "summary ~ '$JOB' AND summary ~ '$STREAM' AND summary ~ '$ARCH'" \
  --plain --no-headers

# For build / build-node-image (no architecture)
jira issue list --parent $PARENT -s~Closed \
  -q "summary ~ '$JOB' AND summary ~ '$STREAM'" \
  --plain --no-headers
```

**If found → Return `RELATED_ISSUE: <JIRA-KEY>`**

---

### Pass 3: Semantic Analysis

For failures not caught by Pass 1 or 2, fetch all open subtasks and analyze semantically:

```bash
# Fetch all open subtasks with summaries
jira issue list --parent $PARENT -s~Closed --plain --no-headers
```

Provide the failure details and fetched subtask list to analyze:

**Failure to check:**
- Job: `$JOB`
- Build: `$BUILD`
- Stream: `$STREAM`
- Arch: `$ARCH` (if applicable)
- Root cause hint: (if known from triage)

**Analysis prompt:**
> Review these open Jira subtasks and determine if any track the same root cause as this failure. Consider:
> - Same stream/arch combination
> - Same error patterns (cloud upload, chronyd, registry auth, etc.)
> - Related downstream jobs (build failure caused by build-arch failure)
>
> Return the matching Jira key if found, or "NO_MATCH" if this appears to be a new distinct issue.

**If LLM identifies a match → Return `SEMANTIC_MATCH: <JIRA-KEY>`**

---

## Output Format

Return one of:

| Result | Meaning | Action |
|--------|---------|--------|
| `EXACT_MATCH: COS-XXXX` | Exact build already tracked | Skip - no action needed |
| `RELATED_ISSUE: COS-XXXX` | Same job+stream+arch tracked | Comment on existing issue |
| `SEMANTIC_MATCH: COS-XXXX` | Same root cause identified | Comment on existing issue |
| `NEW_FAILURE` | No existing tracking | Proceed with triage/creation |

## Comment Template for Duplicate Occurrences

When a `RELATED_ISSUE` or `SEMANTIC_MATCH` is found, add a comment to the existing issue instead of creating a duplicate.

**Note:** For `EXACT_MATCH`, no comment is needed - the build is already tracked in the issue summary.

```bash
jira issue comment add <EXISTING-KEY> $'Additional occurrence detected:
- **Build:** [#<build>](<jenkins-url>)
- **Timestamp:** <timestamp>

Same failure pattern - consolidating under this issue.' --no-input
```

## Batch Mode (for pipeline-monitor)

When checking multiple failures, optimize by fetching subtasks once:

```bash
# Fetch all subtasks once
jira issue list --parent $PARENT --plain --no-headers > /tmp/subtasks.txt
```

Then perform Pass 1 and Pass 2 locally by parsing the cached file. Only run Pass 3 (semantic analysis) for failures that pass both checks.
