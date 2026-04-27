---
name: rhcos-repositories
description: RHCOS GitHub repositories, package definitions, and test locations
---

# RHCOS Repositories

GitHub repositories, package definitions, and test locations for RHEL CoreOS.

> Related: `rhcos-build-pipeline`, `rhcos-versions`

## GitHub Repositories

| Repository | Purpose | Key Files/Directories |
|------------|---------|----------------------|
| [coreos/fedora-coreos-config](https://github.com/coreos/fedora-coreos-config) | Upstream FCOS manifests (inherited by RHCOS) | `manifest.yaml`, `manifests/`, `tests/`, `kola-denylist.yaml` |
| [coreos/rhel-coreos-config](https://github.com/coreos/rhel-coreos-config) | RHCOS/SCOS config (RHEL-specific packages) | `manifest-*.yaml`, `packages-rhcos.yaml`, `tests/kola/`, `kola-denylist.yaml` |
| [coreos/coreos-assembler](https://github.com/coreos/coreos-assembler) | Build tool (cosa) and kola test framework | `mantle/kola/` (tests), `src/`, `docs/` |
| [coreos/fedora-coreos-pipeline](https://github.com/coreos/fedora-coreos-pipeline) | Jenkins pipeline definitions | `jobs/`, `config.yaml` |
| [openshift/os](https://github.com/openshift/os) | Node image layer (adds OCP packages) | `packages-openshift.yaml`, `Containerfile`, `tests/kola/`, `extensions/` |

## Repository Relationships

- `fedora-coreos-config` is a **submodule** inside `rhel-coreos-config`
- `rhel-coreos-config` produces the **base image**
- `openshift/os` **builds FROM** the base image to create the node image

## Package Definitions

### Base OS Packages (Stage 1)

Defined in `rhel-coreos-config`:

| File | Purpose |
|------|---------|
| `packages-rhcos.yaml` | RHCOS-specific packages |
| `manifest-*.yaml` | Stream-specific manifests (repos, versions) |
| `packages-overrides.yaml` | Package version overrides |

Inherited from `fedora-coreos-config`:

| File | Purpose |
|------|---------|
| `manifests/*.yaml` | Modular package groups |
| `manifest-lock.*.json` | Per-architecture package locks |

### OpenShift Packages (Stage 2)

Defined in `openshift/os`:

| File | Purpose |
|------|---------|
| `packages-openshift.yaml` | OCP node packages (kubelet, cri-o, oc, etc.) |
| `extensions/` | Optional extensions (usbguard, etc.) |

## Test Locations

Kola tests are distributed across repositories:

| Repository | Test Path | Test Type |
|------------|-----------|-----------|
| `fedora-coreos-config` | `tests/kola/` | FCOS-specific tests |
| `rhel-coreos-config` | `tests/kola/` | RHCOS-specific tests |
| `openshift/os` | `tests/kola/` | Node image tests |
| `coreos-assembler` | `mantle/kola/tests/` | Core kola tests |

## Test Denylists

Each config repo has a `kola-denylist.yaml` to skip known-failing tests:

- `fedora-coreos-config/kola-denylist.yaml`
- `rhel-coreos-config/kola-denylist.yaml`
- `openshift/os/kola-denylist.yaml`
