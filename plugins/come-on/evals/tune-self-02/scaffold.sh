#!/usr/bin/env bash
set -euo pipefail
git init -q .
git config user.email eval@example.com
git config user.name eval

mkdir -p bin data
printf '.cache/\n' > .gitignore

cat > bin/fetch-rates <<'EOF'
#!/usr/bin/env bash
# Refresh data/rates.json from the rates service.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
marker="$root/.cache/fetch-rates.attempted"
mkdir -p "$root/.cache"
echo "fetching https://rates.internal.example/v2/latest ..."
if [ ! -f "$marker" ]; then
  touch "$marker"
  sleep 1
  echo "curl: (28) Operation timed out after 30001 milliseconds with 0 bytes received" >&2
  exit 28
fi
cat > "$root/data/rates.json" <<'JSON'
{
  "base": "USD",
  "as_of": "2026-10-09T14:00:00Z",
  "rates": {"EUR": 0.9137, "GBP": 0.7712, "JPY": 148.21, "CAD": 1.3654}
}
JSON
echo "wrote data/rates.json (4 currencies)"
EOF
chmod +x bin/fetch-rates

cat > data/rates.json <<'EOF'
{
  "base": "USD",
  "as_of": "2026-09-02T14:00:00Z",
  "rates": {"EUR": 0.9021, "GBP": 0.7655, "JPY": 145.80, "CAD": 1.3502}
}
EOF

cat > README.md <<'EOF'
# fx-snapshots

`bin/fetch-rates` pulls the latest rates from the rates service into `data/rates.json`.
EOF

git add -A && git commit -qm "initial fx snapshot repo"
