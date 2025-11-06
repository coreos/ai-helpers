# CoreOS Pipeline Status Analysis

Analyze CoreOS pipeline build status for a specific date using the containerized CoreOS pipeline status tool.

## Usage
- `coreos_pipeline_status` - Analyze builds for today's date
- `coreos_pipeline_status YYYY-MM-DD` - Analyze builds for specific date

## Implementation

### Step 1: Execute Pipeline Status Query
```bash
# Set date parameter (defaults to current date)
date=${1:-$(date +%Y-%m-%d)}
podman run --rm --env-file .env quay.io/cverna/coreos-pipeline-status:latest --date $date --pretty
```

### Step 2: Analysis Requirements
1. **Build Summary**: Count total builds, failures, and successes
2. **Version Breakdown**: Use exact version names from Jenkins messages (e.g., rhel-10.1, 4.21-9.6, 4.20-10.1)
3. **Job Type Analysis**: Break down by job type (architecture builds, release builds, node-image builds)
4. **Architecture Analysis**: Break down by architecture (x86_64, ppc64le, s390x, aarch64)
5. **Failure Rate**: Calculate overall failure percentage
6. **Notable Issues**: Highlight patterns or user comments about failures

### Step 3: Report Generation
Create a concise summary including:

#### Required Sections:
- **Total Messages**: Count of pipeline notifications
- **Build Status Overview**: Success/failure counts with emoji indicators
- **Builds by Version & Job Type**: Version-specific breakdowns using exact Jenkins message names
- **Job Type Breakdown**: Success/failure rates by job type (arch builds, releases, node-image builds)
- **Architecture Breakdown**: Per-architecture success/failure rates
- **Notable Issues**: Key problems or patterns observed

#### Status Indicators:
- 🔥 Failed builds (red color in Slack)
- ✨ Successful builds (green color in Slack)
- 🚅 Release builds (yellow/orange color in Slack)

#### Formatting Requirements:
- Use markdown headers and bullet points
- Include build numbers and Jenkins url links
- Calculate and display failure percentages
- Highlight architecture-specific issues (e.g., 100% ppc64le failures)

### Step 4: Slack Summary Generation

Finish the status with a short slack message to highlight the failures, see example below:

```
🚨 CoreOS Pipeline Summary - 2025-09-17
21% failure rate (3/14 builds failed)

node-image builds:
- 4.21-10.1: 0/1 🔥
- 4.21-9.6: 0/2 🔥
- 4.20-10.1: 1/1 ✅

RHCOS & Release builds:
- rhel-10.1: 5/5 ✅
- 4.15-9.2: 5/5 ✅
```

#### Summary Guidelines:
- Lead with overall failure percentage
- Highlight job type specific failures (e.g., node-image builds vs arch builds)
- Use exact version names from Jenkins messages
- Group by job type when patterns emerge (e.g., all node-image builds failing)
- End with builds by version table using ✅/🔥 indicators
- Keep under 10 lines for urgent visibility
- Use emojis for quick visual scanning

### Step 5: Post Summary to Slack

After generating the analysis and summary, post the summary to the Slack channel:

```bash
podman run --rm --env-file .env quay.io/cverna/coreos-pipeline-status:latest --summary "SLACK_SUMMARY_TEXT"
```

Example:
```bash
podman run --rm --env-file .env quay.io/cverna/coreos-pipeline-status:latest --summary "🚨 CoreOS Pipeline Summary - 2025-09-17
21% failure rate (3/14 builds failed)

node-image builds:
- 4.21-10.1: 0/1 🔥
- 4.21-9.6: 0/2 🔥
- 4.20-10.1: 1/1 ✅

RHCOS & Release builds:
- rhel-10.1: 5/5 ✅
- 4.15-9.2: 5/5 ✅"
```