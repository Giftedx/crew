"""vLLM-based local inference service for high-throughput LLM serving.

This service provides 5-10x throughput improvement over standard implementations
using PagedAttention, continuous batching, and optimized quantization.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

try:
    from vllm import LLM, SamplingParams
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.engine.async_llm_engine import AsyncLLMEngine

    VLLM_AVAILABLE = True
    logger.info("vLLM available for high-performance local inference")
except ImportError:  # pragma: no cover
    LLM = None
    SamplingParams = None
    AsyncEngineArgs = None
    AsyncLLMEngine = None
    VLLM_AVAILABLE = False
    logger.debug("vLLM not available - high-performance local inference disabled")

from core.secure_config import get_config


@dataclass
class vLLMConfig:
    """Configuration for vLLM inference service."""

    model_name: str = "microsoft/DialoGPT-medium"
    tensor_parallel_size: int = 1
    max_model_len: int = 2048
    gpu_memory_utilization: float = 0.9
    quantization: str | None = None  # "awq", "gptq", "squeezellm", etc.
    dtype: str = "auto"  # "half", "float16", "bfloat16", "float32"
    max_num_batched_tokens: int | None = None
    max_num_seqs: int = 256  # Maximum number of sequences in a batch
    max_paddings: int = 256
    enable_prefix_caching: bool = True
    disable_log_stats: bool = False


class vLLMLocalInferenceService:
    """High-performance local LLM inference using vLLM."""

    def __init__(self, config: vLLMConfig | None = None):
        """Initialize vLLM inference service."""
        self.config = config or vLLMConfig()
        self.engine: AsyncLLMEngine | None = None
        self.sync_engine: LLM | None = None
        self.initialized = False
        self.lock = threading.Lock()

        if not VLLM_AVAILABLE:
            logger.warning("vLLM not available - local inference disabled")
            return

        # Load configuration from secure config
        try:
            secure_config = get_config()
            self.config.model_name = getattr(secure_config, "vllm_model_name", self.config.model_name)
            self.config.tensor_parallel_size = int(
                getattr(secure_config, "vllm_tensor_parallel_size", self.config.tensor_parallel_size)
            )
            self.config.max_model_len = int(getattr(secure_config, "vllm_max_model_len", self.config.max_model_len))
            self.config.gpu_memory_utilization = float(
                getattr(secure_config, "vllm_gpu_memory_utilization", self.config.gpu_memory_utilization)
            )
            self.config.quantization = getattr(secure_config, "vllm_quantization", self.config.quantization)
        except Exception as e:
            logger.warning(f"Could not load vLLM configuration: {e}")

    def initialize_sync_engine(self) -> bool:
        """Initialize synchronous vLLM engine."""
        if not VLLM_AVAILABLE:
            return False

        with self.lock:
            if self.sync_engine is not None:
                return True

            try:
                logger.info(f"Initializing vLLM sync engine with model: {self.config.model_name}")

                self.sync_engine = LLM(
                    model=self.config.model_name,
                    tensor_parallel_size=self.config.tensor_parallel_size,
                    max_model_len=self.config.max_model_len,
                    gpu_memory_utilization=self.config.gpu_memory_utilization,
                    quantization=self.config.quantization,
                    dtype=self.config.dtype,
                    max_num_batched_tokens=self.config.max_num_batched_tokens,
                    max_num_seqs=self.config.max_num_seqs,
                    enable_prefix_caching=self.config.enable_prefix_caching,
                    disable_log_stats=self.config.disable_log_stats,
                )

                self.initialized = True
                logger.info("vLLM sync engine initialized successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to initialize vLLM sync engine: {e}")
                return False

    async def initialize_async_engine(self) -> bool:
        """Initialize asynchronous vLLM engine for better throughput."""
        if not VLLM_AVAILABLE:
            return False

        if self.engine is not None:
            return True

        try:
            logger.info(f"Initializing vLLM async engine with model: {self.config.model_name}")

            engine_args = AsyncEngineArgs(
                model=self.config.model_name,
                tensor_parallel_size=self.config.tensor_parallel_size,
                max_model_len=self.config.max_model_len,
                gpu_memory_utilization=self.config.gpu_memory_utilization,
                quantization=self.config.quantization,
                dtype=self.config.dtype,
                max_num_batched_tokens=self.config.max_num_batched_tokens,
                max_num_seqs=self.config.max_num_seqs,
                max_paddings=self.config.max_paddings,
                enable_prefix_caching=self.config.enable_prefix_caching,
                disable_log_stats=self.config.disable_log_stats,
            )

            self.engine = AsyncLLMEngine.from_engine_args(engine_args)
            self.initialized = True
            logger.info("vLLM async engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize vLLM async engine: {e}")
            return False

    def generate_sync(
        self,
        prompts: list[str],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512,
        stop: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate responses synchronously with batching."""
        if not self.initialized or not self.sync_engine:
            if not self.initialize_sync_engine():
                return [{"error": "vLLM engine not available"} for _ in prompts]

        # At this point, sync_engine should be initialized
        if self.sync_engine is None:
            return [{"error": "Failed to initialize sync engine"} for _ in prompts]

        try:
            start_time = time.time()

            # Create sampling parameters
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stop=stop,
            )

            # Generate responses (automatically batched by vLLM)
            outputs = self.sync_engine.generate(prompts, sampling_params)

            generation_time = time.time() - start_time

            # Format results
            results = []
            for output in outputs:
                result = {
                    "text": output.outputs[0].text,
                    "finish_reason": output.outputs[0].finish_reason,
                    "tokens_generated": len(output.outputs[0].token_ids),
                    "generation_time": generation_time / len(outputs),  # Per-prompt time
                }
                results.append(result)

            logger.debug(
                f"Generated {len(results)} responses in {generation_time:.2f}s "
                f"({len(results) / generation_time:.1f} requests/sec)"
            )

            return results

        except Exception as e:
            logger.error(f"vLLM sync generation failed: {e}")
            return [{"error": str(e)} for _ in prompts]

    async def generate_async(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512,
        stop: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate response asynchronously."""
        if not self.initialized or not self.engine:
            if not await self.initialize_async_engine():
                return {"error": "vLLM async engine not available"}

        # At this point, engine should be initialized
        if self.engine is None:
            return {"error": "Failed to initialize async engine"}

        try:
            start_time = time.time()

            # Create sampling parameters
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stop=stop,
            )

            # Generate response
            request_id = f"req_{int(time.time() * 1000)}"
            results_generator = self.engine.generate(prompt, sampling_params, request_id)

            # Collect all results
            final_output = None
            async for request_output in results_generator:
                final_output = request_output

            generation_time = time.time() - start_time

            if final_output is None:
                return {"error": "No output generated"}

            # Format result
            result = {
                "text": final_output.outputs[0].text,
                "finish_reason": final_output.outputs[0].finish_reason,
                "tokens_generated": len(final_output.outputs[0].token_ids),
                "generation_time": generation_time,
            }

            logger.debug(f"Generated async response in {generation_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"vLLM async generation failed: {e}")
            return {"error": str(e)}

    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 512,
        stop: list[str] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generate streaming response."""
        if not self.initialized or not self.engine:
            if not await self.initialize_async_engine():
                yield {"error": "vLLM async engine not available"}
                return

        # At this point, engine should be initialized
        if self.engine is None:
            yield {"error": "Failed to initialize async engine"}
            return

        try:
            # Create sampling parameters
            sampling_params = SamplingParams(
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stop=stop,
            )

            # Generate streaming response
            request_id = f"stream_{int(time.time() * 1000)}"
            results_generator = self.engine.generate(prompt, sampling_params, request_id)

            async for request_output in results_generator:
                # Yield incremental updates
                if request_output.outputs:
                    output = request_output.outputs[0]
                    yield {
                        "text": output.text,
                        "finish_reason": output.finish_reason,
                        "tokens_generated": len(output.token_ids),
                        "finished": request_output.finished,
                    }

        except Exception as e:
            logger.error(f"vLLM streaming generation failed: {e}")
            yield {"error": str(e)}

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the loaded model."""
        if not self.initialized:
            return {"error": "Engine not initialized"}

        return {
            "model_name": self.config.model_name,
            "tensor_parallel_size": self.config.tensor_parallel_size,
            "max_model_len": self.config.max_model_len,
            "gpu_memory_utilization": self.config.gpu_memory_utilization,
            "quantization": self.config.quantization,
            "dtype": self.config.dtype,
            "max_num_seqs": self.config.max_num_seqs,
            "prefix_caching_enabled": self.config.enable_prefix_caching,
            "vllm_available": VLLM_AVAILABLE,
            "initialized": self.initialized,
        }


# Global service instance
_vllm_service: vLLMLocalInferenceService | None = None


def get_vllm_service() -> vLLMLocalInferenceService:
    """Get the global vLLM inference service."""
    global _vllm_service
    if _vllm_service is None:
        _vllm_service = vLLMLocalInferenceService()
    return _vllm_service


def is_vllm_available() -> bool:
    """Check if vLLM is available and configured."""
    return VLLM_AVAILABLE and get_vllm_service().initialized


# Integration with OpenRouter service for local model routing
class vLLMOpenRouterAdapter:
    """Adapter to use vLLM with OpenRouter-like interface."""

    def __init__(self):
        self.vllm_service = get_vllm_service()

    def route_to_local_model(
        self,
        prompt: str,
        model: str,
        task_type: str = "general",
    ) -> dict[str, Any]:
        """Route request to local vLLM model."""
        if not model.startswith("local/"):
            return {"error": "Not a local model"}

        # Extract local model name
        # Local model name extraction removed (unused variable)

        try:
            # Use sync generation for OpenRouter compatibility
            results = self.vllm_service.generate_sync(
                prompts=[prompt],
                temperature=0.1,  # Lower temperature for consistency
                max_tokens=512,
            )

            if results and "error" not in results[0]:
                result = results[0]
                return {
                    "status": "success",
                    "model": model,
                    "response": result["text"],
                    "tokens": result["tokens_generated"],
                    "generation_time": result["generation_time"],
                    "local_inference": True,
                }
            else:
                error = results[0].get("error", "Unknown error") if results else "No results"
                return {
                    "status": "error",
                    "error": f"vLLM generation failed: {error}",
                    "model": model,
                }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Local model routing failed: {e}",
                "model": model,
            }
