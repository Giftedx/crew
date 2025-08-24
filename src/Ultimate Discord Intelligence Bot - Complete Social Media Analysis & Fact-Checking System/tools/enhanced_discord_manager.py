import requests
import json
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
from crewai_tools import BaseTool
import mimetypes
import os
from dataclasses import dataclass
import re

@dataclass
class DiscordChannel:
    """Discord channel configuration"""
    id: str
    name: str
    webhook_url: Optional[str] = None
    max_file_size: int = 100 * 1024 * 1024  # 100MB default
    allowed_types: List[str] = None

@dataclass
class ContentItem:
    """Content item for Discord posting"""
    title: str
    platform: str
    creator: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    drive_links: Optional[Dict] = None
    metadata: Optional[Dict] = None
    thumbnail_url: Optional[str] = None

class DiscordRateLimiter:
    """Discord-specific rate limiter with webhook and API considerations"""
    
    def __init__(self):
        self.webhook_limits = {}  # Per webhook rate limiting
        self.global_limits = {
            'messages_per_second': 50,
            'requests_per_second': 10,
            'last_request': 0
        }
    
    async def check_webhook_limit(self, webhook_url: str) -> bool:
        """Check if webhook is within rate limits"""
        current_time = time.time()
        
        if webhook_url not in self.webhook_limits:
            self.webhook_limits[webhook_url] = {
                'requests': [],
                'last_429': 0
            }
        
        webhook_data = self.webhook_limits[webhook_url]
        
        # Clean old requests (last 10 seconds)
        webhook_data['requests'] = [
            req_time for req_time in webhook_data['requests']
            if current_time - req_time < 10
        ]
        
        # Check if we're still rate limited from a previous 429
        if current_time - webhook_data['last_429'] < 60:
            return False
        
        # Check current rate (5 requests per 2 seconds per webhook)
        if len(webhook_data['requests']) >= 5:
            return False
        
        return True
    
    async def record_request(self, webhook_url: str, was_rate_limited: bool = False):
        """Record a request and handle rate limiting"""
        current_time = time.time()
        
        if webhook_url not in self.webhook_limits:
            self.webhook_limits[webhook_url] = {
                'requests': [],
                'last_429': 0
            }
        
        webhook_data = self.webhook_limits[webhook_url]
        webhook_data['requests'].append(current_time)
        
        if was_rate_limited:
            webhook_data['last_429'] = current_time
    
    async def wait_if_needed(self, webhook_url: str):
        """Wait if rate limited"""
        while not await self.check_webhook_limit(webhook_url):
            await asyncio.sleep(1)

