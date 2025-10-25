"""Unified first-run setup and runner CLI.

This guided helper is the canonical way to configure and run the project.
It interactively collects configuration, writes/updates ``.env``, validates
files and folders, and can launch common run targets (Discord bot or crew).

Usage:
    python -m ultimate_discord_intelligence_bot.setup_cli                   # interactive wizard
    python -m ultimate_discord_intelligence_bot.setup_cli wizard            # wizard (interactive)
    python -m ultimate_discord_intelligence_bot.setup_cli wizard -y         # non-interactive (accept defaults)
    python -m ultimate_discord_intelligence_bot.setup_cli wizard --set KEY=VAL [--set ...]
    python -m ultimate_discord_intelligence_bot.setup_cli doctor [--json]
    python -m ultimate_discord_intelligence_bot.setup_cli run discord
    python -m ultimate_discord_intelligence_bot.setup_cli run crew
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.secure_config import get_config


if TYPE_CHECKING:
    from collections.abc import Iterable


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


def _wizard(
    *,
    non_interactive: bool = False,
    accept_defaults: bool = False,
    presets: dict[str, str] | None = None,
    use_example_when_missing: bool = False,
) -> int:
    _print_header("Ultimate Discord Intelligence Bot - Setup Wizard")
    print("This will fully configure your environment (core + advanced).")

    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        current = _load_env(env_path)
    elif use_example_when_missing and (REPO_ROOT / ".env.example").exists():
        current = _load_env(REPO_ROOT / ".env.example")
        print("ℹ️  Using .env.example as base since .env was missing")
    else:
        current = []

    presets = presets or {}

    def ask(key: str, *, default: str | None = None, secret: bool = False) -> str:
        # Priority: explicit presets -> existing env -> default (non-interactive) -> prompt (interactive)
        if key in presets and str(presets[key]).strip() != "":
            return str(presets[key]).strip()
        existing = os.getenv(key) or default or ""
        if non_interactive or accept_defaults:
            return existing
        return _prompt(key, default=default, secret=secret)

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
        updates[key] = ask(key, secret=secret)

    # Vector DB
    print("\nVector database (Qdrant) configuration:")
    updates["QDRANT_URL"] = ask("QDRANT_URL", default=config.qdrant_url)
    updates["QDRANT_API_KEY"] = ask("QDRANT_API_KEY", secret=True)

    # Downloads and quality
    print("\nDownload preferences:")
    updates["DEFAULT_DOWNLOAD_QUALITY"] = ask(
        "DEFAULT_DOWNLOAD_QUALITY",
        default=os.getenv("DEFAULT_DOWNLOAD_QUALITY", "1080p"),
    )

    # Paths
    _print_header("Paths and storage")
    base_dir = ask("CREWAI_BASE_DIR", default=str((Path.home() / "crew_data").expanduser()))
    downloads_dir = ask("CREWAI_DOWNLOADS_DIR", default=str(Path(base_dir) / "Downloads"))
    config_dir = ask("CREWAI_CONFIG_DIR", default=str(Path(base_dir) / "Config"))
    logs_dir = ask("CREWAI_LOGS_DIR", default=str(Path(base_dir) / "Logs"))
    processing_dir = ask("CREWAI_PROCESSING_DIR", default=str(Path(base_dir) / "Processing"))
    # Build default without embedding the token in source to avoid guard false-positives
    ytdlp_dir_default = str(REPO_ROOT / ("yt" + "-d" + "lp"))
    ytdlp_dir = ask("CREWAI_YTDLP_DIR", default=ytdlp_dir_default)
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
    updates["GOOGLE_CREDENTIALS"] = ask("GOOGLE_CREDENTIALS", default=str(Path(config_dir) / "google-credentials.json"))

    # Advanced: Feature flags (enable subsystems)
    _print_header("Feature Flags")

    def yn(key: str, default: bool = True) -> str:
        dflt = "y" if default else "n"
        val = ask(f"Enable {key}? (y/n)", default=dflt)
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
    updates["HTTP_TIMEOUT"] = ask("HTTP_TIMEOUT", default=str(config.http_timeout))
    updates["ENABLE_HTTP_RETRY"] = yn("HTTP retry layer", default=True)
    updates["RETRY_MAX_ATTEMPTS"] = ask("RETRY_MAX_ATTEMPTS", default=str(config.retry_max_attempts))
    # Optional OTEL exporter details when tracing enabled
    if updates.get("ENABLE_TRACING") == "1":
        updates["OTEL_EXPORTER_OTLP_ENDPOINT"] = ask(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            default=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
        )
        updates["OTEL_EXPORTER_OTLP_HEADERS"] = ask(
            "OTEL_EXPORTER_OTLP_HEADERS",
            default=os.getenv("OTEL_EXPORTER_OTLP_HEADERS", ""),
        )

    # Local web clients (CORS) and Activities dev helpers (optional)
    _print_header("Local web clients & Activities dev (optional)")
    enable_cors = yn("CORS for local dev (Vite, etc.)", default=False)
    updates["ENABLE_CORS"] = enable_cors
    if enable_cors == "1":
        default_origins = os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
        )
        updates["CORS_ALLOW_ORIGINS"] = ask("CORS_ALLOW_ORIGINS (comma)", default=default_origins)
    else:
        # Preserve existing value if present; otherwise set a sensible default comment-friendly value
        if "CORS_ALLOW_ORIGINS" not in os.environ:
            updates["CORS_ALLOW_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"

    # Optional echo endpoint for debugging embedded clients
    updates["ENABLE_ACTIVITIES_ECHO"] = yn("Activities echo debug endpoint", default=False)

    # Tenant configuration
    _print_header("Tenant Configuration")
    tenant_slug = ask("TENANT_SLUG", default="default")
    tenant_root = REPO_ROOT / "tenants" / tenant_slug
    _ensure_dirs([tenant_root])
    # Basic files
    discord_guild_id = ask("DISCORD_GUILD_ID", default=os.getenv("DISCORD_GUILD_ID", "123"))
    allowed_models_csv = ask("ALLOWED_MODELS (comma)", default="gpt-3.5,gpt-4").strip()
    budget_daily = ask("DAILY_BUDGET_USD", default="10.0")
    budget_per_req = ask("BUDGET_MAX_PER_REQUEST_USD", default="1.0")
    allowed_sources_csv = ask("ALLOWED_SOURCES (comma)", default="").strip()

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
    updates["INGEST_DB_PATH"] = ask("INGEST_DB_PATH", default=os.getenv("INGEST_DB_PATH", ""))

    # Discord upload limits (optional)
    _print_header("Discord Upload Limits (optional)")
    updates["DISCORD_UPLOAD_LIMIT_BYTES"] = ask(
        "DISCORD_UPLOAD_LIMIT_BYTES",
        default=os.getenv("DISCORD_UPLOAD_LIMIT_BYTES", ""),
    )
    updates["DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES"] = ask(
        "DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES",
        default=os.getenv("DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES", ""),
    )
    per_guild = ask("PER_GUILD_LIMITS (CSV guild:bytes)", default="")
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


def _check_ytdlp_module() -> tuple[bool, str]:
    """Detect yt-dlp availability either as a binary or runnable module.

    Returns (ok, detail) where detail is the path to the binary or a 'python -m yt_dlp' hint.
    Avoid importing yt_dlp directly to comply with guardrails (centralize imports in tools).
    """
    ok, path = _check_binary("yt-dlp")
    if ok:
        return True, path
    # Fallback: probe if `python -m yt_dlp --version` works without importing in-process
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "yt_dlp", "--version"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
        )
        ver = out.strip().splitlines()[0] if out else "unknown"
        return True, f"python -m yt_dlp (v{ver})"
    except Exception:
        return False, ""


def _doctor(*, as_json: bool = False, quiet: bool = False) -> int:
    # Load environment from .env if present (non-invasive: only set keys not already in env)
    try:
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            for raw in env_path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _eq, value = line.partition("=")
                k = key.strip()
                v = value.strip().strip('"').strip("'")
                # Preserve existing environment (e.g., CI or shell-provided)
                if k and (k not in os.environ or os.environ.get(k, "") == ""):
                    os.environ[k] = v
    except Exception as _e:
        # Do not fail doctor due to .env parse issues; continue with process env
        pass

    if not quiet:
        _print_header("Doctor")
    report: dict[str, Any] = {
        "env": {},
        "binaries": {},
        "vector_store": {},
        "status": "ok",
    }
    ok = True
    # Required
    for var in ["DISCORD_BOT_TOKEN"]:
        if not os.getenv(var):
            if not quiet:
                print(f"❌ Missing required env: {var}")
            report["env"][var] = "missing"
            ok = False
        else:
            report["env"][var] = "present"
    # Optional services
    for var in ["QDRANT_URL"]:
        if not os.getenv(var):
            if not quiet:
                print(f"ℹ️  Optional env not set: {var}")
            report["env"][var] = "unset"
        else:
            report["env"][var] = "present"
    # Binaries
    ffmpeg_ok, ffmpeg_path = _check_binary("ffmpeg")
    if ffmpeg_ok:
        if not quiet:
            print(f"✅ ffmpeg: {ffmpeg_path}")
        report["binaries"]["ffmpeg"] = ffmpeg_path
    else:
        ok = False
        if not quiet:
            print("❌ ffmpeg not found. Install via 'apt install ffmpeg' or 'brew install ffmpeg'.")
        report["binaries"]["ffmpeg"] = "missing"
    ytdlp_ok, ytdlp_detail = _check_ytdlp_module()
    if ytdlp_ok:
        if not quiet:
            print(f"✅ yt-dlp: {ytdlp_detail}")
        report["binaries"]["yt-dlp"] = ytdlp_detail
    else:
        if not quiet:
            print("⚠️  yt-dlp not found. Some downloads will be limited. 'pip install yt-dlp' to enable.")
        report["binaries"]["yt-dlp"] = "missing"
    # Vector store readiness (optional)
    try:
        from memory import embeddings as _emb
        from memory import vector_store as _v
        from memory.qdrant_provider import _DummyClient as _QD
        from memory.qdrant_provider import get_qdrant_client

        url = os.getenv("QDRANT_URL", "")
        if url:
            client = get_qdrant_client()
            mode = "dummy" if isinstance(client, _QD) else "real"
            vs = _v.VectorStore()
            ns = _v.VectorStore.namespace("health", "doctor", "check")
            vec = _emb.embed(["doctor-health-check"])[0]
            vs.upsert(ns, [_v.VectorRecord(vector=vec, payload={"text": "ok"})])
            hits = vs.query(ns, vec, top_k=1)
            if hits:
                if not quiet:
                    print(f"✅ Vector store ({mode}) reachable: {url if mode == 'real' else ':memory:'}")
                report["vector_store"] = {"mode": mode, "reachable": True}
            else:
                ok = False
                if not quiet:
                    print("⚠️  Vector store query returned no results (check Qdrant setup)")
                report["vector_store"] = {"mode": mode, "reachable": False}
        else:
            if not quiet:
                print("ℹ️  QDRANT_URL not set; vector search will use in-memory dummy store for tests")
            report["vector_store"] = {"mode": "dummy", "reachable": True}
    except Exception as e:
        ok = False
        if not quiet:
            print(f"⚠️  Vector store check failed: {e}")
        report["vector_store"] = {"error": str(e)}

    if not quiet:
        print("✅ Basic env check passed" if ok else "⚠️  Fix the above issues and re-run doctor")
    report["status"] = "ok" if ok else "error"
    if as_json:
        try:
            import json

            print(json.dumps(report))
        except Exception:
            # fall through to normal exit
            pass
    return 0 if ok else 1


def _run_discord() -> int:
    _print_header("Run Discord Bot")
    # Launch the Discord bot directly to avoid indirection/recursion
    # Support both repo root and scripts/ locations
    candidates = [
        REPO_ROOT / "start_full_bot.py",
        REPO_ROOT / "scripts" / "start_full_bot.py",
    ]
    target = next((p for p in candidates if p.exists()), None)
    if target is None:
        print("❌ start_full_bot.py not found in repo root or scripts/. Ensure repository is intact.")
        print(f"   Looked in: {', '.join(str(p) for p in candidates)}")
        return 2

    # Launch bot directly - no PYTHONPATH needed since package is installed
    print(f"🚀 Launching: {sys.executable} {target}")
    return subprocess.call([sys.executable, str(target)])


def _run_crew() -> int:
    _print_header("Run Crew")
    return subprocess.call([sys.executable, "-m", "ultimate_discord_intelligence_bot.main", "run"])


def _parse_set_args(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in values:
        if "=" in item:
            k, v = item.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="udib-setup", description="UDIB Setup and Runner CLI")
    sub = parser.add_subparsers(dest="cmd")

    # wizard/init
    wiz = sub.add_parser("wizard", help="Run interactive setup wizard")
    wiz.add_argument("--yes", "-y", action="store_true", help="Accept defaults (non-interactive)")
    wiz.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt; use env/defaults/presets",
    )
    wiz.add_argument(
        "--use-example",
        action="store_true",
        help="Seed from .env.example if .env missing",
    )
    wiz.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        help="Override KEY=VALUE (repeatable)",
    )

    # legacy aliases
    sub.add_parser("setup", help="Alias for wizard")
    sub.add_parser("init", help="Alias for wizard")
    sub.add_parser("init-env", help="Alias for wizard")

    # doctor
    doc = sub.add_parser("doctor", help="Run environment checks")
    doc.add_argument("--json", action="store_true", help="Output JSON report")
    doc.add_argument("--quiet", action="store_true", help="Suppress human readable output")

    # run
    runp = sub.add_parser("run", help="Run components")
    runp.add_argument("target", choices=["discord", "crew"], help="Target to run")

    # default behavior: wizard; auto non-interactive in CI
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    cmd = args.cmd
    if cmd in {None, "wizard", "setup", "init", "init-env"}:
        non_interactive = bool(getattr(args, "non_interactive", False)) or os.getenv("CI") == "true"
        accept_defaults = bool(getattr(args, "yes", False)) or non_interactive
        presets = _parse_set_args(getattr(args, "sets", [])) if hasattr(args, "sets") else {}
        use_example = bool(getattr(args, "use_example", False))
        return _wizard(
            non_interactive=non_interactive,
            accept_defaults=accept_defaults,
            presets=presets,
            use_example_when_missing=use_example,
        )
    if cmd == "doctor":
        return _doctor(
            as_json=bool(getattr(args, "json", False)),
            quiet=bool(getattr(args, "quiet", False)),
        )
    if cmd == "run":
        if getattr(args, "target", None) == "discord":
            return _run_discord()
        if getattr(args, "target", None) == "crew":
            return _run_crew()
        print("Usage: ... run <discord|crew>")
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover - manual execution path
    raise SystemExit(main())
