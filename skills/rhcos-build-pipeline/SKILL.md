---
name: rhcos-build-pipeline
description: RHCOS build pipeline - scheduling, two-stage builds, versionlock mechanism, and troubleshooting
---

# RHCOS Build Pipeline

Knowledge about the RHEL CoreOS build pipeline, Jenkins jobs, and multi-architecture builds.

> Related: `rhcos-repositories`, `rhcos-artifacts`, `rhcos-versions`

## Build Process Overview

RHCOS is built in two stages:

**Stage 1: Base Image** (`build` + `build-arch` jobs)
- Input: `rhel-coreos-config` repository (contains `fedora-coreos-config` as submodule)
- The `build` job runs for x86_64 and triggers `build-arch` for other architectures
- `build-arch` runs in parallel for aarch64, ppc64le, s390x
- All `build-arch` jobs must succeed for the pipeline to continue
- Output: Bootable container with RHEL/CentOS Stream content only (no OpenShift components)

**Stage 2: Node Image** (`build-node-image` job)
- Input: Base image from Stage 1 + `openshift/os` Containerfile
- Adds OpenShift packages: kubelet, cri-o, oc, etc.
- Output: `rhel-coreos` or `stream-coreos` image in OCP release payload

## Jenkins Jobs

| Job | Architecture | Purpose | Output |
|-----|--------------|---------|--------|
| `build` | x86_64 | Main RHCOS base image build, triggers build-arch | Bootable container (RHEL content only) |
| `build-arch` | aarch64, ppc64le, s390x | Architecture-specific base builds (triggered by `build`) | Multi-arch base images |
| `build-node-image` | all | Node image build (adds OCP packages) | `rhel-coreos` / `stream-coreos` |
| `release` | all | Release builds | Production releases |

## Build and Build-Arch Relationship

The `build` job orchestrates multi-architecture builds:

1. `build` job starts for x86_64
2. `build` triggers `build-arch` jobs for aarch64, ppc64le, s390x in parallel
3. `build` waits for all `build-arch` jobs to complete
4. If any `build-arch` job fails, the parent `build` job fails
5. Only when all architectures succeed does `build-node-image` proceed

When investigating a `build` failure, check if the root cause is in `build-arch`:

```bash
# Check if build-arch jobs failed
coreos-tools jenkins builds list build-arch --status FAILURE -n 5

# Get the triggering build job number from build-arch parameters
coreos-tools jenkins builds info build-arch <build-number>
```

## Architectures

| Architecture | Description | Build Job |
|--------------|-------------|-----------|
| `x86_64` | AMD64/Intel 64-bit | `build` |
| `aarch64` | ARM 64-bit | `build-arch` |
| `ppc64le` | IBM POWER little-endian | `build-arch` |
| `s390x` | IBM Z mainframe | `build-arch` |

## Build Scheduling

### build-mechanical Job

The `build-mechanical` job is the main scheduler for RHCOS base image builds:

- **Schedule:** Daily at **10:00 UTC** (cron: `0 10 * * *`)
- **Source:** `jobs/build-mechanical.Jenkinsfile` in [fedora-coreos-pipeline](https://github.com/coreos/fedora-coreos-pipeline)
- **Behavior:** Triggers `build` jobs **sequentially** for all mechanical streams

**Execution Order:**
```
c10s → c9s → rhel-10.2 → rhel-9.8 → rhel-9.6
```

Due to sequential execution (each build takes 2-3 hours), later streams start much later:
- `c10s`: ~10:00 UTC
- `rhel-9.6`: ~17:00-18:00 UTC (last in queue)

### Checking Schedule

```bash
# View recent build-mechanical runs
coreos-tools jenkins builds list build-mechanical -n 10

# Check what streams were triggered in a specific run
coreos-tools jenkins builds log build-mechanical <build-number> | grep "Triggering build"
```

## FORCE Parameter

The `FORCE` parameter controls whether to rebuild even if no changes are detected.

| FORCE Value | Behavior |
|-------------|----------|
| `false` (default) | Skip build if no config changes detected (shows "💤 no new build") |
| `true` | Always rebuild, even without config changes |

**When FORCE is needed:**
- Forcing an immediate rebuild to pick up new packages from repos (before next scheduled run)
- Recovering from a failed build that left stale state

**When FORCE is NOT needed:**
- Normal scheduled builds (they run daily and usually produce new builds)
- The `build-mechanical` job does NOT use FORCE; it relies on cosa detecting changes

**How cosa detects changes:**
- Checks if source config (rhel-coreos-config) commit changed
- Checks package manifest/lockfile changes
- Does NOT automatically detect RHEL repo package updates (mechanical streams don't use strict lockfiles)

## Versionlock Mechanism

During `build-node-image`, packages from the base image are versionlocked to prevent
unexpected upgrades. This is done **dynamically at build time**, not via static config files.

### How It Works

1. `build` job creates base image with packages at specific versions (e.g., `NetworkManager-1.52.0-9`)
2. `build-node-image` runs `rpm-ostree experimental compose treefile-apply`
3. This creates versionlocks for ALL packages in the base image
4. New packages can be installed, but locked packages cannot be upgraded

You can see this in the build logs:
```
Adding versionlock on: NetworkManager-1:1.52.0-9.el9_6.*
Adding versionlock on: NetworkManager-tui-1:1.52.0-9.el9_6.*
...
```

### Version Skew Problem

If a new package in the repos requires a newer version of a locked package, DNF fails:

```
Error: package NetworkManager-ovs-1:1.52.0-10 requires NetworkManager = 1:1.52.0-10,
       but package NetworkManager-1:1.52.0-9 is filtered out by exclude filtering
```

**Typical scenario:**
1. Base image built with package version X
2. RHEL repos updated with package version X+1
3. A new dependency package requires version X+1
4. `build-node-image` fails because version X is locked and X+1 is excluded

**Fix:** Rebuild the base image (`build` job) to pick up the newer package version:
```bash
coreos-tools jenkins jobs build build --param STREAM=rhel-9.6
```

## Job Commands

```bash
# List all jobs
coreos-tools jenkins jobs list

# Get job info (health, last builds)
coreos-tools jenkins jobs info <job-name>

# Trigger a build
coreos-tools jenkins jobs build <job-name> --param STREAM=<stream>

# Trigger a forced build (bypass "no changes" detection)
coreos-tools jenkins jobs build <job-name> --param STREAM=<stream> --param FORCE=true

# View build queue
coreos-tools jenkins queue list

# List nodes
coreos-tools jenkins nodes list
```
