---
name: backport
description: Backport upstream commits (from GitHub PRs or commit SHAs) into CentOS Stream or RHEL dist-git RPM packages, including JIRA ticket creation and spec file updates. Use when the user asks to backport a commit, cherry-pick a patch, or port an upstream fix to a dist-git package.
---

# Backport Skill

**Purpose:** Automate the process of backporting upstream commits (from
GitHub PRs or commit SHAs) into CentOS Stream or RHEL dist-git RPM packages,
including JIRA ticket creation and spec file updates.

**When to Use:** Invoke this skill when the user asks to backport a commit,
cherry-pick a patch, or port an upstream fix to a dist-git package.

**Never push automatically.** Always leave `centpkg push` / `rhpkg push` to
the user.

> Related: `rhcos-versions`, `pipeline-jira`

## Background: supported streams and multiple runs

A fix must be patched **top-down** into every currently supported stream
between the newest development branch and the oldest affected one, skipping
only streams that are out of support - e.g. upstream, then CentOS Stream
10/9 (current dev), then every supported RHEL Z-stream down to the oldest
affected one. Skipping a stream causes a regression: a customer who
upgrades from a patched older stream to a stream that was never patched
hits the bug again. Verify the current list of supported streams before
backporting (streams age out of support roughly annually, and new
Z-streams/dev branches appear over time) - don't assume the list is static.

In practice this means **running this skill's workflow once per target
stream**, newest to oldest, each with its own target branch, JIRA ticket,
and commit:

- **For the first (newest) stream**, run the full workflow below (Steps
  1-9): fetch and examine the upstream commit, generate a patch, update the
  spec, verify with prep, create the JIRA ticket, branch, and commit.
- **For every stream after the first, start with the cherry-pick**: a
  backport commit already exists on the first stream's branch, carrying
  both the patch file and the spec update together. Branch from the new
  target and try `git cherry-pick <prior-backport-commit-sha>` *before*
  redoing any of Steps 2-6. Only fall back to regenerating the patch from
  scratch if that cherry-pick conflicts. See "Backporting to Additional
  Streams" after Step 9 for the full sequence.

A **RHEL Jira issue** (project `RHEL`) tracks the fix landing in a specific
RHEL/CentOS Stream version and is the source of truth driving the build. A
separate **OCPBUGS issue** (different project, not covered by this skill)
tracks the fix reaching an OCP release/payload and can simply link to the
RHEL issue instead of requiring its own RPM build.

## Workflow

### Step 1: Gather Information

Collect the following from the user (ask if not provided):

- **Source commit or PR** - a GitHub PR URL, commit SHA, or branch name
- **Upstream local repo path** - where the upstream source is cloned locally
- **Target dist-git repo path** - the CentOS Stream or RHEL dist-git
  package directory
- **Target branch** - which dist-git branch to base on (e.g., `c10s`,
  `c9s`, `rhel-10.0.0`)
- **JIRA component** - the component name in the RHEL project (e.g.,
  `ostree`, `rpm-ostree`, `podman`). Infer from the package name if
  obvious, otherwise ask.
- **JIRA assignee** - the assignee's user identifier (e.g.,
  `rhn-support-jmarrero`). Use `currentUser()` to search for existing
  tickets. Ask the user if not provided.
- **Fix version** - the target RHEL release (e.g., `rhel-10.3`). Ask the
  user if not obvious from the target branch.

If the user provides a GitHub PR URL, fetch the PR page and identify the
commit SHA(s) to backport.

### Step 2: Fetch and Examine the Upstream Commit

> Only the first stream needs this step in full - for later streams, try
> the cherry-pick in "Backporting to Additional Streams" first.

- Navigate to the user's local upstream repo
- Fetch the latest if needed: `git fetch origin`
- Examine the commit:
  ```
  git show <commit-sha> --stat
  git log --oneline <commit-sha> -1
  ```
- Generate the full patch to review the changes:
  ```
  git format-patch -1 <commit-sha> --stdout
  ```
- Identify which files are modified and confirm scope with the user if the
  change is large

