#!/usr/bin/env python3
"""
Jenkins Plugin Compatibility Checker

Checks Jenkins plugin versions against a running Jenkins instance to find
the highest compatible version of each plugin without requiring fast-tracks
(pinning newer base image plugin versions).

Can also identify what fast-tracks are needed for a specific target version.

Usage:
    # Check all plugins in plugins.txt for upgrades
    ./check-plugin-compat.py --plugins-file jenkins/controller/plugins.txt \
                             --base-plugins base-plugins.txt

    # Check specific plugins
    ./check-plugin-compat.py --plugins mcp-server,pipeline-graph-view \
                             --base-plugins base-plugins.txt

    # Check what fast-tracks a specific version needs
    ./check-plugin-compat.py --plugins mcp-server:0.194 \
                             --base-plugins base-plugins.txt \
                             --show-fast-tracks

    # Get base plugins from a running Jenkins pod
    ./check-plugin-compat.py --from-pod jenkins-xyz --namespace fedora-coreos-pipeline \
                             --plugins mcp-server

Requirements:
    Python 3.9+, no external dependencies. Optional: oc CLI for --from-pod.
"""

import argparse
import io
import json
import re
import subprocess
import sys
import urllib.request
import zipfile
from dataclasses import dataclass, field

ARCHIVES_BASE = "https://archives.jenkins.io/plugins"


def version_key(v):
    nums = re.findall(r'\d+', v)
    return tuple(int(n) for n in nums) if nums else (0,)


@dataclass
class DepIssue:
    dep_name: str
    current_version: str
    required_version: str
    issue_type: str  # "too_old" or "missing"


@dataclass
class PluginResult:
    name: str
    current_version: str
    best_version: str = ""
    latest_version: str = ""
    issues_at_latest: list = field(default_factory=list)
    versions_checked: int = 0
    fast_tracks_needed: list = field(default_factory=list)


def fetch_available_versions(plugin_name, current_version):
    url = f"{ARCHIVES_BASE}/{plugin_name}/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "jenkins-plugin-compat/1.0"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    except Exception as e:
        print(f"  Warning: failed to fetch versions for {plugin_name}: {e}", file=sys.stderr)
        return []

    versions = re.findall(r'href="([^"]+)/"', html)
    versions = [v for v in versions if v not in ("..", "latest") and not v.startswith("http")]

    candidates = sorted(
        [v for v in versions if version_key(v) > version_key(current_version)],
        key=version_key, reverse=True
    )
    return candidates


def get_manifest(plugin_name, version):
    url = f"{ARCHIVES_BASE}/{plugin_name}/{version}/{plugin_name}.hpi"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "jenkins-plugin-compat/1.0"})
        data = urllib.request.urlopen(req, timeout=30).read()
        z = zipfile.ZipFile(io.BytesIO(data))
        manifest = z.read("META-INF/MANIFEST.MF").decode("utf-8")

        lines = manifest.split("\n")
        full_lines = []
        for line in lines:
            if line.startswith(" ") and full_lines:
                full_lines[-1] += line[1:]
            else:
                full_lines.append(line)

        jenkins_version = None
        deps = []
        for line in full_lines:
            if line.startswith("Jenkins-Version:"):
                jenkins_version = line.split(":", 1)[1].strip()
            if line.startswith("Plugin-Dependencies:"):
                for d in line.split(":", 1)[1].strip().split(","):
                    d = d.strip()
                    if not d:
                        continue
                    optional = ";resolution:=optional" in d
                    d = d.replace(";resolution:=optional", "")
                    nv = d.split(":")
                    if len(nv) == 2:
                        deps.append({
                            "name": nv[0],
                            "version": nv[1],
                            "optional": optional
                        })
        return jenkins_version, deps
    except Exception:
        return None, None


