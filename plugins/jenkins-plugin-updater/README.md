# Jenkins Plugin Updater

Check Jenkins plugin versions for compatibility with the base OpenShift Jenkins image and find the highest version that works without requiring fast-tracks.

## Standalone usage

The script runs anywhere with Python 3.9+ and no external dependencies.

```bash
# Check all plugins against a running Jenkins pod
./tools/check-plugin-compat.py \
  --from-pod jenkins-xyz -n fedora-coreos-pipeline \
  --plugins-file jenkins/controller/plugins.txt

# Check specific plugins against a saved baseline
./tools/check-plugin-compat.py \
  --base-plugins base-plugins.txt \
  --jenkins-version 2.541.3 \
  --plugins mcp-server,pipeline-graph-view

# Show what fast-tracks are needed for a target version
./tools/check-plugin-compat.py \
  --from-pod jenkins-xyz -n fedora-coreos-pipeline \
  --plugins mcp-server:0.194 \
  --show-fast-tracks

# JSON output
./tools/check-plugin-compat.py \
  --from-pod jenkins-xyz -n fedora-coreos-pipeline \
  --plugins-file jenkins/controller/plugins.txt \
  --json
```

### Capturing a baseline

```bash
oc logs <pod-name> -n fedora-coreos-pipeline \
  | grep '\.jpi:' \
  | sed 's|.*/||; s|\.jpi:| |' \
  | sort > base-plugins.txt
```

## Claude Code usage

If installed as a plugin, use the `/check-plugin-compat` slash command.

## How it works

For each plugin, the tool:
1. Fetches available versions from `archives.jenkins.io`
2. Downloads each version's HPI file and parses `META-INF/MANIFEST.MF`
3. Checks `Jenkins-Version` against the running Jenkins core
4. Checks ALL dependencies (including optional) against installed base plugins
5. Reports the highest version where all checks pass

Jenkins enforces minimum versions for optional dependencies when the plugin is already installed — this is the most common source of unexpected failures.
