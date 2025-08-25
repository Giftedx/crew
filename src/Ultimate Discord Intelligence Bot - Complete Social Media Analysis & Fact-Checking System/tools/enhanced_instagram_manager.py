import os
import json
import subprocess
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests
import time

from crewai_tools import BaseTool
from ..settings import DOWNLOADS_DIR, CONFIG_DIR

class InstagramContentManager:
    """
    Hybrid Instagram content management system combining multiple tools
    for comprehensive coverage of stories, posts, and livestreams.
    """
    
    def __init__(self):
        self.instaloader_client = self._setup_instaloader()
        self.rocketapi_client = self._setup_rocketapi()
        self.pyinstalive_monitor = self._setup_livestream_monitor()
        self.download_directory = DOWNLOADS_DIR / "Instagram"
        self.download_directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_instaloader(self):
        """Setup Instaloader client with optimized configuration"""
        try:
            import instaloader
            L = instaloader.Instaloader(
                download_pictures=True,
                download_videos=True,
                download_video_thumbnails=True,
                download_geotags=True,
                download_comments=True,
                compress_json=False,
                save_metadata=True,
                max_connection_attempts=3,
                request_timeout=30.0
            )
            
            # Load session to avoid repeated logins
            session_file = str(CONFIG_DIR / "instagram_session")
            try:
                L.load_session_from_file('instagram_username', session_file)
                logging.info("Loaded Instagram session from file")
            except:
                # In production, use environment variables for credentials
                username = os.getenv('INSTAGRAM_USERNAME')
                password = os.getenv('INSTAGRAM_PASSWORD')
                if username and password:
                    L.login(username, password)
                    L.save_session_to_file(session_file)
                    logging.info("Created new Instagram session")
                else:
                    logging.warning("No Instagram credentials provided")
            
            return L
        except ImportError:
            logging.error("Instaloader not available. Install with: pip install instaloader")
            return None
        except Exception as e:
            logging.error(f"Failed to setup Instaloader: {e}")
            return None
    
    def _setup_rocketapi(self):
        """Setup RocketAPI client for enhanced Instagram access"""
        try:
            api_key = os.getenv('ROCKET_API_KEY')
            if api_key:
                return RocketAPIClient(api_key)
            else:
                logging.info("RocketAPI key not provided, using free tier limitations")
                return None
        except Exception as e:
            logging.error(f"Failed to setup RocketAPI: {e}")
            return None
    
    def _setup_livestream_monitor(self):
        """Setup PyInstaLive for livestream recording"""
        try:
            # Check if PyInstaLive is available
            result = subprocess.run(['pyinstalive', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True
            return False
        except FileNotFoundError:
            logging.info("PyInstaLive not available. Install from: https://github.com/dvingerh/PyInstaLive")
            return False
    
    async def monitor_account(self, username: str) -> Dict:
        """Comprehensive monitoring of an Instagram account"""
        results = {
            'username': username,
            'timestamp': datetime.now().isoformat(),
            'stories': [],
            'posts': [],
            'livestream': None,
            'errors': []
        }
        
        # Check for stories
        try:
            stories_result = await self.download_stories(username)
            results['stories'] = stories_result.get('stories', [])
        except Exception as e:
            results['errors'].append(f"Stories error: {str(e)}")
            logging.error(f"Error downloading stories for {username}: {e}")
        
        # Check for recent posts
        try:
            posts_result = await self.download_recent_posts(username)
            results['posts'] = posts_result.get('posts', [])
        except Exception as e:
            results['errors'].append(f"Posts error: {str(e)}")
            logging.error(f"Error downloading posts for {username}: {e}")
        
        # Check for livestream
        try:
            livestream_result = await self.monitor_livestreams(username)
            results['livestream'] = livestream_result
        except Exception as e:
            results['errors'].append(f"Livestream error: {str(e)}")
            logging.error(f"Error monitoring livestream for {username}: {e}")
        
        return results
    
    async def download_stories(self, username: str) -> Dict:
        """Download Instagram stories using Instaloader"""
        if not self.instaloader_client:
            return {'status': 'error', 'error': 'Instaloader not available'}
        
        try:
            import instaloader
            profile = instaloader.Profile.from_username(
                self.instaloader_client.context, username
            )
            
            stories_downloaded = []
            story_dir = self.download_directory / "Stories" / username
            story_dir.mkdir(parents=True, exist_ok=True)
            
            for story in profile.get_stories():
                for item in story.get_items():
                    try:
                        # Download with organized naming
                        self.instaloader_client.download_storyitem(
                            item, str(story_dir)
                        )
                        
                        # Create metadata
                        story_metadata = {
                            'story_id': item.mediaid,
                            'url': item.url,
                            'type': 'video' if item.is_video else 'photo',
                            'expiring': str(item.expiring_local),
                            'local_path': str(story_dir / f"{item.mediaid}"),
                            'downloaded_at': datetime.now().isoformat(),
                            'username': username,
                            'caption': getattr(item, 'caption', ''),
                            'view_count': getattr(item, 'view_count', 0)
                        }
                        
                        stories_downloaded.append(story_metadata)
                        
                        # Save individual metadata
                        metadata_file = story_dir / f"{item.mediaid}_metadata.json"
                        with open(metadata_file, 'w') as f:
                            json.dump(story_metadata, f, indent=2)
                        
                        logging.info(f"Downloaded story {item.mediaid} for {username}")
                        
                    except Exception as e:
                        logging.error(f"Error downloading story item {item.mediaid}: {e}")
                        continue
            
            return {
                'status': 'success',
                'stories_count': len(stories_downloaded),
                'stories': stories_downloaded,
                'download_path': str(story_dir)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def download_recent_posts(self, username: str, max_posts: int = 10) -> Dict:
        """Download recent Instagram posts"""
        if not self.instaloader_client:
            return {'status': 'error', 'error': 'Instaloader not available'}
        
        try:
            import instaloader
            profile = instaloader.Profile.from_username(
                self.instaloader_client.context, username
            )
            
            posts_downloaded = []
            posts_dir = self.download_directory / "Posts" / username
            posts_dir.mkdir(parents=True, exist_ok=True)
            
            for i, post in enumerate(profile.get_posts()):
                if i >= max_posts:
                    break
                
                try:
                    # Download post
                    self.instaloader_client.download_post(post, str(posts_dir))
                    
                    # Create metadata
                    post_metadata = {
                        'post_id': post.shortcode,
                        'url': f"https://www.instagram.com/p/{post.shortcode}/",
                        'type': 'video' if post.is_video else 'photo',
                        'caption': post.caption or '',
                        'likes': post.likes,
                        'comments': post.comments,
                        'date': post.date.isoformat(),
                        'local_path': str(posts_dir / post.shortcode),
                        'downloaded_at': datetime.now().isoformat(),
                        'username': username,
                        'tagged_users': [str(user) for user in post.tagged_users]
                    }
                    
                    posts_downloaded.append(post_metadata)
                    
                    # Save individual metadata
                    metadata_file = posts_dir / f"{post.shortcode}_metadata.json"
                    with open(metadata_file, 'w') as f:
                        json.dump(post_metadata, f, indent=2)
                    
                    logging.info(f"Downloaded post {post.shortcode} for {username}")
                    
                except Exception as e:
                    logging.error(f"Error downloading post {post.shortcode}: {e}")
                    continue
            
            return {
                'status': 'success',
                'posts_count': len(posts_downloaded),
                'posts': posts_downloaded,
                'download_path': str(posts_dir)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def monitor_livestreams(self, username: str) -> Dict:
        """Monitor for livestreams using RocketAPI + PyInstaLive"""
        try:
            # First check if user is live using RocketAPI (if available)
            if self.rocketapi_client:
                live_status = await self.rocketapi_client.get_user_live(username)
                
                if live_status.get('is_live'):
                    return await self._start_livestream_recording(username, live_status)
            
            # Fallback to basic check using Instaloader
            if self.instaloader_client:
                try:
                    import instaloader
                    profile = instaloader.Profile.from_username(
                        self.instaloader_client.context, username
                    )
                    
                    # Check if profile indicates live status (limited capability)
                    if hasattr(profile, 'is_live') and profile.is_live:
                        return await self._start_livestream_recording(username, {'is_live': True})
                    
                except Exception as e:
                    logging.error(f"Error checking livestream status with Instaloader: {e}")
            
            return {'status': 'not_live', 'username': username}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def _start_livestream_recording(self, username: str, live_status: Dict) -> Dict:
        """Start recording livestream using PyInstaLive"""
        if not self.pyinstalive_monitor:
            return {
                'status': 'live_detected_no_recorder',
                'username': username,
                'message': 'Livestream detected but PyInstaLive not available'
            }
        
        try:
            lives_dir = self.download_directory / "Lives" / username
            lives_dir.mkdir(parents=True, exist_ok=True)
            
            # Start PyInstaLive recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = lives_dir / f"{timestamp}_live"
            
            cmd = [
                'pyinstalive',
                '-d', username,
                '--output', str(output_path),
                '--log', str(lives_dir / f"{timestamp}_live.log")
            ]
            
            # Start recording in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Save process info for monitoring
            process_info = {
                'pid': process.pid,
                'command': ' '.join(cmd),
                'started_at': datetime.now().isoformat(),
                'output_path': str(output_path)
            }
            
            process_file = lives_dir / f"{timestamp}_process.json"
            with open(process_file, 'w') as f:
                json.dump(process_info, f, indent=2)
            
            return {
                'status': 'live_detected',
                'username': username,
                'recording_started': True,
                'broadcast_id': live_status.get('broadcast_id'),
                'process_pid': process.pid,
                'output_path': str(output_path),
                'started_at': process_info['started_at']
            }
            
        except Exception as e:
            return {
                'status': 'live_detected_error',
                'username': username,
                'error': str(e)
            }

class RocketAPIClient:
    """RocketAPI client for enhanced Instagram access"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.rocket-api.com/instagram"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    async def get_user_live(self, username: str) -> Dict:
        """Check if user is currently live"""
        try:
            response = self.session.get(
                f"{self.base_url}/user/{username}/live",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'is_live': data.get('is_live', False),
                    'broadcast_id': data.get('broadcast_id'),
                    'viewer_count': data.get('viewer_count', 0),
                    'started_at': data.get('started_at')
                }
            else:
                logging.error(f"RocketAPI error: {response.status_code} - {response.text}")
                return {'is_live': False, 'error': 'API request failed'}
                
        except Exception as e:
            logging.error(f"RocketAPI request error: {e}")
            return {'is_live': False, 'error': str(e)}

class EnhancedInstagramContentTool(BaseTool):
    """Enhanced Instagram Content Tool with hybrid monitoring approach"""
    
    name: str = "Enhanced Instagram Content Tool"
    description: str = "Monitor and download Instagram stories, posts, and livestreams with comprehensive coverage"
    
    def __init__(self):
        super().__init__()
        self.content_manager = InstagramContentManager()
    
    async def _run(self, username: str, content_types: List[str] = None) -> str:
        """Monitor Instagram account for specified content types"""
        
        if content_types is None:
            content_types = ['stories', 'posts', 'livestream']
        
        try:
            # Apply rate limiting
            can_proceed, wait_time = await rate_limiter.check_rate_limit('instagram_requests')
            if not can_proceed and wait_time:
                await asyncio.sleep(wait_time)
            
            # Monitor account
            results = await self.content_manager.monitor_account(username)
            
            # Record successful request
            await rate_limiter.record_request('instagram_requests')
            
            # Filter results based on requested content types
            filtered_results = {
                'username': username,
                'timestamp': results['timestamp'],
                'errors': results['errors']
            }
            
            if 'stories' in content_types:
                filtered_results['stories'] = results['stories']
            if 'posts' in content_types:
                filtered_results['posts'] = results['posts']
            if 'livestream' in content_types:
                filtered_results['livestream'] = results['livestream']
            
            return json.dumps(filtered_results, indent=2)
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'username': username,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return json.dumps(error_result, indent=2)

# Standalone monitoring function for scheduled execution
async def monitor_instagram_accounts(accounts: List[str]) -> Dict:
    """Monitor multiple Instagram accounts"""
    manager = InstagramContentManager()
    results = {}
    
    for account in accounts:
        try:
            logging.info(f"Monitoring Instagram account: {account}")
            account_results = await manager.monitor_account(account)
            results[account] = account_results
            
            # Add delay between accounts to respect rate limits
            await asyncio.sleep(2)
            
        except Exception as e:
            logging.error(f"Error monitoring account {account}: {e}")
            results[account] = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    return results

if __name__ == "__main__":
    # Example usage
    async def main():
        accounts = ['example_username']  # Replace with actual usernames
        results = await monitor_instagram_accounts(accounts)
        print(json.dumps(results, indent=2))
    
    asyncio.run(main())