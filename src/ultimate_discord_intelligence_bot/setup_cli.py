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
import contextlib
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Iterable

# Critical: Ensure platform proxy is set up BEFORE any imports that reference platform.core
# This must happen before sitecustomize attempt because module execution order matters
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

# Now run the bootstrap to augment stdlib platform module
try:
    from ultimate_discord_intelligence_bot.core.bootstrap import ensure_platform_proxy

    ensure_platform_proxy()
except Exception:
    pass  # Fail silently - defensive for edge cases

# Ensure repo-local sitecustomize is loaded to proxy stdlib 'platform' to our package
with contextlib.suppress(Exception):  # pragma: no cover - defensive import for CLI execution context
    import sitecustomize as _sitecustomize  # noqa: F401


# More robust REPO_ROOT detection that works when run as module
def _find_repo_root() -> Path:
    """Find repository root by walking up from current file/module location."""
    # When run as module, __file__ might not be reliable, so try multiple approaches
    candidates = []

    # Try __file__ approach first
    if __file__:
        current = Path(__file__).resolve()
        for _ in range(5):  # Walk up max 5 levels
            if (current / ".git").exists() or (current / "pyproject.toml").exists():
                candidates.append(current)
            current = current.parent

    # Try current working directory
    cwd = Path.cwd()
    if (cwd / ".git").exists() or (cwd / "pyproject.toml").exists():
        candidates.append(cwd)

    # Try walking up from cwd
    current = cwd
    for _ in range(3):
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            candidates.append(current)
        current = current.parent

    # Try environment variable if set
    env_repo_root = os.getenv("REPO_ROOT")
    if env_repo_root:
        env_path = Path(env_repo_root).resolve()
        if (env_path / ".git").exists() or (env_path / "pyproject.toml").exists():
            candidates.append(env_path)

    # Try common repo locations relative to src/
    if __file__ and "src" in str(Path(__file__)):
        # If we're in src/, go up one level
        src_root = Path(__file__).resolve().parent.parent.parent
        if (src_root / ".git").exists() or (src_root / "pyproject.toml").exists():
            candidates.append(src_root)

    # Try hardcoded fallback for this specific repo
    hardcoded_root = Path("/home/crew")
    if (hardcoded_root / ".git").exists() or (hardcoded_root / "pyproject.toml").exists():
        candidates.append(hardcoded_root)

    # Return the first valid candidate, preferring ones with .git
    for candidate in candidates:
        if (candidate / ".git").exists():
            return candidate
    for candidate in candidates:
        if (candidate / "pyproject.toml").exists():
            return candidate

    # Fallback to cwd if nothing found
    return cwd


REPO_ROOT = _find_repo_root()


