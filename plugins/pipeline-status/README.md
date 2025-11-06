# CoreOS Pipeline Status Analysis

Analyze CoreOS pipeline build status for a specific date using the containerized CoreOS pipeline status tool.

## Usage
- `coreos_pipeline_status` - Analyze builds for today's date
- `coreos_pipeline_status YYYY-MM-DD` - Analyze builds for specific date

## Environment Variable

You need a .env file in your $HOME path with the following variables defined:

```
# Slack Configuration
# Get these tokens from your Slack workspace
SLACK_XOXC_TOKEN=xoxc-some_token
SLACK_XOXD_TOKEN=xoxd-some_token

# Slack channel ID (e.g., C1234567890)
# jenkins-rhcos-art
SLACK_CHANNEL=the_slack_channel_id
```
