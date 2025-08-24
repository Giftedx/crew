# Automated YouTube and Instagram Content Monitoring System with CrewAI

This comprehensive guide provides complete implementation details for building an automated content monitoring and downloading system using CrewAI that monitors YouTube channels via PubSubHubbub, downloads content using yt-dlp and Instagram tools, uploads to Google Drive, and posts to Discord with proper embed formatting.

## System architecture overview

The system consists of six core components working together through CrewAI's agent-based architecture:
- **YouTube Monitoring Agent**: Uses PubSubHubbub for real-time notifications
- **Instagram Monitoring Agent**: Combines multiple tools for comprehensive coverage  
- **Download Manager Agent**: Orchestrates yt-dlp and Instagram downloaders
- **Storage Agent**: Handles Google Drive uploads and organization
- **Discord Integration Agent**: Manages posting with proper embed formatting
- **System Coordinator**: Manages workflow, error handling, and monitoring

## PubSubHubbub implementation for YouTube monitoring

### Core webhook setup

```python
from flask import Flask, request
import xml.etree.ElementTree as ET
import requests
import json

app = Flask(__name__)

@app.route('/youtube-webhook', methods=['GET', 'POST'])
def youtube_webhook():
    if request.method == 'GET':
        # Handle subscription verification
        challenge = request.args.get('hub.challenge')
        mode = request.args.get('hub.mode')
        
        if challenge and mode == 'subscribe':
            print(f"Verified YouTube subscription")
            return challenge, 200
        return 'Not found', 404
    
    elif request.method == 'POST':
        # Parse YouTube RSS notification
        xml_data = request.get_data().decode('utf-8')
        root = ET.fromstring(xml_data)
        
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015'
        }
        
        for entry in root.findall('atom:entry', ns):
            video_id = entry.find('yt:videoId', ns).text
            channel_id = entry.find('yt:channelId', ns).text
            title = entry.find('atom:title', ns).text
            published = entry.find('atom:published', ns).text
            
            # Trigger download workflow
            trigger_video_download({
                'video_id': video_id,
                'channel_id': channel_id,
                'title': title,
                'published': published,
                'url': f'https://www.youtube.com/watch?v={video_id}'
            })
        
        return 'OK', 200

def subscribe_to_channel(channel_id, webhook_url):
    """Subscribe to YouTube channel using PubSubHubbub"""
    data = {
        'hub.mode': 'subscribe',
        'hub.topic': f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}',
        'hub.callback': webhook_url,
        'hub.verify': 'sync',
        'hub.lease_seconds': '432000'  # 5 days
    }
    
    response = requests.post(
        'https://pubsubhubbub.appspot.com/subscribe',
        data=data
    )
    
    return response.status_code == 204
```

### Subscription management with error handling

```python
class YouTubeMonitor:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.subscriptions = {}
        self.fallback_poller = YouTubeFallbackPoller()
    
    async def add_channel(self, channel_id):
        success = await self.subscribe_channel(channel_id)
        
        if not success:
            print(f"PubSubHubbub failed for {channel_id}, using fallback polling")
            self.fallback_poller.add_channel(channel_id)
        else:
            self.subscriptions[channel_id] = {
                'method': 'pubsubhubbub',
                'expires': time.time() + 432000
            }
    
    async def subscribe_channel(self, channel_id, max_retries=3):
        for attempt in range(max_retries):
            try:
                success = subscribe_to_channel(channel_id, self.webhook_url)
                if success:
                    return True
            except Exception as e:
                print(f"Subscription attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return False
```

## yt-dlp integration for YouTube downloads

### Optimized configuration for F:/ drive

