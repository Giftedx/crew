"""Discord bot modularization package.

This package hosts the Discord gateway, commands, and orchestration logic
previously implemented in the monolithic `scripts/start_full_bot.py`.

Modules:
- discord_env: Safe discord import + lightweight shims
- env: Environment checks and defaults
- ingest: Ingest worker startup helpers
- tools_bootstrap: Tool container and loading/attachment
- prefix_commands: Legacy prefix commands and helpers
- autointel: Autonomous orchestration, embed builder, view, KB helpers
- slash_commands: Slash command registrations (admin + user)
- events: Core event handlers
- runner: create_full_bot() and main() entrypoint
"""

__all__ = [
    "runner",
]
