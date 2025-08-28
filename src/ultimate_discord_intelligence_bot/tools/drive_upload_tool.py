import logging
import os

from crewai.tools import BaseTool
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# The Google client libraries make network requests, which are slow and can fail.
# To keep the tool resilient and idempotent we check for the existence of folders
# before creating new ones and surface helpful error messages when credentials
# are missing or invalid.

from ..settings import GOOGLE_CREDENTIALS

class DriveUploadTool(BaseTool):
    name: str = "Google Drive Upload Tool"
    description: str = "Upload files to Google Drive and create shareable links"
    
    def __init__(self):
        super().__init__()
        self.service = self._setup_service()
        self.base_folder_id, self.subfolders = self._setup_folder_structure()

    def _setup_service(self):
        """Initialise the Drive service using service account credentials."""
        credentials_path = str(GOOGLE_CREDENTIALS)
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
            )
        except Exception as exc:  # pragma: no cover - exercised in integration env
            logging.error("Invalid Google credentials at %s: %s", credentials_path, exc)
            raise

        return build("drive", "v3", credentials=credentials)

    def _find_folder(self, name: str, parent_id: str | None = None) -> str | None:
        """Return folder id if a folder with ``name`` exists under ``parent_id``."""
        query = ["name = '{}'".format(name.replace("'", "\'")), "mimeType = 'application/vnd.google-apps.folder'", "trashed = false"]
        if parent_id:
            query.append(f"'{parent_id}' in parents")
        result = (
            self.service.files()
            .list(q=" and ".join(query), fields="files(id)")
            .execute()
        )
        files = result.get("files", [])
        return files[0]["id"] if files else None

    def _get_or_create_folder(self, name: str, parent_id: str | None = None) -> str:
        folder_id = self._find_folder(name, parent_id)
        if folder_id:
            return folder_id
        file_metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            file_metadata["parents"] = [parent_id]
        file = (
            self.service.files()
            .create(body=file_metadata, fields="id")
            .execute()
        )
        return file.get("id")

    def _setup_folder_structure(self):
        """Create or reuse an organised folder structure on Drive."""
        base_folder = self._get_or_create_folder("CrewAI_Content")

        subfolders = {
            "youtube": self._get_or_create_folder("YouTube_Videos", base_folder),
            "instagram": self._get_or_create_folder("Instagram_Content", base_folder),
            "processed": self._get_or_create_folder("Processed_Content", base_folder),
        }

        return base_folder, subfolders

    def _run(self, file_path: str, platform: str) -> dict:
        """Upload video file with Discord-compatible sharing setup"""
        try:
            folder_id = self.subfolders.get(platform, self.base_folder_id)

            file_metadata = {"name": os.path.basename(file_path), "parents": [folder_id]}

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

            file_id = response.get("id")

            self._make_public(file_id)
            links = self._generate_discord_links(file_id)

            return {
                "file_id": file_id,
                "file_name": response.get("name"),
                "file_size": response.get("size"),
                "links": links,
                "status": "success",
            }
        except Exception as e:
            logging.exception("Drive upload failed")
            return {"status": "error", "error": str(e)}

    def _make_public(self, file_id: str):
        """Make file publicly accessible"""
        permission = {
            'role': 'reader',
            'type': 'anyone'
        }
        self.service.permissions().create(fileId=file_id, body=permission).execute()

    def _generate_discord_links(self, file_id: str) -> dict:
        """Generate various link formats for Discord compatibility"""
        return {
            'preview_link': f"https://drive.google.com/file/d/{file_id}/preview",
            'direct_link': f"https://drive.google.com/uc?id={file_id}",
            'view_link': f"https://drive.google.com/file/d/{file_id}/view",
            'thumbnail': f"https://drive.google.com/thumbnail?id={file_id}&sz=w1920-h1080"
        }

    # Expose run for pipeline compatibility
    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
