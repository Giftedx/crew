from crewai_tools import BaseTool
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

class DriveUploadTool(BaseTool):
    name: str = "Google Drive Upload Tool"
    description: str = "Upload files to Google Drive and create shareable links"
    
    def __init__(self):
        super().__init__()
        self.service = self._setup_service()
        self.base_folder_id, self.subfolders = self._setup_folder_structure()

    def _setup_service(self):
        credentials_path = "F:/yt-auto/crewaiv2/CrewAI_Content_System/Config/google-credentials.json"
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)

    def _create_folder(self, name, parent_id=None):
        """Create a folder on Google Drive."""
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        file = self.service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')

    def _setup_folder_structure(self):
        """Create organized folder structure"""
        base_folder = self._create_folder("CrewAI_Content_System")
        
        subfolders = {
            'youtube': self._create_folder("YouTube_Videos", base_folder),
            'instagram': self._create_folder("Instagram_Content", base_folder),
            'processed': self._create_folder("Processed_Content", base_folder)
        }
        
        return base_folder, subfolders

    def _run(self, file_path: str, platform: str) -> dict:
        """Upload video file with Discord-compatible sharing setup"""
        
        # Determine target folder
        folder_id = self.subfolders.get(platform, self.base_folder_id)
        
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        
        # Use resumable upload for large video files
        media = MediaFileUpload(
            file_path,
            mimetype='video/mp4',
            resumable=True,
            chunksize=256 * 1024 * 1024  # 256MB chunks
        )
        
        # Upload with progress tracking
        request = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,size,webViewLink'
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        
        file_id = response.get('id')
        
        # Make publicly accessible for Discord
        self._make_public(file_id)
        
        # Generate Discord-compatible links
        links = self._generate_discord_links(file_id)
        
        return {
            'file_id': file_id,
            'file_name': response.get('name'),
            'file_size': response.get('size'),
            'links': links,
            'status': 'success'
        }

    def _make_public(self, file_id: str):
        """Make file publicly accessible"""
        permission = {
            'role': 'reader',
            'type': 'anyone'
        }
        self.service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()

    def _generate_discord_links(self, file_id: str) -> dict:
        """Generate various link formats for Discord compatibility"""
        return {
            'preview_link': f"https://drive.google.com/file/d/{file_id}/preview",
            'direct_link': f"https://drive.google.com/uc?id={file_id}",
            'view_link': f"https://drive.google.com/file/d/{file_id}/view",
            'thumbnail': f"https://drive.google.com/thumbnail?id={file_id}&sz=w1920-h1080"
        }