class EnhancedDiscordManager:
    """Enhanced Discord manager with intelligent posting strategies"""
    
    def __init__(self, channels_config: List[DiscordChannel]):
        self.channels = {ch.name: ch for ch in channels_config}
        self.rate_limiter = DiscordRateLimiter()
        self.posting_strategies = {
            'auto': self._auto_posting_strategy,
            'embed_only': self._embed_only_strategy,
            'file_only': self._file_upload_strategy,
            'hybrid': self._hybrid_strategy
        }
    
    async def post_content(self, content: ContentItem, channel_name: str, strategy: str = 'auto') -> Dict:
        """Post content to Discord using specified strategy"""
        
        if channel_name not in self.channels:
            return {
                'status': 'error',
                'error': f'Channel {channel_name} not found',
                'available_channels': list(self.channels.keys())
            }
        
        channel = self.channels[channel_name]
        
        if not channel.webhook_url:
            return {
                'status': 'error',
                'error': f'No webhook URL configured for channel {channel_name}'
            }
        
        # Wait for rate limits
        await self.rate_limiter.wait_if_needed(channel.webhook_url)
        
        # Select and execute posting strategy
        strategy_func = self.posting_strategies.get(strategy, self._auto_posting_strategy)
        
        try:
            result = await strategy_func(content, channel)
            
            # Record the request
            was_rate_limited = result.get('status') == 'rate_limited'
            await self.rate_limiter.record_request(channel.webhook_url, was_rate_limited)
            
            return result
            
        except Exception as e:
            logging.error(f"Error posting to {channel_name}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'channel': channel_name,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _auto_posting_strategy(self, content: ContentItem, channel: DiscordChannel) -> Dict:
        """Automatically choose the best posting strategy based on content"""
        
        # Check if we have a local file and its size
        if content.file_path and Path(content.file_path).exists():
            file_size = Path(content.file_path).stat().st_size
            
            # If file is small enough and supported, try direct upload
            if file_size <= channel.max_file_size:
                mime_type, _ = mimetypes.guess_type(content.file_path)
                if mime_type and (mime_type.startswith('video/') or mime_type.startswith('image/')):
                    logging.info(f"Using file upload strategy for {content.title}")
                    return await self._file_upload_strategy(content, channel)
        
        # Default to embed strategy if we have Drive links
        if content.drive_links:
            logging.info(f"Using embed strategy for {content.title}")
            return await self._embed_only_strategy(content, channel)
        
        # Fallback to text-only post
        logging.info(f"Using text-only strategy for {content.title}")
        return await self._text_only_strategy(content, channel)
    
    async def _embed_only_strategy(self, content: ContentItem, channel: DiscordChannel) -> Dict:
        """Post using rich embeds with links"""
        
        embed = self._create_rich_embed(content)
        
        payload = {
            "username": "CrewAI Content Monitor",
            "avatar_url": "https://i.imgur.com/your-bot-avatar.png",
            "embeds": [embed],
            "allowed_mentions": {"parse": []}  # Prevent unwanted mentions
        }
        
        return await self._send_webhook(channel.webhook_url, payload)
    
    async def _file_upload_strategy(self, content: ContentItem, channel: DiscordChannel) -> Dict:
        """Post with direct file upload"""
        
        if not content.file_path or not Path(content.file_path).exists():
            return await self._embed_only_strategy(content, channel)
        
        file_path = Path(content.file_path)
        
        # Create message content
        message_content = self._create_file_message_content(content)
        
        # Prepare files for upload
        files = {
            'file': (
                file_path.name,
                open(file_path, 'rb'),
                mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
            ),
            'payload_json': (
                None,
                json.dumps({
                    "content": message_content,
                    "username": "CrewAI Content Monitor",
                    "avatar_url": "https://i.imgur.com/your-bot-avatar.png"
                })
            )
        }
        
        try:
            response = requests.post(
                channel.webhook_url,
                files=files,
                timeout=300  # 5 minutes for file uploads
            )
            
            return self._handle_response(response)
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
        finally:
            # Ensure file handle is closed
            files['file'][1].close()
    
    async def _hybrid_strategy(self, content: ContentItem, channel: DiscordChannel) -> Dict:
        """Use both file upload and embed for maximum compatibility"""
        
        # First try file upload
        file_result = await self._file_upload_strategy(content, channel)
        
        if file_result.get('status') == 'success':
            # Add a follow-up embed with additional information
            await asyncio.sleep(1)  # Small delay between messages
            
            embed = self._create_supplementary_embed(content)
            payload = {
                "embeds": [embed],
                "username": "CrewAI Content Monitor"
            }
            
            embed_result = await self._send_webhook(channel.webhook_url, payload)
            
            return {
                'status': 'success',
                'strategy': 'hybrid',
                'file_upload': file_result,
                'embed': embed_result
            }
        else:
            # Fallback to embed only
            return await self._embed_only_strategy(content, channel)
    
    async def _text_only_strategy(self, content: ContentItem, channel: DiscordChannel) -> Dict:
        """Simple text-only post as fallback"""
        
        message = self._create_text_message(content)
        
        payload = {
            "content": message,
            "username": "CrewAI Content Monitor",
            "avatar_url": "https://i.imgur.com/your-bot-avatar.png"
        }
        
        return await self._send_webhook(channel.webhook_url, payload)
    
    def _create_rich_embed(self, content: ContentItem) -> Dict:
        """Create a rich embed for content"""
        
        # Platform-specific colors
        colors = {
            'youtube': 0xFF0000,
            'instagram': 0xE4405F,
            'twitter': 0x1DA1F2,
            'tiktok': 0x000000,
            'default': 0x7289DA
        }
        
        embed = {
            "title": self._truncate_text(content.title, 256),
            "color": colors.get(content.platform.lower(), colors['default']),
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": f"CrewAI Monitor • {content.platform.title()}",
                "icon_url": self._get_platform_icon(content.platform)
            },
            "author": {
                "name": content.creator,
                "icon_url": self._get_creator_avatar(content.creator)
            }
        }
        
        # Add description
        description_parts = [
            f"**🎬 Creator:** {content.creator}",
            f"**📱 Platform:** {content.platform.title()}"
        ]
        
        if content.metadata:
            if content.metadata.get('duration'):
                description_parts.append(f"**⏱️ Duration:** {content.metadata['duration']}")
            if content.metadata.get('upload_date'):
                description_parts.append(f"**📅 Uploaded:** {content.metadata['upload_date']}")
            if content.metadata.get('file_size'):
                size_mb = int(content.metadata['file_size']) / (1024 * 1024)
                description_parts.append(f"**💾 Size:** {size_mb:.1f} MB")
        
        embed["description"] = "\n".join(description_parts)
        
        # Add thumbnail
        if content.thumbnail_url:
            embed["thumbnail"] = {"url": content.thumbnail_url}
        elif content.drive_links and content.drive_links.get('thumbnail'):
            embed["thumbnail"] = {"url": content.drive_links['thumbnail']}
        
        # Add fields for actions
        fields = []
        
        if content.drive_links:
            if content.drive_links.get('preview_link'):
                fields.append({
                    "name": "🎥 Watch Online",
                    "value": f"[Google Drive Preview]({content.drive_links['preview_link']})",
                    "inline": True
                })
            
            if content.drive_links.get('direct_link'):
                fields.append({
                    "name": "💾 Download",
                    "value": f"[Direct Download]({content.drive_links['direct_link']})",
                    "inline": True
                })
        
        if fields:
            embed["fields"] = fields
        
        return embed
    
    def _create_supplementary_embed(self, content: ContentItem) -> Dict:
        """Create a supplementary embed with additional metadata"""
        
        embed = {
            "title": "📊 Content Analysis",
            "color": 0x36393F,
            "timestamp": datetime.now().isoformat()
        }
        
        fields = []
        
        if content.metadata:
            # Add relevant metadata fields
            metadata_mapping = {
                'video_id': '🆔 Video ID',
                'view_count': '👀 Views',
                'like_count': '👍 Likes',
                'comment_count': '💬 Comments',
                'tags': '🏷️ Tags',
                'category': '📂 Category'
            }
            
            for key, label in metadata_mapping.items():
                if key in content.metadata and content.metadata[key]:
                    value = content.metadata[key]
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value[:5])  # Limit to 5 items
                    fields.append({
                        "name": label,
                        "value": str(value)[:1024],  # Discord field value limit
                        "inline": True
                    })
        
        if fields:
            embed["fields"] = fields
        else:
            embed["description"] = "Additional analysis data will be available soon."
        
        return embed
    
    def _create_file_message_content(self, content: ContentItem) -> str:
        """Create message content for file uploads"""
        
        parts = [
            f"🎥 **{content.title}**",
            f"📱 **Platform:** {content.platform.title()}",
            f"👤 **Creator:** {content.creator}"
        ]
        
        if content.metadata:
            if content.metadata.get('duration'):
                parts.append(f"⏱️ **Duration:** {content.metadata['duration']}")
            if content.metadata.get('upload_date'):
                parts.append(f"📅 **Date:** {content.metadata['upload_date']}")
        
        return "\n".join(parts)
    
    def _create_text_message(self, content: ContentItem) -> str:
        """Create a simple text message"""
        
        return (
            f"🎥 **New Content:** {content.title}\n"
            f"👤 **Creator:** {content.creator}\n"
            f"📱 **Platform:** {content.platform.title()}\n"
            f"🕒 **Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    async def _send_webhook(self, webhook_url: str, payload: Dict) -> Dict:
        """Send webhook with proper error handling"""
        
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            return {'status': 'error', 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'error': str(e)}
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle Discord webhook response"""
        
        if response.status_code == 204:
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
        elif response.status_code == 429:
            # Rate limited
            retry_after = 60  # Default to 60 seconds
            
            try:
                error_data = response.json()
                retry_after = error_data.get('retry_after', 60)
            except:
                pass
            
            return {
                'status': 'rate_limited',
                'retry_after': retry_after,
                'message': 'Rate limited by Discord'
            }
        else:
            error_text = response.text
            try:
                error_data = response.json()
                error_text = error_data.get('message', error_text)
            except:
                pass
            
            return {
                'status': 'error',
                'status_code': response.status_code,
                'error': error_text
            }
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to Discord limits"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _get_platform_icon(self, platform: str) -> str:
        """Get platform-specific icon URL"""
        icons = {
            'youtube': 'https://i.imgur.com/youtube-icon.png',
            'instagram': 'https://i.imgur.com/instagram-icon.png',
            'twitter': 'https://i.imgur.com/twitter-icon.png',
            'tiktok': 'https://i.imgur.com/tiktok-icon.png'
        }
        return icons.get(platform.lower(), 'https://i.imgur.com/default-icon.png')
    
    def _get_creator_avatar(self, creator: str) -> str:
        """Get creator avatar URL (placeholder implementation)"""
        # In a real implementation, you might cache avatar URLs
        return f"https://api.dicebear.com/7.x/initials/svg?seed={creator}"
    
    async def post_system_message(self, message: str, channel_name: str, level: str = 'info') -> Dict:
        """Post system messages (errors, alerts, etc.)"""
        
        if channel_name not in self.channels:
            return {'status': 'error', 'error': 'Channel not found'}
        
        channel = self.channels[channel_name]
        
        # Level-specific formatting
        level_config = {
            'info': {'color': 0x36393F, 'emoji': 'ℹ️'},
            'warning': {'color': 0xFFCC4D, 'emoji': '⚠️'},
            'error': {'color': 0xF04747, 'emoji': '❌'},
            'success': {'color': 0x43B581, 'emoji': '✅'}
        }
        
        config = level_config.get(level, level_config['info'])
        
        embed = {
            "title": f"{config['emoji']} System {level.title()}",
            "description": message,
            "color": config['color'],
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "CrewAI System Monitor"
            }
        }
        
        payload = {
            "username": "CrewAI System",
            "embeds": [embed]
        }
        
        await self.rate_limiter.wait_if_needed(channel.webhook_url)
        result = await self._send_webhook(channel.webhook_url, payload)
        await self.rate_limiter.record_request(channel.webhook_url, result.get('status') == 'rate_limited')
        
        return result

class EnhancedDiscordBotTool(BaseTool):
    """Enhanced Discord Bot Tool with intelligent posting"""
    
    name: str = "Enhanced Discord Bot Tool"
    description: str = "Post content to Discord with intelligent strategy selection and comprehensive error handling"
    
    def __init__(self, channels_config: List[Dict]):
        super().__init__()
        # Convert dict config to DiscordChannel objects
        channels = [
            DiscordChannel(
                id=ch.get('id', ''),
                name=ch['name'],
                webhook_url=ch.get('webhook_url'),
                max_file_size=ch.get('max_file_size', 100 * 1024 * 1024),
                allowed_types=ch.get('allowed_types', ['video/*', 'image/*'])
            )
            for ch in channels_config
        ]
        self.discord_manager = EnhancedDiscordManager(channels)
    
    def _run(self, content_data: Dict, channel_name: str, strategy: str = 'auto') -> str:
        """Post content to Discord using specified strategy"""
        
        # Convert input data to ContentItem
        content = ContentItem(
            title=content_data.get('title', 'New Content'),
            platform=content_data.get('platform', 'unknown'),
            creator=content_data.get('creator', 'Unknown Creator'),
            file_path=content_data.get('file_path'),
            file_size=content_data.get('file_size'),
            drive_links=content_data.get('drive_links'),
            metadata=content_data.get('metadata'),
            thumbnail_url=content_data.get('thumbnail_url')
        )
        
        # Run async posting
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self.discord_manager.post_content(content, channel_name, strategy)
        )
        
        return json.dumps(result, indent=2)

# Configuration helper
def load_discord_channels_config(config_path: str = None) -> List[Dict]:
    """Load Discord channels configuration from file"""
    
    if config_path is None:
        config_path = "F:/yt-auto/crewaiv2/CrewAI_Content_System/Config/discord_channels.yaml"
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('channels', [])
    except Exception as e:
        logging.warning(f"Could not load Discord config from {config_path}: {e}")
        # Return default configuration
        return [
            {
                'name': 'general',
                'id': '123456789',
                'webhook_url': os.getenv('DISCORD_WEBHOOK_URL'),
                'max_file_size': 100 * 1024 * 1024
            }
        ]

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    channels_config = load_discord_channels_config()
    
    # Create Discord manager
    discord_manager = EnhancedDiscordManager([
        DiscordChannel(**ch) for ch in channels_config
    ])
    
    # Example content
    content = ContentItem(
        title="Test Video",
        platform="youtube",
        creator="Test Creator",
        metadata={
            'duration': '10:30',
            'upload_date': '2024-01-15',
            'file_size': 50000000
        },
        drive_links={
            'preview_link': 'https://drive.google.com/file/d/example/preview',
            'direct_link': 'https://drive.google.com/uc?id=example'
        }
    )
    
    # Post content
    async def test_post():
        result = await discord_manager.post_content(content, 'general', 'auto')
        print(json.dumps(result, indent=2))
    
    asyncio.run(test_post())