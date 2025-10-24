"""High-level orchestration for OpenRouterService routing."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from obs import metrics

from ..prompt_compression_tool import PromptCompressionTool
from ..settings import get_settings
from .budget import enforce_budget_limits
from .cache_layer import check_caches
from .context import prepare_route_state
from .execution import execute_offline, execute_online, handle_failure


if TYPE_CHECKING:  # pragma: no cover
    from .service import OpenRouterService


def route_prompt(
    service: OpenRouterService,
    prompt: str,
    *,
    task_type: str,
    model: str | None,
    provider_opts: dict[str, Any] | None,
    compress: bool = True,
) -> dict[str, Any]:
    state = prepare_route_state(service, prompt, task_type, model, provider_opts)
    metrics.ROUTER_DECISIONS.labels(**state.labels()).inc()

    if compress and get_settings().enable_prompt_compression:
        compressor = PromptCompressionTool()
        result = compressor.run(
            contexts=[prompt],
            target_token=provider_opts.get("max_tokens", 2000) * 2 if provider_opts else 4000,
        )
        if result.success:
            state.prompt = result.data["compressed_prompt"]
            logging.getLogger("router").info(
                f"Compressed prompt: {result.data['tokens_saved']} tokens saved "
                f"({result.data['compression_ratio']:.2%} reduction)"
            )

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
    except Exception as exc:  # pragma: no cover
        return handle_failure(service, state, exc)
