"""Execution paths for OpenRouter routing."""
from __future__ import annotations
import logging
import os as _os
import sys
import time
from platform.http.http_utils import REQUEST_TIMEOUT_SECONDS, http_request_with_retry, is_retry_enabled
from platform.http.http_utils import resilient_post as _default_resilient_post
from platform.observability import metrics
from typing import TYPE_CHECKING, Any
from .quality import basic_quality_assessment, quality_assessment
from .service import get_settings
if TYPE_CHECKING:
    from .state import RouteState
try:
    from platform.observability.enhanced_langsmith_integration import trace_llm_call as _trace_llm_call

    def trace_llm_call(*args: Any, **kwargs: Any) -> None:
        _trace_llm_call(*args, **kwargs)
except Exception:

    def trace_llm_call(*_args: Any, **_kwargs: Any) -> None:
        return None
try:
    from platform.vllm_service import is_vllm_available as _is_vllm_available
    from platform.vllm_service import vLLMOpenRouterAdapter as _VLLMAdapterCtor
except Exception:
    _is_vllm_available = None
    _VLLMAdapterCtor = None
vllm_adapter_ctor: Any | None = _VLLMAdapterCtor
log = logging.getLogger(__name__)
_MODULE_NAMES = ('ultimate_discord_intelligence_bot.services.openrouter_service', 'src.ultimate_discord_intelligence_bot.services.openrouter_service')

def _call_resilient_post(*args: Any, **kwargs: Any) -> Any:
    module = None
    for name in _MODULE_NAMES:
        module = sys.modules.get(name)
        if module is not None:
            break
    if module is not None and hasattr(module, 'resilient_post'):
        return module.resilient_post(*args, **kwargs)
    return _default_resilient_post(*args, **kwargs)

def execute_offline(service: OpenRouterService, state: RouteState) -> dict[str, Any]:
    prompt = state.prompt
    chosen = state.chosen_model
    provider = state.provider
    provider_family = state.provider_family
    labels = state.labels()
    response = prompt.upper()
    latency_ms = (time.perf_counter() - state.start_time) * 1000
    tokens_out = service.prompt_engine.count_tokens(response, chosen)
    qa_score: float | None = None
    try:
        truthy = {'1', 'true', 'yes', 'on'}
        if (_os.getenv('ENABLE_QUALITY_ASSESSMENT', '1') or '1').lower() in truthy:
            min_tokens = 80
            try:
                overrides = state.provider_overrides or {}
                mt = overrides.get('quality_min_tokens') if isinstance(overrides, dict) else None
                if isinstance(mt, int) and mt > 0:
                    min_tokens = int(mt)
            except Exception:
                pass
            try:
                qa = quality_assessment(str(response), prompt=str(state.prompt or ''), min_tokens=min_tokens)
            except Exception:
                qa = basic_quality_assessment(str(response), min_tokens=min_tokens)
            qa_score = float(qa.get('score', 0.0))
    except Exception:
        qa_score = None
    reward = _compute_reward(service, state, latency_ms, quality_score=qa_score)
    service.learning.update(state.task_type, chosen, reward=reward)
    service._adaptive_record_outcome(state, reward=reward, status='success', metadata={'latency_ms': latency_ms, 'tokens_out': tokens_out, 'execution_mode': 'offline', 'cache_hit': False})
    metrics.LLM_MODEL_SELECTED.labels(**labels, task=state.task_type, model=chosen, provider=provider_family).inc()
    metrics.LLM_ESTIMATED_COST.labels(**labels, model=chosen, provider=provider_family).observe(state.projected_cost)
    metrics.LLM_LATENCY.labels(**labels).observe(latency_ms)
    if service.logger:
        service.logger.log_llm_call(state.task_type, chosen, str(provider), state.tokens_in, tokens_out, float(state.projected_cost), latency_ms, None, True, None)
    result = {'status': 'success', 'model': chosen, 'response': response, 'tokens': state.tokens_in, 'provider': provider}
    if state.cache_metadata:
        result.setdefault('cache_info', state.cache_metadata)
    if state.compression_metadata:
        result.setdefault('compression_info', state.compression_metadata)
    try:
        if qa_score is not None:
            min_tokens = 80
            try:
                overrides = state.provider_overrides or {}
                mt = overrides.get('quality_min_tokens') if isinstance(overrides, dict) else None
                if isinstance(mt, int) and mt > 0:
                    min_tokens = int(mt)
            except Exception:
                pass
            try:
                qa_block = quality_assessment(str(response), prompt=str(state.prompt or ''), min_tokens=min_tokens)
            except Exception:
                qa_block = basic_quality_assessment(str(response), min_tokens=min_tokens)
            result['quality_assessment'] = qa_block
    except Exception:
        pass
    trace_llm_call(name=f'openrouter_{state.task_type}', prompt=prompt, response=response, model=chosen, metadata={'provider': provider, 'task_type': state.task_type, 'offline': True}, latency_ms=latency_ms, token_usage={'input_tokens': state.tokens_in, 'output_tokens': tokens_out, 'total_tokens': state.tokens_in + tokens_out}, cost=state.projected_cost)
    _persist_caches(service, state, result)
    _charge_tracker(state)
    result['cached'] = False
    state.result = result
    return result

