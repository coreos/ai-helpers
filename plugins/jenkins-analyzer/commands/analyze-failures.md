---
description: Analyze Jenkins build failures and generate a summary with root cause findings
argument-hint: "[job-name] [-n count] [--stream stream-name]"
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
  - WebFetch
  - AskUserQuestion
---

# Analyze Jenkins Build Failures

Analyze recent failures from a Jenkins job, fetch console logs, compare with last known good builds, identify root causes, and generate a comprehensive summary.

## Arguments

- `job-name`: Jenkins job name to analyze (optional)
- `-n count`: Number of recent failures to analyze (default: 5)
- `--stream stream-name`: Filter by stream (e.g., `c9s`, `rhel-9.8`, `rhel-9.4`)

If no job name is provided, the command will query the last 5 failures from the following jobs: `build`, `build-arch`, `build-node-image`, and `release`, then ask the user which failure to investigate.

## Execution Steps

### Step 1: List Recent Failures

If a specific job name is provided, run:

```bash
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list <job-name> --status FAILURE -n <count> --pretty
```

If no job name is provided, query failures from all default jobs in parallel:

```bash
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list build --status FAILURE -n 5 --pretty
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list build-arch --status FAILURE -n 5 --pretty
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list build-node-image --status FAILURE -n 5 --pretty
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list release --status FAILURE -n 5 --pretty
```

If a stream is specified, filter the results:

```bash
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list <job-name> --status FAILURE -n 20 --pretty | jq '[.builds[] | select(.description | test("<stream>"; "i"))] | first'
```

Parse the JSON output to get the list of failed builds with their build numbers and timestamps.

### Step 1b: Ask User to Select Failure (when no job specified)

If no job name was provided, display the combined list of recent failures from all jobs to the user in a clear format showing:
- Job name
- Build number
- Build description (includes stream info like `[c9s]`, `[rhel-9.8]`)
- Timestamp
- Brief status

Then use the AskUserQuestion tool to ask which failure(s) they want to investigate. Present the failures as options for the user to choose from.

### Step 2: Get Build Details

For each failed build, get detailed information:

```bash
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds info <job-name> <build-number> --pretty
```

This provides:
- Build parameters (STREAM, FORCE, etc.)
- Trigger cause (upstream job, user, timer)
- Duration and timestamps

### Step 3: Find Last Known Good Build

For each failed build, find the last successful build for the same stream:

```bash
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list <job-name> --status SUCCESS -n 100 --pretty | jq '[.builds[] | select(.description | test("<stream>"; "i")) | select(.description | test("no new build") | not)] | first'
```

Get details of the last known good build:

```bash
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds info <job-name> <good-build-number> --pretty
```

### Step 4: Fetch and Compare Logs

Fetch logs for both the failed and last good build:

```bash
# Failed build log
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds log <job-name> <failed-build-number> | jq -r '.console_log[]' > /tmp/failed_build.log

# Last good build log
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds log <job-name> <good-build-number> | jq -r '.console_log[]' > /tmp/good_build.log
```

### Step 5: Compare Component Versions

Extract and compare key component versions between builds:

```bash
# coreos-assembler version
grep -A 5 "coreos-assembler-git.json" /tmp/failed_build.log | head -10
grep -A 5 "coreos-assembler-git.json" /tmp/good_build.log | head -10

# rpm-ostree version
grep -i "rpm-ostree-[0-9]" /tmp/failed_build.log | head -3
grep -i "rpm-ostree-[0-9]" /tmp/good_build.log | head -3

# Kernel version
grep -i "dracut.*kver" /tmp/failed_build.log | head -1
grep -i "dracut.*kver" /tmp/good_build.log | head -1
```

### Step 6: Investigate Component Changes

If component versions differ (especially coreos-assembler), use GitHub CLI to find changes:

```bash
# Compare cosa commits between builds
gh api repos/coreos/coreos-assembler/compare/<old-commit>...<new-commit> --jq '.commits[] | {sha: .sha[0:7], date: .commit.author.date, message: .commit.message | split("\n")[0]}'

# Get details of suspicious commits
gh api repos/coreos/coreos-assembler/commits/<commit-sha> --jq '{sha: .sha, author: .commit.author.name, message: .commit.message}'

# Get the diff
gh api repos/coreos/coreos-assembler/commits/<commit-sha> --jq '.files[] | {filename: .filename, patch: .patch}'
```

### Step 7: Analyze Failure Details