### Step 3: Check Patch Applicability

Before generating the patch, verify it will apply cleanly to the target
version:

- Read the dist-git spec file and find the `Version:` field (e.g.,
  `Version: 2026.1`)
- Identify the corresponding upstream tag (e.g., `v2026.1` for version
  `2026.1`)
- Compare the modified files between the upstream tag and the commit's
  parent:
  ```
  git diff v<version> <commit-sha>^ -- <modified-files>
  ```
- If the diff output is empty, the patch applies cleanly - no rebasing
  needed
- If the diff output is not empty, the patch may need manual adjustment -
  warn the user and show the conflicting changes

### Step 4: Generate the Patch

Generate a `git format-patch` from the upstream repo and place it directly
in the dist-git directory:

```
git format-patch -1 <commit-sha> --stdout > /path/to/dist-git/0001-short-description.patch
```

Patch naming convention: use the default `git format-patch` output name,
e.g.:

```
0001-sysroot-Merge-bootconfig-extra-from-previously-stage.patch
```

### Step 5: Update the Spec File

- Read the current spec file (e.g., `ostree.spec`)
- Find the `Source0:` line (or the last existing `Patch` line if patches
  already exist)
- Add a `PatchN:` line immediately after:
  ```
  Patch0: 0001-descriptive-name.patch
  ```
- Use the next available patch number if patches already exist (e.g.,
  `Patch1:`, `Patch2:`, ...)
- Verify the `%prep` section uses `%autosetup -Sgit` - this auto-applies
  all `PatchN:` entries via `git-am`. If the spec uses a different setup
  macro, add the appropriate `%patch` macro call instead.

### Step 6: Verify with centpkg/rhpkg prep

Run the appropriate prep command to confirm the patch applies cleanly:

- CentOS Stream: `centpkg prep`
- RHEL: `rhpkg prep`

This downloads the source tarball from the lookaside cache (if not already
cached locally), extracts it, initializes a git repo, and applies all
patches. The output must show:

```
Applied patch <filename>.patch cleanly.
```

If the patch fails to apply:

- Read the reject output to understand what conflicted
- Adjust the patch manually or rebase against the target version
- Re-run `centpkg prep` / `rhpkg prep` until it passes

### Step 7: Create or Reuse JIRA Ticket

Before creating a new ticket, search for an existing one that covers the
same issue:

```
JQL: project = RHEL AND component = <component> AND assignee = currentUser() ORDER BY updated DESC
```

Replace `<component>` with the component gathered in Step 1 (e.g.,
`ostree`). If a matching ticket exists, ask the user whether to reuse it or
create a new one.

**Creating a New Ticket**

Use `jira_create_issue` with these fields:

| Field | Value | Notes |
|---|---|---|
| `project_key` | `RHEL` | Always RHEL for backport bugs |
| `issue_type` | `Bug` | |
| `summary` | Short description of the backport | e.g., "ostree is not merging kargs correctly when source key is added" |
| `description` | Narrative paragraph explaining what is being backported and why, referencing the upstream PR/commit URL | |
| `components` | `<component>` | From Step 1 (e.g., `ostree`, `rpm-ostree`, `podman`) |
| `assignee` | `<assignee>` | From Step 1 (e.g., `rhn-support-jmarrero`). Ask the user if not provided. |

`additional_fields` (JSON string): `{"labels": []}` - labels are empty by
default unless the user specifies otherwise.

Note: if you don't know the correct component name, use
`jira_get_project_components` with `project_key: RHEL` to list available
components, or infer from the dist-git package name.

**Setting Fix Version**

Use `jira_update_issue` to set the Fix Version to the target release
gathered in Step 1. If the user did not specify one, ask them now - do not
guess.

To find the correct version ID, use `jira_get_project_versions` with
`project_key: RHEL` and search for the target release name. Use the
version ID (not the name) in the update.

**Setting Severity**

Use `jira_search_fields` with keyword `Severity` to find the field ID, then
`jira_get_field_options` to get valid values. Use `jira_update_issue` to
set it.

