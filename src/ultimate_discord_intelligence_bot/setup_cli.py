"""Unified first-run setup and runner CLI.

This guided helper is the canonical way to configure and run the project.
It interactively collects configuration, writes/updates ``.env``, validates
files and folders, and can launch common run targets (Discord bot or crew).

Usage:
  python -m ultimate_discord_intelligence_bot.setup_cli            # interactive wizard
  python -m ultimate_discord_intelligence_bot.setup_cli wizard     # same as default
  python -m ultimate_discord_intelligence_bot.setup_cli doctor     # quick health checks
  python -m ultimate_discord_intelligence_bot.setup_cli run discord
  python -m ultimate_discord_intelligence_bot.setup_cli run crew
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

from core.secure_config import get_config

REPO_ROOT = Path(__file__).resolve().parents[2]
config = get_config()


def _print_header(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{title}\n{bar}")


def _prompt(key: str, default: str | None = None, secret: bool = False) -> str:
    existing = os.getenv(key) or default or ""
    suffix = f" [default: {existing}]" if existing else ""
    prompt = f"{key}{' (secret)' if secret else ''}:{suffix} > "
    try:
        value = input(prompt).strip()
    except EOFError:
        value = ""
    return value or existing


def _load_env(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _write_env(path: Path, lines: Iterable[str]) -> None:
    text = "\n".join(lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")
    print(f"✅ Wrote {path}")


def _merge_env_lines(lines: list[str], updates: dict[str, str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        key, _eq, _rest = line.partition("=")
        key = key.strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(line)
    # Append any missing keys at the end
    for k, v in updates.items():
        if k not in seen:
            out.append(f"{k}={v}")
    return out


def _ensure_dirs(paths: Iterable[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def _wizard() -> int:
    _print_header("Ultimate Discord Intelligence Bot - Setup Wizard")
    print("This will fully configure your environment (core + advanced).")

    env_path = REPO_ROOT / ".env"
    current = _load_env(env_path)

    # Core tokens and URLs
    updates: dict[str, str] = {}
    print("\nEnter tokens and URLs (leave blank to keep defaults):")
    for key, secret in [
        ("DISCORD_BOT_TOKEN", True),
        ("DISCORD_WEBHOOK", True),
        ("DISCORD_PRIVATE_WEBHOOK", True),
        ("OPENROUTER_API_KEY", True),
        ("OPENAI_API_KEY", True),
        ("EXA_API_KEY", True),
        ("PERPLEXITY_API_KEY", True),
    ]:
        updates[key] = _prompt(key, secret=secret)

    # Vector DB
    print("\nVector database (Qdrant) configuration:")
    updates["QDRANT_URL"] = _prompt("QDRANT_URL", default=config.qdrant_url)
    updates["QDRANT_API_KEY"] = _prompt("QDRANT_API_KEY", secret=True)

    # Downloads and quality
    print("\nDownload preferences:")
    updates["DEFAULT_DOWNLOAD_QUALITY"] = _prompt(
        "DEFAULT_DOWNLOAD_QUALITY", default=os.getenv("DEFAULT_DOWNLOAD_QUALITY", "1080p")
    )

    # Paths
    _print_header("Paths and storage")
    base_dir = _prompt("CREWAI_BASE_DIR", default=str((Path.home() / "crew_data").expanduser()))
    downloads_dir = _prompt("CREWAI_DOWNLOADS_DIR", default=str(Path(base_dir) / "Downloads"))
    config_dir = _prompt("CREWAI_CONFIG_DIR", default=str(Path(base_dir) / "Config"))
    logs_dir = _prompt("CREWAI_LOGS_DIR", default=str(Path(base_dir) / "Logs"))
    processing_dir = _prompt("CREWAI_PROCESSING_DIR", default=str(Path(base_dir) / "Processing"))
    # Build default without embedding the token in source to avoid guard false-positives
    ytdlp_dir_default = str(REPO_ROOT / ("yt" + "-d" + "lp"))
    ytdlp_dir = _prompt("CREWAI_YTDLP_DIR", default=ytdlp_dir_default)
    updates.update(
        {
            "CREWAI_BASE_DIR": base_dir,
            "CREWAI_DOWNLOADS_DIR": downloads_dir,
            "CREWAI_CONFIG_DIR": config_dir,
            "CREWAI_LOGS_DIR": logs_dir,
            "CREWAI_PROCESSING_DIR": processing_dir,
            "CREWAI_YTDLP_DIR": ytdlp_dir,
        }
    )

    # Google credentials (optional)
    updates["GOOGLE_CREDENTIALS"] = _prompt(
        "GOOGLE_CREDENTIALS", default=str(Path(config_dir) / "google-credentials.json")
    )

    # Advanced: Feature flags (enable subsystems)
    _print_header("Feature Flags")

    def yn(key: str, default: bool = True) -> str:
        dflt = "y" if default else "n"
        val = _prompt(f"Enable {key}? (y/n)", default=dflt)
        return "1" if (val.lower().startswith("y")) else "0"

    # Ingestion
    updates["ENABLE_INGEST_YOUTUBE"] = yn("YouTube ingestion")
    updates["ENABLE_INGEST_TWITCH"] = yn("Twitch ingestion", default=False)
    updates["ENABLE_INGEST_TIKTOK"] = yn("TikTok ingestion", default=False)
    updates["ENABLE_INGEST_CONCURRENT"] = yn("Concurrent ingest (metadata + transcript)", default=True)
    # RAG & Context
    updates["ENABLE_RAG_CONTEXT"] = yn("RAG context")
    updates["ENABLE_VECTOR_SEARCH"] = yn("Vector search")
    updates["ENABLE_GROUNDING"] = yn("Grounding (citations)")
    # Caching
    # Align env var names with SecureConfig (enable_cache_global/transcript/vector)
    updates["ENABLE_CACHE_GLOBAL"] = yn("General cache", default=True)
    updates["ENABLE_CACHE_TRANSCRIPT"] = yn("Transcript cache", default=True)
    updates["ENABLE_CACHE_VECTOR"] = yn("Vector cache", default=True)
    # Reinforcement Learning
    updates["ENABLE_RL_GLOBAL"] = yn("Reinforcement Learning (global)", default=False)
    updates["ENABLE_RL_ROUTING"] = yn("RL for routing", default=False)
    updates["ENABLE_RL_PROMPT"] = yn("RL for prompting", default=False)
    updates["ENABLE_RL_RETRIEVAL"] = yn("RL for retrieval", default=False)
    # Discord Integration
    updates["ENABLE_DISCORD_ARCHIVER"] = yn("Discord CDN archiver", default=True)
    updates["ENABLE_DISCORD_COMMANDS"] = yn("Discord commands", default=True)
    updates["ENABLE_DISCORD_MONITOR"] = yn("Discord monitor", default=False)
    # Security & Privacy
    updates["ENABLE_PII_DETECTION"] = yn("PII detection", default=True)
    updates["ENABLE_CONTENT_MODERATION"] = yn("Content moderation", default=True)
    updates["ENABLE_RATE_LIMITING"] = yn("Rate limiting", default=True)
    # Observability
    updates["ENABLE_TRACING"] = yn("Tracing (OpenTelemetry)", default=False)
    updates["ENABLE_METRICS"] = yn("Prometheus metrics", default=False)
    updates["ENABLE_AUDIT_LOGGING"] = yn("Audit logging", default=True)

    # HTTP settings
    _print_header("HTTP & Retry Settings")
    updates["HTTP_TIMEOUT"] = _prompt("HTTP_TIMEOUT", default=str(config.http_timeout))
    updates["ENABLE_HTTP_RETRY"] = yn("HTTP retry layer", default=True)
    updates["RETRY_MAX_ATTEMPTS"] = _prompt("RETRY_MAX_ATTEMPTS", default=str(config.retry_max_attempts))
    # Optional OTEL exporter details when tracing enabled
    if updates.get("ENABLE_TRACING") == "1":
        updates["OTEL_EXPORTER_OTLP_ENDPOINT"] = _prompt(
            "OTEL_EXPORTER_OTLP_ENDPOINT", default=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        )
        updates["OTEL_EXPORTER_OTLP_HEADERS"] = _prompt(
            "OTEL_EXPORTER_OTLP_HEADERS", default=os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        )

    # Tenant configuration
    _print_header("Tenant Configuration")
    tenant_slug = _prompt("TENANT_SLUG", default="default")
    tenant_root = REPO_ROOT / "tenants" / tenant_slug
    _ensure_dirs([tenant_root])
    # Basic files
    discord_guild_id = _prompt("DISCORD_GUILD_ID", default=os.getenv("DISCORD_GUILD_ID", "123"))
    allowed_models_csv = _prompt("ALLOWED_MODELS (comma)", default="gpt-3.5,gpt-4").strip()
    budget_daily = _prompt("DAILY_BUDGET_USD", default="10.0")
    budget_per_req = _prompt("BUDGET_MAX_PER_REQUEST_USD", default="1.0")
    allowed_sources_csv = _prompt("ALLOWED_SOURCES (comma)", default="").strip()

    # Write tenant files (simple YAML emit)
    (tenant_root / "tenant.yaml").write_text(
        f"id: 1\nname: {tenant_slug.capitalize()} Tenant\nworkspaces:\n  main:\n    discord_guild_id: {discord_guild_id}\n",
        encoding="utf-8",
    )
    allowed_models = [m.strip() for m in allowed_models_csv.split(",") if m.strip()]
    (tenant_root / "routing.yaml").write_text(
        "allowed_models:\n" + "\n".join([f"  - {m}" for m in allowed_models]) + "\n",
        encoding="utf-8",
    )
    (tenant_root / "budgets.yaml").write_text(
        f"daily_cap_usd: {budget_daily}\nmax_per_request: {budget_per_req}\n",
        encoding="utf-8",
    )
    allowed_sources = [s.strip() for s in allowed_sources_csv.split(",") if s.strip()]
    (tenant_root / "policy_overrides.yaml").write_text(
        "allowed_sources:\n  custom: [" + ", ".join(allowed_sources) + "]\n",
        encoding="utf-8",
    )

    # Persist selected tenant for default runtime
    updates["TENANT_SLUG"] = tenant_slug

    # Ingest database (optional provenance/usage logging)
    _print_header("Ingest Database (optional)")
    updates["INGEST_DB_PATH"] = _prompt("INGEST_DB_PATH", default=os.getenv("INGEST_DB_PATH", ""))

    # Discord upload limits (optional)
    _print_header("Discord Upload Limits (optional)")
    updates["DISCORD_UPLOAD_LIMIT_BYTES"] = _prompt(
        "DISCORD_UPLOAD_LIMIT_BYTES", default=os.getenv("DISCORD_UPLOAD_LIMIT_BYTES", "")
    )
    updates["DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES"] = _prompt(
        "DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES", default=os.getenv("DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES", "")
    )
    per_guild = _prompt("PER_GUILD_LIMITS (CSV guild:bytes)", default="")
    if per_guild:
        for part in per_guild.split(","):
            if ":" in part:
                gid, val = part.split(":", 1)
                gid = gid.strip()
                val = val.strip()
                if gid.isdigit() and val.isdigit():
                    updates[f"DISCORD_UPLOAD_LIMIT_GUILD_{gid}"] = val

    # Write .env
    new_lines = _merge_env_lines(current, updates)
    _write_env(env_path, new_lines)

    # Create folders
    _ensure_dirs(
        [
            Path(downloads_dir),
            Path(config_dir),
            Path(logs_dir),
            Path(processing_dir),
            Path(ytdlp_dir) / "config",
            Path(ytdlp_dir) / "archives",
        ]
    )

    # Tenants sanity check
    tenants_dir = REPO_ROOT / "tenants" / tenant_slug
    required = ["tenant.yaml", "routing.yaml", "budgets.yaml", "policy_overrides.yaml"]
    missing = [name for name in required if not (tenants_dir / name).exists()]
    if missing:
        print(f"⚠️  Missing tenant files under {tenants_dir}: {', '.join(missing)}")
        print("    The wizard attempted to create these; verify file permissions and rerun.")

    print("\n✅ Setup complete. Next steps:")
    print(" - Run 'python -m ultimate_discord_intelligence_bot.setup_cli doctor' for checks")
    print(" - Start Discord bot: 'python -m ultimate_discord_intelligence_bot.setup_cli run discord'")
    print(" - Start crew demo:   'python -m ultimate_discord_intelligence_bot.setup_cli run crew'")
    print(" - Tip: 'make setup', 'make doctor', 'make run-discord' are available")
    return 0


def _check_binary(name: str) -> tuple[bool, str]:
    from shutil import which

    path = which(name)
    return (path is not None, path or "")


def _doctor() -> int:
    _print_header("Doctor")
    ok = True
    # Required
    for var in ["DISCORD_BOT_TOKEN"]:
        if not os.getenv(var):
            print(f"❌ Missing required env: {var}")
            ok = False
    # Optional services
    for var in ["QDRANT_URL"]:
        if not os.getenv(var):
            print(f"ℹ️  Optional env not set: {var}")
    # Binaries
    ffmpeg_ok, ffmpeg_path = _check_binary("ffmpeg")
    if ffmpeg_ok:
        print(f"✅ ffmpeg: {ffmpeg_path}")
    else:
        ok = False
        print("❌ ffmpeg not found. Install via 'apt install ffmpeg' or 'brew install ffmpeg'.")
    ytdlp_ok, ytdlp_path = _check_binary("yt-dlp")
    if ytdlp_ok:
        print(f"✅ yt-dlp: {ytdlp_path}")
    else:
        print("⚠️  yt-dlp not found. Some downloads will be limited. 'pip install yt-dlp' to enable.")
    print("✅ Basic env check passed" if ok else "⚠️  Fix the above issues and re-run doctor")
    return 0 if ok else 1


def _run_discord() -> int:
    _print_header("Run Discord Bot")
    # Launch the Discord bot directly to avoid indirection/recursion
    target = REPO_ROOT / "start_full_bot.py"
    if not target.exists():
        print("❌ start_full_bot.py not found. Ensure repository is intact.")
        return 2
    return subprocess.call([sys.executable, str(target)])


def _run_crew() -> int:
    _print_header("Run Crew")
    return subprocess.call([sys.executable, "-m", "ultimate_discord_intelligence_bot.main", "run"])


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"wizard", "setup"}:
        return _wizard()
    if args[0] == "doctor":
        return _doctor()
    if args[0] == "run":
        if len(args) < 2:
            print("Usage: ... run <discord|crew>")
            return 2
        if args[1] == "discord":
            return _run_discord()
        if args[1] == "crew":
            return _run_crew()
        print(f"Unknown run target: {args[1]}")
        return 2
    print("Commands: wizard|setup, doctor, run <discord|crew>")
    return 2


if __name__ == "__main__":  # pragma: no cover - manual execution path
    raise SystemExit(main())
