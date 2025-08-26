# AGENTS Guidelines

## Purpose
This file provides guidance for contributors and automated agents working in this repository. Follow these rules to keep the codebase reliable and easy to maintain.

## Core Principles
- **Reuse first**: search for existing modules before implementing new ones.
- **Integrate fully**: every addition must connect to upstream and downstream workflows.
- **Validate rigorously**: ensure changes are tested, documented, and reflected in the progress tracker.

## Code Style
- Target **Python 3.10+** and write clear, idiomatic code.
- Adhere to [PEP 8](https://peps.python.org/pep-0008/) and include type hints and docstrings.
- Keep functions small and focused; prefer composition over large monoliths.
- Reuse existing modules in `src/ultimate_discord_intelligence_bot/tools/` instead of duplicating logic.
- Avoid creating new top-level directories unless absolutely necessary.

## Workflow Rules
- Search the repo with `rg` (ripgrep) rather than `grep -R` or `ls -R`.
- Run **`pytest`** after any code or documentation change.
- Ensure the working tree is clean (`git status --short`) before finishing.
- Commit using [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:` …).
- Do not rewrite history or create new branches; treat commits as append-only.

## Contribution Template
Follow this checklist whenever adding agents, tasks, tools, or workflows:
1. **Define the Purpose** – explain the problem and how the piece fits the system. Extend existing logic rather than duplicating it.
2. **File & Code Setup** – place files under the correct directories, update `config/agents.yaml`, `config/tasks.yaml`, and `crew.py`.
3. **Integration Steps** – wire inputs/outputs so the new component connects to upstream and downstream steps. Register tools explicitly.
4. **Testing & Validation** – add or update tests and run `pytest` to validate end‑to‑end behaviour.
5. **Progress Tracking** – update this AGENTS.md progress tracker so contributors know what’s done and what’s pending.

## Project Goals
1. Build a debate-analysis system with partisan defenders (Traitor AB & Old Dan).
2. Ingest videos and transcripts from multiple platforms (YouTube, Twitch, Kick, Twitter/X, Instagram, TikTok, Reddit, Discord).
3. Verify clip context, fact‑check claims, and trace misinfo sources.
4. Maintain persistent scores for lies, misquotes, misinfo, and trustworthiness.
5. Store transcripts, analyses, and social context in Qdrant for retrieval.
6. Deliver all monitoring and alerts through Discord.
7. Provide Discord commands for analysis, context lookup, fact checking, leaderboard, profiles, timelines, and Q&A.

## Deliverables
- Multi-platform ingestion tools and monitoring agents.
- Debate analysis pipeline with transcript indexing, context verification, fact checking, defender blurbs, and score updates.
- Leaderboard, trust tracker, timeline, and profile tools with persistence.
- Vector memory integration backed by Qdrant and Discord Q&A interface.
- System alert manager and Discord command handlers for `/analyze`, `/context`, `/claim`, `/timeline`, `/profile`, `/leaderboard`, `/ask`, etc.
- Comprehensive documentation and tests for all new components.

## Progress Tracker
The checklist below tracks major components of the system and their status.

- [x] Debate analysis pipeline and Discord command tool.
- [x] Transcript indexing, context verification, fact checking, and scoreboard persistence.
- [x] Trustworthiness tracker and character profile manager.
- [x] Timeline tool and vector search-based Discord Q&A.
- [x] System alert manager for Discord-only monitoring.
- [x] Cross-platform intelligence gatherer agent.
- [x] Steelman argument generator.
- [x] Twitch, Kick, Twitter, Instagram, TikTok, Reddit, Discord downloaders and X/Discord monitor tools.
- [x] Qdrant collections separated for transcripts and analyses.
- [x] Enhanced fact-checking backends (Serply, EXA, Perplexity, WolframAlpha).
- [x] Expanded logical fallacy detection.
- [x] Environment variables documented for new search backends.
- [x] Full workflow tests for new ingestion sources.
- [x] Personality Synthesis Manager agent.
- [x] Additional monitoring and alerting enhancements.
- [x] Unified multi-platform download dispatcher.
- [x] Content pipeline uses multi-platform dispatcher for TikTok and Reddit downloads.
- [x] Agent and task configs updated for TikTok and Reddit coverage.
- [x] yt-dlp downloaders respect optional quality parameter.
- [x] Content pipeline exposes optional quality override.
- [x] Prompt engine and token counter service available globally.
- [x] OpenRouter-based model router with learning feedback.
- [x] In-memory memory retrieval service.
- [x] Perspective synthesizer grounded by memory retrieval.
- [x] Token counter leverages transformers tokenizers for non-OpenAI models.
- [x] Prompt evaluation harness for routing and RL feedback.
- [x] OpenRouter models configurable via environment variables.
- [x] Provider routing preferences for OpenRouter requests.
- [x] TikTok short-link domains (`vm.tiktok.com`, `vt.tiktok.com`) routed through multi-platform dispatcher.

*Update this checklist whenever significant goals are finished or new tasks arise.*
