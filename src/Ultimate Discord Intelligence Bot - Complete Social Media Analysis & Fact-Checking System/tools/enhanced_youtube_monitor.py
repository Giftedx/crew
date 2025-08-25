from flask import Flask, request
import xml.etree.ElementTree as ET
import requests
import json
import asyncio
import time
import logging
from typing import Dict, List, Optional
from crewai_tools import BaseTool
import subprocess
from functools import wraps
from datetime import datetime

# Enhanced Resilience System
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
        def decorator(func):
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
        def decorator(func):
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
                        logging.info(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                
                raise Exception(f"Max retries ({max_retries}) exceeded")
            
            return wrapper
        return decorator
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter"""
        import random
        base_wait = min(2 ** attempt, 64)  # Cap at 64 seconds
        jitter = random.uniform(0.5, 1.5)
        return base_wait * jitter

# Global resilience instance
resilience = SystemResilience()

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

# Global rate limiter
rate_limiter = RateLimitManager()

class YouTubeMonitor:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.subscriptions = {}
        self.fallback_poller = YouTubeFallbackPoller()
    
    async def add_channel(self, channel_id: str):
        success = await self.subscribe_channel(channel_id)
        
        if not success:
            logging.info(f"PubSubHubbub failed for {channel_id}, using fallback polling")
            self.fallback_poller.add_channel(channel_id)
        else:
            self.subscriptions[channel_id] = {
                'method': 'pubsubhubbub',
                'expires': time.time() + 432000
            }
    
    async def subscribe_channel(self, channel_id: str, max_retries: int = 3) -> bool:
        for attempt in range(max_retries):
            try:
                success = self._subscribe_to_channel(channel_id, self.webhook_url)
                if success:
                    return True
            except Exception as e:
                logging.error(f"Subscription attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return False
    
    def _subscribe_to_channel(self, channel_id: str, webhook_url: str) -> bool:
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

class YouTubeFallbackPoller:
    def __init__(self):
        self.channels = []
        self.last_checked = {}
    
    def add_channel(self, channel_id: str):
        if channel_id not in self.channels:
            self.channels.append(channel_id)

class EnhancedYouTubeDownloadTool(BaseTool):
    name: str = "Enhanced YouTube Download Tool"
    description: str = "Download YouTube videos with comprehensive error handling and optimal settings"
    
    @resilience.circuit_breaker('youtube_api')
    @resilience.retry_with_backoff(max_retries=5, strategy='exponential')
    def _run(self, video_url: str, quality: str = "1080p") -> str:
        """Download YouTube video using yt-dlp with enhanced CrewAI integration"""

        from ..settings import DOWNLOADS_DIR, YTDLP_CONFIG

        config_file = str(YTDLP_CONFIG)
        
        # Construct command with quality-specific settings
        command = [
            "yt-dlp",
            "--config-locations", config_file,
            "--print", "%(id)s|%(title)s|%(uploader)s|%(duration)s|%(filesize_approx)s",
            video_url
        ]
        
        return self._download_video_with_recovery(command, video_url)
    
    def _download_video_with_recovery(self, base_command: List[str], video_url: str) -> str:
        """Download with fallback strategies"""
        strategies = [
            self._download_with_standard_format,
            self._download_with_fallback_format,
            self._download_with_audio_only
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                logging.info(f"Attempting download strategy {i+1} for {video_url}")
                return strategy(base_command, video_url)
            except Exception as e:
                logging.warning(f"Strategy {i+1} failed: {e}")
                continue
        
        raise Exception("All download strategies failed")
    
    def _download_with_standard_format(self, command: List[str], video_url: str) -> str:
        """Standard download with optimal format"""
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=1800  # 30 minutes max
        )
        
        return self._parse_result(result, command)
    
    def _download_with_fallback_format(self, command: List[str], video_url: str) -> str:
        """Fallback with lower quality format"""
        fallback_command = command.copy()
        fallback_command.extend(["-f", "best[height<=720]/best"])
        
        result = subprocess.run(
            fallback_command,
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        return self._parse_result(result, fallback_command)
    
    def _download_with_audio_only(self, command: List[str], video_url: str) -> str:
        """Final fallback - audio only"""
        audio_command = command.copy()
        audio_command.extend(["-f", "bestaudio/best"])
        
        result = subprocess.run(
            audio_command,
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes for audio only
        )
        
        return self._parse_result(result, audio_command)
    
    def _parse_result(self, result, command: List[str]) -> str:
        """Parse subprocess result and return formatted response"""
        if result.returncode == 0:
            output_lines = result.stdout.strip().split('\n')
            if output_lines:
                download_info = output_lines[-1].split('|')
                
                if len(download_info) >= 5:
                    return json.dumps({
                        'status': 'success',
                        'video_id': download_info[0],
                        'title': download_info[1],
                        'uploader': download_info[2],
                        'duration': download_info[3],
                        'file_size': download_info[4],
                        'local_path': str(DOWNLOADS_DIR / 'YouTube' / download_info[2]),
                        'download_command': ' '.join(command)
                    })
            
            return json.dumps({
                'status': 'success',
                'message': 'Download completed but metadata parsing failed',
                'output': result.stdout
            })
        else:
            return json.dumps({
                'status': 'error',
                'error': result.stderr,
                'command': ' '.join(command)
            })

# Flask Webhook Server
app = Flask(__name__)

@app.route('/youtube-webhook', methods=['GET', 'POST'])
def youtube_webhook():
    if request.method == 'GET':
        # Handle subscription verification
        challenge = request.args.get('hub.challenge')
        mode = request.args.get('hub.mode')
        
        if challenge and mode == 'subscribe':
            logging.info(f"Verified YouTube subscription")
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
            
            # Trigger download workflow asynchronously
            video_data = {
                'video_id': video_id,
                'channel_id': channel_id,
                'title': title,
                'published': published,
                'url': f'https://www.youtube.com/watch?v={video_id}'
            }
            
            # In a real implementation, trigger CrewAI workflow here
            asyncio.create_task(trigger_video_processing(video_data))
        
        return 'OK', 200

async def trigger_video_processing(video_data: Dict):
    """Trigger CrewAI workflow for new video"""
    try:
        logging.info(f"Processing new video: {video_data['title']}")
        # Here you would trigger your CrewAI crew with the video data
        # crew = UltimateDiscordIntelligenceBotCompleteSocialMediaAnalysisFactCheckingSystemCrew()
        # result = crew.crew().kickoff(inputs={'new_video': video_data})
    except Exception as e:
        logging.error(f"Error processing video {video_data.get('video_id')}: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Configure webhook URL for your environment
    webhook_url = "https://your-domain.com/youtube-webhook"
    
    # Initialize YouTube monitor
    monitor = YouTubeMonitor(webhook_url)
    
    # Start Flask webhook server
    app.run(host='0.0.0.0', port=8080, debug=False)