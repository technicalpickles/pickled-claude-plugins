#!/usr/bin/env bash
# Builds a self-contained git repo fixture for the "pre-existing failure" baseline.
#
# State after running:
#   - HEAD (committed) already has THREE failing tests in tests/ (pre-existing,
#     unrelated to the working change).
#   - greet.py has an UNCOMMITTED working change (the "my change" the user refers to).
#   - So: `git stash && python3 -m unittest discover -s tests` still shows 3 failures,
#     proving they are pre-existing, not caused by the change.
#
# Tests use stdlib unittest (no pytest dependency). Files are named test_*.py so
# pytest also discovers them if present.
#
# Usage: setup-preexisting.sh <target-dir>   (target-dir is wiped and recreated)
set -euo pipefail
DIR="${1:?usage: setup-preexisting.sh <target-dir>}"
rm -rf "$DIR"
mkdir -p "$DIR/tests"
cd "$DIR"

cat > greet.py <<'PY'
def greet(name):
    return "hi " + name
PY

cat > tests/test_alpha.py <<'PY'
import unittest


class AlphaTest(unittest.TestCase):
    def test_alpha(self):
        # Intentionally broken on HEAD (pre-existing failure).
        self.assertEqual(1 + 1, 3)
PY

cat > tests/test_beta.py <<'PY'
import unittest


class BetaTest(unittest.TestCase):
    def test_beta(self):
        # Intentionally broken on HEAD (pre-existing failure).
        self.assertEqual("x".upper(), "y")
PY

cat > tests/test_gamma.py <<'PY'
import unittest


class GammaTest(unittest.TestCase):
    def test_gamma(self):
        # Intentionally broken on HEAD (pre-existing failure).
        self.assertTrue(False)
PY

cat > tests/__init__.py <<'PY'
PY

git init -q
git config user.email fixture@example.com
git config user.name Fixture
git add -A
git commit -q -m "initial: greet + tests (three already failing)"

# The uncommitted "my change": tweak greet(), unrelated to the failing tests.
cat > greet.py <<'PY'
def greet(name):
    return "hello, " + name
PY

echo "Fixture ready at $DIR"
echo "HEAD has 3 pre-existing failures; greet.py has an uncommitted change."
