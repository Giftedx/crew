from __future__ import annotations
import json
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, get_args, get_origin
from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined
from platform.observability import metrics
from ultimate_discord_intelligence_bot.services.request_budget import current_request_tracker
from .cache import CacheKeyGenerator, ResponseCache
from .recovery import EnhancedErrorRecovery
from .streaming import ProgressTracker, StreamingResponse, StreamingStructuredRequest
if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from platform.llm.providers.openrouter import OpenRouterService
logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseModel)

@dataclass
class StructuredRequest:
    """Data class for structured LLM request parameters."""
    prompt: str
    response_model: Any
    task_type: str = 'general'
    model: str | None = None
    provider_opts: dict[str, Any] | None = None
    max_retries: int = 3

class StructuredLLMService:
    """Enhanced LLM service with structured output validation.

    The Instructor integration is optional. If available in runtime, the
    service will prefer it; otherwise it falls back to JSON prompting + validation.
    """
    instructor_client: Any | None

    def __init__(self, openrouter_service: OpenRouterService, cache_max_entries: int | None=1000, cache_max_memory_mb: float | None=100.0, cache_enable_compression: bool=True, cache_compression_min_size_bytes: int=1024):
        self.openrouter = openrouter_service
        self.cache = ResponseCache(default_ttl_seconds=3600, max_entries=cache_max_entries, max_memory_mb=cache_max_memory_mb, enable_compression=cache_enable_compression, compression_min_size_bytes=cache_compression_min_size_bytes)
        self.error_recovery = EnhancedErrorRecovery(max_failures=5, reset_timeout=60.0, base_delay=1.0)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300
        self.instructor_client = None
        self._instructor_available = False
        try:
            import instructor
            from openai import OpenAI as _OpenAI
            base_client = _OpenAI(base_url='https://openrouter.ai/api/v1', api_key=self.openrouter.api_key)
            self.instructor_client = instructor.from_openai(base_client)
            self._instructor_available = True
            logger.info('Instructor client initialized for structured outputs')
        except Exception:
            logger.debug('Instructor not available - using fallback parsing')
            self.instructor_client = None

    def _perform_cache_maintenance(self):
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            expired_count = self.cache.clear_expired()
            stale_count = self.cache.cleanup_stale_entries()
            self._last_cleanup = current_time
            if expired_count or stale_count:
                logger.info(f'Cache maintenance: removed {expired_count} expired, {stale_count} stale entries')

    def route_structured(self, request: StructuredRequest) -> BaseModel | dict[str, Any]:
        start_time = time.time()
        self._perform_cache_maintenance()
        cache_key = CacheKeyGenerator.generate_key(request)
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            cache_labels = {**metrics.label_ctx(), 'task': request.task_type, 'method': 'cache'}
            metrics.STRUCTURED_LLM_REQUESTS.labels(**cache_labels).inc()
            metrics.STRUCTURED_LLM_CACHE_HITS.labels(**cache_labels).inc()
            return cached_result
        cache_labels = {**metrics.label_ctx(), 'task': request.task_type, 'method': 'cache'}
        metrics.STRUCTURED_LLM_CACHE_MISSES.labels(**cache_labels).inc()
        if not self.error_recovery.should_attempt_request(request.model, None):
            return {'status': 'error', 'error': 'Service temporarily unavailable due to repeated failures', 'circuit_breaker': 'open'}
        use_instructor = self.instructor_client is not None and self._is_structured_model_compatible(request.model)
        method = 'instructor' if use_instructor else 'fallback'
        labels = {**metrics.label_ctx(), 'task': request.task_type, 'method': method}
        metrics.STRUCTURED_LLM_REQUESTS.labels(**labels).inc()
        try:
            if use_instructor:
                result = self._route_with_instructor(request)
            else:
                result = self._route_with_fallback_parsing(request)
            if isinstance(result, dict) and result.get('status') == 'error':
                self.error_recovery.record_failure(request.model, None)
                error_type = result.get('error', 'unknown').split(':')[0].strip().lower()
                metrics.STRUCTURED_LLM_ERRORS.labels(**labels, error_type=error_type).inc()
                metrics.STRUCTURED_LLM_LATENCY.labels(**labels).observe((time.time() - start_time) * 1000)
                return result
            if isinstance(result, BaseModel):
                ttl = self.cache.get_ttl_for_request(request)
                self.cache.set(cache_key, result, ttl)
            self.error_recovery.record_success(request.model, None)
            selected_model = request.model or 'auto-selected'
            success_labels = {**labels, 'model': selected_model}
            metrics.STRUCTURED_LLM_SUCCESS.labels(**success_labels).inc()
            metrics.STRUCTURED_LLM_LATENCY.labels(**labels).observe((time.time() - start_time) * 1000)
            return result
        except Exception as e:
            self.error_recovery.record_failure(request.model, None)
            error_type = type(e).__name__.lower()
            metrics.STRUCTURED_LLM_ERRORS.labels(**labels, error_type=error_type).inc()
            metrics.STRUCTURED_LLM_LATENCY.labels(**labels).observe((time.time() - start_time) * 1000)
            return {'status': 'error', 'error': f'Unexpected error: {e!s}'}

    async def route_structured_streaming(self, request: StreamingStructuredRequest) -> AsyncGenerator[StreamingResponse, None]:
        progress_tracker = ProgressTracker(request.progress_callback)
        progress_tracker.start_operation('Structured LLM streaming request')
        self._perform_cache_maintenance()
        cache_key = CacheKeyGenerator.generate_key(request)
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            cache_labels = {**metrics.label_ctx(), 'task': request.task_type, 'method': 'cache'}
            metrics.STRUCTURED_LLM_CACHE_HITS.labels(**cache_labels).inc()
            progress_tracker.complete_operation('Retrieved from cache')
            yield StreamingResponse(partial_result=cached_result, is_complete=True, progress_percent=100.0, raw_chunks=[])
            return
        cache_labels = {**metrics.label_ctx(), 'task': request.task_type, 'method': 'cache'}
        metrics.STRUCTURED_LLM_CACHE_MISSES.labels(**cache_labels).inc()
        if not self.error_recovery.should_attempt_request(request.model, None):
            progress_tracker.error_operation('Service temporarily unavailable due to repeated failures')
            yield StreamingResponse(partial_result=None, is_complete=True, progress_percent=100.0, error='Service temporarily unavailable due to repeated failures')
            return
        use_instructor = self.instructor_client is not None and self._is_structured_model_compatible(request.model)
        method = 'instructor_streaming' if use_instructor else 'fallback_streaming'
        labels = {**metrics.label_ctx(), 'task': request.task_type, 'method': method}
        metrics.STRUCTURED_LLM_REQUESTS.labels(**labels).inc()
        try:
            if use_instructor:
                async for response in self._route_with_instructor_streaming(request, progress_tracker):
                    yield response
            else:
                async for response in self._route_with_fallback_streaming(request, progress_tracker):
                    yield response
        except Exception as e:
            self.error_recovery.record_failure(request.model, None)
            error_type = type(e).__name__.lower()
            metrics.STRUCTURED_LLM_ERRORS.labels(**labels, error_type=error_type).inc()
            progress_tracker.error_operation(f'Unexpected error: {e!s}')
            yield StreamingResponse(partial_result=None, is_complete=True, progress_percent=100.0, error=str(e))

    def _is_structured_model_compatible(self, model: str | None) -> bool:
        if not model:
            return False
        structured_models = ['openai/gpt-4o', 'openai/gpt-4o-mini', 'openai/gpt-4-turbo', 'anthropic/claude-3-5-sonnet', 'anthropic/claude-3-opus', 'anthropic/claude-3-haiku', 'google/gemini-1.5-pro', 'google/gemini-1.5-flash']
        return any((supported in model.lower() for supported in structured_models))

    def _route_with_instructor(self, request: StructuredRequest) -> BaseModel | dict[str, Any]:
        if self.instructor_client is None:
            return self._route_with_fallback_parsing(request)
        try:
            selected_model = request.model or self.openrouter._choose_model_from_map(request.task_type, self.openrouter.models_map)
            usage_labels = {**metrics.label_ctx(), 'task': request.task_type, 'model': selected_model}
            metrics.STRUCTURED_LLM_INSTRUCTOR_USAGE.labels(**usage_labels).inc()
            response = self.instructor_client.chat.completions.create(model=selected_model, response_model=request.response_model, messages=[{'role': 'user', 'content': request.prompt}], max_retries=request.max_retries, temperature=0.1)
            cost = getattr(response, 'usage', {}).get('total_cost', 0.0) if hasattr(response, 'usage') else 0.0
            if cost > 0:
                tracker = current_request_tracker()
                if tracker:
                    try:
                        tracker.charge(cost, f'structured_{request.task_type}')
                        metrics.LLM_ESTIMATED_COST.labels(**metrics.label_ctx(), model=selected_model, provider='instructor').observe(cost)
                    except Exception:
                        pass
            return response
        except Exception:
            return self._route_with_fallback_parsing(request)

    async def _route_with_instructor_streaming(self, request: StreamingStructuredRequest, progress_tracker: ProgressTracker) -> AsyncGenerator[StreamingResponse, None]:
        if self.instructor_client is None:
            async for resp in self._route_with_fallback_streaming(request, progress_tracker):
                yield resp
            return
        try:
            progress_tracker.update_progress('Initializing Instructor streaming', 10.0)
            selected_model = request.model or self.openrouter._choose_model_from_map(request.task_type, self.openrouter.models_map)
            progress_tracker.update_progress(f'Selected model: {selected_model}', 20.0)
            regular_request = StructuredRequest(prompt=request.prompt, response_model=request.response_model, task_type=request.task_type, model=request.model, provider_opts=request.provider_opts, max_retries=request.max_retries)
            progress_tracker.update_progress('Processing with Instructor', 50.0)
            result = self._route_with_instructor(regular_request)
            if isinstance(result, dict) and result.get('status') == 'error':
                progress_tracker.error_operation(result.get('error', 'Unknown error'))
                yield StreamingResponse(partial_result=None, is_complete=True, progress_percent=100.0, error=result.get('error', 'Unknown error'))
            else:
                if isinstance(result, BaseModel):
                    cache_key = CacheKeyGenerator.generate_key(request)
                    ttl = self.cache.get_ttl_for_request(request)
                    self.cache.set(cache_key, result, ttl)
                progress_tracker.complete_operation('Streaming completed successfully')
                yield StreamingResponse(partial_result=result if isinstance(result, BaseModel) else None, is_complete=True, progress_percent=100.0, raw_chunks=[])
        except Exception as e:
            progress_tracker.error_operation(f'Instructor streaming failed: {e!s}')
            async for resp in self._route_with_fallback_streaming(request, progress_tracker):
                yield resp

    async def _route_with_fallback_streaming(self, request: StreamingStructuredRequest, progress_tracker: ProgressTracker) -> AsyncGenerator[StreamingResponse, None]:
        progress_tracker.update_progress('Starting fallback streaming', 10.0)
        try:
            regular_request = StructuredRequest(prompt=request.prompt, response_model=request.response_model, task_type=request.task_type, model=request.model, provider_opts=request.provider_opts, max_retries=request.max_retries)
            progress_tracker.update_progress('Processing request', 30.0)
            result = self._route_with_fallback_parsing(regular_request)
            progress_tracker.update_progress('Parsing response', 70.0)
            if isinstance(result, dict) and result.get('status') == 'error':
                progress_tracker.error_operation(result.get('error', 'Unknown error'))
                yield StreamingResponse(partial_result=None, is_complete=True, progress_percent=100.0, error=result.get('error', 'Unknown error'))
            else:
                if isinstance(result, BaseModel):
                    cache_key = CacheKeyGenerator.generate_key(request)
                    ttl = self.cache.get_ttl_for_request(request)
                    self.cache.set(cache_key, result, ttl)
                progress_tracker.complete_operation('Fallback streaming completed')
                yield StreamingResponse(partial_result=result if isinstance(result, BaseModel) else None, is_complete=True, progress_percent=100.0, raw_chunks=[])
        except Exception as e:
            progress_tracker.error_operation(f'Streaming failed: {e!s}')
            yield StreamingResponse(partial_result=None, is_complete=True, progress_percent=100.0, error=str(e))

    def _route_with_fallback_parsing(self, request: StructuredRequest) -> BaseModel | dict[str, Any]:
        selected_model = request.model or 'auto-selected'
        fallback_labels = {**metrics.label_ctx(), 'task': request.task_type, 'model': selected_model}
        metrics.STRUCTURED_LLM_FALLBACK_USAGE.labels(**fallback_labels).inc()
        structured_prompt = self._enhance_prompt_for_json(request.prompt, request.response_model)
        for attempt in range(request.max_retries):
            try:
                if not self.error_recovery.should_attempt_request(request.model, None):
                    return {'status': 'error', 'error': 'Service temporarily unavailable due to repeated failures', 'circuit_breaker': 'open', 'attempt': attempt + 1}
                response = self.openrouter.route(prompt=structured_prompt, task_type=request.task_type, model=request.model, provider_opts=request.provider_opts)
                if response.get('status') != 'success':
                    error_response = self._handle_response_error(response, request, attempt)
                    if error_response is None:
                        continue
                    return error_response
                raw_response = response.get('response', '')
                validated_model = self._parse_and_validate_json(raw_response, request.response_model)
                if validated_model:
                    self.error_recovery.record_success(request.model, None)
                    estimated_structured_cost = self._estimate_structured_cost(response, request.task_type)
                    if estimated_structured_cost > 0:
                        tracker = current_request_tracker()
                        if tracker:
                            try:
                                tracker.charge(estimated_structured_cost, f'structured_{request.task_type}')
                                provider_family = self._extract_provider_family(response)
                                metrics.LLM_ESTIMATED_COST.labels(**metrics.label_ctx(), model=selected_model, provider=provider_family).observe(estimated_structured_cost)
                            except Exception:
                                pass
                    return validated_model
                enhanced_prompt = self._handle_parsing_failure(request, attempt, structured_prompt)
                if enhanced_prompt is None:
                    break
                structured_prompt = enhanced_prompt
            except Exception as e:
                error_response = self._handle_exception_error(e, request, attempt, locals().get('response'))
                if error_response is None:
                    continue
                return error_response
        return {'status': 'error', 'error': 'Failed to generate structured output', 'attempts': request.max_retries}

    def _handle_response_error(self, response: dict[str, Any], request: StructuredRequest, attempt: int) -> dict[str, Any] | None:
        error_category = self.error_recovery.categorize_error(Exception(response.get('error', 'Unknown error')))
        self.error_recovery.record_failure(request.model, None)
        if error_category in ['rate_limit', 'timeout'] and attempt < request.max_retries - 1:
            backoff_delay = self.error_recovery.get_backoff_delay(attempt)
            time.sleep(backoff_delay)
            return None
        return response

    def _handle_parsing_failure(self, request: StructuredRequest, attempt: int, structured_prompt: str) -> str | None:
        if attempt >= request.max_retries - 1:
            return None
        backoff_delay = self.error_recovery.get_backoff_delay(attempt, max_delay=5.0)
        time.sleep(backoff_delay)
        return self._enhance_prompt_with_example(structured_prompt, request.response_model)

    def _handle_exception_error(self, e: Exception, request: StructuredRequest, attempt: int, response: dict[str, Any] | None) -> dict[str, Any] | None:
        error_category = self.error_recovery.categorize_error(e)
        self.error_recovery.record_failure(request.model, None)
        if attempt < request.max_retries - 1 and error_category in ['rate_limit', 'timeout', 'parsing']:
            backoff_delay = self.error_recovery.get_backoff_delay(attempt)
            time.sleep(backoff_delay)
            return None
        if attempt == request.max_retries - 1:
            return {'status': 'error', 'error': f'Structured output generation failed after {request.max_retries} attempts', 'raw_response': response.get('response', '') if response else '', 'last_error': str(e), 'error_category': error_category}
        return None

    def _enhance_prompt_for_json(self, prompt: str, response_model: type[BaseModel]) -> str:
        schema = response_model.model_json_schema()
        json_prompt = f'\n{prompt}\n\nIMPORTANT: Respond with valid JSON that matches this exact schema:\n\n{json.dumps(schema, indent=2)}\n\nYour response must be valid JSON only - no additional text or explanation.\n'
        return json_prompt

    def _enhance_prompt_with_example(self, prompt: str, response_model: type[BaseModel]) -> str:
        try:
            example = self._generate_example_instance(response_model)
            example_json = example.model_dump_json(indent=2)
            enhanced_prompt = f'\n{prompt}\n\nExample of the expected JSON format:\n{example_json}\n\nRespond with valid JSON in this exact format.\n'
            return enhanced_prompt
        except Exception:
            return prompt

    def _generate_example_instance(self, response_model: type[BaseModel]) -> BaseModel:
        field_values: dict[str, Any] = {}
        for field_name, field_info in response_model.model_fields.items():
            if field_info.default is not PydanticUndefined and field_info.default is not None:
                field_values[field_name] = field_info.default
            elif hasattr(field_info, 'default_factory') and field_info.default_factory is not None:
                field_values[field_name] = self._generate_example_value(field_info.annotation)
            else:
                field_values[field_name] = self._generate_example_value(field_info.annotation)
        return response_model(**field_values)

    def _generate_example_value(self, field_type: Any) -> Any:
        type_examples = {str: 'example_string', int: 0, float: 0.0, bool: False}
        if field_type in type_examples:
            return type_examples[field_type]
        origin = get_origin(field_type)
        if origin is list or field_type is list:
            args = get_args(field_type)
            item_type = args[0] if args else str
            return [self._generate_example_value(item_type)]
        if origin is dict or field_type is dict:
            return {'key': 'value'}
        return 'example'

    def _parse_and_validate_json(self, raw_response: str, response_model: type[T]) -> T | None:
        parsing_start = time.time()
        labels = {**metrics.label_ctx(), 'task': 'parsing'}
        try:
            cleaned = raw_response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)
            validated = response_model(**data)
            return validated
        except json.JSONDecodeError:
            metrics.STRUCTURED_LLM_PARSING_FAILURES.labels(**metrics.label_ctx(), task='parsing', method='fallback').inc()
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)
            return None
        except ValidationError:
            metrics.STRUCTURED_LLM_VALIDATION_FAILURES.labels(**metrics.label_ctx(), task='validation', method='fallback').inc()
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)
            return None
        except Exception:
            metrics.STRUCTURED_LLM_PARSING_FAILURES.labels(**metrics.label_ctx(), task='parsing', method='fallback').inc()
            metrics.STRUCTURED_LLM_PARSING_LATENCY.labels(**labels).observe((time.time() - parsing_start) * 1000)
            return None

    def _estimate_structured_cost(self, response: dict[str, Any], task_type: str) -> float:
        try:
            if 'cost' in response:
                return float(response['cost'])
            tokens_in = response.get('tokens', 0)
            response_text = response.get('response', '')
            estimated_output_tokens = len(response_text.split()) * 1.3
            base_cost_per_1k = 0.002
            total_tokens = tokens_in + estimated_output_tokens
            estimated_cost = total_tokens / 1000 * base_cost_per_1k
            return max(estimated_cost, 0.001)
        except Exception:
            return 0.001

    def _extract_provider_family(self, response: dict[str, Any]) -> str:
        try:
            provider_info = response.get('provider', {})
            if isinstance(provider_info, dict):
                order = provider_info.get('order', [])
                if order and len(order) > 0:
                    return str(order[0])
            elif isinstance(provider_info, str):
                return provider_info
            return 'unknown'
        except Exception:
            return 'unknown'

def create_structured_llm_service(openrouter_service: OpenRouterService, cache_max_entries: int | None=1000, cache_max_memory_mb: float | None=100.0, cache_enable_compression: bool=True, cache_compression_min_size_bytes: int=1024) -> StructuredLLMService:
    return StructuredLLMService(openrouter_service=openrouter_service, cache_max_entries=cache_max_entries, cache_max_memory_mb=cache_max_memory_mb, cache_enable_compression=cache_enable_compression, cache_compression_min_size_bytes=cache_compression_min_size_bytes)