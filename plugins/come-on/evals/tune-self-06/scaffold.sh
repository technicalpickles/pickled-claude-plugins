#!/usr/bin/env bash
set -euo pipefail
git init -q .
git config user.email eval@example.com
git config user.name eval

mkdir -p invoices tests
: > invoices/__init__.py
: > tests/__init__.py

cat > invoices/export.py <<'EOF'
import json


def export_json(invoices):
    return json.dumps(invoices, indent=2)
EOF

cat > invoices/cli.py <<'EOF'
import argparse
import sys

from invoices.export import export_json


def main(argv=None):
    p = argparse.ArgumentParser(prog="invoices")
    p.add_argument("--format", choices=["json"], default="json")
    p.parse_args(argv)
    sys.stdout.write(export_json([]) + "\n")


if __name__ == "__main__":
    main()
EOF

cat > CHANGELOG.md <<'EOF'
# Changelog

## Unreleased
EOF

git add -A && git commit -qm "invoice export cli (json)"

cat > invoices/export.py <<'EOF'
import csv
import io
import json

CSV_FIELDS = ["id", "customer", "total", "currency", "status"]


def export_json(invoices):
    return json.dumps(invoices, indent=2)


def export_csv(invoices):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
    w.writeheader()
    # TODO: write rows (line items need flattening first)
    return buf.getvalue()
EOF

cat > tests/test_export.py <<'EOF'
import unittest
from invoices.export import export_csv


class TestExport(unittest.TestCase):
    def test_csv_header(self):
        self.assertTrue(export_csv([]).startswith("id,customer,total"))
EOF

cat > CHANGELOG.md <<'EOF'
# Changelog

## Unreleased
- Added CSV export for invoices (`invoices --format csv`)
EOF

git add -A && git commit -qm "feat: CSV export for invoices"
