# Working with Colima Skill

A Claude Code skill for working with [Colima](https://github.com/abiosoft/colima), a container runtime for macOS.

## When This Skill Activates

- Docker commands fail with "Cannot connect to Docker daemon"
- Starting/stopping container environments on macOS
- Managing multiple Docker profiles/contexts
- Troubleshooting container environment issues
- SSH agent forwarding for Docker builds

## Structure

```
working-with-colima/
├── SKILL.md                     # Entry point (~80 lines)
├── README.md                    # This file
├── docs/
│   └── test-cases.md            # RED/GREEN test validation
└── references/
    ├── docker-contexts.md       # Context switching, DOCKER_HOST
    ├── profile-management.md    # Creating, configuring profiles
    ├── troubleshooting.md       # Common issues and solutions
    ├── common-options.md        # CLI flags, VM configuration
    └── colima-upstream/         # Official Colima docs
        ├── README.md
        ├── FAQ.md
        └── INSTALL.md
```

## Design

Uses **progressive disclosure**:
- `SKILL.md` is a compact navigation map with quick reference
- Detailed content lives in `references/` for when deeper knowledge is needed
- Upstream docs included locally for comprehensive reference

## Testing

See `docs/test-cases.md` for RED/GREEN validation scenarios used during development.

Key finding: Without this skill, agents default to Docker Desktop troubleshooting. With this skill, agents correctly use Colima-specific diagnostics (`colima status`, Docker contexts, correct socket paths).

## Updating Upstream Docs

To refresh the upstream Colima documentation:

```bash
uvx gitingest https://github.com/abiosoft/colima -i "*.md" -o /tmp/colima-docs.txt
# Then manually update files in references/colima-upstream/
```
