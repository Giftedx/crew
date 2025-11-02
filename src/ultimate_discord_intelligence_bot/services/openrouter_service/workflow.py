"""High-level orchestration for OpenRouterService routing."""
from __future__ import annotations
import logging
import time
from typing import TYPE_CHECKING, Any
from platform.observability import metrics
try:
    from ..prompt_compression_tool import PromptCompressionTool
except Exception:
    PromptCompressionTool = None
from .budget import enforce_budget_limits
from .cache_layer import check_caches
from .context import prepare_route_state
from .execution import execute_offline, execute_online, handle_failure
from .service import get_settings
if TYPE_CHECKING:
    from .service import OpenRouterService

def route_prompt(service: OpenRouterService, prompt: str, *, task_type: str, model: str | None, provider_opts: dict[str, Any] | None, compress: bool=True) -> dict[str, Any]:
    state = prepare_route_state(service, prompt, task_type, model, provider_opts)
    metrics.ROUTER_DECISIONS.labels(**state.labels()).inc()
    if compress and get_settings().enable_prompt_compression and (PromptCompressionTool is not None):
        try:
            compressor = PromptCompressionTool()
            result = compressor.run(contexts=[prompt], target_token=provider_opts.get('max_tokens', 2000) * 2 if provider_opts else 4000)
            if result.success:
                state.prompt = result.data['compressed_prompt']
                logging.getLogger('router').info(f'Compressed prompt: {result.data['tokens_saved']} tokens saved ({result.data['compression_ratio']:.2%} reduction)')
        except Exception:
            pass
    budget_error = enforce_budget_limits(service, state)
    if budget_error is not None:
        return budget_error
    cache_hit = check_caches(service, state)
    if cache_hit is not None:
        return cache_hit
    state.start_time = time.perf_counter()
    if state.offline_mode:
        return execute_offline(service, state)
    try:
        return execute_online(service, state)
    except Exception as exc:
        return handle_failure(service, state, exc)