For standard backports, "Moderate" is the typical value. "Normal" is **NOT**
valid.

**Transitioning to In Progress**

Use `jira_get_transitions` to find the available transitions for the
issue, then `jira_transition_issue` to move it to In Progress.

Important: the transition to In Progress may require the Severity field to
be set first. Always set severity before transitioning.

**Record the Ticket Number**

Save the ticket key (e.g., `RHEL-174914`) for use in the commit message.

### Step 8: Create Branch and Commit

**Branching**

1. Fetch the latest from origin:
   ```
   git fetch origin
   ```
2. Create a new branch based on the target branch, named
   `backport-<ticket-number>`:
   ```
   git checkout -b backport-<ticket-number> origin/<target-branch>
   ```
   Example:
   ```
   git checkout -b backport-174914 origin/c10s
   ```
3. **Start here if a backport commit for this fix already exists on
   another branch** (second stream onward): try
   `git cherry-pick <prior-backport-commit-sha>` instead of redoing
   Steps 2-6. If it applies cleanly, skip straight to amending the commit
   message in the "Committing" section below with this stream's ticket
   key. If it conflicts, abort the cherry-pick (`git cherry-pick --abort`)
   and fall back to Steps 2-6 for this stream.
   If committing fresh (no prior commit), stage and commit directly (see
   below).

**Committing**

Stage the patch file and spec file, then commit:

```
git add <patch-file> <package>.spec
git commit -m "Backport https://github.com/<org>/<repo>/pull/<PR-number>" -m "Resolves: RHEL-XXXXXX"
```

Commit message format:

- First `-m`: `Backport <full URL to upstream PR>`
- Second `-m`: `Resolves: <JIRA-ticket-key>`

Example:

```
git commit \
  -m "Backport https://github.com/ostreedev/ostree/pull/3587" \
  -m "Resolves: RHEL-174914"
```

If this commit came from a successful cherry-pick (Branching step 3), the
trailer still refers to the **previous** stream's ticket - amend it to
reference this stream's own ticket instead:

```
git commit --amend -m "Backport https://github.com/<org>/<repo>/pull/<PR-number>" \
                    -m "Resolves: <THIS-STREAM-TICKET-KEY>"
```

**Verify the Final State**

```
git log --oneline -3
```

Expected output:

```
b121ede Backport https://github.com/ostreedev/ostree/pull/3587
adb53bd Release 2026.1
d2cc9cc Release 2025.7
```

### Step 9: Inform User to Push

**CRITICAL: NEVER push automatically. Always leave pushing to the user.**

Print the following:

```
Changes committed locally on branch backport-<ticket-number>.
When ready, push with:
  centpkg push    (for CentOS Stream)
  rhpkg push      (for RHEL)
```

If more supported streams remain (see Background above), continue with
"Backporting to Additional Streams" below for the next stream down.

## Backporting to Additional Streams

For the second and every subsequent stream (working top-down), don't
restart from Step 2. Instead:

1. Run Step 1 again only for anything that changed (target dist-git repo
   path, target branch, fix version); component and the upstream
   commit/PR stay the same.
2. Run Step 7 to create (or reuse) **a new JIRA ticket for this stream** -
   each stream gets its own ticket, with its own Fix Version.
3. Branch from this stream's target branch and attempt the cherry-pick
   first (Step 8, Branching step 3):
   ```
   git fetch origin
   git checkout -b backport-<this-stream-ticket-number> origin/<this-target-branch>
   git cherry-pick <prior-backport-commit-sha>
   ```
4. **If the cherry-pick applies cleanly**: amend the commit message to
   reference this stream's ticket key (see "Committing" above) and move on
   to Step 9 - Steps 2-6 are not needed since the patch file and spec
   update travel with the cherry-picked commit.
5. **If the cherry-pick conflicts**: run `git cherry-pick --abort`, then
   fall back to the full Steps 2-6 for this stream (the patch or spec may
   need to differ here, e.g. different `Version:` or file layout).
6. Repeat for the next stream down until every in-support stream is
   covered.

## Summary Checklist

