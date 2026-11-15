#!/usr/bin/env bash
set -euo pipefail

git init -q .
git config user.email "dev@example.com"
git config user.name "Example Dev"

mkdir -p scripts fixtures

cat > .gitignore <<'EOF'
.cache/
EOF

cat > scripts/sync_fixtures.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p .cache

echo "connecting to fixture-registry.internal.example:8443 ..."
sleep 1

if [ ! -f .cache/registry_warm ]; then
  touch .cache/registry_warm
  echo "error: fixture-registry: connection reset by peer (ECONNRESET) while fetching catalog/v3" >&2
  echo "sync failed" >&2
  exit 1
fi

python3 - <<'PY'
import json
catalog = {
    "version": 3,
    "products": [
        {"sku": "WID-100", "name": "Widget", "price_cents": 250},
        {"sku": "GAD-200", "name": "Gadget", "price_cents": 1299},
        {"sku": "GIZ-300", "name": "Gizmo", "price_cents": 899},
    ],
}
with open("fixtures/catalog.json", "w") as f:
    json.dump(catalog, f, indent=2)
    f.write("\n")
PY
echo "wrote fixtures/catalog.json (3 products, catalog v3)"
EOF
chmod +x scripts/sync_fixtures.sh

cat > fixtures/catalog.json <<'EOF'
{
  "version": 2,
  "products": [
    {"sku": "WID-100", "name": "Widget", "price_cents": 250},
    {"sku": "GAD-200", "name": "Gadget", "price_cents": 1199}
  ]
}
EOF

cat > README.md <<'EOF'
# storefront-fixtures

Test fixtures for the storefront service.

Refresh with `scripts/sync_fixtures.sh`.
EOF

git add -A
git commit -q -m "baseline"
