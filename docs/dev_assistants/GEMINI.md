# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the `ultimate-discord-intelligence-bot` project.

## Project Overview

The `ultimate-discord-intelligence-bot` is a sophisticated, tenant-aware Discord bot built with Python and the `crewAI` framework. It's designed to ingest, analyze, and respond to information from various sources, including YouTube, Twitch, and TikTok. The bot's core functionality revolves around providing grounded, fact-checked answers, and it includes advanced features like debate analysis, reinforcement learning for model routing, and a comprehensive governance and privacy framework.

The project is structured as a collection of services and tools that work together to provide a seamless experience. The main components are:

*   **Core Services**: These provide foundational capabilities like prompt building, token metering, cost-guarded model routing, caching, and reinforcement learning hooks.
*   **Ingestion & RAG**: This component handles the asynchronous ingestion of content from various platforms, transcript analysis, and storage in a Qdrant vector memory.
*   **Discord Bot**: The bot itself, which exposes a variety of commands for users to interact with the system. It's built using the `discord.py` library.
*   **Tools**: A rich set of tools that provide a wide range of capabilities, from downloading content and transcribing audio to performing sentiment analysis and detecting logical fallacies.

## Building and Running

The project uses `pip` for dependency management and `ruff` for linting and formatting. The main dependencies are listed in the `pyproject.toml` file.

### Setup

1.  **Install Python**: Ensure you have Python 3.10 or higher installed.
2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -e .[dev]
    ```

### Running the Bot

Run the bot via the unified setup CLI:

```bash
python -m ultimate_discord_intelligence_bot.setup_cli run discord
```

### Development Workflow

The project has a well-defined development workflow, which is documented in `CONTRIBUTING.md`. The key commands are:

*   **`make format`**: Auto-fix style and imports.
*   **`make lint`**: Run the linter.
*   **`make type`**: Run the static type checker.
*   **`make test`**: Run the test suite.

## Development Conventions

The project has a strong emphasis on code quality and maintainability. The following are some of the key development conventions:

*   **Tenant-aware design**: All operations should be tenant-aware, with explicit `TenantContext` passed to all relevant functions.
*   **Feature flags**: New functionality should be guarded by feature flags to allow for gradual rollout and testing.
*   **Error handling**: The project uses a `StepResult` class for handling structured outcomes from pipeline and tool steps.
*   **Typing**: The project uses `mypy` for static type checking, and new code should be fully annotated.
*   **Testing**: The project uses `pytest` for testing, and new code should be accompanied by tests.
*   **Commit style**: The project follows the Conventional Commits specification.
