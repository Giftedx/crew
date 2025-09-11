import logging
import os
from typing import Any

from core.secure_config import get_config

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool

# Optional heavy Google client dependencies. Tests monkeypatch `_setup_service`, so we
# avoid import errors when these libraries are absent by deferring/failing gracefully.
try:  # pragma: no cover - import guarding
    from google.oauth2 import service_account  # pragma: no cover
    from googleapiclient.discovery import build  # type: ignore[import-not-found]  # pragma: no cover
    from googleapiclient.http import MediaFileUpload  # type: ignore[import-not-found]  # pragma: no cover

    _GOOGLE_LIBS_AVAILABLE = True
except Exception:  # broad: any import error should mark feature unavailable
    service_account = build = MediaFileUpload = None  # type: ignore
    _GOOGLE_LIBS_AVAILABLE = False

# The Google client libraries make network requests, which are slow and can fail.
# To keep the tool resilient and idempotent we check for the existence of folders
# before creating new ones and surface helpful error messages when credentials
# are missing or invalid.

from ..settings import GOOGLE_CREDENTIALS


class DriveUploadTool(BaseTool[StepResult]):
    name: str = "Google Drive Upload Tool"
    description: str = "Upload files to Google Drive and create shareable links"
    # Allow dynamic attributes (service, folders) assigned in __init__ under pydantic v2
    model_config = {"extra": "allow"}

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()
        self.service = self._setup_service()
        # Annotate attributes for mypy
        self.base_folder_id: str | None
        self.subfolders: dict[str, str]
        if self.service:
            self.base_folder_id, self.subfolders = self._setup_folder_structure()
        else:
            self.base_folder_id = None
            self.subfolders = {}

    def _setup_service(self) -> Any:  # external client returns dynamic resource
        """Initialise the Drive service using service account credentials."""
        # Check if Google Drive is explicitly disabled
        config = get_config()
        if config.disable_google_drive:
            print("⚠️  Google Drive disabled via environment variable")
            return None

        if not _GOOGLE_LIBS_AVAILABLE:  # pragma: no cover - exercised via import path
            print("⚠️  Google client libraries not available - Drive uploads disabled")
            return None
        credentials_path = str(GOOGLE_CREDENTIALS)
        if service_account is None or build is None:  # pragma: no cover - safety net
            return None
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
            )
        except Exception as exc:  # pragma: no cover - exercised in integration env
            logging.warning("Google credentials unavailable at %s: %s", credentials_path, exc)
            print("⚠️  Google Drive credentials invalid - Drive uploads disabled")
            return None

        return build("drive", "v3", credentials=credentials)

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
        # file_metadata is a loose dict accepted by the Drive API client
        file_metadata: dict[str, Any] = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            file_metadata["parents"] = [parent_id]
        file = self.service.files().create(body=file_metadata, fields="id").execute()
        # Drive API guarantees an 'id' field in successful response
        return str(file.get("id"))

    def _setup_folder_structure(self) -> tuple[str, dict[str, str]]:
        """Create or reuse an organised folder structure on Drive."""
        base_folder = self._get_or_create_folder("CrewAI_Content")

        subfolders = {
            "youtube": self._get_or_create_folder("YouTube_Videos", base_folder),
            "instagram": self._get_or_create_folder("Instagram_Content", base_folder),
            "processed": self._get_or_create_folder("Processed_Content", base_folder),
        }

        return base_folder, subfolders

    def _run(self, file_path: str, platform: str) -> StepResult:
        """Upload video file with Discord-compatible sharing setup"""
        # Check if Google Drive is available
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

            if MediaFileUpload is None:  # pragma: no cover - import guard path
                raise RuntimeError("google client library unavailable (MediaFileUpload missing)")
            media = MediaFileUpload(
                file_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=256 * 1024 * 1024,  # 256MB chunks
            )

            request = self.service.files().create(
                body=file_metadata, media_body=media, fields="id,name,size,webViewLink"
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logging.info("Upload progress: %s%%", int(status.progress() * 100))

            if response is None:  # pragma: no cover - defensive fallback (should not happen)
                raise RuntimeError("upload response missing after chunk loop")
            file_id = response.get("id")

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

    # Expose run for pipeline compatibility
    def run(self, *args, **kwargs) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            return self._run(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - unexpected
            self._metrics.counter("tool_runs_total", labels={"tool": "drive_upload", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc), platform="GoogleDrive", command="upload wrapper")
