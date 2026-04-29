---
name: rhcos-ocp-release
description: OCP release queries - latest versions, RHCOS images, and RPM package lists
---

# RHCOS OCP Release

Query OCP release versions, RHCOS container images, and RPM package lists.

> Related: `rhcos-versions`, `rhcos-artifacts`, `rhcos-brew`, `rhcos-build-pipeline`, `bug-investigation`

## Release Controller API

Base URL: `https://amd64.ocp.releases.ci.openshift.org`

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/v1/releasestreams/accepted` | All accepted releases grouped by stream |
| `/api/v1/releasestream/<stream>/latest` | Latest release in a stream |
| `/api/v1/releasestream/<stream>/tags` | All tags in a stream with metadata |

### Available Streams

| Stream | Description |
|--------|-------------|
| `4-stable` | All stable 4.x releases |
| `4-dev-preview` | Developer preview releases |
| `4.21.0-0.nightly` | 4.21 nightly builds |
| `4.21.0-0.ci` | 4.21 CI builds |

## Querying Latest Versions

### Latest Stable Release (any minor)

```bash
curl -s "https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestream/4-stable/latest" | jq .
```

### Latest Z-Stream for Specific Minor Version

```bash
# Get latest 4.21.x GA release (excluding RCs)
curl -s "https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestreams/accepted" | \
  jq -r '."4-stable"[] | select(startswith("4.21.") and (contains("-rc") | not))' | head -1
```

### Latest Nightly for Specific Minor Version

```bash
curl -s "https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestream/4.21.0-0.nightly/latest" | jq .
```

### List All Accepted Versions for a Minor Release

```bash
curl -s "https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestreams/accepted" | \
  jq -r '."4-stable"[] | select(startswith("4.21."))'
```

## RHCOS Variants

Starting with OCP 4.21, each release ships **two RHCOS variants** simultaneously:

| Variant | Image Name | RHEL Base | OCP Versions |
|---------|------------|-----------|--------------|
| RHEL 9 | `rhel-coreos` | RHEL 9.x | 4.x – present |
| RHEL 10 | `rhel-coreos-10` | RHEL 10.x | 4.21+ |

When querying RPM packages or images for OCP 4.21+, always specify which variant you want with `--rpmdb-image`.

## RPM Package Lists

The `oc adm release info --rpmdb` flag extracts RPM package information directly from the release image metadata without pulling the full container image. This is significantly faster than the traditional `podman pull` approach.

### Prerequisites

- `--rpmdb-cache` directory is required (e.g., `/tmp/rpmdb-cache`)
- Pull secret with access to `quay.io/openshift-release-dev/ocp-v4.0-art-dev`

### List All RPMs in a Release

```bash
# Default (RHEL 9 variant, all OCP versions)
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache

# Explicit RHEL 9 variant (OCP 4.21+)
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos

# RHEL 10 variant (OCP 4.21+ only)
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos-10
```

### Query Specific Package

```bash
# RHEL 9 variant - get kernel version
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos | grep kernel

# Example output:
#   kernel-5.14.0-570.19.1.el9_6
#   kernel-core-5.14.0-570.19.1.el9_6
#   kernel-modules-5.14.0-570.19.1.el9_6

# RHEL 10 variant - get kernel version (OCP 4.21+)
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos-10 | grep kernel

# Example output:
#   kernel-6.12.0-x.el10
#   kernel-core-6.12.0-x.el10
#   kernel-modules-6.12.0-x.el10
```

### Compare RPMs Between Releases

The `--rpmdb-diff` flag shows package changes between two releases:

```bash
# Compare RHEL 9 variant across two releases
oc adm release info \
  quay.io/openshift-release-dev/ocp-release:<version1>-x86_64 \
  quay.io/openshift-release-dev/ocp-release:<version2>-x86_64 \
  --rpmdb-diff --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos

# Compare RHEL 10 variant across two releases (OCP 4.21+)
oc adm release info \
  quay.io/openshift-release-dev/ocp-release:<version1>-x86_64 \
  quay.io/openshift-release-dev/ocp-release:<version2>-x86_64 \
  --rpmdb-diff --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos-10

# Example output:
# Changed:
#   kernel 5.14.0-570.19.1.el9_6 → 5.14.0-570.23.1.el9_6
#   cri-o 1.32.4-2.rhaos4.19.git98d1c09.el9 → 1.32.5-3.rhaos4.19.git9607a04.el9
# Added:
#   new-package-1.0.0-1.el9
# Removed:
#   old-package-1.0.0-1.el9
```

### Target Other Images

By default, `--rpmdb` queries the `rhel-coreos` (RHEL 9) image. Use `--rpmdb-image` to target other images:

```bash
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image <image-name>
```

### Legacy Method (Fallback)

Only use this method if `--rpmdb` is unavailable or not working. The modern `--rpmdb` approach above is significantly faster and doesn't require pulling multi-GB container images.

```bash
# Get RHEL 9 RHCOS image reference
RHCOS_IMAGE=$(oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 --image-for rhel-coreos)

