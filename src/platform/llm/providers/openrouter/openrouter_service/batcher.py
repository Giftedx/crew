"""Request batching for OpenRouter service.

This module provides request batching capabilities to efficiently
process multiple concurrent requests to the same model.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags


if TYPE_CHECKING:
    from .service import OpenRouterService
log = logging.getLogger(__name__)


@dataclass
class BatchedRequest:
    """Represents a request in a batch."""

    prompt: str
    task_type: str
    model: str
    provider_opts: dict[str, Any] | None
    future: asyncio.Future[dict[str, Any]]
    request_id: str
    timestamp: float


@dataclass
class BatchConfig:
    """Configuration for request batching."""

    batch_size: int = 5
    wait_time_ms: int = 50
    max_wait_time_ms: int = 500
    enable_batching: bool = True


class RequestBatcher:
    """Batches concurrent requests for efficient processing."""

    def __init__(self, service: OpenRouterService, config: BatchConfig | None = None) -> None:
        """Initialize request batcher.

        Args:
            service: The OpenRouter service instance
            config: Batching configuration
        """
        self._service = service
        self._config = config or BatchConfig()
        self._feature_flags = FeatureFlags()
        self._batches: dict[str, list[BatchedRequest]] = defaultdict(list)
        self._batch_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._processing_tasks: dict[str, asyncio.Task] = {}
        self._stats = {
            "total_requests": 0,
            "batched_requests": 0,
            "individual_requests": 0,
            "batches_processed": 0,
            "average_batch_size": 0.0,
            "total_savings_ms": 0.0,
        }

    def _get_batch_key(self, model: str, task_type: str) -> str:
        """Generate a key for batching requests.

        Args:
            model: The model name
            task_type: The task type

        Returns:
            Batch key string
        """
        return f"{model}:{task_type}"

    async def _process_batch(self, batch_key: str, requests: list[BatchedRequest]) -> None:
        """Process a batch of requests.

        Args:
            batch_key: The batch key
            requests: List of requests to process
        """
        try:
            if not requests:
                return
            start_time = time.perf_counter()
            model = requests[0].model
            batch_payload = {
                "model": model,
                "messages": [{"role": "user", "content": req.prompt} for req in requests],
                "batch_mode": True,
            }
            if requests[0].provider_opts:
                batch_payload["provider"] = requests[0].provider_opts
            result = await self._make_batch_request(batch_payload)
            if result.get("status") == "success":
                responses = result.get("responses", [])
                for i, request in enumerate(requests):
                    if i < len(responses):
                        response = responses[i]
                        request.future.set_result(
                            {
                                "status": "success",
                                "model": model,
                                "response": response,
                                "tokens": self._service.prompt_engine.count_tokens(response, model),
                                "provider": requests[0].provider_opts,
                                "batched": True,
                            }
                        )
                    else:
                        request.future.set_result(
                            {
                                "status": "error",
                                "error": "No response in batch",
                                "model": model,
                                "tokens": 0,
                                "provider": requests[0].provider_opts,
                            }
                        )
            else:
                error_response = {
                    "status": "error",
                    "error": result.get("error", "Batch request failed"),
                    "model": model,
                    "tokens": 0,
                    "provider": requests[0].provider_opts,
                }
                for request in requests:
                    request.future.set_result(error_response)
            processing_time = time.perf_counter() - start_time
            self._stats["batches_processed"] += 1
            self._stats["batched_requests"] += len(requests)
            current_avg = self._stats["average_batch_size"]
            batch_count = self._stats["batches_processed"]
            self._stats["average_batch_size"] = (current_avg * (batch_count - 1) + len(requests)) / batch_count
            estimated_individual_time = len(requests) * 100
            actual_time = processing_time * 1000
            savings = max(0, estimated_individual_time - actual_time)
            self._stats["total_savings_ms"] += savings
            log.debug(
                "Processed batch of %d requests in %.2fms (estimated savings: %.2fms)",
                len(requests),
                actual_time,
                savings,
            )
        except Exception as e:
            log.error("Batch processing failed: %s", e)
            error_response = {
                "status": "error",
                "error": f"Batch processing failed: {e!s}",
                "model": requests[0].model if requests else "unknown",
                "tokens": 0,
                "provider": requests[0].provider_opts if requests else {},
            }
            for request in requests:
                if not request.future.done():
                    request.future.set_result(error_response)

    async def _make_batch_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Make a batch request to the OpenRouter API.

        Args:
            payload: The batch request payload

        Returns:
            Response dictionary
        """
        try:
            messages = payload.get("messages", [])
            responses = []
            for message in messages:
                individual_payload = {"model": payload["model"], "messages": [message]}
                if "provider" in payload:
                    individual_payload["provider"] = payload["provider"]
                result = self._service.route(
                    prompt=message["content"],
                    task_type="general",
                    model=payload["model"],
                    provider_opts=payload.get("provider"),
                )
                if result.success:
                    responses.append(result.data.get("response", ""))
                else:
                    responses.append(f"Error: {result.error}")
            return {"status": "success", "responses": responses}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def add_request(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a request to the batch or process individually.

        Args:
            prompt: The prompt to process
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options

        Returns:
            Response dictionary
        """
        if not self._feature_flags.ENABLE_OPENROUTER_REQUEST_BATCHING or not self._config.enable_batching:
            result = self._service.route(prompt, task_type, model, provider_opts)
            self._stats["individual_requests"] += 1
            return result.data if result.success else {"status": "error", "error": result.error}
        model = model or "openai/gpt-4o-mini"
        batch_key = self._get_batch_key(model, task_type)
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        request = BatchedRequest(
            prompt=prompt,
            task_type=task_type,
            model=model,
            provider_opts=provider_opts,
            future=future,
            request_id=f"{batch_key}_{int(time.time() * 1000)}",
            timestamp=time.time(),
        )
        async with self._batch_locks[batch_key]:
            self._batches[batch_key].append(request)
            self._stats["total_requests"] += 1
            should_process = len(self._batches[batch_key]) >= self._config.batch_size or (
                self._batches[batch_key]
                and time.time() - self._batches[batch_key][0].timestamp >= self._config.max_wait_time_ms / 1000
            )
            if should_process:
                batch_requests = self._batches[batch_key].copy()
                self._batches[batch_key].clear()
                task = asyncio.create_task(self._process_batch(batch_key, batch_requests))
                self._processing_tasks[batch_key] = task
                task.add_done_callback(lambda t: self._processing_tasks.pop(batch_key, None))
            elif batch_key not in self._processing_tasks:
                task = asyncio.create_task(self._wait_and_process_batch(batch_key))
                self._processing_tasks[batch_key] = task
                task.add_done_callback(lambda t: self._processing_tasks.pop(batch_key, None))
        return await future

    async def _wait_and_process_batch(self, batch_key: str) -> None:
        """Wait for the configured time and then process the batch.

        Args:
            batch_key: The batch key to process
        """
        try:
            await asyncio.sleep(self._config.wait_time_ms / 1000)
            async with self._batch_locks[batch_key]:
                if self._batches[batch_key]:
                    batch_requests = self._batches[batch_key].copy()
                    self._batches[batch_key].clear()
                    await self._process_batch(batch_key, batch_requests)
        except Exception as e:
            log.error("Error in wait and process batch: %s", e)

    def get_stats(self) -> dict[str, Any]:
        """Get batching statistics.

        Returns:
            Dictionary with batching statistics
        """
        total_requests = self._stats["total_requests"]
        batching_rate = self._stats["batched_requests"] / total_requests * 100 if total_requests > 0 else 0
        return {
            **self._stats,
            "batching_rate_percent": round(batching_rate, 2),
            "active_batches": len(self._batches),
            "active_processing_tasks": len(self._processing_tasks),
            "config": {
                "batch_size": self._config.batch_size,
                "wait_time_ms": self._config.wait_time_ms,
                "max_wait_time_ms": self._config.max_wait_time_ms,
                "enable_batching": self._config.enable_batching,
            },
        }

    def reset_stats(self) -> None:
        """Reset batching statistics."""
        self._stats = {
            "total_requests": 0,
            "batched_requests": 0,
            "individual_requests": 0,
            "batches_processed": 0,
            "average_batch_size": 0.0,
            "total_savings_ms": 0.0,
        }

    async def flush_all_batches(self) -> None:
        """Flush all pending batches immediately."""
        for batch_key in list(self._batches.keys()):
            async with self._batch_locks[batch_key]:
                if self._batches[batch_key]:
                    batch_requests = self._batches[batch_key].copy()
                    self._batches[batch_key].clear()
                    await self._process_batch(batch_key, batch_requests)

    async def close(self) -> None:
        """Close the batcher and process any remaining batches."""
        await self.flush_all_batches()
        for task in self._processing_tasks.values():
            if not task.done():
                task.cancel()
        if self._processing_tasks:
            await asyncio.gather(*self._processing_tasks.values(), return_exceptions=True)
        log.debug("Request batcher closed")


class BatchManager:
    """Manages request batching across the service."""

    def __init__(self, service: OpenRouterService) -> None:
        """Initialize batch manager.

        Args:
            service: The OpenRouter service instance
        """
        self._service = service
        self._batcher = RequestBatcher(service)
        self._feature_flags = FeatureFlags()

    async def route_batched(
        self,
        prompt: str,
        task_type: str = "general",
        model: str | None = None,
        provider_opts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Route a request with batching support.

        Args:
            prompt: The prompt to route
            task_type: Type of task
            model: Specific model to use
            provider_opts: Provider-specific options

        Returns:
            Response dictionary
        """
        return await self._batcher.add_request(prompt, task_type, model, provider_opts)

    def get_stats(self) -> dict[str, Any]:
        """Get batch manager statistics.

        Returns:
            Dictionary with batch statistics
        """
        return self._batcher.get_stats()

    async def close(self) -> None:
        """Close the batch manager."""
        await self._batcher.close()


_batch_manager: BatchManager | None = None


def get_batch_manager(service: OpenRouterService) -> BatchManager:
    """Get or create batch manager for the service.

    Args:
        service: The OpenRouter service instance

    Returns:
        BatchManager instance
    """
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = BatchManager(service)
    return _batch_manager


async def close_batch_manager() -> None:
    """Close the global batch manager."""
    global _batch_manager
    if _batch_manager:
        await _batch_manager.close()
        _batch_manager = None