def execute_online(service: OpenRouterService, state: RouteState) -> dict[str, Any]:
    prompt = state.prompt
    chosen = state.chosen_model
    provider = state.provider
    provider_family = state.provider_family
    payload: dict[str, Any] = {'model': chosen, 'messages': [{'role': 'user', 'content': prompt}]}
    if provider:
        payload['provider'] = provider
    settings = get_settings()
    if chosen.startswith('local/') and vllm_adapter_ctor is not None and _has_vllm() and getattr(settings, 'enable_vllm_local', False):
        try:
            AdapterType: Any = vllm_adapter_ctor
            adapter = AdapterType()
            vllm_result = adapter.route_to_local_model(prompt, chosen, state.task_type)
            if vllm_result.get('status') == 'success':
                latency_ms = (time.perf_counter() - state.start_time) * 1000
                trace_llm_call(name=f'vllm_{state.task_type}', prompt=prompt, response=vllm_result['response'], model=chosen, metadata={'provider': 'vllm', 'task_type': state.task_type, 'local_inference': True}, latency_ms=latency_ms, token_usage={'input_tokens': state.tokens_in, 'output_tokens': vllm_result.get('tokens', 0), 'total_tokens': state.tokens_in + vllm_result.get('tokens', 0)}, cost=state.projected_cost)
                _charge_tracker(state)
                state.result = vllm_result
                return vllm_result
        except Exception as exc:
            log.warning('vLLM local inference failed: %s, falling back to HTTP', exc)
    if getattr(settings, 'local_llm_url', None):
        local_model = chosen.split('/', 1)[1] if '/' in chosen else chosen
        local_payload = {'model': local_model, 'messages': payload['messages']}
        local_url = str(getattr(settings, 'local_llm_url', '')).rstrip('/') + '/v1/chat/completions'
        resp = _call_resilient_post(local_url, json_payload=local_payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
        if resp is not None and getattr(resp, 'status_code', 200) < 400:
            data = resp.json()
            message = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            latency_ms = (time.perf_counter() - state.start_time) * 1000
            tokens_out = service.prompt_engine.count_tokens(message, local_model)
            result_local = {'status': 'success', 'model': chosen, 'response': message, 'tokens': state.tokens_in, 'provider': {'order': ['local']}}
            _post_success(service, state, result_local, tokens_out, latency_ms, provider_family, offline=False)
            return result_local
    url = 'https://openrouter.ai/api/v1/chat/completions'
    api_key = service.api_key or ''
    headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
    ref = getattr(settings, 'openrouter_referer', None) or _os.getenv('OPENROUTER_REFERER')
    if ref:
        ref = str(ref)
        headers['Referer'] = ref
        headers['HTTP-Referer'] = ref
    title = getattr(settings, 'openrouter_title', None) or _os.getenv('OPENROUTER_TITLE')
    if title:
        headers['X-Title'] = str(title)
    resp = None

    def _is_overflow_error(response: Any) -> bool:
        try:
            status = getattr(response, 'status_code', None)
            body_txt = None
            body = None
            try:
                body = response.json() if hasattr(response, 'json') else None
            except Exception:
                body = None
            try:
                body_txt = response.text if hasattr(response, 'text') else None
            except Exception:
                body_txt = None
            if status in (400, 413, 422):
                markers = ('maximum context length', 'context length exceeded', 'too many tokens', 'prompt is too long', 'exceeds the maximum allowed', 'token limit')
                text = ' '.join([str(body) if body is not None else '', str(body_txt) if body_txt is not None else '']).lower()
                return any((m in text for m in markers))
        except Exception:
            pass
        return False

    def _retry_after_compression(reason: str) -> dict[str, Any] | None:
        """Attempt a single retry with aggressive prompt compression.

        Returns a result dict when retry succeeds; otherwise None to allow normal error handling.
        """
        try:
            target_reduction = 0.5
            max_tokens = None
            try:
                overrides = state.provider_overrides or {}
                mt = overrides.get('max_tokens') if isinstance(overrides, dict) else None
                if isinstance(mt, int) and mt > 0:
                    max_tokens = int(max(256, mt * 2))
            except Exception:
                max_tokens = None
            new_text, meta = service.prompt_engine.optimise_with_metadata(state.prompt, target_token_reduction=target_reduction, max_tokens=max_tokens, force_enable=True)
            if not isinstance(new_text, str) or not new_text.strip():
                return None
            state.prompt = new_text
            state.compression_metadata = meta
            state.tokens_in = service.prompt_engine.count_tokens(new_text, state.chosen_model)
            retry_payload = {'model': state.chosen_model, 'messages': [{'role': 'user', 'content': state.prompt}]}
            if provider:
                retry_payload['provider'] = provider
            retry_resp = _call_resilient_post(url, headers=headers, json_payload=retry_payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
            if retry_resp is None or getattr(retry_resp, 'status_code', 200) >= 400:
                return None
            data2 = retry_resp.json() if retry_resp is not None else {}
            message2 = data2.get('choices', [{}])[0].get('message', {}).get('content', '')
            latency_ms2 = (time.perf_counter() - state.start_time) * 1000
            tokens_out2 = service.prompt_engine.count_tokens(message2, state.chosen_model)
            result2 = {'status': 'success', 'model': state.chosen_model, 'response': message2, 'tokens': state.tokens_in, 'provider': provider, 'retry_reason': reason}
            if state.cache_metadata:
                result2.setdefault('cache_info', state.cache_metadata)
            _post_success(service, state, result2, tokens_out2, latency_ms2, provider_family, offline=False)
            return result2
        except Exception:
            return None
    if is_retry_enabled():
        try:
            resp = http_request_with_retry('POST', url, request_callable=lambda u, **_: _call_resilient_post(u, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS), max_attempts=3)
        except Exception as retry_exc:
            latency_ms = (time.perf_counter() - state.start_time) * 1000
            if service.logger:
                try:
                    service.logger.log_llm_call(state.task_type, chosen, str(provider), state.tokens_in, 0, float(state.projected_cost), latency_ms, None, False, str(retry_exc))
                except Exception as log_exc:
                    log.debug('logger failure in retry give-up: %s', log_exc)
            error = {'status': 'error', 'error': str(retry_exc), 'model': chosen, 'tokens': state.tokens_in, 'provider': provider}
            state.error = error
            service._adaptive_record_outcome(state, reward=0.0, status='error', metadata={'stage': 'http_retry', 'error': str(retry_exc), 'latency_ms': latency_ms})
            return error
    else:
        resp = _call_resilient_post(url, headers=headers, json_payload=payload, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
    if resp is None or getattr(resp, 'status_code', 200) >= 400:
        overflow_like = False
        try:
            status_c = getattr(resp, 'status_code', None)
            overflow_like = bool(status_c in (413,)) or _is_overflow_error(resp)
        except Exception:
            overflow_like = False
        if resp is not None and overflow_like:
            result_retry = _retry_after_compression('overflow_detected')
            if result_retry is not None:
                return result_retry
        code = getattr(resp, 'status_code', 'unknown')
        raise RuntimeError(f'openrouter_error status={code}')
    data = resp.json() if resp is not None else {}
    message = data.get('choices', [{}])[0].get('message', {}).get('content', '')
    latency_ms = (time.perf_counter() - state.start_time) * 1000
    tokens_out = service.prompt_engine.count_tokens(message, chosen)
    result = {'status': 'success', 'model': chosen, 'response': message, 'tokens': state.tokens_in, 'provider': provider}
    if state.cache_metadata:
        result.setdefault('cache_info', state.cache_metadata)
    _post_success(service, state, result, tokens_out, latency_ms, provider_family, offline=False)
    return result

def handle_failure(service: OpenRouterService, state: RouteState, exc: Exception) -> dict[str, Any]:
    latency_ms = (time.perf_counter() - state.start_time) * 1000
    if service.logger:
        service.logger.log_llm_call(state.task_type, state.chosen_model, str(state.provider), state.tokens_in, 0, 0.0, latency_ms, None, False, None)
    log.error('OpenRouterService route failed task=%s model=%s provider=%s err=%s', state.task_type, state.chosen_model, state.provider_family, exc, exc_info=True)
    error = {'status': 'error', 'error': str(exc), 'model': state.chosen_model, 'tokens': state.tokens_in, 'provider': state.provider}
    state.error = error
    service._adaptive_record_outcome(state, reward=0.0, status='exception', metadata={'error': str(exc), 'latency_ms': latency_ms})
    return error

def _post_success(service: OpenRouterService, state: RouteState, result: dict[str, Any], tokens_out: int, latency_ms: float, provider_family: str, *, offline: bool) -> None:
    qa_score: float | None = None
    try:
        truthy = {'1', 'true', 'yes', 'on'}
        if (_os.getenv('ENABLE_QUALITY_ASSESSMENT', '1') or '1').lower() in truthy:
            min_tokens = 80
            try:
                overrides = state.provider_overrides or {}
                mt = overrides.get('quality_min_tokens') if isinstance(overrides, dict) else None
                if isinstance(mt, int) and mt > 0:
                    min_tokens = int(mt)
            except Exception:
                pass
            try:
                qa = quality_assessment(str(result.get('response') or ''), prompt=str(state.prompt or ''), min_tokens=min_tokens, expect_json=bool(getattr(state, 'expects_json', False)))
            except Exception:
                qa = basic_quality_assessment(str(result.get('response') or ''), min_tokens=min_tokens)
            result['quality_assessment'] = qa
            qa_score = float(qa.get('score', 0.0))
    except Exception:
        qa_score = None
    reward = _compute_reward(service, state, latency_ms, quality_score=qa_score)
    service.learning.update(state.task_type, state.chosen_model, reward=reward)
    cache_meta = state.cache_metadata or {}
    cache_hit = any((isinstance(meta, dict) and meta.get('status') == 'hit' for meta in cache_meta.values()))
    service._adaptive_record_outcome(state, reward=reward, status='success', metadata={'latency_ms': latency_ms, 'tokens_out': tokens_out, 'execution_mode': 'offline' if offline else 'online', 'cache_hit': cache_hit})
    labels = state.labels()
    metrics.LLM_MODEL_SELECTED.labels(**labels, task=state.task_type, model=state.chosen_model, provider=provider_family).inc()
    metrics.LLM_ESTIMATED_COST.labels(**labels, model=state.chosen_model, provider=provider_family).observe(state.projected_cost)
    metrics.LLM_LATENCY.labels(**labels).observe(latency_ms)
    if service.logger:
        service.logger.log_llm_call(state.task_type, state.chosen_model, str(state.provider), state.tokens_in, tokens_out, float(state.projected_cost), latency_ms, None, True, None)
    metadata = {'provider': state.provider, 'task_type': state.task_type, 'offline': offline}
    if not offline:
        metadata['api_endpoint'] = 'openrouter'
    if state.cache_metadata:
        result.setdefault('cache_info', state.cache_metadata)
    if state.compression_metadata:
        result.setdefault('compression_info', state.compression_metadata)
    trace_llm_call(name=f'openrouter_{state.task_type}', prompt=state.prompt, response=result.get('response'), model=state.chosen_model, metadata=metadata, latency_ms=latency_ms, token_usage={'input_tokens': state.tokens_in, 'output_tokens': tokens_out, 'total_tokens': state.tokens_in + tokens_out}, cost=state.projected_cost)
    _persist_caches(service, state, result)
    _charge_tracker(state)
    result['cached'] = False
    state.result = result

def _persist_caches(service: OpenRouterService, state: RouteState, result: dict[str, Any]) -> None:
    if service.semantic_cache is not None:
        try:
            sc = service.semantic_cache
            if sc is not None:
                sc.set(state.prompt, state.chosen_model, result, namespace=state.namespace)
            log.debug('semantic_cache_set completed for model=%s ns=%s', state.chosen_model, state.namespace)
        except Exception:
            pass
    if service.cache and state.cache_key:
        service.cache.set(state.cache_key, result)

def _charge_tracker(state: RouteState) -> None:
    tracker = state.tracker
    if tracker:
        try:
            tracker.charge(state.projected_cost, state.task_type)
        except Exception as charge_exc:
            log.debug('request budget charge failed task=%s model=%s err=%s', state.task_type, state.chosen_model, charge_exc)

def _compute_reward(service: OpenRouterService, state: RouteState, latency_ms: float, quality_score: float | None=None) -> float:
    settings = get_settings()
    rl: dict[str, Any] = {}
    if service.tenant_registry:
        ctx_t = state.ctx_effective
        rl = service.tenant_registry.get_rl_overrides(ctx_t) if ctx_t else {}

    def _as_float(val: Any, default: float) -> float:
        try:
            if val is None:
                return default
            return float(val)
        except Exception:
            return default
    w_cost = _as_float(rl.get('reward_cost_weight', getattr(settings, 'reward_cost_weight', 0.5)), 0.5)
    w_lat = _as_float(rl.get('reward_latency_weight', getattr(settings, 'reward_latency_weight', 0.5)), 0.5)
    w_qual_raw = rl.get('reward_quality_weight', getattr(settings, 'reward_quality_weight', None))
    if w_qual_raw is None:
        try:
            env_v = _os.getenv('REWARD_QUALITY_WEIGHT')
            w_qual_raw = float(env_v) if env_v is not None and str(env_v).strip() != '' else 0.0
        except Exception:
            w_qual_raw = 0.0
    w_qual = _as_float(w_qual_raw, 0.0)
    if w_cost == 0.0 and w_lat == 0.0 and (w_qual == 0.0 or quality_score is None):
        w_cost = w_lat = 0.5
    active_quality = quality_score is not None and w_qual > 0.0
    norm = w_cost + w_lat + (w_qual if active_quality else 0.0)
    if norm <= 0.0:
        norm = 1.0
    w_cost /= norm
    w_lat /= norm
    w_qual = w_qual / norm if active_quality else 0.0
    cost_norm = 0.0
    if state.projected_cost > 0:
        if rl.get('reward_cost_weight') is not None or rl.get('reward_latency_weight') is not None:
            denom = state.projected_cost
        else:
            denom = state.effective_max if state.effective_max and state.effective_max != float('inf') else state.projected_cost
        cost_norm = min(1.0, state.projected_cost / max(denom, 1e-09))
    lat_window = float(rl.get('reward_latency_ms_window', getattr(settings, 'reward_latency_ms_window', 2000) or 2000))
    lat_window = max(1.0, lat_window)
    lat_norm = min(1.0, latency_ms / lat_window)
    cost_component = 1.0 - cost_norm
    lat_component = 1.0 - lat_norm
    qual_component = float(quality_score) if active_quality else 0.0
    reward = w_cost * cost_component + w_lat * lat_component + w_qual * qual_component
    return max(0.0, min(1.0, reward))

def _has_vllm() -> bool:
    try:
        if _is_vllm_available is None:
            return False
        return bool(_is_vllm_available())
    except Exception:
        return False
if TYPE_CHECKING:
    from .service import OpenRouterService