def check_compatibility(plugin_name, version, base_plugins, jenkins_version):
    req_jenkins, deps = get_manifest(plugin_name, version)
    if req_jenkins is None:
        return None, "could not fetch manifest"

    if jenkins_version and version_key(req_jenkins) > version_key(jenkins_version):
        return [DepIssue("jenkins-core", jenkins_version, req_jenkins, "too_old")], None

    issues = []
    for dep in deps:
        cur = base_plugins.get(dep["name"])
        if cur is None and not dep["optional"]:
            issues.append(DepIssue(dep["name"], "MISSING", dep["version"], "missing"))
        elif cur is not None and version_key(cur) < version_key(dep["version"]):
            issues.append(DepIssue(dep["name"], cur, dep["version"], "too_old"))

    return issues, None


def find_best_version(plugin_name, current_version, base_plugins, jenkins_version,
                      max_versions=15, target_version=None):
    result = PluginResult(name=plugin_name, current_version=current_version)

    if target_version:
        candidates = [target_version]
    else:
        candidates = fetch_available_versions(plugin_name, current_version)

    if not candidates:
        result.best_version = current_version
        return result

    result.latest_version = candidates[0]

    for ver in candidates[:max_versions]:
        result.versions_checked += 1
        issues, err = check_compatibility(plugin_name, ver, base_plugins, jenkins_version)

        if err:
            continue

        if not issues:
            result.best_version = ver
            break
        elif ver == candidates[0]:
            result.issues_at_latest = issues

        if target_version and issues:
            result.fast_tracks_needed = [
                i for i in issues if i.issue_type == "too_old" and i.dep_name != "jenkins-core"
            ]

    if not result.best_version:
        result.best_version = current_version

    return result


def parse_plugins_file(path):
    plugins = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) == 2:
                plugins[parts[0]] = parts[1]
    return plugins


def get_base_plugins_from_pod(pod_name, namespace):
    cmd = ["oc", "logs", pod_name, "-n", namespace]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Error: failed to get logs from pod {pod_name}: {result.stderr}", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("Error: 'oc' command not found. Install the OpenShift CLI or use --base-plugins instead.", file=sys.stderr)
        sys.exit(1)

    plugins = {}
    for line in result.stdout.split("\n"):
        if ".jpi:" in line:
            match = re.search(r'/([^/]+)\.jpi:(.+)', line)
            if match:
                plugins[match.group(1)] = match.group(2)

    jenkins_version = None
    match = re.search(r'Starting version (\S+)', result.stdout)
    if match:
        jenkins_version = match.group(1)

    return plugins, jenkins_version


def get_base_plugins_from_file(path):
    plugins = {}
    with open(path) as f:
        for line in f:
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                plugins[parts[0]] = parts[1]
    return plugins


