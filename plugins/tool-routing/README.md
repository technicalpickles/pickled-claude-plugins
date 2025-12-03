# Tool Routing Plugin

Intercepts tool calls and suggests better alternatives.

## Installation

Add to your Claude Code plugins.

## Usage

Routes are configured in `hooks/tool-routes.yaml`. Other plugins can contribute routes by including their own `hooks/tool-routes.yaml`.

Project-specific routes go in `.claude/tool-routes.yaml`.

## CLI

- `tool-routing check` - Hook entry point (reads tool call from stdin)
- `tool-routing test` - Run inline test fixtures
- `tool-routing list` - Show merged routes from all sources
