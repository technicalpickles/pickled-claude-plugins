# git-guard

Detects and reverts agent writes to git internals: config keys that execute code, hook files, and redirects. The verdict core is pure Python (stdlib only): it takes a hand-built snapshot of repo state and returns what to revert or warn about, without touching the filesystem or reading command text.

Status: pure core only, no hooks wired. What the probe that feeds it must guarantee is in [docs/probe-contract.md](docs/probe-contract.md).

git-guard is a speed bump, not a security boundary. It runs as you, so an agent that knows about it can edit its state. It catches confused agents and generic injections, and makes persistence visible or undone.

## Development

```bash
uv run --directory plugins/git-guard pytest tests/ -v
```
