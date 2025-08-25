import os
import json
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from crewai_tools import BaseTool
from datetime import datetime
import mimetypes
import io
import hashlib

from ..settings import GOOGLE_CREDENTIALS

class EnhancedDriveManager:
    """Enhanced Google Drive manager with resumable uploads and Discord-compatible links"""
    
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or str(GOOGLE_CREDENTIALS)
        self.service = self._setup_service()
        self.base_folder_id, self.subfolders = self._setup_folder_structure()
        self.upload_cache = {}  # Cache for tracking uploads
    
    def _setup_service(self):
        """Setup Google Drive service with proper authentication"""
        try:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Test the connection
            about = service.about().get(fields='user').execute()
            logging.info(f"Connected to Google Drive as: {about['user']['emailAddress']}")
            
            return service
            
        except Exception as e:
            logging.error(f"Failed to setup Google Drive service: {e}")
            raise
    
    def _create_folder(self, name: str, parent_id: str = None, description: str = "") -> str:
        """Create a folder on Google Drive with error handling"""
        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'description': description
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id,name,parents'
            ).execute()
            
            folder_id = folder.get('id')
            logging.info(f"Created folder '{name}' with ID: {folder_id}")
            
            return folder_id
            
        except HttpError as e:
            if e.resp.status == 409:  # Folder already exists
                # Search for existing folder
                query = f"name='{name}' and mimeType='application/vnd.google-apps.folder'"
                if parent_id:
                    query += f" and '{parent_id}' in parents"
                
                results = self.service.files().list(
                    q=query,
                    fields="files(id, name)"
                ).execute()
                
                files = results.get('files', [])
                if files:
                    logging.info(f"Found existing folder '{name}' with ID: {files[0]['id']}")
                    return files[0]['id']
            
            logging.error(f"Error creating folder '{name}': {e}")
            raise
    
    def _setup_folder_structure(self) -> tuple[str, Dict[str, str]]:
        """Create organized folder structure for content system"""
        try:
            # Create base folder
            base_folder_id = self._create_folder(
                "CrewAI_Content_System",
                description="Automated content monitoring and analysis system"
            )
            
            # Create platform-specific subfolders
            subfolders = {
                'youtube': self._create_folder(
                    "YouTube_Content", 
                    base_folder_id,
                    "YouTube videos and metadata"
                ),
                'instagram': self._create_folder(
                    "Instagram_Content", 
                    base_folder_id,
                    "Instagram stories, posts, and lives"
                ),
                'analysis': self._create_folder(
                    "Content_Analysis", 
                    base_folder_id,
                    "Transcripts, analysis, and processed data"
                ),
                'social_media': self._create_folder(
                    "Social_Media_Intelligence", 
                    base_folder_id,
                    "Social media monitoring and analytics"
                ),
                'fact_checks': self._create_folder(
                    "Fact_Checks", 
                    base_folder_id,
                    "Fact-checking reports and truth scores"
                ),
                'backups': self._create_folder(
                    "System_Backups", 
                    base_folder_id,
                    "System backups and recovery data"
                )
            }
            
            # Create year-based subfolders for better organization
            current_year = str(datetime.now().year)
            for platform, folder_id in subfolders.items():
                if platform in ['youtube', 'instagram']:
                    year_folder_id = self._create_folder(current_year, folder_id)
                    subfolders[f"{platform}_{current_year}"] = year_folder_id
            
            logging.info(f"Folder structure created with base ID: {base_folder_id}")
            return base_folder_id, subfolders
            
        except Exception as e:
            logging.error(f"Failed to setup folder structure: {e}")
            raise
    
    def upload_for_discord(self, file_path: str, platform: str, metadata: Dict = None) -> Dict:
        """Upload video file with Discord-compatible sharing setup"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'status': 'error',
                    'error': f'File not found: {file_path}'
                }
            
            # Determine target folder
            current_year = str(datetime.now().year)
            folder_key = f"{platform}_{current_year}"
            folder_id = self.subfolders.get(folder_key, self.subfolders.get(platform, self.base_folder_id))
            
            # Create creator-specific subfolder if metadata provided
            if metadata and metadata.get('creator'):
                creator_name = self._sanitize_folder_name(metadata['creator'])
                creator_folder_id = self._create_folder(creator_name, folder_id)
                folder_id = creator_folder_id
            
            # Prepare file metadata
            file_metadata = {
                'name': file_path.name,
                'parents': [folder_id],
                'description': self._generate_file_description(metadata)
            }
            
            # Add custom properties for better organization
            if metadata:
                properties = {}
                for key in ['video_id', 'channel_id', 'platform', 'upload_date']:
                    if key in metadata:
                        properties[key] = str(metadata[key])
                
                if properties:
                    file_metadata['properties'] = properties
            
            # Check file size and use appropriate upload method
            file_size = file_path.stat().st_size
            
            if file_size > 100 * 1024 * 1024:  # 100MB threshold
                logging.info(f"Large file detected ({file_size / (1024*1024):.1f}MB), using resumable upload")
                return self._upload_large_file(file_path, file_metadata, file_size)
            else:
                logging.info(f"Small file ({file_size / (1024*1024):.1f}MB), using standard upload")
                return self._upload_small_file(file_path, file_metadata)
            
        except Exception as e:
            logging.error(f"Upload failed for {file_path}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_path': str(file_path)
            }
    
    def _upload_large_file(self, file_path: Path, file_metadata: Dict, file_size: int) -> Dict:
        """Upload large files using resumable upload"""
        try:
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Create resumable media upload
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True,
                chunksize=8 * 1024 * 1024  # 8MB chunks
            )
            
            # Create upload request
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink,mimeType'
            )
            
            # Execute resumable upload with progress tracking
            response = None
            last_progress = 0
            
            while response is None:
                try:
                    status, response = request.next_chunk()
                    
                    if status:
                        progress = int(status.progress() * 100)
                        if progress > last_progress + 10:  # Log every 10% increment
                            logging.info(f"Upload progress: {progress}%")
                            last_progress = progress
                            
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # Resumable upload can recover from these errors
                        logging.warning(f"Recoverable upload error: {e}, retrying...")
                        time.sleep(5)
                        continue
                    else:
                        raise
            
            return self._finalize_upload(response)
            
        except Exception as e:
            logging.error(f"Resumable upload failed: {e}")
            raise
    
    def _upload_small_file(self, file_path: Path, file_metadata: Dict) -> Dict:
        """Upload small files using standard upload"""
        try:
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Create standard media upload
            media = MediaFileUpload(str(file_path), mimetype=mime_type)
            
            # Upload file
            response = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,webViewLink,mimeType'
            ).execute()
            
            return self._finalize_upload(response)
            
        except Exception as e:
            logging.error(f"Standard upload failed: {e}")
            raise
    
    def _finalize_upload(self, response: Dict) -> Dict:
        """Finalize upload and setup Discord-compatible sharing"""
        try:
            file_id = response.get('id')
            
            if not file_id:
                raise ValueError("No file ID returned from upload")
            
            # Make file publicly accessible for Discord
            self._make_public(file_id)
            
            # Generate Discord-compatible links
            links = self._generate_discord_links(file_id)
            
            # Create upload result
            result = {
                'status': 'success',
                'file_id': file_id,
                'file_name': response.get('name'),
                'file_size': response.get('size'),
                'mime_type': response.get('mimeType'),
                'web_view_link': response.get('webViewLink'),
                'links': links,
                'uploaded_at': datetime.now().isoformat()
            }
            
            logging.info(f"Successfully uploaded {result['file_name']} (ID: {file_id})")
            return result
            
        except Exception as e:
            logging.error(f"Upload finalization failed: {e}")
            raise
    
    def _make_public(self, file_id: str):
        """Make file publicly accessible with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                permission = {
                    'role': 'reader',
                    'type': 'anyone'
                }
                
                self.service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    fields='id'
                ).execute()
                
                logging.info(f"Made file {file_id} publicly accessible")
                return
                
            except HttpError as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Permission setting attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logging.error(f"Failed to make file public after {max_retries} attempts: {e}")
                    raise
    
    def _generate_discord_links(self, file_id: str) -> Dict:
        """Generate various link formats for Discord compatibility"""
        return {
            'preview_link': f"https://drive.google.com/file/d/{file_id}/preview",
            'direct_link': f"https://drive.google.com/uc?id={file_id}",
            'view_link': f"https://drive.google.com/file/d/{file_id}/view",
            'thumbnail': f"https://drive.google.com/thumbnail?id={file_id}&sz=w1920-h1080",
            'embed_video': f"https://drive.google.com/file/d/{file_id}/preview",
            'download_link': f"https://drive.google.com/uc?export=download&id={file_id}"
        }
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Sanitize folder names for Drive compatibility"""
        import re
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Limit length
        sanitized = sanitized[:100]
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        return sanitized or 'Unknown'
    
    def _generate_file_description(self, metadata: Dict = None) -> str:
        """Generate comprehensive file description from metadata"""
        if not metadata:
            return "Uploaded by CrewAI Content System"
        
        description_parts = ["CrewAI Content System Upload"]
        
        if metadata.get('platform'):
            description_parts.append(f"Platform: {metadata['platform']}")
        
        if metadata.get('creator'):
            description_parts.append(f"Creator: {metadata['creator']}")
        
        if metadata.get('title'):
            description_parts.append(f"Title: {metadata['title']}")
        
        if metadata.get('upload_date'):
            description_parts.append(f"Original Date: {metadata['upload_date']}")
        
        if metadata.get('duration'):
            description_parts.append(f"Duration: {metadata['duration']}")
        
        description_parts.append(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return " | ".join(description_parts)
    
    def get_file_info(self, file_id: str) -> Dict:
        """Get comprehensive file information"""
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields='id,name,size,mimeType,createdTime,modifiedTime,webViewLink,properties,description'
            ).execute()
            
            return {
                'status': 'success',
                'file_info': file_info
            }
            
        except HttpError as e:
            logging.error(f"Failed to get file info for {file_id}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def delete_file(self, file_id: str) -> Dict:
        """Delete a file from Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            logging.info(f"Deleted file {file_id}")
            
            return {
                'status': 'success',
                'message': f'File {file_id} deleted successfully'
            }
            
        except HttpError as e:
            logging.error(f"Failed to delete file {file_id}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def list_folder_contents(self, folder_id: str = None) -> Dict:
        """List contents of a folder"""
        try:
            folder_id = folder_id or self.base_folder_id
            
            query = f"'{folder_id}' in parents and trashed = false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id,name,mimeType,size,createdTime,modifiedTime)",
                orderBy="createdTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            return {
                'status': 'success',
                'folder_id': folder_id,
                'file_count': len(files),
                'files': files
            }
            
        except HttpError as e:
            logging.error(f"Failed to list folder contents: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

class EnhancedDriveUploadTool(BaseTool):
    """Enhanced Google Drive Upload Tool with comprehensive error handling"""
    
    name: str = "Enhanced Google Drive Upload Tool"
    description: str = "Upload files to Google Drive with resumable uploads and Discord-compatible links"
    
    def __init__(self, credentials_path: str = None):
        super().__init__()
        self.drive_manager = EnhancedDriveManager(credentials_path)
    
    def _run(self, file_path: str, platform: str = "general", metadata: Dict = None) -> str:
        """Upload file to Google Drive with enhanced features"""
        try:
            # Apply rate limiting
            import asyncio
            
            async def rate_limited_upload():
                can_proceed, wait_time = await rate_limiter.check_rate_limit('drive_api_writes')
                if not can_proceed and wait_time:
                    await asyncio.sleep(wait_time)
                
                # Perform upload
                result = self.drive_manager.upload_for_discord(file_path, platform, metadata)
                
                # Record successful request
                if result.get('status') == 'success':
                    await rate_limiter.record_request('drive_api_writes')
                
                return result
            
            # Run the async function
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(rate_limited_upload())
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'file_path': file_path,
                'timestamp': datetime.now().isoformat()
            }
            
            logging.error(f"Drive upload tool error: {e}")
            return json.dumps(error_result, indent=2)