# Get RHEL 10 RHCOS image reference (OCP 4.21+)
RHCOS10_IMAGE=$(oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 --image-for rhel-coreos-10)

# Pull and query (slow - downloads ~1GB image)
podman pull $RHCOS_IMAGE
podman run --rm $RHCOS_IMAGE rpm -qa --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n' | sort
```

## Multi-Architecture Support

Replace `amd64` in the URL with other architectures:

| Architecture | Release Controller URL |
|--------------|------------------------|
| x86_64 | `amd64.ocp.releases.ci.openshift.org` |
| aarch64 | `arm64.ocp.releases.ci.openshift.org` |
| ppc64le | `ppc64le.ocp.releases.ci.openshift.org` |
| s390x | `s390x.ocp.releases.ci.openshift.org` |

## Examples

### Full Workflow: Get Latest 4.21 RPMs (Both Variants)

```bash
# 1. Find latest version
VERSION=$(curl -s "https://amd64.ocp.releases.ci.openshift.org/api/v1/releasestreams/accepted" | \
  jq -r '."4-stable"[] | select(startswith("4.21.") and (contains("-rc") | not))' | head -1)

# 2. List RPMs - RHEL 9 variant
oc adm release info quay.io/openshift-release-dev/ocp-release:${VERSION}-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos

# 3. List RPMs - RHEL 10 variant (OCP 4.21+)
oc adm release info quay.io/openshift-release-dev/ocp-release:${VERSION}-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos-10

# 4. Query specific package in both variants
oc adm release info quay.io/openshift-release-dev/ocp-release:${VERSION}-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos | grep kernel

oc adm release info quay.io/openshift-release-dev/ocp-release:${VERSION}-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos-10 | grep kernel
```

## RHEL Package Flow to RHCOS

RHCOS picks up packages from RHEL composes. Understanding the brew tag flow is essential for tracking when packages will appear in RHCOS. For OCP 4.21+, this applies independently to both the RHEL 9 and RHEL 10 variants.

### Brew Tag Flow

| Tag | Meaning | When RHCOS Picks It Up |
|-----|---------|------------------------|
| `rhel-9.X.0-pending` | Tagged for 9.X GA content | Picked up in pre-GA RHCOS (RHEL 9) builds |
| `rhel-9.X.0-z-pending` | Tagged for 0-day errata | Picked up after GA (RHEL 9, 0-day builds) |
| `rhel-10.X.0-pending` | Tagged for 10.X GA content | Picked up in pre-GA RHCOS (RHEL 10) builds |
| `rhel-10.X.0-z-pending` | Tagged for 0-day errata | Picked up after GA (RHEL 10, 0-day builds) |

**Key insight:** If a package only has the `-z-pending` tag, it won't appear in RHCOS until after RHEL GA unless an exception is granted. This applies to both RHEL 9 and RHEL 10 variants independently.

### Checking Brew Tags

```bash
# Check tag history for a build (RHEL 9)
brew list-history --tag rhel-9.8.0-pending --build <package-nvr>

# Example (RHEL 9)
brew list-history --tag rhel-9.8.0-pending --build resource-agents-4.10.0-107.el9

# Check tag history for a build (RHEL 10)
brew list-history --tag rhel-10.0.0-pending --build <package-nvr>
```

> See `rhcos-brew` skill for more brew commands and NVR conventions.

## RHEL Compose Structure

RHCOS builds consume packages from RHEL composes. The compose type determines timing. For OCP 4.21+, both RHEL 9 and RHEL 10 composes feed their respective RHCOS variants.

### Compose Types

| Suffix | Type | Description |
|--------|------|-------------|
| `.d.#` | Development | Development compose (e.g., `RHEL-9.8.0-20260308.d.3`) |
| `.n.#` | Nightly | Nightly compose, picked up by next RHCOS build |

### Compose URL Patterns

```
# RHEL 9
https://download.eng.brq.redhat.com/rhel-9/composes/RHEL-9/RHEL-9.X.0-YYYYMMDD.<type>.<num>/

# RHEL 10
https://download.eng.brq.redhat.com/rhel-10/composes/RHEL-10/RHEL-10.X.0-YYYYMMDD.<type>.<num>/
```

Example structure (same for both RHEL 9 and RHEL 10):
```
RHEL-9.8.0-20260308.d.3/
└── compose/
    ├── BaseOS/x86_64/os/Packages/
    ├── AppStream/x86_64/os/Packages/
    └── HighAvailability/x86_64/os/Packages/
```

