"""Instagram Graph API integration client."""
from __future__ import annotations
import logging
from typing import Any
import httpx
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class InstagramClient:
    """Instagram Graph API client for creator operations."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = 'https://graph.facebook.com/v18.0'
        self.headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    def _make_request(self, endpoint: str, params: dict[str, Any] | None=None) -> StepResult:
        """Make authenticated request to Instagram Graph API."""
        try:
            params = params or {}
            params['access_token'] = self.access_token
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
            logger.error(f'Instagram API request failed: {e}')
            return StepResult.fail(f'Instagram API request failed: {e!s}')
        except Exception as e:
            logger.error(f'Unexpected error in Instagram API request: {e}')
            return StepResult.fail(f'Unexpected error: {e!s}')

    def get_user_info(self, user_id: str, fields: list[str] | None=None) -> StepResult:
        """Get user information."""
        if not fields:
            fields = ['id', 'username', 'account_type', 'media_count', 'followers_count', 'follows_count']
        params = {'fields': ','.join(fields)}
        return self._make_request(user_id, params)

    def get_media_list(self, user_id: str, limit: int=25, after: str | None=None) -> StepResult:
        """Get user's media list."""
        params = {'limit': min(limit, 100)}
        if after:
            params['after'] = after
        return self._make_request(f'{user_id}/media', params)

    def get_media_info(self, media_id: str, fields: list[str] | None=None) -> StepResult:
        """Get media information."""
        if not fields:
            fields = ['id', 'media_type', 'media_url', 'permalink', 'caption', 'timestamp', 'like_count', 'comments_count']
        params = {'fields': ','.join(fields)}
        return self._make_request(media_id, params)

    def get_media_comments(self, media_id: str, limit: int=25, after: str | None=None) -> StepResult:
        """Get media comments."""
        params = {'limit': min(limit, 100)}
        if after:
            params['after'] = after
        return self._make_request(f'{media_id}/comments', params)

    def get_stories(self, user_id: str) -> StepResult:
        """Get user's stories."""
        return self._make_request(f'{user_id}/stories')

    def get_insights(self, user_id: str, metric: str, period: str='day', since: str | None=None, until: str | None=None) -> StepResult:
        """Get user insights (requires Instagram Business Account)."""
        params = {'metric': metric, 'period': period}
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        return self._make_request(f'{user_id}/insights', params)

    def get_media_insights(self, media_id: str, metric: str) -> StepResult:
        """Get media insights (requires Instagram Business Account)."""
        params = {'metric': metric}
        return self._make_request(f'{media_id}/insights', params)

    def get_hashtag_info(self, hashtag_name: str) -> StepResult:
        """Get hashtag information."""
        return self._make_request('ig_hashtag_search', params={'q': hashtag_name})

    def get_hashtag_media(self, hashtag_id: str, limit: int=25, after: str | None=None) -> StepResult:
        """Get recent media for a hashtag."""
        params = {'limit': min(limit, 100)}
        if after:
            params['after'] = after
        return self._make_request(f'{hashtag_id}/recent_media', params)

    def get_hashtag_top_media(self, hashtag_id: str, limit: int=25, after: str | None=None) -> StepResult:
        """Get top media for a hashtag."""
        params = {'limit': min(limit, 100)}
        if after:
            params['after'] = after
        return self._make_request(f'{hashtag_id}/top_media', params)

    def get_user_mentioned_media(self, user_id: str, limit: int=25, after: str | None=None) -> StepResult:
        """Get media where user is mentioned."""
        params = {'limit': min(limit, 100)}
        if after:
            params['after'] = after
        return self._make_request(f'{user_id}/mentioned_media', params)

    def get_user_tagged_media(self, user_id: str, limit: int=25, after: str | None=None) -> StepResult:
        """Get media where user is tagged."""
        params = {'limit': min(limit, 100)}
        if after:
            params['after'] = after
        return self._make_request(f'{user_id}/media', params)

    def create_media_container(self, user_id: str, image_url: str, caption: str, media_type: str='IMAGE') -> StepResult:
        """Create media container for posting (requires Instagram Business Account)."""
        params = {'image_url': image_url, 'caption': caption, 'media_type': media_type}
        return self._make_request(f'{user_id}/media', params)

    def publish_media(self, user_id: str, creation_id: str) -> StepResult:
        """Publish media container (requires Instagram Business Account)."""
        params = {'creation_id': creation_id}
        return self._make_request(f'{user_id}/media_publish', params)

    def get_available_insights_metrics(self, user_id: str) -> StepResult:
        """Get available insights metrics for a user."""
        return self._make_request(f'{user_id}/insights', params={'metric': 'impressions,reach,follower_count,website_clicks'})

    def get_available_media_insights_metrics(self, media_id: str) -> StepResult:
        """Get available insights metrics for media."""
        return self._make_request(f'{media_id}/insights', params={'metric': 'impressions,reach,likes,comments,shares,saved'})

    def extract_user_id_from_url(self, url: str) -> str | None:
        """Extract user ID from Instagram URL."""
        import re
        patterns = ['instagram\\.com/([^/?]+)', 'instagram\\.com/p/[^/]+/@([^/?]+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_media_id_from_url(self, url: str) -> str | None:
        """Extract media ID from Instagram URL."""
        import re
        patterns = ['instagram\\.com/p/([^/?]+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def health_check(self) -> StepResult:
        """Perform health check on Instagram client."""
        try:
            result = self.get_user_info('me')
            if result.success:
                return StepResult.ok(data={'service': 'instagram', 'status': 'healthy', 'access_token_configured': bool(self.access_token)})
            else:
                return StepResult.fail('Instagram API health check failed')
        except Exception as e:
            logger.error(f'Instagram client health check failed: {e}')
            return StepResult.fail(f'Health check failed: {e!s}')