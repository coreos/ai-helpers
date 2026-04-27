---
name: rhcos-artifacts
description: RHCOS build artifacts, package comparison, and coreos-assembler version tracking
---

# RHCOS Artifacts

Build artifacts, package comparison commands, and coreos-assembler version tracking.

> Related: `rhcos-build-pipeline`, `pipeline-failures`

## Build Artifacts

Common artifacts available from builds:

| Artifact | Description |
|----------|-------------|
| `coreos-assembler-git.json` | cosa version info |
| `manifest-lock.*.json` | Package manifest locks |
| `builds.json` | Build metadata |
| `meta.json` | Build metadata |

## Artifact Commands

```bash
# List build artifacts
coreos-tools jenkins builds artifacts <job-name> <build-number>

# Download a specific artifact
coreos-tools jenkins builds artifacts <job-name> <build-number> --download <artifact-name>

# Download to specific path
coreos-tools jenkins builds artifacts <job-name> <build-number> --download <artifact-name> -o /tmp/output.json
```

## Package Comparison

### Single Build Diff

Shows what packages changed/upgraded in this build:

```bash
coreos-tools jenkins builds diff <job-name> <build-number>
```

### Two Build Comparison

Compare packages between two builds:

```bash
coreos-tools jenkins builds diff <job-name> <build1> <build2>
```

Output format:
```json
{
  "build1": 3399,
  "build2": 3463,
  "stream": "rhel-9.6",
  "added": ["new-package-1.0.0.x86_64 (rhel-9.6-baseos)"],
  "removed": ["old-package-2.0.0.x86_64 (rhel-9.4-appstream)"],
  "changed": [
    {
      "name": "kernel",
      "build1": "kernel-5.14.0-427.112.1.el9_4.x86_64 (rhel-9.4-server-ose-4.17)",
      "build2": "kernel-5.14.0-570.94.1.el9_6.x86_64 (rhel-9.6-early-kernel)"
    }
  ]
}
```

### Analyzing Diffs

```bash
# List all changed package names
coreos-tools jenkins builds diff <job-name> <b1> <b2> | jq -r '.changed[].name'

# Show kernel changes specifically
coreos-tools jenkins builds diff <job-name> <b1> <b2> | jq '.changed[] | select(.name == "kernel")'

# Count changes
coreos-tools jenkins builds diff <job-name> <b1> <b2> | jq '{added: (.added | length), removed: (.removed | length), changed: (.changed | length)}'
```

## Comparing coreos-assembler Versions

When cosa version differs between good and bad builds:

```bash
# Download cosa git info from both builds
coreos-tools jenkins builds artifacts <job-name> <failed-build> --download coreos-assembler-git.json -o /tmp/failed-cosa.json
coreos-tools jenkins builds artifacts <job-name> <good-build> --download coreos-assembler-git.json -o /tmp/good-cosa.json

# Compare
diff /tmp/good-cosa.json /tmp/failed-cosa.json

# Find commits between versions using GitHub CLI
gh api repos/coreos/coreos-assembler/compare/<old-commit>...<new-commit> \
  --jq '.commits[] | {sha: .sha[0:7], date: .commit.author.date, message: .commit.message | split("\n")[0]}'

# Get details of a specific commit
gh api repos/coreos/coreos-assembler/commits/<commit-sha> \
  --jq '{sha: .sha, author: .commit.author.name, message: .commit.message}'
```
