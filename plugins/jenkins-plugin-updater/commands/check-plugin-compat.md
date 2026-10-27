---
name: check-plugin-compat
description: Check Jenkins plugin versions for compatibility with the base image and find the highest working version without fast-tracks
allowed-tools: Bash, Read, Edit, Write
---

# Jenkins Plugin Compatibility Checker

You have access to `$PLUGIN_ROOT/tools/check-plugin-compat.py` — a standalone Python script that checks plugin version compatibility.

## How to use

### From a running Jenkins pod (recommended)

```bash
python3 $PLUGIN_ROOT/tools/check-plugin-compat.py \
  --from-pod <pod-name> -n fedora-coreos-pipeline \
  --plugins-file jenkins/controller/plugins.txt
```

### From a saved base plugins file

First capture the baseline from a running pod:
```bash
oc logs <pod-name> -n fedora-coreos-pipeline | grep '\.jpi:' | sed 's|.*/||; s|\.jpi:| |' | sort > /tmp/base-plugins.txt
```

Then check:
```bash
python3 $PLUGIN_ROOT/tools/check-plugin-compat.py \
  --base-plugins /tmp/base-plugins.txt \
  --jenkins-version 2.541.3 \
  --plugins-file jenkins/controller/plugins.txt
```

### Check specific plugins

```bash
python3 $PLUGIN_ROOT/tools/check-plugin-compat.py \
  --from-pod <pod-name> -n fedora-coreos-pipeline \
  --plugins mcp-server,pipeline-graph-view
```

### Check what fast-tracks a specific version needs

```bash
python3 $PLUGIN_ROOT/tools/check-plugin-compat.py \
  --from-pod <pod-name> -n fedora-coreos-pipeline \
  --plugins mcp-server:0.194 \
  --show-fast-tracks
```

### JSON output for scripting

```bash
python3 $PLUGIN_ROOT/tools/check-plugin-compat.py \
  --from-pod <pod-name> -n fedora-coreos-pipeline \
  --plugins-file jenkins/controller/plugins.txt \
  --json
```

## Key concepts

- **Base image plugins**: Plugins baked into the openshift/jenkins image. You can't change their version without fast-tracking.
- **Fast-track**: Pinning a newer version of a base image plugin in `plugins.txt` to satisfy a dependency. Add to the fast-track section at the bottom.
- Jenkins enforces ALL dependency version minimums, **including optional ones**, when the dependency plugin is already installed.
- A plugin may also fail if it requires a newer Jenkins core version than what's running.

## After finding compatible versions

Update `jenkins/controller/plugins.txt` and test with an s2i build:
```bash
oc start-build jenkins-s2i --from-dir=. -n fedora-coreos-pipeline
```
Then check the Jenkins pod logs for dependency errors.
