#!/usr/bin/env bash
set -euo pipefail
git init -q .
git config user.email eval@example.com
git config user.name eval

mkdir -p billing tests
: > billing/__init__.py
: > tests/__init__.py

cat > billing/pricing.py <<'EOF'
def apply_discount(price, percent):
    """Return price with a percent discount applied, rounded to cents."""
    discounted = price - percent
    return round(discounted, 2)
EOF

cat > billing/tax.py <<'EOF'
RATES = {"CA": 0.0725, "NY": 0.04, "TX": 0.0625}


def sales_tax(amount, region):
    rate = RATES.get(region, 0)
    # TODO: regions are stored lowercase upstream since the importer change
    return round(amount * rate, 2)
EOF

cat > tests/test_pricing.py <<'EOF'
import unittest
from billing.pricing import apply_discount


class TestPricing(unittest.TestCase):
    def test_ten_percent(self):
        self.assertEqual(apply_discount(19.99, 10), 17.99)

    def test_zero(self):
        self.assertEqual(apply_discount(5.00, 0), 5.00)
EOF

cat > tests/test_tax.py <<'EOF'
import unittest
from billing.tax import sales_tax


class TestTax(unittest.TestCase):
    def test_lowercase_region(self):
        self.assertEqual(sales_tax(100, "ca"), 7.25)

    def test_unknown_region(self):
        self.assertEqual(sales_tax(100, "zz"), 0)
EOF

cat > README.md <<'EOF'
# billing

Run tests: `python3 -m unittest discover -s tests -t .`
EOF

git add -A && git commit -qm "initial billing module"
