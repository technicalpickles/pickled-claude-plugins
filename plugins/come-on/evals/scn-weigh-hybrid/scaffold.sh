#!/usr/bin/env bash
set -euo pipefail
mkdir -p db docs/adr
printf 'ActiveRecord::Schema.define do\n  create_table "accounts" do |t|\n    t.jsonb "settings", default: {}   # accounts.settings\n  end\nend\n' > db/schema.rb
printf "# ADR 0012: Don't store fields we filter on in JSONB\n" > docs/adr/0012-avoid-jsonb-for-queried-fields.md