### Timing

1. Package tagged in brew with `rhel-9.X.0-pending` or `rhel-10.X.0-pending`
2. Package appears in nightly RHEL compose (for the respective RHEL version)
3. Next RHCOS build picks up the compose
4. Package appears in RHCOS nightly for that variant (typically next day)

## Extensions Image Inspection

RHCOS extensions (optional packages) are stored in a separate image. Use this to verify a package is included.

### Check Extensions Image

```bash
# List all extension RPMs
podman run --entrypoint /bin/sh \
  quay.io/openshift-release-dev/ocp-v4.0-art-dev:4.22-9.8-node-image-extensions \
  -c 'ls /usr/share/rpm-ostree/extensions/*.rpm'

# Check for a specific package
podman run --entrypoint /bin/sh \
  quay.io/openshift-release-dev/ocp-v4.0-art-dev:4.22-9.8-node-image-extensions \
  -c 'ls /usr/share/rpm-ostree/extensions/resource*.rpm'
```

### Image Naming Convention

```
quay.io/openshift-release-dev/ocp-v4.0-art-dev:<ocp-version>-<rhel-version>-node-image-extensions
```

Examples:
- `4.22-9.8-node-image-extensions` - OCP 4.22 with RHEL 9.8
- `4.21-9.6-node-image-extensions` - OCP 4.21 with RHEL 9.6 (RHEL 9 variant)
- `4.21-10.0-node-image-extensions` - OCP 4.21 with RHEL 10.0 (RHEL 10 variant, OCP 4.21+)

## Monitoring RHCOS Builds

### Slack Channel

The `#jenkins-rhcos-art` Slack channel shows RHCOS build status. For OCP 4.21+, look for successful node image builds for both RHEL 9 (`4.X-9.Y`) and RHEL 10 (`4.X-10.Y`) variants.

### Build Status

When a package isn't appearing in RHCOS:

1. Check if the RHCOS pipeline is passing (failures block package updates)
2. Look for successful node image builds in the channel
3. Once pipeline succeeds, packages from the latest compose will be included

## Troubleshooting: Package Not in RHCOS

Step-by-step workflow when a package isn't showing up:

### Step 0: Identify Which Variant Is Affected

For OCP 4.21+, determine whether the package is missing from the RHEL 9 variant, the RHEL 10 variant, or both:

```bash
# Check RHEL 9 variant
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos | grep <package>

# Check RHEL 10 variant (OCP 4.21+)
oc adm release info quay.io/openshift-release-dev/ocp-release:<version>-x86_64 \
  --rpmdb --rpmdb-cache /tmp/rpmdb-cache --rpmdb-image rhel-coreos-10 | grep <package>
```

The remaining steps apply independently to each variant based on its RHEL base version.

### Step 1: Check Brew Tags

```bash
# Does the build have the right tag?
brew list-tags --build=<package-nvr>

# Check tag history (RHEL 9)
brew list-history --tag rhel-9.X.0-pending --build <package-nvr>

# Check tag history (RHEL 10)
brew list-history --tag rhel-10.X.0-pending --build <package-nvr>
```

**Expected:** Build should have `rhel-9.X.0-pending` or `rhel-10.X.0-pending` tag (not just `-z-pending`).

### Step 2: Check RHEL Compose

Browse the compose directory to verify the package is included:

```
# RHEL 9
https://download.eng.brq.redhat.com/rhel-9/composes/RHEL-9/

# RHEL 10
https://download.eng.brq.redhat.com/rhel-10/composes/RHEL-10/
```

Look for nightly composes (`.n.#` suffix) and check the relevant repo (BaseOS, AppStream, HighAvailability).

### Step 3: Check RHCOS Pipeline

- Check `#jenkins-rhcos-art` for recent build status
- For OCP 4.21+, look for successful builds for both `4.X-9.Y` (RHEL 9) and `4.X-10.Y` (RHEL 10) node images
- Pipeline failures block package updates for that variant

### Step 4: Verify in Extensions Image

```bash
podman run --entrypoint /bin/sh \
  quay.io/openshift-release-dev/ocp-v4.0-art-dev:<version>-node-image-extensions \
  -c 'ls /usr/share/rpm-ostree/extensions/<package>*.rpm'
```

### Common Issues

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Package has `-z-pending` only | Tagged for 0-day, not GA | Ask maintainer to request exception for GA content |
| Package in dev compose only | Not yet in nightly | Wait for nightly compose |
| Pipeline failing | Build blocked | Wait for pipeline fix, check `#jenkins-rhcos-art` |
| Older version appears | Compose not updated yet | Check compose timestamp, wait for next nightly |