For the failed build log, identify:
- The specific error message or failure point
- The stage/step where the failure occurred
- Any stack traces or error codes
- Test failures (look for `FAIL:` in kola output)

Look for common patterns:
- `ERROR:` or `FATAL:` messages
- `FAIL:` test results (kola tests)
- Stack traces and exceptions
- Timeout errors
- Network/connectivity issues
- Resource exhaustion (disk, memory)
- Permission denied errors
- Missing dependencies

For test failures, extract the failing test name:
```bash
grep -E "FAIL:|failed:" /tmp/failed_build.log | tail -20
```

### Step 8: Generate Summary

Create a summary report with:

1. **Overview**: Total failures analyzed, date range covered
2. **Failed Build Details**:
   - Build number, stream, and timestamp
   - Error summary (1-2 sentences)
   - Failing test or stage
3. **Last Known Good Build**:
   - Build number and date
   - Key differences from failed build
4. **Component Changes**:
   - coreos-assembler commits between good and bad builds
   - Package version changes
   - Kernel version changes
5. **Root Cause Analysis**:
   - Identified cause with evidence
   - Relevant commits/changes
   - Severity (critical, high, medium, low)
6. **Recommendations**:
   - Specific fix suggestions
   - Links to relevant PRs/issues
   - Workarounds if available

### Step 9: Create JIRA Sub-tasks (Optional)

When requested, create JIRA sub-tasks under the current week's Pipeline Monitoring task to track failures.

IMPORTANT, each new build failure needs to be it's own sub-task, that includes retries that have failed.

First, find the current week's monitoring task:

```bash
jira issue list --project COS --type Task -q "summary ~ 'Pipeline Monitoring'" --plain
```

Then create a sub-task for each failure with appropriate labels:

```bash
jira issue create --type Sub-task --parent <PARENT-KEY> --project COS \
  --summary "<job> #<build-number> - <stream> <brief-description>" \
  --label flake-infrastructure \
  --body "<detailed-markdown-description>" --no-input
```

**Labels to use**:
- `flake-infrastructure`: For transient infrastructure issues (Fedora repo timeouts, GitHub 500 errors, network issues)
- `flake-test`: For flaky test failures
- `bug`: For actual bugs requiring code fixes

The sub-task body should include:
- Build details (job, number, stream, timestamp, duration, Jenkins URL)
- Root cause analysis
- Error messages (in code blocks)
- Source file locations if applicable
- Resolution status and retry build numbers

To add comments to existing issues:

```bash
jira issue comment add <ISSUE-KEY> "<comment-text>" --no-input
```

### Step 10: Trigger Build Retries (Optional)

When requested, trigger a retry for a failed build, IMPORTANT, make sure to check if a build is already running before doing a retry.

```bash
podman run --rm --network=host --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py jobs build <job-name> -p STREAM=<stream> -p FORCE=true --pretty
```

**Note**: Use `jobs build` (not `builds trigger`) to trigger new builds.

Monitor the retry status:

```bash
podman run --rm --network=host --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds list <job-name> -n 5 --pretty
```

## Output Format

Present the summary in a clear, readable format with sections and bullet points. Include:
- Jenkins build URLs for reference
- GitHub compare URLs for component changes
- Specific commit SHAs and messages for root causes

## Example Usage

```
/analyze-failures                           # Query all default jobs and let user choose
/analyze-failures build                     # Analyze failures from build job
/analyze-failures build --stream c9s        # Analyze c9s stream failures
/analyze-failures build --stream rhel-9.8   # Analyze rhel-9.8 stream failures
/analyze-failures build -n 3                # Analyze last 3 failures
```

## Prerequisites

- `.env` file in current directory with Jenkins credentials:
  - `JENKINS_URL`
  - `JENKINS_USER`
  - `JENKINS_API_TOKEN`
- `podman` available and able to pull `quay.io/cverna/coreos-agent-tools`
- `gh` (GitHub CLI) installed and authenticated for commit analysis
- `jq` installed for JSON parsing

## Additional Commands

The jenkins.py CLI provides additional useful commands:

```bash
# List all jobs
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py jobs list --pretty

# Get job info (health, last builds)
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py jobs info <job-name> --pretty

# View build queue
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py queue list --pretty

# List nodes
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py nodes list --pretty

# List build artifacts
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py builds artifacts <job-name> <build-number> --pretty

# Backwards compatible failures command
podman run --rm --env-file .env quay.io/cverna/coreos-agent-tools jenkins.py failures <job-name> -n 5 --pretty
```
