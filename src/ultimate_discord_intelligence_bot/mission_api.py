"""Mission API — unified entrypoint for pipeline execution.

This module provides a single, tenant-aware function `run_mission` that all
surfaces (HTTP API, Discord, CLI/Crew) can call to execute the appropriate
pipeline. It intentionally avoids changes to restricted directories and reuses
existing orchestrators.

Behaviors:
- If `inputs` contains a non-empty `url`, it invokes the legacy
  `ContentPipeline.process_video(url, quality)`.
- Otherwise, it invokes the newer `UnifiedPipeline.process_content(...)`.

All results are returned as `ultimate_discord_intelligence_bot.step_result.StepResult`.
Additional metadata (provider/model/policy/etc.) can be attached by callers or
subsystems later; this API preserves and passes through metadata on the
StepResult.
"""
from __future__ import annotations
from typing import Any
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult

def _safe_str(value: Any) -> str | None:
    try:
        if isinstance(value, str):
            v = value.strip()
            return v if v else None
        return None
    except Exception:
        return None

async def run_mission(inputs: dict[str, Any], tenant_ctx: Any | None=None) -> StepResult:
    """Run a mission based on provided inputs within an optional tenant context.

    Args:
        inputs: A mapping that may include:
            - url: Video URL to process (triggers ContentPipeline)
            - quality: Optional max resolution (e.g., "1080p") for downloads
            - content: Free-form content to process with the UnifiedPipeline
            - content_type: Optional content type for UnifiedPipeline (default: analysis)
            - tenant, workspace: Optional identifiers when UnifiedPipeline is used
        tenant_ctx: Optional TenantContext for scoping. If provided, will be used
            with `with_tenant(...)` for the duration of the call.

    Returns:
        StepResult: standardized outcome with any subsystem metadata preserved.
    """
    url = _safe_str(inputs.get('url'))
    content = inputs.get('content')
    from ultimate_discord_intelligence_bot.tenancy import with_tenant
    if url:
        quality = _safe_str(inputs.get('quality')) or '1080p'
        from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
        try:
            with with_tenant(tenant_ctx) if tenant_ctx is not None else with_tenant(None):
                pipeline = ContentPipeline()
                result = await pipeline.process_video(url, quality=quality)
                result = await _maybe_evaluate_and_annotate(result, task_name='url_analysis', inputs=inputs, tenant_ctx=tenant_ctx, pipeline_path='url')
                return result
        except Exception as exc:
            return StepResult.fail(f'ContentPipeline execution failed: {exc!s}', error_category=None)
    from ultimate_discord_intelligence_bot.services.unified_pipeline import PipelineConfig, UnifiedPipeline
    content_text = content if isinstance(content, str) else ''
    content_type = _safe_str(inputs.get('content_type')) or 'analysis'
    tenant = _safe_str(inputs.get('tenant')) or ''
    workspace = _safe_str(inputs.get('workspace')) or ''
    try:
        with with_tenant(tenant_ctx) if tenant_ctx is not None else with_tenant(None):
            pipeline = UnifiedPipeline(PipelineConfig())
            init_result = await pipeline.initialize()
            if not init_result.success:
                return init_result
            result = await pipeline.process_content(content=content_text, content_type=content_type, tenant=tenant, workspace=workspace)
            await pipeline.shutdown()
            result = await _maybe_evaluate_and_annotate(result, task_name=f'unified_{content_type}', inputs=inputs, tenant_ctx=tenant_ctx, pipeline_path='unified')
            return result
    except Exception as exc:
        return StepResult.fail(f'UnifiedPipeline execution failed: {exc!s}', error_category=None)