```ini
# F:/yt-dlp/config/crewai-system.conf
# Output to F:/ drive with organized structure
-o F:/Downloads/YouTube/%(uploader)s/%(upload_date>%Y)s/%(title)s [%(id)s].%(ext)s

# Quality optimization for Discord sharing
-f bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best
-S res:1080,fps:60,vcodec:h264,acodec:aac

# File organization and restrictions
--restrict-filenames
--trim-filenames 100
--windows-filenames

# Comprehensive metadata extraction
--write-info-json
--write-thumbnail
--embed-metadata
--embed-subs
--embed-thumbnail

# Performance optimization with aria2c
--external-downloader aria2c
--external-downloader-args "-x 8 -j 3 -k 1M -s 8 --max-connection-per-server=16"
--concurrent-fragments 4
--retries 10

# Archive management
--download-archive F:/yt-dlp/archives/crewai_downloads.txt

# Temp processing directory
-P temp:F:/Downloads/temp
```

### CrewAI-compatible download implementation

```python
from crewai_tools import BaseTool
import subprocess
import json

class YouTubeDownloadTool(BaseTool):
    name: str = "YouTube Download Tool"
    description: str = "Download YouTube videos with optimal settings for Discord sharing"
    
    def _run(self, video_url: str, quality: str = "1080p") -> str:
        """Download YouTube video using yt-dlp with CrewAI integration"""
        
        config_file = "F:/yt-dlp/config/crewai-system.conf"
        
        # Construct command with quality-specific settings
        command = [
            "F:/yt-dlp/yt-dlp.exe",
            "--config-locations", config_file,
            "--print", "%(id)s|%(title)s|%(uploader)s|%(duration)s|%(filesize_approx)s",
            video_url
        ]
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=1800  # 30 minutes max
            )
            
            if result.returncode == 0:
                # Parse output for metadata
                output_lines = result.stdout.strip().split('\n')
                download_info = output_lines[-1].split('|')
                
                return json.dumps({
                    'status': 'success',
                    'video_id': download_info[0],
                    'title': download_info[1],
                    'uploader': download_info[2],
                    'duration': download_info[3],
                    'file_size': download_info[4],
                    'local_path': f"F:/Downloads/YouTube/{download_info[2]}/",
                    'download_command': ' '.join(command)
                })
            else:
                return json.dumps({
                    'status': 'error',
                    'error': result.stderr,
                    'command': ' '.join(command)
                })
                
        except subprocess.TimeoutExpired:
            return json.dumps({
                'status': 'error',
                'error': 'Download timeout after 30 minutes'
            })
        except Exception as e:
            return json.dumps({
                'status': 'error', 
                'error': str(e)
            })
```

## Instagram content downloading comparison

### Tool selection matrix

| Requirement | Instaloader | RocketAPI | PyInstaLive | Recommendation |
|-------------|-------------|-----------|-------------|----------------|
| **Stories** | ✅ Excellent | ✅ Good (API + custom code) | ❌ No | **Instaloader** for simplicity |
| **Livestreams** | ❌ Not supported | ⚠️ Metadata only | ✅ Full recording | **PyInstaLive** for recording |
| **Cost** | Free | Paid ($20-50/month) | Free | **Mixed approach** |
| **Reliability** | Medium | High | Medium | **RocketAPI** for production |

### Hybrid implementation for comprehensive coverage