After completing the backport, provide a summary covering each item:

- [ ] Upstream commit identified and reviewed
- [ ] Current list of supported streams verified (not assumed from memory)
- [ ] First stream: patch generated via `git format-patch`
- [ ] First stream: spec file updated with `PatchN:` line
- [ ] `centpkg prep` / `rhpkg prep` confirms clean apply
- [ ] JIRA ticket created (or existing ticket reused) in RHEL project, per
      stream
- [ ] Component set (e.g., `ostree`, `rpm-ostree`)
- [ ] Assignee set (e.g., `rhn-support-jmarrero`)
- [ ] Severity set (e.g., `Moderate`)
- [ ] Fix Version set per stream (looked up dynamically via
      `jira_get_project_versions`)
- [ ] Ticket transitioned to In Progress (via `jira_get_transitions` +
      `jira_transition_issue`)
- [ ] New branch created as `backport-<ticket-number>` from
      `origin/<target-branch>`, per stream
- [ ] Later streams: cherry-pick of the prior backport commit tried first,
      falling back to regeneration only on conflict
- [ ] Each commit includes the backport PR link and a stream-specific
      `Resolves:` line
- [ ] User informed to push manually, per stream
- [ ] Repeated for every supported stream, top-down

## JIRA Field Reference

All field IDs, version IDs, and transition IDs should be looked up
dynamically. Do not hardcode them.

- **Field IDs:** Use `jira_search_fields` with a keyword (e.g., `Severity`,
  `Fix Version`) to find the correct field ID.
- **Field options:** Use `jira_get_field_options` with the field ID to get
  valid dropdown values.
- **Transitions:** Use `jira_get_transitions` with the issue key to get
  available transitions.
- **Version IDs:** Use `jira_get_project_versions` with
  `project_key: RHEL` to look up version IDs.
- **Components:** Use `jira_get_project_components` with
  `project_key: RHEL` to look up component names.

## Error Handling

**Patch does not apply cleanly**

- Check if there are intermediate commits between the release tag and the
  patch parent that modify the same file
- Run `git diff v<version> <commit-sha>^ -- <file>` in the upstream repo to
  see what changed
- The patch may need to be rebased or manually adjusted
- Re-run `centpkg prep` / `rhpkg prep` after every adjustment

**Cherry-pick conflicts when backporting to an additional stream**

- `git cherry-pick --abort` to back out cleanly
- Fall back to Steps 2-6 for this stream - the file layout, spec macros, or
  `Version:` may differ enough from the stream you cherry-picked from

**JIRA severity value rejected**

- "Normal" is NOT a valid value - use "Moderate" instead
- Always use exact case-sensitive values: `Low`, `Moderate`, `Important`,
  `Critical`, `Urgent`
- If the update fails with "Specify a valid value for Severity", use
  `jira_search_fields` to find the Severity field ID, then
  `jira_get_field_options` to re-check valid options

**JIRA transition fails with "Severity required"**

- The Severity field must be set BEFORE transitioning to In Progress
- Set severity first via `jira_update_issue`, then call
  `jira_transition_issue`

**JIRA MCP tools not available**

- Confirm a Jira MCP server (e.g. `mcp-atlassian`) is configured and
  connected for your Cursor/Claude Code setup - check the MCP server list
  in settings
- `mcp-atlassian` requires `uv` to be installed (`sudo dnf install uv` on
  Fedora, or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- If tools are still unavailable after config changes, restart the MCP
  connection/client

**Source tarball not in lookaside cache**

- `centpkg prep` / `rhpkg prep` will download it automatically from the
  lookaside cache
- If the download fails, run `centpkg sources` or `rhpkg sources` manually
- If the tarball is not yet uploaded, the user may need to upload it first
  with `centpkg upload` / `rhpkg upload`

## References

- CentOS Stream dist-git: https://gitlab.com/redhat/centos-stream/rpms/
- RHEL dist-git: https://gitlab.com/redhat/rhel/rpms/
- MCP Atlassian: https://github.com/sooperset/mcp-atlassian
