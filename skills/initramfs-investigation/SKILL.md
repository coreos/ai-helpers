---
name: initramfs-investigation
description: Investigate initramfs issues - extraction, module analysis, and comparing working vs failing builds
---

# Initramfs Investigation

Knowledge for investigating initramfs-related boot failures by comparing working and failing builds in FCOS and RHCOS.

> Related: `pipeline-failures` (CI failures), `rhcos-cosa` (cosa builds), `rhcos-artifacts` (build artifacts)

## Initramfs Extraction

### Identify Compression Format

```bash
# Check magic bytes
head -c 6 initramfs.img | od -A x -t x1z
```

| Magic Bytes | Format | Tool |
|-------------|--------|------|
| `28 b5 2f fd` | zstd | `zstdcat` |
| `1f 8b` | gzip | `zcat` |
| `fd 37 7a 58` | xz | `xzcat` |
| `30 37 30 37` | CPIO (uncompressed) | Direct `cpio` |

### Extract Initramfs

```bash
# For zstd-compressed (FCOS/RHCOS default)
mkdir extracted && cd extracted
zstdcat ../initramfs.img | cpio -idm

# For gzip-compressed
zcat ../initramfs.img | cpio -idm

# For multi-segment (early microcode + main)
skipcpio initramfs.img | zstdcat | cpio -idm
```

### List Contents Without Extraction

```bash
# Using lsinitrd
lsinitrd initramfs.img

# Manual listing
zstdcat initramfs.img | cpio -t | head -50
```

## Kernel Module Analysis

### Find Modules in Initramfs

```bash
# List kernel modules
find extracted -name "*.ko*" | head -20

# Find specific module
find extracted -name "scsi_transport_iscsi*"
```

### Examine Module

```bash
# Decompress module first (if .ko.xz)
xz -d extracted/usr/lib/modules/*/kernel/drivers/scsi/module.ko.xz

# List all ELF sections
readelf -S module.ko

# Check module architecture
readelf -h module.ko | grep -E "Data|Machine|Class"
```

## FCOS Build Artifacts

### Download Initramfs

```bash
# List available builds
curl -s "https://builds.coreos.fedoraproject.org/prod/streams/<stream>/builds/builds.json" | jq -r '.builds[].id' | head -10

# Get build metadata
curl -s "https://builds.coreos.fedoraproject.org/prod/streams/<stream>/builds/<version>/<arch>/meta.json" | jq .

# Download initramfs
curl -LO "https://builds.coreos.fedoraproject.org/prod/streams/<stream>/builds/<version>/<arch>/fedora-coreos-<version>-live-initramfs.<arch>.img"
```

Streams: `stable`, `testing`, `next`, `rawhide`

### Compare Package Versions Between Builds

```bash
# Get package diff from meta.json (shows what changed from previous build)
curl -s ".../meta.json" | jq '.pkgdiff'

# Check specific package (e.g., kernel)
curl -s ".../meta.json" | jq '.pkgdiff[] | select(.[0] | test("kernel"))'
```

## RHCOS Build Artifacts

### From RHCOS Release Browser (Internal)

Base URL: `https://releases-rhcos--prod-pipeline.apps.int.prod-stable-spoke1-dc-iad2.itup.redhat.com`

```bash
# List available builds for a stream
curl -s "https://releases-rhcos--prod-pipeline.apps.int.prod-stable-spoke1-dc-iad2.itup.redhat.com/storage/prod/streams/<stream>/builds/builds.json" | jq -r '.builds[].id' | head -10

# Get build metadata
curl -s "https://releases-rhcos--prod-pipeline.apps.int.prod-stable-spoke1-dc-iad2.itup.redhat.com/storage/prod/streams/<stream>/builds/<buildid>/<arch>/meta.json" | jq .

# Get initramfs path from metadata
curl -s ".../meta.json" | jq -r '.images["live-initramfs"].path'

# Download initramfs
curl -LO "https://releases-rhcos--prod-pipeline.apps.int.prod-stable-spoke1-dc-iad2.itup.redhat.com/storage/prod/streams/<stream>/builds/<buildid>/<arch>/<initramfs-filename>"
```

Streams: `rhel-9.4`, `rhel-9.6`, `rhel-10.0`, `rhel-10.2`, etc.

## Comparing Working vs Failing Initramfs

### 1. Identify Working and Failing Builds

From CI failure logs or build history, identify:
- **Last working build** (e.g., `45.20260323.91.1`)
- **First failing build** (e.g., `45.20260324.91.1`)

### 2. Download Both Initramfs

```bash
# FCOS example
curl -LO ".../45.20260323.91.1/<arch>/fedora-coreos-45.20260323.91.1-live-initramfs.<arch>.img"
curl -LO ".../45.20260324.91.1/<arch>/fedora-coreos-45.20260324.91.1-live-initramfs.<arch>.img"

mv *323* initramfs-working.img
mv *324* initramfs-failing.img
```

### 3. Extract Both

```bash
mkdir working failing

cd working && zstdcat ../initramfs-working.img | cpio -idm 2>/dev/null && cd ..
cd failing && zstdcat ../initramfs-failing.img | cpio -idm 2>/dev/null && cd ..
```

### 4. Compare Kernel Versions

```bash
ls working/usr/lib/modules/
ls failing/usr/lib/modules/
```

### 5. Compare Specific Files

```bash
# Compare dracut modules included
diff <(ls working/usr/lib/dracut/modules.d/) <(ls failing/usr/lib/dracut/modules.d/)

# Compare a specific module's ELF sections
diff <(readelf -S working/usr/lib/modules/*/kernel/path/to/module.ko) \
     <(readelf -S failing/usr/lib/modules/*/kernel/path/to/module.ko)

# Compare file sizes
find working -type f -name "*.ko*" -exec ls -la {} \; | sort > /tmp/working-modules.txt
find failing -type f -name "*.ko*" -exec ls -la {} \; | sort > /tmp/failing-modules.txt
diff /tmp/working-modules.txt /tmp/failing-modules.txt
```

### 6. Check dracut Configuration

```bash
# Compare dracut config
diff working/usr/lib/dracut/dracut.conf.d/ failing/usr/lib/dracut/dracut.conf.d/

# Check specific dracut scripts
diff working/usr/lib/dracut/modules.d/95iscsi/parse-iscsiroot.sh \
     failing/usr/lib/dracut/modules.d/95iscsi/parse-iscsiroot.sh
```

## Analyzing Console Logs

When investigating boot failures from kola tests:

```bash
# Extract kola artifacts
tar -xf kola-upgrade-<arch>.tar.xz

# Find console logs
find . -name "console.txt"

# Look for first error (not cascade failures)
grep -n -E "FATAL|failed to|Failed to|error:" console.txt | head -10

# Check module loading
grep -E "modprobe|insmod|systemd-modules-load" console.txt
```

## Reference

- [dracut documentation](https://github.com/dracut-ng/dracut-ng)
- [FCOS builds browser](https://builds.coreos.fedoraproject.org/browser)
- [RHCOS release browser](https://releases-rhcos--prod-pipeline.apps.int.prod-stable-spoke1-dc-iad2.itup.redhat.com/)
- [coreos-assembler](https://github.com/coreos/coreos-assembler)
