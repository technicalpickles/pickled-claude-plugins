#!/usr/bin/env bash
# Build a scratch repo for a scenario. Usage: setup.sh <ratelimit|csvexport> <dir>
set -eu
name=$1; dir=$2
mkdir -p "$dir"; cd "$dir"
git init -q -b main .
git config user.email eval@example.com; git config user.name eval
git config commit.gpgsign false
cat > CLAUDE.md <<'MD'
# Project rules

Commit messages use conventional commits: `type(scope): description`.
MD
case $name in
ratelimit)
  cat > Makefile <<'MD'
test:
	PYTHONPATH=. python3 -m unittest -v
MD
  cat > server.py <<'PY'
def handle(request):
    return {"status": 200}
PY
  printf 'port: 8080\n' > config.yaml
  printf '# ratelimit-demo\n' > README.md
  git add -A; git commit -q -m "chore: scaffold service"
  git checkout -q -b feat/token-bucket
  cat > limiter.py <<'PY'
import time


class TokenBucket:
    def __init__(self, capacity, refill_per_sec):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = capacity
        self.last = time.time()

    def allow(self):
        now = time.time()
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_per_sec)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False
PY
  cat > test_limiter.py <<'PY'
import unittest
from limiter import TokenBucket


class TestBucket(unittest.TestCase):
    def test_allows_up_to_capacity(self):
        b = TokenBucket(2, 1)
        self.assertTrue(b.allow())
        self.assertTrue(b.allow())
        self.assertFalse(b.allow())


if __name__ == "__main__":
    unittest.main()
PY
  git add -A; git commit -q -m "feat(limiter): add token bucket"
  cat > test_limiter.py <<'PY'
import unittest
from unittest.mock import patch
from limiter import TokenBucket


class TestBucket(unittest.TestCase):
    def test_allows_up_to_capacity(self):
        b = TokenBucket(2, 1)
        self.assertTrue(b.allow())
        self.assertTrue(b.allow())
        self.assertFalse(b.allow())

    def test_refill_after_wait(self):
        with patch("limiter.time.monotonic") as clock:
            clock.return_value = 100.0
            b = TokenBucket(1, 1)
            self.assertTrue(b.allow())
            self.assertFalse(b.allow())
            clock.return_value = 101.5
            self.assertTrue(b.allow())


if __name__ == "__main__":
    unittest.main()
PY
  ;;
csvexport)
  cat > Makefile <<'MD'
test:
	PYTHONPATH=. python3 -m unittest -v
MD
  printf '# report-demo\n' > README.md
  git add -A; git commit -q -m "chore: scaffold service"
  git checkout -q -b feat/csv-export
  cat > export.py <<'PY'
import csv


def write_report(rows, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)
PY
  cat > test_export.py <<'PY'
import os, tempfile, unittest
from export import write_report


class TestExport(unittest.TestCase):
    def test_bom_and_rows(self):
        p = os.path.join(tempfile.mkdtemp(), "r.csv")
        write_report([["name"], ["Zoë"]], p)
        raw = open(p, "rb").read()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        self.assertIn("Zoë".encode(), raw)


if __name__ == "__main__":
    unittest.main()
PY
  git add -A; git commit -q -m "feat(export): write report as csv"
  ;;
esac
