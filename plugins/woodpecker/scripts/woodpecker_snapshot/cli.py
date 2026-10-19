"""Thin wrapper around woodpecker-cli: run it, parse its output, classify its errors."""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

TAB = "\t"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class WpError(Exception):
    NOT_INSTALLED = "not_installed"
    NOT_CONFIGURED = "not_configured"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    NETWORK_DENIED = "network_denied"
    UNREACHABLE = "unreachable"
    OTHER = "other"

    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind
        self.message = message


@dataclass
class Pipeline:
    number: int
    status: str
    commit: str
    branch: str
    event: str


@dataclass
class Step:
    workflow: str
    name: str
    state: str


def _error_text(stderr: str) -> str:
    """The fatal error from woodpecker-cli's JSON log lines, or the raw text."""
    fatal: List[str] = []
    plain: List[str] = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            plain.append(line)
            continue
        if isinstance(obj, dict) and obj.get("level") == "fatal" and obj.get("error"):
            fatal.append(str(obj["error"]))
    if fatal:
        return fatal[-1]
    return "\n".join(plain) or stderr.strip()


def classify_error(stderr: str) -> WpError:
    message = _error_text(stderr)
    low = message.lower()
    if "is not configured" in low:
        kind = WpError.NOT_CONFIGURED
    elif re.search(r"client error 40[13]", low):
        kind = WpError.UNAUTHORIZED
    elif "client error 404" in low:
        kind = WpError.NOT_FOUND
    elif low.endswith(": forbidden") and "client error" not in low:
        # What the command sandbox's network filter looks like from inside the CLI.
        kind = WpError.NETWORK_DENIED
    elif (
        re.search(r"client error 5\d\d", low)
        or "dial tcp" in low
        or "no such host" in low
        or "i/o timeout" in low
        or re.search(r"\beof\b", low)
    ):
        kind = WpError.UNREACHABLE
    else:
        kind = WpError.OTHER
    return WpError(kind, message)


def _version_key(path: str):
    # .../installs/<tool>/<version>/...; compare numerically so 3.19.0 > 3.9.0.
    parts = path.split(os.sep)
    version = parts[parts.index("installs") + 2] if "installs" in parts else ""
    return [int(n) for n in re.findall(r"\d+", version)]


def find_binary(binary: str = "woodpecker-cli") -> str:
    """The CLI on PATH, else the newest mise-installed copy, else the bare name.

    Agents often run with a PATH that lacks mise's shims, so a pinned install is
    invisible even though it's on disk. Returning the bare name when nothing is
    found lets the runner raise FileNotFoundError, which reports as not installed.
    """
    found = shutil.which(binary)
    if found:
        return found
    data = os.environ.get("MISE_DATA_DIR") or os.path.join(os.path.expanduser("~"), ".local", "share", "mise")
    pattern = os.path.join(data, "installs", "*woodpecker*cli*", "*", "**", binary)
    candidates = [c for c in glob.glob(pattern, recursive=True) if os.access(c, os.X_OK) and os.path.isfile(c)]
    if candidates:
        return max(candidates, key=_version_key)
    return binary


Runner = Callable[[Sequence[str], Optional[str]], "subprocess.CompletedProcess"]


def _default_runner(argv: Sequence[str], cwd: Optional[str]):
    env = dict(os.environ)
    # The update check calls woodpecker-ci.org, which the command sandbox denies.
    env.setdefault("WOODPECKER_DISABLE_UPDATE_CHECK", "true")
    return subprocess.run(
        list(argv), cwd=cwd, env=env, capture_output=True, text=True, timeout=60
    )


class WoodpeckerCli:
    def __init__(
        self,
        binary: Optional[str] = None,
        cwd: Optional[str] = None,
        runner: Optional[Runner] = None,
    ):
        self.binary = binary or find_binary()
        self.cwd = cwd
        self.runner = runner or _default_runner
        self._injected = runner is not None

    def _run(self, args: Sequence[str]) -> str:
        # An injected runner gets bare args so tests can match on them.
        argv = list(args) if self._injected else [self.binary] + list(args)
        try:
            result = self.runner(argv, self.cwd)
        except FileNotFoundError:
            raise WpError(WpError.NOT_INSTALLED, "woodpecker-cli is not on PATH or under the mise installs dir")
        except subprocess.TimeoutExpired:
            raise WpError(WpError.UNREACHABLE, "woodpecker-cli timed out after 60s")
        if result.returncode != 0:
            raise classify_error(result.stderr or "")
        return result.stdout

    def pipelines(self, repo: str, limit: int = 100) -> List[Pipeline]:
        template = TAB.join(
            ["{{.Number}}", "{{.Status}}", "{{.Commit}}", "{{.Branch}}", "{{.Event}}"]
        )
        out = self._run(
            ["pipeline", "ls", repo, "--limit", str(limit), "--output", "go-format=" + template]
        )
        rows: List[Pipeline] = []
        for line in out.splitlines():
            parts = line.split(TAB)
            if len(parts) != 5 or not parts[0].strip().isdigit():
                continue
            rows.append(Pipeline(int(parts[0]), parts[1], parts[2], parts[3], parts[4]))
        return rows

    def steps(self, repo: str, number: int) -> List[Step]:
        # ps templates take lowercase keys (.workflow, .step), unlike `pipeline ls`.
        template = TAB.join(["{{.workflow.Name}}", "{{.step.Name}}", "{{.step.State}}"])
        out = self._run(["pipeline", "ps", repo, str(number), "--format", template])
        rows: List[Step] = []
        for line in ANSI_RE.sub("", out).splitlines():
            parts = line.split(TAB)
            if len(parts) == 3 and parts[1].strip():
                rows.append(Step(parts[0], parts[1], parts[2].strip()))
        return rows

    def log(self, repo: str, number: int, step: str) -> str:
        return self._run(["pipeline", "log", "show", repo, str(number), step])