# Utility function for batch uploads
def batch_upload_files(file_paths: List[str], platform: str, metadata_list: List[Dict] = None) -> Dict:
    """Upload multiple files in batch with progress tracking"""
    drive_manager = EnhancedDriveManager()
    results = {
        'batch_id': hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
        'started_at': datetime.now().isoformat(),
        'total_files': len(file_paths),
        'completed': 0,
        'failed': 0,
        'results': []
    }
    
    for i, file_path in enumerate(file_paths):
        try:
            logging.info(f"Uploading file {i+1}/{len(file_paths)}: {file_path}")
            
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
            result = drive_manager.upload_for_discord(file_path, platform, metadata)
            
            if result.get('status') == 'success':
                results['completed'] += 1
            else:
                results['failed'] += 1
            
            results['results'].append({
                'file_path': file_path,
                'result': result
            })
            
            # Add delay between uploads to respect rate limits
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Batch upload error for {file_path}: {e}")
            results['failed'] += 1
            results['results'].append({
                'file_path': file_path,
                'result': {
                    'status': 'error',
                    'error': str(e)
                }
            })
    
    results['completed_at'] = datetime.now().isoformat()
    
    logging.info(f"Batch upload completed: {results['completed']} success, {results['failed']} failed")
    
    return results

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    drive_manager = EnhancedDriveManager()
    
    # Test file upload (replace with actual file path)
    test_file = str((Path.home() / "test_video.mp4"))
    if os.path.exists(test_file):
        metadata = {
            'platform': 'youtube',
            'creator': 'Test Creator',
            'title': 'Test Video',
            'video_id': 'test123',
            'upload_date': '2024-01-01'
        }
        
        result = drive_manager.upload_for_discord(test_file, 'youtube', metadata)
        print(json.dumps(result, indent=2))
    else:
        print("Test file not found")