"""Pre-publication content filter for Discord posts."""
from __future__ import annotations
import logging
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class ContentFilter:
    """Filter content before posting to Discord."""

    def __init__(self):
        """Initialize content filter."""
        self._moderation_service = None

    def _get_moderation_service(self):
        """Get OpenAI moderation service (lazy loaded)."""
        if self._moderation_service is None:
            from platform.security.openai_moderation import OpenAIModerationService
            self._moderation_service = OpenAIModerationService()
        return self._moderation_service

    def check_content(self, content: str, trusted_source: bool=False) -> StepResult:
        """Check content before publication.

        Args:
            content: Content to check
            trusted_source: Whether source is trusted (allows override)

        Returns:
            StepResult with filtered content or blocking decision
        """
        try:
            if trusted_source:
                logger.debug('Skipping moderation check for trusted source')
                return StepResult.ok(data={'content': content, 'action': 'allow'})
            moderation = self._get_moderation_service()
            result = moderation.check_content(content)
            if result.flagged:
                logger.warning(f'Content flagged by moderation: {result.categories}')
                return StepResult.fail(f'Content blocked by moderation. Flagged categories: {list(result.categories.keys())}', metadata={'categories': result.categories, 'scores': result.category_scores, 'action': 'block'})
            return StepResult.ok(data={'content': content, 'action': 'allow', 'moderation_result': result.category_scores})
        except Exception as e:
            logger.error(f'Content filter error: {e}')
            return StepResult.ok(data={'content': content, 'action': 'allow', 'error': str(e)})

    def check_batch(self, contents: list[str], trusted_source: bool=False) -> list[StepResult]:
        """Check multiple contents in batch.

        Args:
            contents: List of content to check
            trusted_source: Whether source is trusted

        Returns:
            List of StepResult objects
        """
        if trusted_source:
            return [StepResult.ok(data={'content': c, 'action': 'allow'}) for c in contents]
        try:
            moderation = self._get_moderation_service()
            results = moderation.check_batch(contents)
            step_results = []
            for content, result in zip(contents, results, strict=False):
                if result.flagged:
                    step_results.append(StepResult.fail(f'Content blocked: {list(result.categories.keys())}', metadata={'categories': result.categories, 'action': 'block'}))
                else:
                    step_results.append(StepResult.ok(data={'content': content, 'action': 'allow'}))
            return step_results
        except Exception as e:
            logger.error(f'Batch content filter error: {e}')
            return [StepResult.ok(data={'content': c, 'action': 'allow'}) for c in contents]