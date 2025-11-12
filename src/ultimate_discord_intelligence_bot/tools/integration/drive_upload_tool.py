import logging
import os
from platform.config.configuration import get_config
from typing import Any, ClassVar

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from .._base import BaseTool


try:
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError, ResumableUploadError
    from googleapiclient.http import MediaFileUpload

    _GOOGLE_LIBS_AVAILABLE = True
except Exception:
    service_account = build = MediaFileUpload = None
    OAuthCredentials = None
    GoogleRequest = None

    class HttpError(Exception):
        status_code: int | None = None

    class ResumableUploadError(Exception):
        resp: Any | None = None
        error: Any | None = None

    _GOOGLE_LIBS_AVAILABLE = False
import contextlib

from app.config.settings import get_settings


class DriveUploadTool(BaseTool[StepResult]):
    name: str = "Google Drive Upload Tool"
    description: str = "Upload files to Google Drive and create shareable links"
    model_config: ClassVar[dict[str, Any]] = {"extra": "allow"}

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()
        self.service = self._setup_service()
        self.base_folder_id: str | None
        self.subfolders: dict[str, str]
        if self.service:
            try:
                self.base_folder_id, self.subfolders = self._setup_folder_structure()
            except Exception as exc:
                logging.warning("Drive folder setup failed; disabling uploads for this run: %s", exc)
                self.base_folder_id = None
                self.subfolders = {}
        else:
            self.base_folder_id = None
            self.subfolders = {}

    def _setup_service(self) -> Any:
        """Initialise the Drive service using either user OAuth or service account credentials.

        Precedence:
        - If PREFER_GOOGLE_OAUTH is true (1/true/yes) AND a token file exists, use OAuth.
        - Otherwise attempt service account credentials (GOOGLE_CREDENTIALS).
        """
        config = get_config()
        if config.disable_google_drive:
            print("i  Google Drive disabled via DISABLE_GOOGLE_DRIVE=1")
            return None
        if not _GOOGLE_LIBS_AVAILABLE:
            print("⚠️  Google client libraries not available - Drive uploads disabled")
            return None
        with contextlib.suppress(Exception):
            logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
        prefer_oauth = str(os.getenv("PREFER_GOOGLE_OAUTH", "0")).strip().lower() in {"1", "true", "yes", "on"}
        if prefer_oauth and OAuthCredentials is not None and (build is not None):
            try:
                import json

                settings = get_settings()
                token_path = os.getenv("GOOGLE_OAUTH_TOKEN_PATH", str(settings.config_dir / "google-oauth-token.json"))
                if os.path.exists(token_path):
                    with open(token_path, encoding="utf-8") as f:
                        token_data = json.load(f)
                    if "access_token" in token_data and "token" not in token_data:
                        token_data["token"] = token_data["access_token"]
                    credentials = OAuthCredentials.from_authorized_user_info(
                        token_data, scopes=["https://www.googleapis.com/auth/drive"]
                    )
                    try:
                        if (
                            credentials
                            and credentials.expired
                            and getattr(credentials, "refresh_token", None)
                            and GoogleRequest
                        ):
                            credentials.refresh(GoogleRequest())
                    except Exception as exc:
                        logging.warning("OAuth token refresh failed (continuing): %s", exc)
                    print("🔐 Using Google OAuth user credentials for Drive uploads")
                    try:
                        svc = build("drive", "v3", credentials=credentials, cache_discovery=False)
                        return svc
                    except Exception as exc:
                        logging.warning("Failed to build Drive client with OAuth creds: %s", exc)
                else:
                    print("i  PREFER_GOOGLE_OAUTH set but no token file found; falling back to service account")
            except Exception as exc:
                logging.warning("Google OAuth credentials unavailable: %s", exc)
        settings = get_settings()
        credentials_path = str(settings.config_dir / "google-credentials.json")
        if service_account is None or build is None:
            return None
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
            )
        except Exception as exc:
            settings = get_settings()
            default_path = str((settings.config_dir / "google-credentials.json").expanduser())
            if os.getenv("GOOGLE_CREDENTIALS") and credentials_path != default_path:
                logging.warning("Google credentials unavailable at %s: %s", credentials_path, exc)
                print("⚠️  Google Drive credentials invalid - Drive uploads disabled")
            else:
                print("i  Google Drive not configured (no credentials provided)")
            return None
        try:
            return build("drive", "v3", credentials=credentials, cache_discovery=False)
        except Exception as exc:
            logging.warning("Failed to build Drive client with service account creds: %s", exc)
            return None

    def _find_folder(self, name: str, parent_id: str | None = None) -> str | None:
        """Return folder id if a folder with ``name`` exists under ``parent_id``."""
        query = [
            "name = '{}'".format(name.replace("'", "'")),
            "mimeType = 'application/vnd.google-apps.folder'",
            "trashed = false",
        ]
        if parent_id:
            query.append(f"'{parent_id}' in parents")
        result = self.service.files().list(q=" and ".join(query), fields="files(id)").execute()
        files = result.get("files", [])
        return files[0]["id"] if files else None

    def _get_or_create_folder(self, name: str, parent_id: str | None = None) -> str:
        folder_id = self._find_folder(name, parent_id)
        if folder_id:
            return folder_id
        file_metadata: dict[str, Any] = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            file_metadata["parents"] = [parent_id]
        file = self.service.files().create(body=file_metadata, fields="id").execute()
        return str(file.get("id"))

    def _setup_folder_structure(self) -> tuple[str, dict[str, str]]:
        """Create or reuse an organised folder structure on Drive."""
        base_folder = self._get_or_create_folder("CrewAI_Content")
        subfolders = {
            "youtube": self._get_or_create_folder("YouTube_Videos", base_folder),
            "instagram": self._get_or_create_folder("Instagram_Content", base_folder),
            "processed": self._get_or_create_folder("Processed_Content", base_folder),
        }
        return (base_folder, subfolders)

    def _run(self, file_path: str, platform: str) -> StepResult:
        """Upload video file with Discord-compatible sharing setup"""
        if not self.service or not self.base_folder_id:
            self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload", "outcome": "skipped"}).inc()
            return StepResult.skip(
                message="Google Drive uploads disabled (no credentials configured)",
                file_path=file_path,
                platform=platform,
            )
        try:
            folder_id = self.subfolders.get(platform, self.base_folder_id)
            file_metadata = {"name": os.path.basename(file_path), "parents": [folder_id]}
            if MediaFileUpload is None:
                raise RuntimeError("google client library unavailable (MediaFileUpload missing)")
            media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True, chunksize=256 * 1024 * 1024)
            request = self.service.files().create(
                body=file_metadata, media_body=media, fields="id,name,size,webViewLink"
            )
            response: dict[str, Any] | None = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logging.info("Upload progress: %s%%", int(status.progress() * 100))
            file_id = response.get("id")
            if not file_id:
                raise RuntimeError("Upload succeeded but no file ID returned")
            self._make_public(file_id)
            links = self._generate_discord_links(file_id)
            self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload", "outcome": "success"}).inc()
            return StepResult.ok(
                data={
                    "file_id": file_id,
                    "file_name": response.get("name"),
                    "file_size": response.get("size"),
                    "links": links,
                }
            )
        except Exception as e:
            try:
                is_quota = False
                status_code: int | None = None
                reason: str | None = None
                if isinstance(e, ResumableUploadError):
                    resp = getattr(e, "resp", None)
                    status_code = getattr(resp, "status", None)
                    text = str(e)
                    if "storageQuotaExceeded" in text or "Service Accounts do not have storage quota" in text:
                        is_quota = True
                        reason = "storageQuotaExceeded"
                elif isinstance(e, HttpError):
                    status_code = getattr(e, "status_code", None) or getattr(getattr(e, "resp", None), "status", None)
                    text = str(e)
                    if "storageQuotaExceeded" in text:
                        is_quota = True
                        reason = "storageQuotaExceeded"
                if is_quota and (status_code == 403 or status_code is None):
                    logging.warning(
                        "Google Drive quota unavailable for service account; skipping upload (status=%s)",
                        status_code or "unknown",
                    )
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "drive_upload", "outcome": "skipped"}
                    ).inc()
                    return StepResult.skip(
                        message="Drive upload skipped: service account has no storage quota. Use a shared drive or OAuth domain-wide delegation.",
                        status_code=403,
                        reason=reason or "quota",
                        platform="GoogleDrive",
                        command=f"upload {os.path.basename(file_path)}",
                        file_path=file_path,
                    )
            except Exception:
                pass
            logging.exception("Drive upload failed")
            self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload", "outcome": "error"}).inc()
            return StepResult.fail(
                error=str(e), platform="GoogleDrive", command=f"upload {os.path.basename(file_path)}"
            )

    def _make_public(self, file_id: str) -> None:
        """Make file publicly accessible"""
        permission = {"role": "reader", "type": "anyone"}
        self.service.permissions().create(fileId=file_id, body=permission).execute()

    def _generate_discord_links(self, file_id: str) -> dict[str, str]:
        """Generate various link formats for Discord compatibility"""
        return {
            "preview_link": f"https://drive.google.com/file/d/{file_id}/preview",
            "direct_link": f"https://drive.google.com/uc?id={file_id}",
            "view_link": f"https://drive.google.com/file/d/{file_id}/view",
            "thumbnail": f"https://drive.google.com/thumbnail?id={file_id}&sz=w1920-h1080",
        }

    def run(self, *args, **kwargs) -> StepResult:
        try:
            return self._run(*args, **kwargs)
        except Exception as exc:
            self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc), platform="GoogleDrive", command="upload wrapper")
