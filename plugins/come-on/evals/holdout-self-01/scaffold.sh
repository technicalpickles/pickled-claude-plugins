#!/usr/bin/env bash
set -euo pipefail

git init -q .
git config user.email "dev@example.com"
git config user.name "Example Dev"

mkdir -p invoicer tests

cat > invoicer/__init__.py <<'EOF'
EOF

cat > invoicer/fmt.py <<'EOF'
def format_amount(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100:,}.{cents % 100:02d}"


def format_date(d):
    return d.strftime("%Y-%m-%d")
EOF

cat > invoicer/invoice.py <<'EOF'
from invoicer.fmt import format_amount


def line_total(qty, unit_cents):
    return qty * unit_cents


def render_line(desc, qty, unit_cents):
    return f"{desc:<20} x{qty:<3} {format_amount(line_total(qty, unit_cents))}"
EOF

cat > invoicer/export.py <<'EOF'
from invoicer import fmt

COLUMNS = [("description", "text"), ("total", "amount"), ("issued", "date")]


def _formatter(kind):
    if kind == "text":
        return str
    return getattr(fmt, "format_" + kind)


def export_row(row):
    return ",".join(_formatter(kind)(row[name]) for name, kind in COLUMNS)
EOF

cat > tests/__init__.py <<'EOF'
EOF

cat > tests/test_invoice.py <<'EOF'
import unittest

from invoicer.invoice import render_line


class InvoiceTest(unittest.TestCase):
    def test_render_line(self):
        self.assertIn("$12.50", render_line("Widget", 5, 250))


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_export.py <<'EOF'
import datetime
import unittest

from invoicer.export import export_row


class ExportTest(unittest.TestCase):
    def test_export_row(self):
        row = {
            "description": "Gadget",
            "total": 123456,
            "issued": datetime.date(2024, 3, 1),
        }
        self.assertEqual(export_row(row), "Gadget,$1,234.56,2024-03-01")


if __name__ == "__main__":
    unittest.main()
EOF

cat > README.md <<'EOF'
# invoicer

Tiny invoice rendering library.

Run tests with `python3 -m unittest discover -s tests -t .`
EOF

git add -A
git commit -q -m "baseline"