def _print_header(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{title}\n{bar}")


def _prompt(key: str, default: str | None = None, secret: bool = False) -> str:
    existing = os.getenv(key) or default or ""
    suffix = f" [default: {existing}]" if existing else ""
    prompt = f"{key}{(' (secret)' if secret else '')}:{suffix} > "
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
        print("i  Using .env.example as base since .env was missing")
    else:
        current = []
    presets = presets or {}

    def ask(key: str, *, default: str | None = None, secret: bool = False) -> str:
        if key in presets and str(presets[key]).strip() != "":
            return str(presets[key]).strip()
        existing = os.getenv(key) or default or ""
        if non_interactive or accept_defaults:
            return existing
        return _prompt(key, default=default, secret=secret)

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
    print("\nVector database (Qdrant) configuration:")
    qdrant_default = os.getenv("QDRANT_URL", "")
    updates["QDRANT_URL"] = ask("QDRANT_URL", default=qdrant_default)
    updates["QDRANT_API_KEY"] = ask("QDRANT_API_KEY", secret=True)
    print("\nDownload preferences:")
    updates["DEFAULT_DOWNLOAD_QUALITY"] = ask(
        "DEFAULT_DOWNLOAD_QUALITY", default=os.getenv("DEFAULT_DOWNLOAD_QUALITY", "1080p")
    )
    _print_header("Paths and storage")
    base_dir = ask("CREWAI_BASE_DIR", default=str((Path.home() / "crew_data").expanduser()))
    downloads_dir = ask("CREWAI_DOWNLOADS_DIR", default=str(Path(base_dir) / "Downloads"))
    config_dir = ask("CREWAI_CONFIG_DIR", default=str(Path(base_dir) / "Config"))
    logs_dir = ask("CREWAI_LOGS_DIR", default=str(Path(base_dir) / "Logs"))
    processing_dir = ask("CREWAI_PROCESSING_DIR", default=str(Path(base_dir) / "Processing"))
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
    updates["GOOGLE_CREDENTIALS"] = ask("GOOGLE_CREDENTIALS", default=str(Path(config_dir) / "google-credentials.json"))
    _print_header("Feature Flags")

    def yn(key: str, default: bool = True) -> str:
        dflt = "y" if default else "n"
        val = ask(f"Enable {key}? (y/n)", default=dflt)
        return "1" if val.lower().startswith("y") else "0"

    updates["ENABLE_INGEST_YOUTUBE"] = yn("YouTube ingestion")
    updates["ENABLE_INGEST_TWITCH"] = yn("Twitch ingestion", default=False)
    updates["ENABLE_INGEST_TIKTOK"] = yn("TikTok ingestion", default=False)
    updates["ENABLE_INGEST_CONCURRENT"] = yn("Concurrent ingest (metadata + transcript)", default=True)
    updates["ENABLE_RAG_CONTEXT"] = yn("RAG context")
    updates["ENABLE_VECTOR_SEARCH"] = yn("Vector search")
    updates["ENABLE_GROUNDING"] = yn("Grounding (citations)")
    updates["ENABLE_CACHE_GLOBAL"] = yn("General cache", default=True)
    updates["ENABLE_CACHE_TRANSCRIPT"] = yn("Transcript cache", default=True)
    updates["ENABLE_CACHE_VECTOR"] = yn("Vector cache", default=True)
    updates["ENABLE_RL_GLOBAL"] = yn("Reinforcement Learning (global)", default=False)
    updates["ENABLE_RL_ROUTING"] = yn("RL for routing", default=False)
    updates["ENABLE_RL_PROMPT"] = yn("RL for prompting", default=False)
    updates["ENABLE_RL_RETRIEVAL"] = yn("RL for retrieval", default=False)
    updates["ENABLE_DISCORD_ARCHIVER"] = yn("Discord CDN archiver", default=True)
    updates["ENABLE_DISCORD_COMMANDS"] = yn("Discord commands", default=True)
    updates["ENABLE_DISCORD_MONITOR"] = yn("Discord monitor", default=False)
    updates["ENABLE_PII_DETECTION"] = yn("PII detection", default=True)
    updates["ENABLE_CONTENT_MODERATION"] = yn("Content moderation", default=True)
    updates["ENABLE_RATE_LIMITING"] = yn("Rate limiting", default=True)
    updates["ENABLE_TRACING"] = yn("Tracing (OpenTelemetry)", default=False)
    updates["ENABLE_METRICS"] = yn("Prometheus metrics", default=False)
    updates["ENABLE_AUDIT_LOGGING"] = yn("Audit logging", default=True)
    _print_header("HTTP & Retry Settings")
    # Use environment or sane defaults to avoid importing heavy config modules here
    updates["HTTP_TIMEOUT"] = ask("HTTP_TIMEOUT", default=os.getenv("HTTP_TIMEOUT", "15"))
    updates["ENABLE_HTTP_RETRY"] = yn("HTTP retry layer", default=True)
    updates["RETRY_MAX_ATTEMPTS"] = ask("RETRY_MAX_ATTEMPTS", default=os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    if updates.get("ENABLE_TRACING") == "1":
        updates["OTEL_EXPORTER_OTLP_ENDPOINT"] = ask(
            "OTEL_EXPORTER_OTLP_ENDPOINT", default=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        )
        updates["OTEL_EXPORTER_OTLP_HEADERS"] = ask(
            "OTEL_EXPORTER_OTLP_HEADERS", default=os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
        )
    _print_header("Local web clients & Activities dev (optional)")
    enable_cors = yn("CORS for local dev (Vite, etc.)", default=False)
    updates["ENABLE_CORS"] = enable_cors
    if enable_cors == "1":
        default_origins = os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
        )
        updates["CORS_ALLOW_ORIGINS"] = ask("CORS_ALLOW_ORIGINS (comma)", default=default_origins)
    elif "CORS_ALLOW_ORIGINS" not in os.environ:
        updates["CORS_ALLOW_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173"
    updates["ENABLE_ACTIVITIES_ECHO"] = yn("Activities echo debug endpoint", default=False)
    _print_header("Tenant Configuration")
    tenant_slug = ask("TENANT_SLUG", default="default")
    tenant_root = REPO_ROOT / "tenants" / tenant_slug
    _ensure_dirs([tenant_root])
    discord_guild_id = ask("DISCORD_GUILD_ID", default=os.getenv("DISCORD_GUILD_ID", "123"))
    allowed_models_csv = ask("ALLOWED_MODELS (comma)", default="gpt-3.5,gpt-4").strip()
    budget_daily = ask("DAILY_BUDGET_USD", default="10.0")
    budget_per_req = ask("BUDGET_MAX_PER_REQUEST_USD", default="1.0")
    allowed_sources_csv = ask("ALLOWED_SOURCES (comma)", default="").strip()
    (tenant_root / "tenant.yaml").write_text(
        f"id: 1\nname: {tenant_slug.capitalize()} Tenant\nworkspaces:\n  main:\n    discord_guild_id: {discord_guild_id}\n",
        encoding="utf-8",
    )
    allowed_models = [m.strip() for m in allowed_models_csv.split(",") if m.strip()]
    (tenant_root / "routing.yaml").write_text(
        "allowed_models:\n" + "\n".join([f"  - {m}" for m in allowed_models]) + "\n", encoding="utf-8"
    )
    (tenant_root / "budgets.yaml").write_text(
        f"daily_cap_usd: {budget_daily}\nmax_per_request: {budget_per_req}\n", encoding="utf-8"
    )
    allowed_sources = [s.strip() for s in allowed_sources_csv.split(",") if s.strip()]
    (tenant_root / "policy_overrides.yaml").write_text(
        "allowed_sources:\n  custom: [" + ", ".join(allowed_sources) + "]\n", encoding="utf-8"
    )
    updates["TENANT_SLUG"] = tenant_slug
    _print_header("Ingest Database (optional)")
    updates["INGEST_DB_PATH"] = ask("INGEST_DB_PATH", default=os.getenv("INGEST_DB_PATH", ""))
    _print_header("Discord Upload Limits (optional)")
    updates["DISCORD_UPLOAD_LIMIT_BYTES"] = ask(
        "DISCORD_UPLOAD_LIMIT_BYTES", default=os.getenv("DISCORD_UPLOAD_LIMIT_BYTES", "")
    )
    updates["DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES"] = ask(
        "DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES", default=os.getenv("DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES", "")
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
    new_lines = _merge_env_lines(current, updates)
    _write_env(env_path, new_lines)
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
        return (True, path)
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "yt_dlp", "--version"], stderr=subprocess.STDOUT, text=True, timeout=5
        )
        ver = out.strip().splitlines()[0] if out else "unknown"
        return (True, f"python -m yt_dlp (v{ver})")
    except Exception:
        return (False, "")


def _doctor(*, as_json: bool = False, quiet: bool = False) -> int:
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
                if k and (k not in os.environ or os.environ.get(k, "") == ""):
                    os.environ[k] = v
    except Exception as _e:
        pass
    if not quiet:
        _print_header("Doctor")
    report: dict[str, Any] = {"env": {}, "binaries": {}, "vector_store": {}, "status": "ok"}
    ok = True
    for var in ["DISCORD_BOT_TOKEN"]:
        if not os.getenv(var):
            if not quiet:
                print(f"❌ Missing required env: {var}")
            report["env"][var] = "missing"
            ok = False
        else:
            report["env"][var] = "present"
    for var in ["QDRANT_URL"]:
        if not os.getenv(var):
            if not quiet:
                print(f"i  Optional env not set: {var}")
            report["env"][var] = "unset"
        else:
            report["env"][var] = "present"
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
    try:
        from domains.memory import embeddings as _emb
        from domains.memory import vector_store as _v
        from domains.memory.vector.qdrant.domains.qdrant_provider import _DummyClient as _QD
        from domains.memory.vector.qdrant.domains.qdrant_provider import get_qdrant_client

        url = os.getenv("QDRANT_URL", "")
        if url:
            client = get_qdrant_client()
            mode = "dummy" if isinstance(client, _QD) else "real"
            vs = _v.VectorStore()
            ns = _v.VectorStore.namespace("health", "doctor", "check")
            content = "doctor-health-check"
            vec = _emb.embed([content])[0]
            rec = _v.VectorRecord(content=content, metadata={"text": "ok"}, vector=vec)
            vs.upsert(ns, [rec])
            hits = vs.query(ns, vec, top_k=1)
            if hits:
                if not quiet:
                    print(f"✅ Vector store ({mode}) reachable: {(url if mode == 'real' else ':memory:')}")
                report["vector_store"] = {"mode": mode, "reachable": True}
            else:
                ok = False
                if not quiet:
                    print("⚠️  Vector store query returned no results (check Qdrant setup)")
                report["vector_store"] = {"mode": mode, "reachable": False}
        else:
            if not quiet:
                print("i  QDRANT_URL not set; vector search will use in-memory dummy store for tests")
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
            pass
    return 0 if ok else 1


def _run_discord() -> int:
    _print_header("Run Discord Bot")
    # Hardcoded path for reliability
    target = Path("/home/crew/scripts/start_full_bot.py")
    if not target.exists():
        print(f"❌ start_full_bot.py not found at {target}")
        return 2
    print(f"🚀 Launching: {sys.executable} {target}")
    # Don't add src to PYTHONPATH - start_full_bot.py handles path setup internally
    # to avoid src/discord/ shadowing the real discord.py package
    return subprocess.call([sys.executable, str(target)])


def _run_crew() -> int:
    _print_header("Run Crew")
    return subprocess.call([sys.executable, "-m", "app.main", "run"])


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
    wiz = sub.add_parser("wizard", help="Run interactive setup wizard")
    wiz.add_argument("--yes", "-y", action="store_true", help="Accept defaults (non-interactive)")
    wiz.add_argument("--non-interactive", action="store_true", help="Do not prompt; use env/defaults/presets")
    wiz.add_argument("--use-example", action="store_true", help="Seed from .env.example if .env missing")
    wiz.add_argument("--set", dest="sets", action="append", default=[], help="Override KEY=VALUE (repeatable)")
    sub.add_parser("setup", help="Alias for wizard")
    sub.add_parser("init", help="Alias for wizard")
    sub.add_parser("init-env", help="Alias for wizard")
    doc = sub.add_parser("doctor", help="Run environment checks")
    doc.add_argument("--json", action="store_true", help="Output JSON report")
    doc.add_argument("--quiet", action="store_true", help="Suppress human readable output")
    runp = sub.add_parser("run", help="Run components")
    runp.add_argument("target", choices=["discord", "crew"], help="Target to run")
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
        return _doctor(as_json=bool(getattr(args, "json", False)), quiet=bool(getattr(args, "quiet", False)))
    if cmd == "run":
        if getattr(args, "target", None) == "discord":
            return _run_discord()
        if getattr(args, "target", None) == "crew":
            return _run_crew()
        print("Usage: ... run <discord|crew>")
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
