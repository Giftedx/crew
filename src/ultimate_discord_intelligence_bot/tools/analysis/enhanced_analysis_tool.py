"""Enhanced content analysis tool with multiple analysis modes."""
from __future__ import annotations
import re
import time
from typing import Any
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import AnalysisTool

class EnhancedAnalysisTool(AnalysisTool):
    """Enhanced content analysis with multiple analysis modes and intelligent fallbacks.

    Performs comprehensive content analysis including political topic detection,
    sentiment analysis, and claim extraction. Supports multiple analysis types
    and provides intelligent fallbacks for different content formats.

    Args:
        content: Content to analyze (str or dict with description/title/url)
        analysis_type: Type of analysis to perform (comprehensive, political, sentiment, claims)
        tenant: Tenant identifier for data isolation
        workspace: Workspace identifier for organization

    Returns:
        StepResult with analysis results including:
        - political_topics: List of detected political topics
        - bias_indicators: List of detected bias indicators
        - sentiment: Overall sentiment (positive/negative/neutral)
        - sentiment_confidence: Confidence score (0.0-1.0)
        - extracted_claims: List of factual claims found
        - processing_time: Time taken for analysis

    Raises:
        StepResult.fail: If analysis fails for any reason

    Example:
        >>> tool = EnhancedAnalysisTool()
        >>> result = tool._run("This policy will improve healthcare", "comprehensive")
        >>> assert result.success
        >>> print(result.data["sentiment"])
    """
    name: str = 'Enhanced Content Analysis Tool'
    description: str = 'Analyze content with multiple analysis modes and intelligent fallbacks'

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _run(self, content: str | dict, analysis_type: str='comprehensive', tenant: str='global', workspace: str='global') -> StepResult:
        """Run enhanced content analysis with comprehensive error handling.

        Args:
            content: Content to analyze (str or dict with description/title/url)
            analysis_type: Type of analysis to perform
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            StepResult with analysis results or error information
        """
        from platform.core.step_result import ErrorContext
        start_time = time.time()
        context = ErrorContext(operation='content_analysis', component='EnhancedAnalysisTool', tenant=tenant, workspace=workspace)
        if not content:
            return StepResult.validation_error(error='Content cannot be empty', context=context, analysis_type=analysis_type)
        try:
            if isinstance(content, dict):
                text = content.get('description', '') + ' ' + content.get('title', '')
                url = content.get('url', '')
                platform = content.get('platform', 'unknown')
            else:
                text = str(content)
                url = ''
                platform = 'text'
            if not text.strip():
                return StepResult.validation_error(error='No text content found to analyze', context=context, content_type=type(content).__name__)
            analysis_result: dict[str, Any] = {'platform': platform, 'url': url, 'analysis_type': analysis_type, 'processing_time': 0, 'timestamp': time.time()}
            if analysis_type in ['comprehensive', 'political']:
                analysis_result.update(self._political_analysis(text))
            if analysis_type in ['comprehensive', 'sentiment']:
                analysis_result.update(self._sentiment_analysis(text))
            if analysis_type in ['comprehensive', 'claims']:
                analysis_result.update(self._claim_extraction(text))
            analysis_result['processing_time'] = time.time() - start_time
            self._metrics.counter('tool_runs_total', labels={'tool': 'enhanced_analysis', 'outcome': 'success'}).inc()
            return StepResult.ok(data=analysis_result)
        except ValueError as e:
            self._metrics.counter('tool_runs_total', labels={'tool': 'enhanced_analysis', 'outcome': 'error'}).inc()
            return StepResult.validation_error(error=f'Invalid input format: {e!s}', context=context, analysis_type=analysis_type)
        except Exception as e:
            self._metrics.counter('tool_runs_total', labels={'tool': 'enhanced_analysis', 'outcome': 'error'}).inc()
            return StepResult.processing_error(error=f'Analysis failed: {e!s}', context=context, processing_time=time.time() - start_time)

    def _political_analysis(self, text: str) -> dict[str, Any]:
        """Analyze political content and bias."""
        text_lower = text.lower()
        political_indicators = {'healthcare': ['healthcare', 'medicare', 'medicaid', 'insurance'], 'economy': ['economy', 'inflation', 'jobs', 'unemployment', 'gdp'], 'climate': ['climate change', 'global warming', 'carbon', 'emissions'], 'immigration': ['immigration', 'border', 'asylum', 'refugees'], 'foreign_policy': ['foreign policy', 'nato', 'ukraine', 'china'], 'social_issues': ['abortion', 'lgbt', 'marriage', 'religious freedom']}
        detected_topics = []
        for topic, keywords in political_indicators.items():
            if any((keyword in text_lower for keyword in keywords)):
                detected_topics.append(topic)
        bias_indicators = {'left_leaning': ['progressive', 'liberal', 'socialist', 'tax the rich'], 'right_leaning': ['conservative', 'traditional', 'free market', 'small government'], 'populist': ['establishment', 'elites', 'drain the swamp', 'system is rigged']}
        bias_detected = []
        for bias_type, indicators in bias_indicators.items():
            if any((indicator in text_lower for indicator in indicators)):
                bias_detected.append(bias_type)
        return {'political_topics': detected_topics, 'bias_indicators': bias_detected, 'political_score': min(len(detected_topics) * 0.2, 1.0)}

    def _sentiment_analysis(self, text: str) -> dict[str, Any]:
        """Analyze sentiment without external dependencies."""
        text_lower = text.lower()
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'love', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'disgusting']
        neutral_words = ['okay', 'fine', 'average', 'normal', 'standard']
        pos_count = sum((1 for word in positive_words if word in text_lower))
        neg_count = sum((1 for word in negative_words if word in text_lower))
        neu_count = sum((1 for word in neutral_words if word in text_lower))
        total = pos_count + neg_count + neu_count
        if total == 0:
            sentiment = 'neutral'
            confidence = 0.5
        elif pos_count > neg_count and pos_count > neu_count:
            sentiment = 'positive'
            confidence = pos_count / total
        elif neg_count > pos_count and neg_count > neu_count:
            sentiment = 'negative'
            confidence = neg_count / total
        else:
            sentiment = 'neutral'
            confidence = max(neu_count, pos_count, neg_count) / total
        return {'sentiment': sentiment, 'sentiment_confidence': confidence, 'positive_indicators': pos_count, 'negative_indicators': neg_count}

    def _claim_extraction(self, text: str) -> dict[str, Any]:
        """Extract factual claims from text."""
        claim_patterns = ['\\b\\w+\\s+is\\s+\\w+', '\\b\\w+\\s+causes?\\s+\\w+', '\\b\\w+\\s+leads?\\s+to\\s+\\w+', '\\ball\\s+\\w+\\s+are\\s+\\w+', '\\bno\\s+\\w+\\s+\\w+']
        extracted_claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            extracted_claims.extend(matches[:3])
        return {'extracted_claims': extracted_claims[:5], 'claim_count': len(extracted_claims)}

    def run(self, content: str | dict, analysis_type: str='comprehensive') -> StepResult:
        return self._run(content, analysis_type)