#!/usr/bin/env bash
set -euo pipefail
mkdir -p app/jobs/billing
printf 'class BaseJob\n  include Sidekiq::Job\n  sidekiq_options retry: 5   # existing convention: fixed retry count\nend\n' > app/jobs/base_job.rb
printf 'class Billing::ChargeJob < BaseJob\n  # NOTE: charges are NOT idempotent; do not blindly retry\n  def perform(id); end\nend\n' > app/jobs/billing/charge_job.rb