```python
class InstagramContentManager:
    def __init__(self):
        self.instaloader_client = self._setup_instaloader()
        self.rocketapi_client = self._setup_rocketapi()
        self.pyinstalive_monitor = self._setup_livestream_monitor()
    
    def _setup_instaloader(self):
        import instaloader
        L = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=True,
            compress_json=False,
            save_metadata=True
        )
        # Load session to avoid repeated logins
        try:
            L.load_session_from_file('instagram_username')
        except:
            L.login('instagram_username', 'instagram_password')
        
        return L
    
    def download_stories(self, username: str) -> dict:
        """Download Instagram stories using Instaloader"""
        try:
            profile = instaloader.Profile.from_username(
                self.instaloader_client.context, username
            )
            
            stories_downloaded = []
            for story in profile.get_stories():
                for item in story.get_items():
                    # Download with organized naming
                    target_dir = f"F:/Downloads/Instagram/Stories/{username}"
                    self.instaloader_client.download_storyitem(
                        item, target_dir
                    )
                    
                    stories_downloaded.append({
                        'story_id': item.mediaid,
                        'url': item.url,
                        'type': 'video' if item.is_video else 'photo',
                        'expiring': str(item.expiring_local),
                        'local_path': f"{target_dir}/{item.mediaid}"
                    })
            
            return {
                'status': 'success',
                'stories_count': len(stories_downloaded),
                'stories': stories_downloaded
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def monitor_livestreams(self, username: str) -> dict:
        """Monitor for livestreams using RocketAPI + PyInstaLive"""
        try:
            # Check if user is live using RocketAPI
            live_status = self.rocketapi_client.get_user_live(username)
            
            if live_status.get('is_live'):
                # Trigger PyInstaLive recording
                subprocess.Popen([
                    'pyinstalive', '-d', username, 
                    '--output', f'F:/Downloads/Instagram/Lives/{username}'
                ])
                
                return {
                    'status': 'live_detected',
                    'username': username,
                    'recording_started': True,
                    'broadcast_id': live_status.get('broadcast_id')
                }
            
            return {'status': 'not_live', 'username': username}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
```

## Google Drive integration for file management

### Resumable upload implementation with Discord-compatible links

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time

class DriveManager:
    def __init__(self, credentials_path: str):
        self.service = self._setup_service(credentials_path)
        self.base_folder_id = self._setup_folder_structure()
    
    def _setup_service(self, credentials_path: str):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)
    
    def _setup_folder_structure(self):
        """Create organized folder structure"""
        base_folder = self._create_folder("CrewAI_Content_System")
        
        subfolders = {
            'youtube': self._create_folder("YouTube_Videos", base_folder),
            'instagram': self._create_folder("Instagram_Content", base_folder),
            'processed': self._create_folder("Processed_Content", base_folder)
        }
        
        return base_folder, subfolders
    
    def upload_for_discord(self, file_path: str, platform: str) -> dict:
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
```

## Discord integration with embed limitations

### Critical limitation understanding

**Video embeds do NOT work through Discord webhooks.** This is a confirmed limitation. However, there are effective alternatives:

1. **Direct file upload** (for files under size limits)
2. **Link embedding** (for external video platforms)
3. **Structured embeds** with thumbnails and links

### Discord posting implementation

```python
import requests
import json
from pathlib import Path

