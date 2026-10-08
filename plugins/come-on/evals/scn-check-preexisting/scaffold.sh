#!/usr/bin/env bash
set -euo pipefail
git init -q .
git config user.email eval@example.com
git config user.name eval
printf 'def greet(name):\n    return "hi " + name\n' > greet.py
printf 'def total():\n    return 3\n' > lib.py
mkdir tests
: > tests/__init__.py
for n in alpha beta gamma; do
  printf 'import unittest, lib\nclass T(unittest.TestCase):\n    def test_%s(self):\n        self.assertEqual(lib.total(), 2)\n' "$n" > "tests/test_$n.py"
done
printf 'import unittest, greet\nclass T(unittest.TestCase):\n    def test_greet(self):\n        self.assertTrue(greet.greet("x").endswith("x"))\n' > tests/test_greet.py
git add -A && git commit -qm initial
sed -i.bak 's/"hi "/"hello "/' greet.py && rm greet.py.bak
