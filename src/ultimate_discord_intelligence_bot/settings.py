import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]

# Base directories
BASE_DIR = Path(os.getenv("CREWAI_BASE_DIR", Path.home() / "crew_data")).expanduser()
DOWNLOADS_DIR = Path(os.getenv("CREWAI_DOWNLOADS_DIR", BASE_DIR / "Downloads")).expanduser()
CONFIG_DIR = Path(os.getenv("CREWAI_CONFIG_DIR", BASE_DIR / "Config")).expanduser()
LOGS_DIR = Path(os.getenv("CREWAI_LOGS_DIR", BASE_DIR / "Logs")).expanduser()
PROCESSING_DIR = Path(os.getenv("CREWAI_PROCESSING_DIR", BASE_DIR / "Processing")).expanduser()

# yt-dlp paths
YTDLP_DIR = Path(os.getenv("CREWAI_YTDLP_DIR", REPO_ROOT / "yt-dlp")).expanduser()
YTDLP_CONFIG = Path(
    os.getenv("CREWAI_YTDLP_CONFIG", YTDLP_DIR / "config" / "crewai-system.conf")
).expanduser()
YTDLP_ARCHIVE = Path(
    os.getenv("CREWAI_YTDLP_ARCHIVE", YTDLP_DIR / "archives" / "crewai_downloads.txt")
).expanduser()
TEMP_DIR = Path(os.getenv("CREWAI_TEMP_DIR", DOWNLOADS_DIR / "temp")).expanduser()

GOOGLE_CREDENTIALS = Path(
    os.getenv("GOOGLE_CREDENTIALS", CONFIG_DIR / "google-credentials.json")
).expanduser()
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")
DISCORD_PRIVATE_WEBHOOK = os.getenv("DISCORD_PRIVATE_WEBHOOK", "")
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Ensure directories exist
for path in [DOWNLOADS_DIR, CONFIG_DIR, LOGS_DIR, PROCESSING_DIR, TEMP_DIR, YTDLP_ARCHIVE.parent]:
    path.mkdir(parents=True, exist_ok=True)