def main():
    parser = argparse.ArgumentParser(
        description="Check Jenkins plugin version compatibility"
    )
    parser.add_argument(
        "--plugins-file",
        help="Path to plugins.txt to check all plugins for upgrades",
    )
    parser.add_argument(
        "--plugins",
        help="Comma-separated plugin names (or name:version for specific versions)",
    )
    parser.add_argument(
        "--base-plugins",
        help="File with base plugin versions (format: 'name version' per line)",
    )
    parser.add_argument(
        "--from-pod",
        help="Get base plugin versions from a running Jenkins pod (requires oc)",
    )
    parser.add_argument(
        "--namespace", "-n",
        default="fedora-coreos-pipeline",
        help="OpenShift namespace (default: fedora-coreos-pipeline)",
    )
    parser.add_argument(
        "--jenkins-version",
        help="Jenkins core version (auto-detected from pod if --from-pod)",
    )
    parser.add_argument(
        "--show-fast-tracks",
        action="store_true",
        help="Show what fast-tracks are needed for target versions",
    )
    parser.add_argument(
        "--max-versions",
        type=int,
        default=15,
        help="Max versions to check per plugin (default: 15)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    if not args.base_plugins and not args.from_pod:
        parser.error("Either --base-plugins or --from-pod is required")

    if not args.plugins and not args.plugins_file:
        parser.error("Either --plugins or --plugins-file is required")

    # Get base plugins
    jenkins_version = args.jenkins_version
    if args.from_pod:
        base_plugins, detected_version = get_base_plugins_from_pod(args.from_pod, args.namespace)
        if not jenkins_version and detected_version:
            jenkins_version = detected_version
        print(f"Base: {len(base_plugins)} plugins from pod {args.from_pod}", file=sys.stderr)
    else:
        base_plugins = get_base_plugins_from_file(args.base_plugins)
        print(f"Base: {len(base_plugins)} plugins from {args.base_plugins}", file=sys.stderr)

    if jenkins_version:
        print(f"Jenkins: {jenkins_version}", file=sys.stderr)

    # Get plugins to check
    plugins_to_check = {}
    if args.plugins_file:
        plugins_to_check = parse_plugins_file(args.plugins_file)
    elif args.plugins:
        for p in args.plugins.split(","):
            if ":" in p:
                name, ver = p.split(":", 1)
                plugins_to_check[name] = ver
            else:
                current = base_plugins.get(p)
                if not current:
                    pf_plugins = {}
                    if args.plugins_file:
                        pf_plugins = parse_plugins_file(args.plugins_file)
                    current = pf_plugins.get(p, "0")
                plugins_to_check[p] = current

    # Check each plugin
    results = []
    for name, current in sorted(plugins_to_check.items()):
        target = None
        if args.show_fast_tracks and args.plugins:
            for p in args.plugins.split(","):
                if ":" in p and p.split(":")[0] == name:
                    target = p.split(":", 1)[1]

        print(f"\nChecking {name} (current: {current})...", file=sys.stderr)
        result = find_best_version(
            name, current, base_plugins, jenkins_version,
            max_versions=args.max_versions, target_version=target
        )
        results.append(result)

    # Output
    if args.json:
        output = []
        for r in results:
            entry = {
                "name": r.name,
                "current": r.current_version,
                "best": r.best_version,
                "latest": r.latest_version,
                "upgraded": r.best_version != r.current_version,
                "versions_checked": r.versions_checked,
            }
            if r.issues_at_latest:
                entry["issues_at_latest"] = [
                    {"dep": i.dep_name, "have": i.current_version,
                     "need": i.required_version, "type": i.issue_type}
                    for i in r.issues_at_latest
                ]
            if r.fast_tracks_needed:
                entry["fast_tracks"] = [
                    {"plugin": i.dep_name, "current": i.current_version,
                     "required": i.required_version}
                    for i in r.fast_tracks_needed
                ]
            output.append(entry)
        print(json.dumps(output, indent=2))
    else:
        print(f"\n{'='*70}")
        print("JENKINS PLUGIN COMPATIBILITY REPORT")
        if jenkins_version:
            print(f"Jenkins: {jenkins_version}")
        print(f"{'='*70}\n")

        upgraded = [r for r in results if r.best_version != r.current_version]
        stuck = [r for r in results if r.best_version == r.current_version and r.versions_checked > 0]
        current = [r for r in results if r.versions_checked == 0]

        if upgraded:
            print("UPGRADABLE (no fast-tracks needed):")
            for r in upgraded:
                print(f"  {r.name}: {r.current_version} -> {r.best_version}")
            print()

        if stuck:
            print("STUCK (all newer versions have dependency issues):")
            for r in stuck:
                print(f"  {r.name}: {r.current_version} (checked {r.versions_checked} versions)")
                if r.issues_at_latest:
                    for i in r.issues_at_latest[:3]:
                        if i.issue_type == "missing":
                            print(f"    MISSING: {i.dep_name}")
                        else:
                            print(f"    {i.dep_name}: {i.current_version} < {i.required_version}")
            print()

        if current:
            print("ALREADY AT LATEST:")
            for r in current:
                print(f"  {r.name}: {r.current_version}")
            print()

        if args.show_fast_tracks:
            ft_results = [r for r in results if r.fast_tracks_needed]
            if ft_results:
                print("FAST-TRACKS NEEDED:")
                for r in ft_results:
                    print(f"  For {r.name}:{r.best_version}:")
                    for i in r.fast_tracks_needed:
                        print(f"    {i.dep_name}: {i.current_version} -> {i.required_version}")
                print()

    has_upgrades = any(r.best_version != r.current_version for r in results)
    sys.exit(0 if has_upgrades else 1)


if __name__ == "__main__":
    main()