async def _maybe_evaluate_and_annotate(result: StepResult, task_name: str, inputs: dict[str, Any], tenant_ctx: Any | None=None, pipeline_path: str | None=None) -> StepResult:
    """Run LangSmith-based evaluation if enabled and annotate result with metrics.

    Computes an evaluation signal and emits metrics. If configured, performs a single deterministic backstop retry with a curated model when confidence is low. Always best-effort and non-throwing.
    """
    try:
        from platform.config.configuration import get_config
        cfg = get_config()
        should_eval = bool(getattr(cfg, 'enable_self_eval_gates', False) or getattr(cfg, 'enable_langsmith_eval', False))
        if not should_eval:
            return result
        from ai.evaluation.langsmith_evaluator import LangSmithEvaluator
        from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
        from ultimate_discord_intelligence_bot.services.unified_pipeline import PipelineConfig, UnifiedPipeline
        evaluator = LangSmithEvaluator()
        try:
            output_data = dict(result.data) if isinstance(result.data, dict) else {'result': str(result.data)}
        except Exception:
            output_data = {'result': str(result.data)}
        eval_res = await evaluator.evaluate_output(task_name=task_name, input_data=inputs, output_data=output_data, context={})
        reward = evaluator.get_reward_signal(eval_res)
        result.metadata.update({'eval_overall_score': getattr(eval_res.metrics, 'overall_score', None), 'eval_quality_score': getattr(eval_res.metrics, 'quality_score', None), 'eval_safety_score': getattr(eval_res.metrics, 'safety_score', None), 'eval_latency_ms': getattr(eval_res.metrics, 'latency_ms', None), 'eval_feedback': getattr(eval_res, 'feedback', None), 'eval_regression_detected': getattr(eval_res, 'regression_detected', False), 'eval_passed': getattr(eval_res, 'passed', False), 'reward': reward})
        labels = {'task': task_name}
        try:
            overall = float(getattr(eval_res.metrics, 'overall_score', 0.0) or 0.0)
            latency = float(getattr(eval_res.metrics, 'latency_ms', 0.0) or 0.0)
            get_metrics().histogram('mission_eval_overall_score', overall, labels=labels)
            get_metrics().histogram('mission_eval_latency_ms', latency, labels=labels)
            get_metrics().histogram('mission_reward', float(reward), labels=labels)
        except Exception:
            pass
        try:

            def cfg_get(name: str, default: Any=None) -> Any:
                try:
                    return cfg.get_setting(name, default)
                except Exception:
                    return default
            backstop_enabled = bool(cfg_get('deterministic_backstop_enabled', False))
            threshold = float(cfg_get('backstop_threshold', 0.7) or 0.7)
            overall = float(getattr(eval_res.metrics, 'overall_score', 0.0) or 0.0)
            backstop_needed = backstop_enabled and (not getattr(eval_res, 'passed', False) or overall < threshold)
            if backstop_needed:
                get_metrics().counter('mission_backstop_needed_total', labels=labels).inc()
                result.metadata.setdefault('backstop', {})
                result.metadata['backstop'].update({'needed': True, 'reason': 'eval_below_threshold' if getattr(eval_res, 'passed', False) else 'eval_failed', 'policy': 'quality_first', 'attempted': False})
                already_attempted = bool(inputs.get('_backstop_attempt'))
                if not already_attempted and tenant_ctx is not None and (pipeline_path in {'url', 'unified'}):
                    curated = str(cfg_get('backstop_curated_models', 'anthropic:claude-3-5-sonnet,openai:gpt-4o,google:gemini-1.5-pro') or '').split(',')
                    curated = [c.strip() for c in curated if ':' in c]
                    forced = curated[0] if curated else None
                    if forced:
                        original_summary = {'provider': result.metadata.get('provider'), 'model': result.metadata.get('model'), 'policy': result.metadata.get('policy'), 'eval_overall_score': result.metadata.get('eval_overall_score')}
                        import os
                        prev_force = os.environ.get('FORCE_ROUTER_SELECTION')
                        os.environ['FORCE_ROUTER_SELECTION'] = forced
                        try:
                            from ultimate_discord_intelligence_bot.tenancy import with_tenant
                            if pipeline_path == 'url':
                                url = _safe_str(inputs.get('url')) or ''
                                quality = _safe_str(inputs.get('quality')) or '1080p'
                                with with_tenant(tenant_ctx):
                                    pipeline = ContentPipeline()
                                    retry_res = await pipeline.process_video(url, quality=quality)
                            else:
                                content_text = inputs.get('content') if isinstance(inputs.get('content'), str) else ''
                                content_type = _safe_str(inputs.get('content_type')) or 'analysis'
                                tenant = _safe_str(inputs.get('tenant')) or ''
                                workspace = _safe_str(inputs.get('workspace')) or ''
                                with with_tenant(tenant_ctx):
                                    pipeline = UnifiedPipeline(PipelineConfig())
                                    init_result = await pipeline.initialize()
                                    if init_result.success:
                                        retry_res = await pipeline.process_content(content=content_text, content_type=content_type, tenant=tenant, workspace=workspace)
                                        await pipeline.shutdown()
                                    else:
                                        retry_res = init_result
                            retry_res = await _maybe_evaluate_and_annotate(retry_res, task_name=task_name, inputs={**inputs, '_backstop_attempt': True}, tenant_ctx=tenant_ctx, pipeline_path=pipeline_path)
                            retry_res.metadata.setdefault('backstop', {})
                            retry_res.metadata['backstop'].update({'needed': True, 'attempted': True, 'forced_model': forced, 'original': original_summary})
                            return retry_res
                        finally:
                            if prev_force is None:
                                import contextlib
                                with contextlib.suppress(KeyError):
                                    del os.environ['FORCE_ROUTER_SELECTION']
                            else:
                                os.environ['FORCE_ROUTER_SELECTION'] = prev_force
        except Exception:
            pass
        return result
    except Exception:
        return result
__all__ = ['run_mission']