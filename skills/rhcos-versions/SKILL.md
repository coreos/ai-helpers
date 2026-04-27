---
name: rhcos-versions
description: RHCOS build variants, streams, and OCP to RHEL version mappings
---

# RHCOS Versions

Build variants, streams, and version mappings for RHEL CoreOS.

> Related: `rhcos-build-pipeline`, `rhcos-repositories`

## Build Variants

Defined in `rhel-coreos-config`:

| Variant | Description | Config File |
|---------|-------------|-------------|
| `rhel-9.8` | RHEL 9.8 based (default) | `manifest-rhel-9.8.yaml` |
| `rhel-10.2` | RHEL 10.2 based | `manifest-rhel-10.2.yaml` |
| `c9s` | CentOS Stream 9 | `manifest-c9s.yaml` |
| `c10s` | CentOS Stream 10 | `manifest-c10s.yaml` |

## Build Streams

| Stream | Description |
|--------|-------------|
| `c9s` | CentOS Stream 9 (upstream development) |
| `c10s` | CentOS Stream 10 (upstream development) |
| `rhel-9.2` | RHEL 9.2 based builds |
| `rhel-9.4` | RHEL 9.4 based builds |
| `rhel-9.6` | RHEL 9.6 based builds |
| `rhel-9.8` | RHEL 9.8 based builds |
| `rhel-10.2` | RHEL 10.2 based builds |

## OCP to RHEL Version Mapping

| OCP Version | RHEL Version |
|-------------|--------------|
| 4.12 | 8.6 |
| 4.13 | 9.2 |
| 4.14 | 9.2 |
| 4.15 | 9.2 |
| 4.16 | 9.4 |
| 4.17 | 9.4 |
| 4.18 | 9.4 |
| 4.19 | 9.6 |
| 4.20 | 9.6 |
| 4.21 | 9.6 |
| 4.22 | 9.8 |
