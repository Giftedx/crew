"""YouTube Data API v3 integration client."""
from __future__ import annotations
import logging
from typing import Any
import httpx
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class YouTubeClient:
    """YouTube Data API v3 client for creator operations."""

    def __init__(self, api_key: str | None=None, access_token: str | None=None):
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        self.headers = {'Content-Type': 'application/json'}
        if access_token:
            self.headers['Authorization'] = f'Bearer {access_token}'

    def _make_request(self, endpoint: str, params: dict[str, Any]) -> StepResult:
        """Make authenticated request to YouTube API."""
        try:
            if not self.access_token and self.api_key:
                params['key'] = self.api_key
            url = f'{self.base_url}/{endpoint}'

            async def _request():
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    return response.json()
            import asyncio
            data = asyncio.run(_request())
            return StepResult.ok(data=data)
        except httpx.HTTPError as e:
            logger.error(f'YouTube API request failed: {e}')
            return StepResult.fail(f'YouTube API request failed: {e!s}')
        except Exception as e:
            logger.error(f'Unexpected error in YouTube API request: {e}')
            return StepResult.fail(f'Unexpected error: {e!s}')

    def get_channel_info(self, channel_id: str) -> StepResult:
        """Get channel information."""
        params = {'part': 'snippet,statistics,contentDetails', 'id': channel_id}
        return self._make_request('channels', params)

    def get_channel_by_username(self, username: str) -> StepResult:
        """Get channel by username."""
        params = {'part': 'snippet,statistics,contentDetails', 'forUsername': username}
        return self._make_request('channels', params)

    def search_channels(self, query: str, max_results: int=10) -> StepResult:
        """Search for channels."""
        params = {'part': 'snippet', 'q': query, 'type': 'channel', 'maxResults': max_results}
        return self._make_request('search', params)

    def get_video_info(self, video_id: str) -> StepResult:
        """Get video information."""
        params = {'part': 'snippet,statistics,contentDetails,status', 'id': video_id}
        return self._make_request('videos', params)

    def search_videos(self, query: str, max_results: int=10, order: str='relevance') -> StepResult:
        """Search for videos."""
        params = {'part': 'snippet', 'q': query, 'type': 'video', 'maxResults': max_results, 'order': order}
        return self._make_request('search', params)

    def get_channel_videos(self, channel_id: str, max_results: int=10) -> StepResult:
        """Get videos from a channel."""
        params = {'part': 'snippet', 'channelId': channel_id, 'type': 'video', 'maxResults': max_results, 'order': 'date'}
        return self._make_request('search', params)

    def get_video_comments(self, video_id: str, max_results: int=20) -> StepResult:
        """Get video comments."""
        params = {'part': 'snippet', 'videoId': video_id, 'maxResults': max_results, 'order': 'time'}
        return self._make_request('commentThreads', params)

    def get_playlist_info(self, playlist_id: str) -> StepResult:
        """Get playlist information."""
        params = {'part': 'snippet,contentDetails', 'id': playlist_id}
        return self._make_request('playlists', params)

    def get_playlist_videos(self, playlist_id: str, max_results: int=10) -> StepResult:
        """Get videos in a playlist."""
        params = {'part': 'snippet,contentDetails', 'playlistId': playlist_id, 'maxResults': max_results}
        return self._make_request('playlistItems', params)

    def get_trending_videos(self, region_code: str='US', category_id: str | None=None) -> StepResult:
        """Get trending videos."""
        params = {'part': 'snippet,statistics,contentDetails', 'chart': 'mostPopular', 'regionCode': region_code, 'maxResults': 25}
        if category_id:
            params['videoCategoryId'] = category_id
        return self._make_request('videos', params)

    def get_video_categories(self, region_code: str='US') -> StepResult:
        """Get video categories."""
        params = {'part': 'snippet', 'regionCode': region_code}
        return self._make_request('videoCategories', params)

    def get_subscription_status(self, channel_id: str) -> StepResult:
        """Check if user is subscribed to a channel (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized('OAuth access token required for subscription check')
        params = {'part': 'snippet', 'forChannelId': channel_id, 'mine': True}
        return self._make_request('subscriptions', params)

    def get_user_subscriptions(self, max_results: int=10) -> StepResult:
        """Get user's subscriptions (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized('OAuth access token required for subscriptions')
        params = {'part': 'snippet,contentDetails', 'mine': True, 'maxResults': max_results}
        return self._make_request('subscriptions', params)

    def get_live_chat_messages(self, video_id: str, max_results: int=50) -> StepResult:
        """Get live chat messages (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized('OAuth access token required for live chat')
        params = {'part': 'snippet,authorDetails', 'liveChatId': video_id, 'maxResults': max_results}
        return self._make_request('liveChat/messages', params)

    def get_channel_analytics(self, channel_id: str, start_date: str, end_date: str) -> StepResult:
        """Get channel analytics (requires OAuth and YouTube Analytics API)."""
        if not self.access_token:
            return StepResult.unauthorized('OAuth access token required for analytics')
        return StepResult.fail('YouTube Analytics API not implemented')

    def extract_video_id(self, url: str) -> str | None:
        """Extract video ID from YouTube URL."""
        import re
        patterns = ['(?:youtube\\.com/watch\\?v=|youtu\\.be/|youtube\\.com/embed/)([^&\\n?#]+)', 'youtube\\.com/watch\\?.*v=([^&\\n?#]+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_channel_id(self, url: str) -> str | None:
        """Extract channel ID from YouTube URL."""
        import re
        patterns = ['youtube\\.com/channel/([^/&\\n?#]+)', 'youtube\\.com/c/([^/&\\n?#]+)', 'youtube\\.com/@([^/&\\n?#]+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def health_check(self) -> StepResult:
        """Perform health check on YouTube client."""
        try:
            result = self.get_video_categories()
            if result.success:
                return StepResult.ok(data={'service': 'youtube', 'status': 'healthy', 'api_key_configured': bool(self.api_key), 'access_token_configured': bool(self.access_token)})
            else:
                return StepResult.fail('YouTube API health check failed')
        except Exception as e:
            logger.error(f'YouTube client health check failed: {e}')
            return StepResult.fail(f'Health check failed: {e!s}')