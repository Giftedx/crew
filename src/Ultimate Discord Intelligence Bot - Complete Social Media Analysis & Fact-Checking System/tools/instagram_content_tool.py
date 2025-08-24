from crewai_tools import BaseTool
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import os

class InstagramContentTool(BaseTool):
    name: str = "Instagram Content Tool"
    description: str = "Download Instagram stories and monitor for livestreams using instagrapi."

    def __init__(self):
        super().__init__()
        self.client = self._setup_instagrapi()

    def _setup_instagrapi(self):
        cl = Client()
        try:
            # It's recommended to use a session file to avoid logging in every time.
            # The session file will be created automatically after the first login.
            if os.path.exists("instagram_session.json"):
                cl.load_settings("instagram_session.json")
                cl.login("YOUR_INSTAGRAM_USERNAME", "YOUR_INSTAGRAM_PASSWORD")
            else:
                cl.login("YOUR_INSTAGRAM_USERNAME", "YOUR_INSTAGRAM_PASSWORD")
                cl.dump_settings("instagram_session.json")
        except LoginRequired:
            print("Login required. Please provide your Instagram credentials.")
        except Exception as e:
            print(f"An error occurred during Instagram login: {e}")
        return cl

    def _run(self, username: str) -> dict:
        """Download Instagram stories and monitor for livestreams"""
        stories = self.download_stories(username)
        livestreams = self.monitor_livestreams(username)
        
        return {
            "stories": stories,
            "livestreams": livestreams
        }

    def download_stories(self, username: str) -> dict:
        """Download Instagram stories using instagrapi"""
        try:
            user_id = self.client.user_id_from_username(username)
            stories = self.client.user_stories(user_id)
            
            stories_downloaded = []
            for story in stories:
                target_dir = f"F:/yt-auto/crewaiv2/CrewAI_Content_System/Downloads/Instagram/Stories/{username}"
                os.makedirs(target_dir, exist_ok=True)
                self.client.story_download(story.pk, folder=target_dir)
                
                stories_downloaded.append({
                    'story_id': story.pk,
                    'url': story.thumbnail_url,
                    'type': 'video' if story.media_type == 2 else 'photo',
                    'local_path': f"{target_dir}/{story.pk}.jpg" # instagrapi downloads stories as jpg and mp4
                })
            
            return {
                'status': 'success',
                'stories_count': len(stories_downloaded),
                'stories': stories_downloaded
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def monitor_livestreams(self, username: str) -> dict:
        """Monitor for livestreams using instagrapi"""
        try:
            user_id = self.client.user_id_from_username(username)
            user_info = self.client.user_info(user_id)
            
            if user_info.is_live:
                # instagrapi does not directly support downloading livestreams.
                # You would need to use a different tool for this, like PyInstaLive.
                # For now, we will just return a notification.
                return {
                    'status': 'live_detected',
                    'username': username,
                    'broadcast_id': user_info.broadcast_id
                }
            
            return {'status': 'not_live', 'username': username}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}