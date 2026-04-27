---
name: rhcos-brew
description: Brew (Red Hat build system) - package searches, NVR naming, tags, and package sources
---

# Brew (Red Hat Build System)

Brew is Red Hat's internal Koji instance for tracking package builds.

> Related: `rhcos-artifacts`, `bug-investigation`

**Web UI:** https://brewweb.engineering.redhat.com/brew/

## Prerequisites

- Red Hat VPN access required
- Anonymous read-only access works without Kerberos

## Package Search

```bash
# Search by package name
brew search package <package-name>

# Examples
brew search package cri-o
brew search package conmon-rs
```

## Build Search

```bash
# Get latest build for a tag
brew latest-build <tag> <package>

# Examples
brew latest-build rhaos-4.18-rhel-9-candidate cri-o
brew latest-build rhaos-4.19-rhel-10-candidate conmon-rs

# List all builds of a package
brew list-builds --package=<package>
brew list-builds --package=cri-o | head -20
```

## Getting Build Information

```bash
# Get detailed build info (source, timestamps, tags)
brew buildinfo <nvr>
brew buildinfo cri-o-1.30.0-1.rhaos4.18.el9

# List tags a build is in
brew list-tags --build=<nvr>
brew list-tags --build=cri-o-1.30.0-1.rhaos4.18.el9

# List RPMs in a build
brew buildinfo <nvr> | grep -A100 "^RPMs:"
```

## Tag Operations

```bash
# List all packages in a tag
brew list-pkgs --tag=<tag>
brew list-pkgs --tag=rhaos-4.18-rhel-9-candidate

# List latest builds in a tag
brew latest-build --all <tag>
brew latest-build --all rhaos-4.18-rhel-9-candidate | head -20

# Get tag info
brew taginfo <tag>
brew taginfo rhaos-4.18-rhel-9-candidate
```

## NVR Naming Convention

NVR = Name-Version-Release

### OpenShift-Specific Packages (Plashet/RHAOS)

Packages with `rhaos` in the release are OpenShift-specific and come from the plashet (RHAOS repo):

```
conmon-rs-0.6.6-0.rhaos4.18.el10.1
└──────┘ └───┘ └─────────────────┘
  name   ver        release
               └────┘ └──┘
              ocp4.18 rhel10
```

### RHEL Packages

Packages from RHEL repos have a different release format:

```
kernel-5.14.0-570.94.1.el9_6.x86_64
└────┘ └───────────────┘ └───┘
 name       version       rhel9.6
```

### Fast-Tracking RHEL Packages

Sometimes RHEL packages are tagged into plashets to fast-track a fix into OpenShift before it lands in the regular RHEL repos. In this case, a RHEL package appears in the `rhaos-4.XX-rhel-Y` tag but retains its original RHEL NVR format.

## Package Sources

| Release Pattern | Source | Example |
|-----------------|--------|---------|
| `*.rhaos4.XX.*` | Plashet (OpenShift-specific) | `cri-o-1.30.0-1.rhaos4.18.el9` |
| `*.el9_6` | RHEL 9.6 repos | `kernel-5.14.0-570.94.1.el9_6` |
| `*.el10` | RHEL 10 repos | `systemd-256-1.el10` |

## Common Tag Patterns

| Tag Pattern | Meaning |
|-------------|---------|
| `rhaos-4.XX-rhel-Y` | OCP 4.XX plashet for RHEL Y (OpenShift packages + fast-tracked RHEL packages) |
| `rhel-Y.Z-baseos` | RHEL Y.Z base OS |
| `rhel-Y.Z-appstream` | RHEL Y.Z AppStream |
| `rhel-Y-server-ose-4.XX` | RHEL Y for OCP 4.XX |

## Finding Package History

```bash
# List all builds of a package chronologically
brew list-builds --package=<package> --reverse

# Compare two builds
brew buildinfo <nvr1>
brew buildinfo <nvr2>
```
