#!/usr/bin/env bash
set -euo pipefail
mkdir -p notes logs config/initializers app
printf '# Handoff (written 2026-08-12)\nRoot cause of flaky checkout spec: cache warmer races the test DB setup.\nNext: remove the cache warmer.\n' > notes/handoff.md
printf '2026-10-05 checkout_spec FAILED: Timeout waiting for payment-stub (port 4010)\n2026-10-06 checkout_spec FAILED: Timeout waiting for payment-stub (port 4010)\n2026-10-07 checkout_spec FAILED: Timeout waiting for payment-stub (port 4010)\n' > logs/ci.log
printf '# cache warmer disabled in test since 2026-08-20\nCACHE_WARMER_ENABLED = !Rails.env.test?\n' > config/initializers/cache.rb
printf 'class CacheWarmer\n  def run; end\nend\n' > app/cache_warmer.rb
