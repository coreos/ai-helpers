# AI Helper Skills

Specialized skills for RHCOS/COREOS pipeline operations, build systems, and infrastructure management.

## Skills

| Skill | Description |
|-------|-------------|
| `initramfs-investigation` | Investigate initramfs issues - extraction, module analysis, and comparing working vs failing builds |
| `pipeline-dedup` | Deduplication logic for CI pipeline failures - check Jira for existing tracking with semantic analysis |
| `pipeline-failures` | Investigate Jenkins CI pipeline failures - failure patterns, root cause analysis, and debugging workflows |
| `pipeline-jira` | Create JIRA issues for CI pipeline failures - COS project conventions and subtask structure |
| `pipeline-triage-workflow` | Ordered agent-style triage for a single failed Jenkins build - gather metadata, logs, classification, summary |
| `rhcos-artifacts` | RHCOS build artifacts, package comparison, and coreos-assembler version tracking |
| `rhcos-brew` | Brew (Red Hat build system) - package searches, NVR naming, tags, and package sources |
| `rhcos-build-pipeline` | RHCOS build pipeline - scheduling, two-stage builds, versionlock mechanism, and troubleshooting |
| `rhcos-ocp-release` | OCP release queries - latest versions, RHCOS images, and RPM package lists |
| `rhcos-repositories` | RHCOS GitHub repositories, package definitions, and test locations |
| `rhcos-versions` | RHCOS build variants, streams, and OCP to RHEL version mappings |

## Usage

Each skill is a `SKILL.md` file with YAML frontmatter containing `name` and `description`. Skills provide specialized knowledge and workflows for AI assistants working with RHCOS infrastructure.

## Related

- [plugins/](../plugins/) - Claude Code plugins with commands
- [agents/](../agents/) - Agent definitions for specialized tasks
