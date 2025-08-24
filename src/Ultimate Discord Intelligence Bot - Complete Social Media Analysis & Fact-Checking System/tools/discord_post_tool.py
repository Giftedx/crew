import requests
import json
from pathlib import Path
from crewai_tools import BaseTool
from datetime import datetime

class DiscordPostTool(BaseTool):
    name: str = "Discord Post Tool"
    description: str = "Post content notifications to Discord with proper formatting"
    
    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url

    def _run(self, content_data: dict, drive_links: dict) -> dict:
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
