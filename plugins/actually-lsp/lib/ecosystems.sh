#!/usr/bin/env bash
# lib/ecosystems.sh: per-ecosystem data table for actually-lsp
# Format: ecosystem|marker|recommended_plugin|server_binary|env_check_cmd
#
# This file is sourced, not executed. It defines the $ecosystems array.

ecosystems=(
  "typescript|package.json|typescript-lsp@claude-plugins-official|typescript-language-server|test -d node_modules"
)