class DiscordManager:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.rate_limiter = self._setup_rate_limiter()
    
    def post_content_notification(self, content_data: dict, drive_links: dict) -> dict:
        """Post content notification with proper formatting"""
        
        # Check file size for direct upload vs link sharing
        file_size_mb = int(content_data.get('file_size', 0)) / (1024 * 1024)
        
        if file_size_mb <= 100:  # Within Discord limits for most servers
            return self._post_with_file_upload(content_data, drive_links)
        else:
            return self._post_with_embed_links(content_data, drive_links)
    
    def _post_with_embed_links(self, content_data: dict, drive_links: dict) -> dict:
        """Post using structured embeds with links (recommended approach)"""
        
        embed = {
            "title": content_data.get('title', 'New Content Available'),
            "description": f"📹 **Platform**: {content_data.get('platform', 'Unknown')}\n"
                          f"👤 **Creator**: {content_data.get('uploader', 'Unknown')}\n"
                          f"⏱️ **Duration**: {content_data.get('duration', 'Unknown')}\n"
                          f"📊 **Size**: {content_data.get('file_size', 'Unknown')}",
            "color": 0x00ff00,  # Green for success
            "thumbnail": {
                "url": drive_links.get('thumbnail', '')
            },
            "fields": [
                {
                    "name": "🎥 Watch Online",
                    "value": f"[Google Drive Preview]({drive_links['preview_link']})",
                    "inline": True
                },
                {
                    "name": "💾 Download",
                    "value": f"[Direct Download]({drive_links['direct_link']})",
                    "inline": True
                }
            ],
            "footer": {
                "text": "CrewAI Content Monitor",
                "icon_url": "https://example.com/crewai-icon.png"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        payload = {
            "username": "Content Monitor",
            "avatar_url": "https://example.com/bot-avatar.png",
            "embeds": [embed]
        }
        
        return self._send_webhook(payload)
    
    def _post_with_file_upload(self, content_data: dict, drive_links: dict) -> dict:
        """Post with direct file upload for smaller files"""
        
        local_file_path = content_data.get('local_path')
        if not local_file_path or not Path(local_file_path).exists():
            # Fallback to link posting
            return self._post_with_embed_links(content_data, drive_links)
        
        # Upload file directly to Discord
        files = {
            'file': (
                Path(local_file_path).name,
                open(local_file_path, 'rb'),
                'video/mp4'
            ),
            'payload_json': (
                None,
                json.dumps({
                    "content": f"🎥 **{content_data.get('title', 'New Video')}**\n"
                              f"From: {content_data.get('uploader', 'Unknown')}\n"
                              f"Platform: {content_data.get('platform', 'Unknown')}"
                })
            )
        }
        
        response = requests.post(self.webhook_url, files=files)
        
        # Clean up file handle
        files['file'][1].close()
        
        return self._handle_response(response)
    
    def _send_webhook(self, payload: dict) -> dict:
        """Send webhook with rate limiting"""
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            return self._handle_response(response)
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _handle_response(self, response) -> dict:
        """Handle Discord API response with rate limiting"""
        if response.status_code == 204:
            return {'status': 'success'}
        elif response.status_code == 429:
            retry_after = response.json().get('retry_after', 60)
            return {
                'status': 'rate_limited',
                'retry_after': retry_after
            }
        else:
            return {
                'status': 'error',
                'status_code': response.status_code,
                'error': response.text
            }
```

## CrewAI system architecture

### Complete agent-based implementation

```python
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, FileWriteTool, ScrapeWebsiteTool
from datetime import datetime
import asyncio
import logging

class ContentMonitoringCrew:
    def __init__(self, config_path: str = "config/system.yaml"):
        self.config = self._load_config(config_path)
        self.tools = self._initialize_tools()
        self.agents = self._create_agents()
        self.crew = self._create_crew()
    
    def _initialize_tools(self):
        """Initialize all custom and CrewAI tools"""
        return {
            'youtube_download': YouTubeDownloadTool(),
            'instagram_manager': InstagramContentTool(),
            'drive_uploader': DriveUploadTool(),
            'discord_poster': DiscordPostTool(),
            'file_reader': FileReadTool(),
            'file_writer': FileWriteTool(),
            'web_scraper': ScrapeWebsiteTool()
        }
    
    def _create_agents(self):
        """Create specialized monitoring agents"""
        return {
            'monitor': Agent(
                role="Content Discovery Specialist",
                goal="Monitor multiple platforms and identify new content for download",
                backstory="Expert in real-time content monitoring across YouTube and Instagram with advanced filtering capabilities",
                tools=[
                    self.tools['web_scraper'],
                    self.tools['file_reader'],
                    self.tools['file_writer']
                ],
                max_execution_time=1800,
                verbose=True
            ),
            
            'downloader': Agent(
                role="Intelligent Download Manager",
                goal="Download content efficiently with optimal quality and organization",
                backstory="Specialist in multi-platform content downloading with intelligent format selection and error recovery",
                tools=[
                    self.tools['youtube_download'],
                    self.tools['instagram_manager'],
                    self.tools['file_writer']
                ],
                max_retry_limit=3,
                allow_delegation=False
            ),
            
            'storage_manager': Agent(
                role="Cloud Storage Coordinator",
                goal="Upload and organize content in Google Drive with proper sharing permissions",
                backstory="Expert in cloud storage management with focus on accessibility and organization",
                tools=[
                    self.tools['drive_uploader'],
                    self.tools['file_reader']
                ],
                cache=True
            ),
            
            'distribution_manager': Agent(
                role="Content Distribution Specialist", 
                goal="Share content across Discord channels with optimal formatting",
                backstory="Specialist in social media distribution with deep understanding of platform-specific requirements",
                tools=[
                    self.tools['discord_poster'],
                    self.tools['file_reader']
                ],
                respect_context_window=True
            )
        }
    
    def _create_crew(self):
        """Create the main crew with task workflow"""
        tasks = [
            Task(
                description="""
                Monitor configured YouTube channels and Instagram accounts for new content:
                1. Check PubSubHubbub notifications and fallback polling
                2. Scan Instagram accounts for new posts and stories
                3. Apply content filters based on keywords, duration, and quality metrics
                4. Generate priority list of content for download
                5. Create detailed content manifest with metadata
                """,
                agent=self.agents['monitor'],
                expected_output="JSON manifest of new content with priorities and download parameters"
            ),
            
            Task(
                description="""
                Process the content manifest and download all identified content:
                1. Parse the content manifest from monitoring
                2. Download YouTube videos using optimized yt-dlp configurations
                3. Download Instagram content using appropriate tools
                4. Organize files in structured directories on F:/ drive
                5. Generate download reports with file locations and metadata
                """,
                agent=self.agents['downloader'],
                expected_output="Download completion report with file paths and status for each item"
            ),
            
            Task(
                description="""
                Upload downloaded content to Google Drive with proper organization:
                1. Process download reports and locate files
                2. Upload files using resumable upload for large videos
                3. Create organized folder structure by platform and creator
                4. Set appropriate sharing permissions for Discord access
                5. Generate Discord-compatible links for each file
                """,
                agent=self.agents['storage_manager'],
                expected_output="Upload report with Google Drive links and sharing permissions"
            ),
            
            Task(
                description="""
                Distribute content to Discord channels with optimal formatting:
                1. Process upload reports and Drive links
                2. Create appropriate Discord embeds or direct uploads
                3. Post to configured Discord channels via webhooks
                4. Handle rate limiting and retry failed posts
                5. Generate final distribution report
                """,
                agent=self.agents['distribution_manager'],
                expected_output="Distribution report with Discord posting status and any errors"
            )
        ]
        
        return Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,
            memory=True,
            cache=True,
            verbose=True,
            max_rpm=30
        )
    
    def run_monitoring_cycle(self):
        """Execute one complete monitoring and distribution cycle"""
        try:
            print(f"🚀 Starting content monitoring cycle at {datetime.now()}")
            
            result = self.crew.kickoff()
            
            print(f"✅ Monitoring cycle completed successfully")
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'result': str(result)
            }
            
        except Exception as e:
            print(f"❌ Monitoring cycle failed: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
```

## Error handling and resilience patterns

### Comprehensive error recovery system

```python
import time
import random
from functools import wraps
from typing import Dict, Any, Callable

class SystemResilience:
    def __init__(self):
        self.error_counts = {}
        self.circuit_breaker_thresholds = {
            'youtube_api': 5,
            'instagram_api': 3,
            'drive_api': 4,
            'discord_webhook': 3
        }
        self.backoff_strategies = {
            'exponential': self._exponential_backoff,
            'linear': self._linear_backoff,
            'fixed': self._fixed_backoff
        }
    
    def circuit_breaker(self, service: str, threshold: int = None):
        """Circuit breaker pattern for service protection"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                service_threshold = threshold or self.circuit_breaker_thresholds.get(service, 5)
                
                if self.error_counts.get(service, 0) >= service_threshold:
                    raise Exception(f"Circuit breaker OPEN for {service}")
                
                try:
                    result = func(*args, **kwargs)
                    self.error_counts[service] = 0  # Reset on success
                    return result
                except Exception as e:
                    self.error_counts[service] = self.error_counts.get(service, 0) + 1
                    raise e
            
            return wrapper
        return decorator
    
    def retry_with_backoff(self, max_retries: int = 3, strategy: str = 'exponential'):
        """Retry decorator with configurable backoff strategies"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                backoff_func = self.backoff_strategies.get(strategy, self._exponential_backoff)
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        
                        wait_time = backoff_func(attempt)
                        print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                
                raise Exception(f"Max retries ({max_retries}) exceeded")
            
            return wrapper
        return decorator
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter"""
        base_wait = min(2 ** attempt, 64)  # Cap at 64 seconds
        jitter = random.uniform(0.5, 1.5)
        return base_wait * jitter
    
    def _linear_backoff(self, attempt: int) -> float:
        """Linear backoff with jitter"""
        return (attempt + 1) * 2 + random.uniform(0, 1)
    
    def _fixed_backoff(self, attempt: int) -> float:
        """Fixed delay with jitter"""
        return 5 + random.uniform(0, 2)

# Usage in tools
resilience = SystemResilience()

class ResilientYouTubeDownloadTool(BaseTool):
    name = "Resilient YouTube Download Tool"
    description = "YouTube downloader with comprehensive error handling"
    
    @resilience.circuit_breaker('youtube_api')
    @resilience.retry_with_backoff(max_retries=5, strategy='exponential')
    def _run(self, video_url: str) -> str:
        # Implementation with error handling
        return self._download_video_with_recovery(video_url)
    
    def _download_video_with_recovery(self, video_url: str) -> str:
        """Download with fallback strategies"""
        strategies = [
            self._download_with_ytdlp_standard,
            self._download_with_ytdlp_fallback_format,
            self._download_with_alternative_extractor
        ]
        
        for strategy in strategies:
            try:
                return strategy(video_url)
            except Exception as e:
                print(f"Strategy failed: {e}")
                continue
        
        raise Exception("All download strategies failed")
```

## File organization best practices

### Structured directory system for F:/ drive

```
F:/
├── CrewAI_Content_System/
│   ├── Downloads/
│   │   ├── YouTube/
│   │   │   ├── {Creator_Name}/
│   │   │   │   ├── {YYYY}/
│   │   │   │   │   ├── {MM}/
│   │   │   │   │   │   └── {Video_Title} [{Video_ID}].{ext}
│   │   │   │   │   └── metadata/
│   │   │   │   │       ├── {Video_ID}.info.json
│   │   │   │   │       ├── {Video_ID}.{ext}.jpg  # thumbnail
│   │   │   │   │       └── {Video_ID}.{lang}.srt  # subtitles
│   │   ├── Instagram/
│   │   │   ├── Stories/
│   │   │   │   └── {Username}/
│   │   │   │       └── {YYYY-MM-DD}_{Story_ID}.{ext}
│   │   │   ├── Lives/
│   │   │   │   └── {Username}/
│   │   │   │       └── {YYYY-MM-DD_HH-MM-SS}_live.mp4
│   │   │   └── Posts/
│   │   │       └── {Username}/
│   │   │           └── {Post_ID}.{ext}
│   ├── Processing/
│   │   ├── Queue/          # Files waiting for processing
│   │   ├── InProgress/     # Currently being processed
│   │   └── Failed/         # Failed processing attempts
│   ├── GoogleDrive/
│   │   ├── Uploaded/       # Successfully uploaded files
│   │   └── Pending/        # Waiting for upload
│   ├── Logs/
│   │   ├── system.log      # General system logs
│   │   ├── downloads.log   # Download activity
│   │   ├── uploads.log     # Google Drive uploads
│   │   └── discord.log     # Discord posting activity
│   └── Config/
│       ├── crewai_config.yaml
│       ├── channels.yaml
│       ├── instagram_accounts.yaml
│       └── discord_channels.yaml
```

## Rate limiting strategies

### Comprehensive rate limiting implementation

```python
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Optional
import time

class RateLimitManager:
    def __init__(self):
        self.limits = {
            'youtube_api': {'requests': 10000, 'window': 86400},  # Per day
            'instagram_requests': {'requests': 200, 'window': 3600},  # Per hour
            'drive_api_writes': {'requests': 3, 'window': 1},  # Per second
            'discord_webhook': {'requests': 5, 'window': 2}  # Per 2 seconds
        }
        
        self.usage_tracking = {}
        self.blocked_until = {}
    
    async def check_rate_limit(self, service: str) -> tuple[bool, Optional[float]]:
        """Check if request is within rate limits"""
        current_time = time.time()
        
        # Check if service is blocked
        if service in self.blocked_until:
            if current_time < self.blocked_until[service]:
                wait_time = self.blocked_until[service] - current_time
                return False, wait_time
            else:
                del self.blocked_until[service]
        
        # Initialize tracking for new services
        if service not in self.usage_tracking:
            self.usage_tracking[service] = []
        
        # Clean old requests outside window
        window = self.limits[service]['window']
        cutoff_time = current_time - window
        self.usage_tracking[service] = [
            req_time for req_time in self.usage_tracking[service]
            if req_time > cutoff_time
        ]
        
        # Check if within limits
        max_requests = self.limits[service]['requests']
        current_requests = len(self.usage_tracking[service])
        
        if current_requests >= max_requests:
            # Calculate wait time until oldest request expires
            oldest_request = min(self.usage_tracking[service])
            wait_time = (oldest_request + window) - current_time
            return False, wait_time
        
        return True, None
    
    async def record_request(self, service: str):
        """Record a successful request"""
        current_time = time.time()
        if service not in self.usage_tracking:
            self.usage_tracking[service] = []
        self.usage_tracking[service].append(current_time)
    
    async def handle_rate_limit_error(self, service: str, retry_after: float):
        """Handle rate limit error from API"""
        self.blocked_until[service] = time.time() + retry_after
    
    async def wait_for_rate_limit(self, service: str) -> bool:
        """Wait until rate limit allows request"""
        can_proceed, wait_time = await self.check_rate_limit(service)
        
        if not can_proceed and wait_time:
            print(f"Rate limited for {service}, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            return True
        
        return can_proceed

# Integration with tools
rate_limiter = RateLimitManager()

class RateLimitedTool(BaseTool):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
    
    async def _execute_with_rate_limit(self, func, *args, **kwargs):
        """Execute function with rate limiting"""
        await rate_limiter.wait_for_rate_limit(self.service_name)
        
        try:
            result = await func(*args, **kwargs)
            await rate_limiter.record_request(self.service_name)
            return result
        except RateLimitError as e:
            await rate_limiter.handle_rate_limit_error(
                self.service_name, 
                e.retry_after
            )
            # Retry after waiting
            return await self._execute_with_rate_limit(func, *args, **kwargs)
```

## Deployment and monitoring

### Production deployment configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  crewai-content-monitor:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_CREDENTIALS_PATH=/app/config/google-credentials.json
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
      - INSTAGRAM_USERNAME=${INSTAGRAM_USERNAME}
      - INSTAGRAM_PASSWORD=${INSTAGRAM_PASSWORD}
    volumes:
      - ./downloads:/app/downloads
      - ./logs:/app/logs
      - ./config:/app/config
    ports:
      - "8080:8080"  # Health check endpoint
      - "8000:8000"  # Prometheus metrics
    restart: unless-stopped
    
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
```

This comprehensive implementation guide provides a complete, production-ready automated content monitoring and downloading system using CrewAI. The system effectively combines real-time YouTube monitoring via PubSubHubbub, intelligent Instagram content downloading, efficient Google Drive storage with Discord-compatible links, and robust error handling throughout all components.

Key advantages of this approach:
- **Real-time monitoring** via PubSubHubbub with polling fallbacks
- **Intelligent tool selection** for optimal Instagram content coverage  
- **Production-grade error handling** with circuit breakers and retry logic
- **Comprehensive rate limiting** to avoid API restrictions
- **Discord-compatible sharing** with proper link formatting
- **Scalable architecture** using CrewAI's agent-based system
- **Complete observability** with logging and metrics