"""
YouTube Data API v3 client with quota accounting, rate limiting, and comprehensive features.

This client provides typed access to YouTube's Data API v3 with proper error handling,
quota management, exponential backoff, and support for all major YouTube features.
"""
from __future__ import annotations
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar
from platform import http_utils
from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_models import YouTubeCaption, YouTubeChannel, YouTubeComment, YouTubeLiveChatMessage, YouTubeQuotaUsage, YouTubeSearchResult, YouTubeVideo
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.creator_ops.auth.oauth_manager import YouTubeOAuthManager
logger = logging.getLogger(__name__)

class YouTubeClient:
    """
    YouTube Data API v3 client with comprehensive features.

    Features:
    - Quota accounting and management
    - Exponential backoff for rate limiting
    - Pagination support
    - Captions API integration
    - Live chat polling
    - Fixture mode for testing
    """
    BASE_URL = 'https://www.googleapis.com/youtube/v3'
    QUOTA_COSTS: ClassVar[dict[str, int]] = {'search': 100, 'videos': 1, 'channels': 1, 'playlists': 1, 'playlistItems': 1, 'comments': 1, 'commentThreads': 1, 'captions': 1, 'liveChat': 1, 'liveStreams': 1, 'liveBroadcasts': 1}

    def __init__(self, api_key: str | None=None, oauth_manager: YouTubeOAuthManager | None=None, config: CreatorOpsConfig | None=None, fixture_mode: bool=False) -> None:
        """Initialize YouTube client."""
        self.api_key = api_key
        self.oauth_manager = oauth_manager
        self.config = config or CreatorOpsConfig()
        self.fixture_mode = fixture_mode
        self.quota_usage = YouTubeQuotaUsage()
        self.last_request_time = 0.0
        self.min_request_interval = 0.1
        self.session = http_utils.requests.Session()
        retry_strategy = http_utils.requests.packages.urllib3.util.retry.Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = http_utils.requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {'Accept': 'application/json'}
        if self.oauth_manager:
            token_result = self.oauth_manager.get_valid_token()
            if token_result.success:
                headers['Authorization'] = f'Bearer {token_result.data['access_token']}'
        return headers

    def _get_auth_params(self) -> dict[str, str]:
        """Get authentication parameters."""
        params = {}
        if self.api_key and (not self.oauth_manager):
            params['key'] = self.api_key
        return params

    def _check_quota(self, operation: str) -> StepResult:
        """Check if quota is available for operation."""
        if self.fixture_mode:
            return StepResult.ok(data={'quota_available': True})
        cost = self.QUOTA_COSTS.get(operation, 1)
        return self.quota_usage.consume_quota(cost)

    def _rate_limit(self) -> None:
        """Apply rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: dict[str, Any] | None=None, operation: str='videos') -> StepResult:
        """Make authenticated request to YouTube API."""
        if self.fixture_mode:
            return self._get_fixture_response(endpoint, params or {})
        quota_result = self._check_quota(operation)
        if not quota_result.success:
            return quota_result
        self._rate_limit()
        url = f'{self.BASE_URL}/{endpoint}'
        request_params = self._get_auth_params()
        if params:
            request_params.update(params)
        headers = self._get_headers()
        try:
            response = http_utils.retrying_get(url, params=request_params, headers=headers, timeout=30, request_fn=self.session.get)
            response.raise_for_status()
            data = response.json()
            return StepResult.ok(**data)
        except http_utils.requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 60))
                logger.warning(f'Rate limited. Retrying after {retry_after} seconds')
                time.sleep(retry_after)
                return self._make_request(endpoint, params, operation)
            elif e.response.status_code == 403:
                error_data = e.response.json()
                error_message = error_data.get('error', {}).get('message', 'Forbidden')
                return StepResult.fail(f'YouTube API error: {error_message}')
            else:
                return StepResult.fail(f'HTTP error {e.response.status_code}: {e!s}')
        except http_utils.requests.exceptions.RequestException as e:
            return StepResult.fail(f'Request failed: {e!s}')
        except Exception as e:
            return StepResult.fail(f'Unexpected error: {e!s}')

    def _get_fixture_response(self, endpoint: str, params: dict[str, Any]) -> StepResult:
        """Get fixture response for testing."""
        try:
            fixture_file = f'fixtures/creator_ops/youtube_{endpoint.replace('/', '_')}.json'
            with open(fixture_file) as f:
                fixture_data = json.load(f)
            if 'part' in params:
                filtered_data = {'kind': fixture_data.get('kind'), 'etag': fixture_data.get('etag')}
                if 'items' in fixture_data:
                    filtered_items = []
                    for item in fixture_data['items']:
                        filtered_item = {}
                        for part in params['part'].split(','):
                            if part in item:
                                filtered_item[part] = item[part]
                        if filtered_item:
                            filtered_items.append(filtered_item)
                    filtered_data['items'] = filtered_items
                return StepResult.ok(data=filtered_data)
            return StepResult.ok(data=fixture_data)
        except FileNotFoundError:
            return StepResult.fail(f'Fixture file not found: {fixture_file}')
        except Exception as e:
            return StepResult.fail(f'Fixture error: {e!s}')

    def get_channel(self, channel_id: str, parts: str='snippet,statistics,status') -> StepResult:
        """Get channel information."""
        params = {'part': parts, 'id': channel_id}
        result = self._make_request('channels', params, 'channels')
        if not result.success:
            return result
        data = result.data
        if not data.get('items'):
            return StepResult.fail(f'Channel not found: {channel_id}')
        channel = YouTubeChannel.from_api_data(data['items'][0])
        return StepResult.ok(data=channel)

    def get_video(self, video_id: str, parts: str='snippet,statistics,status,contentDetails') -> StepResult:
        """Get video information."""
        params = {'part': parts, 'id': video_id}
        result = self._make_request('videos', params, 'videos')
        if not result.success:
            return result
        data = result.data
        if not data.get('items'):
            return StepResult.fail(f'Video not found: {video_id}')
        video = YouTubeVideo.from_api_data(data['items'][0])
        return StepResult.ok(data=video)

    def search_videos(self, query: str, max_results: int=25, order: str='relevance', published_after: datetime | None=None, published_before: datetime | None=None, channel_id: str | None=None, video_category_id: str | None=None, video_duration: str | None=None, video_definition: str | None=None, video_dimension: str | None=None, video_type: str | None=None) -> StepResult:
        """Search for videos."""
        params = {'part': 'snippet', 'q': query, 'type': 'video', 'maxResults': min(max_results, 50), 'order': order}
        if published_after:
            params['publishedAfter'] = published_after.isoformat() + 'Z'
        if published_before:
            params['publishedBefore'] = published_before.isoformat() + 'Z'
        if channel_id:
            params['channelId'] = channel_id
        if video_category_id:
            params['videoCategoryId'] = video_category_id
        if video_duration:
            params['videoDuration'] = video_duration
        if video_definition:
            params['videoDefinition'] = video_definition
        if video_dimension:
            params['videoDimension'] = video_dimension
        if video_type:
            params['videoType'] = video_type
        result = self._make_request('search', params, 'search')
        if not result.success:
            return result
        data = result.data
        search_results = [YouTubeSearchResult.from_api_data(item) for item in data.get('items', [])]
        return StepResult.ok(data={'results': search_results, 'next_page_token': data.get('nextPageToken'), 'total_results': data.get('pageInfo', {}).get('totalResults')})

    def get_channel_videos(self, channel_id: str, max_results: int=25, order: str='date', published_after: datetime | None=None, published_before: datetime | None=None) -> StepResult:
        """Get videos from a channel."""
        params = {'part': 'snippet', 'channelId': channel_id, 'type': 'video', 'maxResults': min(max_results, 50), 'order': order}
        if published_after:
            params['publishedAfter'] = published_after.isoformat() + 'Z'
        if published_before:
            params['publishedBefore'] = published_before.isoformat() + 'Z'
        result = self._make_request('search', params, 'search')
        if not result.success:
            return result
        data = result.data
        search_results = [YouTubeSearchResult.from_api_data(item) for item in data.get('items', [])]
        return StepResult.ok(data={'results': search_results, 'next_page_token': data.get('nextPageToken'), 'total_results': data.get('pageInfo', {}).get('totalResults')})

    def get_video_comments(self, video_id: str, max_results: int=100, order: str='time', page_token: str | None=None) -> StepResult:
        """Get comments for a video."""
        params = {'part': 'snippet', 'videoId': video_id, 'maxResults': min(max_results, 100), 'order': order}
        if page_token:
            params['pageToken'] = page_token
        result = self._make_request('commentThreads', params, 'commentThreads')
        if not result.success:
            return result
        data = result.data
        comments = [YouTubeComment.from_api_data(item) for item in data.get('items', [])]
        return StepResult.ok(data={'comments': comments, 'next_page_token': data.get('nextPageToken'), 'total_results': data.get('pageInfo', {}).get('totalResults')})

    def get_video_captions(self, video_id: str) -> StepResult:
        """Get captions for a video."""
        params = {'part': 'snippet', 'videoId': video_id}
        result = self._make_request('captions', params, 'captions')
        if not result.success:
            return result
        data = result.data
        captions = [YouTubeCaption.from_api_data(item) for item in data.get('items', [])]
        return StepResult.ok(data=captions)

    def download_caption(self, caption_id: str, language: str='en') -> StepResult:
        """Download caption content."""
        if self.fixture_mode:
            mock_content = f'Mock caption content for {caption_id} in {language}'
            return StepResult.ok(data={'content': mock_content})
        quota_result = self._check_quota('captions')
        if not quota_result.success:
            return quota_result
        self._rate_limit()
        url = f'{self.BASE_URL}/captions/{caption_id}'
        params = {'tfmt': 'srt', 'tlang': language}
        headers = self._get_headers()
        auth_params = self._get_auth_params()
        params.update(auth_params)
        try:
            response = http_utils.retrying_get(url, params=params, headers=headers, timeout=30, request_fn=self.session.get)
            response.raise_for_status()
            content = response.text
            return StepResult.ok(data={'content': content})
        except http_utils.requests.exceptions.RequestException as e:
            return StepResult.fail(f'Failed to download caption: {e!s}')

    def get_live_chat_messages(self, live_chat_id: str, max_results: int=200, page_token: str | None=None) -> StepResult:
        """Get live chat messages."""
        params = {'part': 'snippet,authorDetails', 'liveChatId': live_chat_id, 'maxResults': min(max_results, 200)}
        if page_token:
            params['pageToken'] = page_token
        result = self._make_request('liveChat/messages', params, 'liveChat')
        if not result.success:
            return result
        data = result.data
        messages = [YouTubeLiveChatMessage.from_api_data(item) for item in data.get('items', [])]
        return StepResult.ok(data={'messages': messages, 'next_page_token': data.get('nextPageToken'), 'polling_interval_millis': data.get('pollingIntervalMillis')})

    def get_live_stream_details(self, video_id: str) -> StepResult:
        """Get live stream details for a video."""
        video_result = self.get_video(video_id, 'snippet,liveStreamingDetails')
        if not video_result.success:
            return video_result
        video = video_result.data
        if video.live_broadcast_content != 'live':
            return StepResult.fail(f'Video {video_id} is not currently live')
        live_details = video.live_streaming_details
        if not live_details:
            return StepResult.fail(f'No live streaming details found for video {video_id}')
        return StepResult.ok(data=live_details)

    async def poll_live_chat(self, video_id: str, callback: callable, interval_seconds: int=5, max_duration_minutes: int=60) -> StepResult:
        """Poll live chat messages for a video."""
        stream_result = self.get_live_stream_details(video_id)
        if not stream_result.success:
            return stream_result
        live_details = stream_result.data
        live_chat_id = live_details.get('activeLiveChatId')
        if not live_chat_id:
            return StepResult.fail('No active live chat found')
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=max_duration_minutes)
        last_message_time = None
        try:
            while datetime.utcnow() < end_time:
                messages_result = self.get_live_chat_messages(live_chat_id)
                if not messages_result.success:
                    logger.error(f'Failed to get live chat messages: {messages_result.error}')
                    await asyncio.sleep(interval_seconds)
                    continue
                messages_data = messages_result.data
                messages = messages_data['messages']
                polling_interval = messages_data.get('polling_interval_millis', 5000)
                new_messages = []
                for message in messages:
                    if last_message_time is None or message.published_at > last_message_time:
                        new_messages.append(message)
                if messages:
                    last_message_time = max((msg.published_at for msg in messages if msg.published_at))
                if new_messages:
                    try:
                        await callback(new_messages)
                    except Exception as e:
                        logger.error(f'Callback error: {e!s}')
                await asyncio.sleep(polling_interval / 1000.0)
            return StepResult.ok(data={'status': 'completed', 'duration_minutes': max_duration_minutes})
        except Exception as e:
            return StepResult.fail(f'Live chat polling failed: {e!s}')

    def get_quota_usage(self) -> dict[str, Any]:
        """Get current quota usage."""
        return self.quota_usage.to_dict()

    def reset_quota(self) -> None:
        """Reset quota usage (for testing)."""
        self.quota_usage.reset_quota()

    def close(self) -> None:
        """Close the client and cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()