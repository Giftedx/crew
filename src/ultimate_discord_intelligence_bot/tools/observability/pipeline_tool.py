"""Pipeline tool for orchestrating multi-step operations per Copilot instructions."""
from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, TypedDict
from core.circuit_breaker_canonical import CircuitBreaker
from ultimate_discord_intelligence_bot.settings import Settings
from platform.core.step_result import StepResult
from ..platform.observability.metrics import get_metrics
from ..pipeline import ContentPipeline
from ._base import BaseTool
logger = logging.getLogger(__name__)

class _PipelineResult(TypedDict, total=False):
    status: str
    url: str
    quality: str
    processing_time: float
    timestamp: float
    data: Any
    error: str

class PipelineTool(BaseTool[StepResult]):
    """Tool wrapping the content pipeline with circuit breaker protection."""
    name: str = 'Content Pipeline Tool'
    description: str = 'Download, transcribe, analyse and post a video to Discord. Provide url and optional quality.'
    _circuit_breaker: CircuitBreaker | None = None

    def __init__(self, pipeline: Any | None=None):
        self.pipeline = pipeline
        self._metrics = get_metrics()
        if PipelineTool._circuit_breaker is None:
            settings = Settings()
            failure_threshold = getattr(settings, 'pipeline_circuit_failure_threshold', 5)
            recovery_timeout = getattr(settings, 'pipeline_circuit_recovery_timeout', 60.0)
            success_threshold = getattr(settings, 'pipeline_circuit_success_threshold', 2)
            from core.circuit_breaker_canonical import CircuitConfig
            circuit_config = CircuitConfig(failure_threshold=failure_threshold, recovery_timeout=recovery_timeout, success_threshold=success_threshold)
            PipelineTool._circuit_breaker = CircuitBreaker(name='pipeline_tool', config=circuit_config)
            logger.info(f'Initialized pipeline circuit breaker: failure_threshold={failure_threshold}, recovery_timeout={recovery_timeout}s, success_threshold={success_threshold}')

    async def _run(self, url: str, quality: str='1080p', *, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Process video with comprehensive error handling, tenancy, and circuit breaker protection."""
        start_time = time.time()
        if self._circuit_breaker:
            can_execute, _reason = self._circuit_breaker.can_execute()
            if not can_execute:
                duration = time.time() - start_time
                self._metrics.histogram('tool_run_seconds', duration, labels={'tool': 'pipeline'})
                self._metrics.counter('tool_runs_total', labels={'tool': 'pipeline', 'outcome': 'circuit_breaker_open'}).inc()
                error_msg = f'Pipeline circuit breaker is open (too many recent failures). Service temporarily unavailable. Retry after {self._circuit_breaker.recovery_timeout}s.'
                logger.warning(f'Pipeline request rejected by circuit breaker: {url}')
                return StepResult.fail(error=error_msg, url=url, quality=quality, processing_time=duration, timestamp=time.time(), circuit_breaker_status=self._circuit_breaker.get_health_status() if self._circuit_breaker else None)
        try:
            if not url or not isinstance(url, str):
                duration = time.time() - start_time
                self._metrics.histogram('tool_run_seconds', duration, labels={'tool': 'pipeline'})
                self._metrics.counter('tool_runs_total', labels={'tool': 'pipeline', 'outcome': 'error'}).inc()
                if self._circuit_breaker:
                    self._circuit_breaker.record_failure()
                return StepResult.fail(error='URL is required and must be a string', url=url, quality=quality)
            if not quality or not isinstance(quality, str) or (not quality.strip()):
                settings = Settings()
                default_quality = getattr(settings, 'download_quality_default', '720p')
                quality = quality or quality.strip() or default_quality
            logger.info(f'Starting pipeline processing for URL: {url} with quality: {quality}')
            pipeline = ContentPipeline()
            if tenant_id and workspace_id:
                try:
                    from ..tenancy import TenantContext, with_tenant
                    tenant_ctx = TenantContext(tenant_id=tenant_id, workspace_id=workspace_id)
                    with with_tenant(tenant_ctx):
                        result = await pipeline.process_video(url, quality=quality)
                except ImportError:
                    logger.warning('Tenancy modules not found, running without tenant context.')
                    result = await pipeline.process_video(url, quality=quality)
            else:
                result = await pipeline.process_video(url, quality=quality)
            status_raw = result.get('status')
            payload: Any = result.get('data', result)
            processing_time = time.time() - start_time
            if status_raw != 'success':
                error_msg = result.get('error') or f'Pipeline failed at step: {result.get('step', 'unknown')}'
                logger.error(f'Pipeline processing failed for URL {url}: {error_msg}')
                self._metrics.counter('tool_runs_total', labels={'tool': 'pipeline', 'outcome': 'error'}).inc()
                self._metrics.histogram('tool_run_seconds', processing_time, labels={'tool': 'pipeline'})
                if self._circuit_breaker:
                    self._circuit_breaker.record_failure()
                return StepResult.fail(error=error_msg, url=url, quality=quality, processing_time=processing_time, timestamp=time.time(), data=payload, circuit_breaker_status=self._circuit_breaker.get_health_status() if self._circuit_breaker else None)
            logger.info(f'Pipeline processing completed successfully in {processing_time:.2f}s')
            self._metrics.counter('tool_runs_total', labels={'tool': 'pipeline', 'outcome': 'success'}).inc()
            self._metrics.histogram('tool_run_seconds', processing_time, labels={'tool': 'pipeline'})
            if self._circuit_breaker:
                self._circuit_breaker.record_success()
            return StepResult.ok(url=url, quality=quality, processing_time=processing_time, timestamp=time.time(), data=payload, circuit_breaker_status=self._circuit_breaker.get_health_status() if self._circuit_breaker else None)
        except Exception as e:
            error_msg = str(e)
            processing_time = time.time() - start_time
            logger.error(f'Pipeline processing failed for URL {url}: {error_msg}')
            self._metrics.counter('tool_runs_total', labels={'tool': 'pipeline', 'outcome': 'error'}).inc()
            self._metrics.histogram('tool_run_seconds', processing_time, labels={'tool': 'pipeline'})
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()
            return StepResult.fail(error=error_msg, url=url, quality=quality, processing_time=processing_time, timestamp=time.time(), circuit_breaker_status=self._circuit_breaker.get_health_status() if self._circuit_breaker else None)

    def run(self, url: str, quality: str='1080p', *, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Run pipeline with proper async handling."""
        try:
            loop = asyncio.get_running_loop()
            if loop and loop.is_running():
                import concurrent.futures

                def run_in_thread():
                    return asyncio.run(self._run_async(url, quality, tenant_id=tenant_id, workspace_id=workspace_id))
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=300)
        except RuntimeError:
            pass
        return asyncio.run(self._run_async(url, quality, tenant_id=tenant_id, workspace_id=workspace_id))

    async def _run_async(self, url: str, quality: str='1080p', *, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Async version for use within async contexts."""
        return await self._run(url, quality, tenant_id=tenant_id, workspace_id=workspace_id)

    def execute_pipeline_steps(self, steps: list[str], input_data: dict[str, Any]) -> StepResult:
        """Execute pipeline steps following StepResult pattern per instruction #3."""
        if not steps:
            return StepResult.skip(reason='No pipeline steps provided')
        try:
            current_data = input_data
            results: list[dict[str, object]] = []
            for step_name in steps:
                step_result = self._execute_step(step_name, current_data)
                if not step_result.success:
                    return StepResult.fail(error=f'Pipeline failed at step: {step_name}', data={'failed_step': step_name, 'completed_steps': results, 'error': step_result.error})
                current_data = step_result.data
                results.append({'step': step_name, 'success': True, 'data': current_data})
            return StepResult.ok(data={'pipeline_results': results, 'final_output': current_data})
        except Exception as e:
            return StepResult.fail(error=f'Pipeline execution error: {e!s}')

    def _execute_step(self, step_name: str, input_data: dict[str, Any]) -> StepResult:
        """Execute a single pipeline step."""
        if step_name == 'validate':
            if not input_data:
                return StepResult.fail(error='Validation failed: empty input')
            return StepResult.ok(data=input_data)
        elif step_name == 'transform':
            transformed = {**input_data, 'transformed': True}
            return StepResult.ok(data=transformed)
        elif step_name == 'enrich':
            enriched = {**input_data, 'enriched': True, 'metadata': {}}
            return StepResult.ok(data=enriched)
        else:
            return StepResult.skip(reason=f'Unknown step: {step_name}')