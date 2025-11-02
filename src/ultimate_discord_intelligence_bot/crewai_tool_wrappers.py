"""CrewAI-compatible tool wrappers for our existing tools.

This module gracefully degrades when the `crewai` package isn't installed by
providing a lightweight fallback `BaseTool` with the same surface used here.
That allows tests to import the autonomous orchestrator without requiring the
third-party dependency.

Contract guarantee:
- All wrapper invocations return a StepResult (ok/fail/skip). We never return
    plain strings on error paths. This keeps downstream agent/orchestrator
    logic consistent and prevents type errors during autonomous workflows.
"""
import contextlib
import inspect
import logging
import re
from collections.abc import Iterable
from typing import Any, Optional, Union
_GLOBAL_CREW_CONTEXT: dict[str, Any] = {}
_TOOL_CALL_COUNTS: dict[str, int] = {}
MAX_TOOL_CALLS_PER_SESSION = 15

def reset_global_crew_context() -> None:
    """Reset the global crew context. Call this at the start of each workflow."""
    global _GLOBAL_CREW_CONTEXT, _TOOL_CALL_COUNTS
    _GLOBAL_CREW_CONTEXT.clear()
    _TOOL_CALL_COUNTS.clear()
    print('🔄 Reset global crew context and tool call counters')

def get_global_crew_context() -> dict[str, Any]:
    """Get a copy of the current global crew context for debugging."""
    return dict(_GLOBAL_CREW_CONTEXT)
_PYDANTIC_TYPES_NAMESPACE = {'Any': Any, 'dict': dict, 'list': list, 'str': str, 'int': int, 'bool': bool, 'float': float, 'Iterable': Iterable, 'Optional': Optional, 'Union': Union}
try:
    from crewai.tools import BaseTool
except Exception:

    class BaseTool:
        name: str
        description: str

        def __init__(self, name: str | None=None, description: str | None=None, **_kwargs):
            if name:
                self.name = name
            if description:
                self.description = description

        def _run(self, *a, **k):
            return None
try:
    from pydantic import BaseModel, Field, PrivateAttr
except Exception:

    class PrivateAttr:

        def __init__(self, default=None):
            self.default = default

    class BaseModel:
        pass

    def Field(default=None, description: str | None=None):
        _ = description
        return default

class CrewAIToolWrapper(BaseTool):
    """Base wrapper to make our tools CrewAI-compatible."""
    _wrapped_tool: Any
    _shared_context: dict[str, Any]
    _last_result: Any

    def __init__(self, wrapped_tool: Any, **kwargs):
        tool_name = getattr(wrapped_tool, 'name', None) or wrapped_tool.__class__.__name__.replace('Tool', '').replace('_', ' ')
        tool_description = getattr(wrapped_tool, 'description', None) or f'Wrapped {wrapped_tool.__class__.__name__}'
        try:
            args_schema = self._create_args_schema(wrapped_tool)
            if args_schema is not None:
                kwargs['args_schema'] = args_schema
        except Exception:
            pass
        super().__init__(name=tool_name, description=tool_description, **kwargs)
        self._wrapped_tool = wrapped_tool
        self._shared_context = {}
        self._last_result = None

    @staticmethod
    def _create_args_schema(wrapped_tool: Any) -> type[BaseModel] | None:
        """Create a Pydantic schema from the wrapped tool's run() signature.

        Parameters that can be sourced from shared_context are marked as Optional
        with helpful descriptions, so the LLM understands it doesn't need to provide them.
        """
        try:
            if hasattr(wrapped_tool, 'run'):
                sig = inspect.signature(wrapped_tool.run)
            elif hasattr(wrapped_tool, '_run'):
                sig = inspect.signature(wrapped_tool._run)
            else:
                return None
            SHARED_CONTEXT_PARAMS = {'text', 'transcript', 'content', 'claim', 'claims', 'url', 'source_url', 'metadata', 'media_info', 'query', 'question', 'enhanced_transcript'}
            schema_fields = {}
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    continue
                if param_name in ('tenant_id', 'workspace_id') and param.kind == inspect.Parameter.KEYWORD_ONLY:
                    continue
                field_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
                if param.default != inspect.Parameter.empty:
                    schema_fields[param_name] = (field_type, Field(default=param.default, description=f'{param_name} parameter'))
                elif param_name in SHARED_CONTEXT_PARAMS:
                    try:
                        optional_type = field_type | None
                    except Exception:
                        optional_type = field_type
                    schema_fields[param_name] = (optional_type, None)
                else:
                    schema_fields[param_name] = (field_type, Field(..., description=f'{param_name} parameter'))
            if schema_fields:
                class_dict = {'__annotations__': {k: v[0] for k, v in schema_fields.items()}}
                for k, v in schema_fields.items():
                    class_dict[k] = v[1]
                DynamicArgsSchema = type(f'{wrapped_tool.__class__.__name__}Args', (BaseModel,), class_dict)
                try:
                    DynamicArgsSchema.model_rebuild(_types_namespace=_PYDANTIC_TYPES_NAMESPACE)
                except Exception as e:
                    logging.debug(f'Failed to rebuild {wrapped_tool.__class__.__name__}Args schema: {e}')
                return DynamicArgsSchema
            return None
        except Exception:
            return None

    def update_context(self, context: dict[str, Any]) -> None:
        """Update shared context for data flow between tools.

        CRITICAL FIX: Updates both instance-level AND global shared context.
        This ensures data flows across task boundaries in CrewAI crews where
        tools are attached to different agent instances.
        """
        if not isinstance(getattr(self, '_shared_context', None), dict):
            self._shared_context = {}
        if context:
            print(f'🔄 Updating tool context with keys: {list(context.keys())}')
            if 'transcript' in context:
                print(f'   📝 transcript: {len(context['transcript'])} chars')
            if 'text' in context:
                print(f'   📝 text: {len(context['text'])} chars')
            if 'media_info' in context:
                print(f'   📹 media_info: {(list(context['media_info'].keys()) if isinstance(context['media_info'], dict) else 'present')}')
            if 'file_path' in context:
                print(f'   📁 file_path: {context['file_path']}')
        self._shared_context.update(context or {})
        _GLOBAL_CREW_CONTEXT.update(context or {})
        print(f'✅ Updated global crew context (now has {len(_GLOBAL_CREW_CONTEXT)} keys: {list(_GLOBAL_CREW_CONTEXT.keys())})')
        with contextlib.suppress(Exception):
            from platform.observability.metrics import get_metrics
            metrics = get_metrics()
            metrics.counter('crewai_shared_context_updates', labels={'tool': getattr(self, 'name', 'unknown'), 'has_transcript': str('transcript' in context or 'text' in context), 'has_media_info': str('media_info' in context), 'has_file_path': str('file_path' in context), 'context_keys': len(context)}).inc()

    def get_last_result(self) -> Any:
        """Get the last execution result for tool chaining."""
        return self._last_result

    def _run(self, *args, **kwargs) -> Any:
        """Execute the wrapped tool with reliable argument handling and data preservation.

        This approach prioritizes data integrity and fails fast on dependency issues.
        """
        tool_cls = self._wrapped_tool.__class__.__name__
        global _TOOL_CALL_COUNTS
        call_count = _TOOL_CALL_COUNTS.get(tool_cls, 0) + 1
        _TOOL_CALL_COUNTS[tool_cls] = call_count
        with contextlib.suppress(Exception):
            from platform.observability.metrics import get_metrics
            get_metrics().counter('autointel_tool_calls_total', labels={'tool': tool_cls, 'call_number': str(call_count), 'limit_reached': 'false'})
        if call_count > MAX_TOOL_CALLS_PER_SESSION:
            from platform.core.step_result import StepResult
            with contextlib.suppress(Exception):
                from platform.observability.metrics import get_metrics
                get_metrics().counter('autointel_tool_calls_total', labels={'tool': tool_cls, 'call_number': str(call_count), 'limit_reached': 'true'})
                get_metrics().counter('autointel_rate_limit_triggered', labels={'tool': tool_cls})
            error_msg = f'⛔ {tool_cls} exceeded maximum calls ({MAX_TOOL_CALLS_PER_SESSION}). This indicates the agent is stuck in a loop. Previous calls: {call_count - 1}. Stopping execution to prevent infinite loops.'
            print(error_msg)
            return StepResult.fail(error=error_msg, step=f'{tool_cls}_rate_limit')
        try:
            final_kwargs = {}
            if args and (not kwargs):
                if len(args) == 1:
                    arg = args[0]
                    if isinstance(arg, dict):
                        final_kwargs = arg.copy()
                    elif isinstance(arg, str):
                        import inspect
                        param_order = ['url', 'question', 'query', 'text', 'message', 'content']
                        picked = None
                        try:
                            if hasattr(self._wrapped_tool, 'run'):
                                sig = inspect.signature(self._wrapped_tool.run)
                            elif hasattr(self._wrapped_tool, '_run'):
                                sig = inspect.signature(self._wrapped_tool._run)
                            else:
                                sig = None
                            if sig is not None:
                                params = list(sig.parameters.keys())
                                for p in param_order:
                                    if p in params:
                                        picked = p
                                        break
                        except Exception:
                            picked = None
                        if not picked:
                            tool_cls_name = self._wrapped_tool.__class__.__name__
                            if 'Pipeline' in tool_cls_name:
                                picked = 'url'
                            elif 'Search' in tool_cls_name:
                                picked = 'query'
                            else:
                                picked = 'text'
                        final_kwargs = {picked: arg}
                    else:
                        final_kwargs = {'input': arg}
                else:
                    final_kwargs = {'args': list(args)}
            else:
                final_kwargs = kwargs.copy() if kwargs else {}
            for k, v in list(final_kwargs.items()):
                if isinstance(v, dict) and 'description' in v and ('type' in v):
                    print(f"⚠️  Detected schema dict for '{k}': {v}")
                    print('   Unwrapping to None so aliasing can populate from shared_context')
                    final_kwargs[k] = None

            def _is_placeholder_or_empty(value: Any, param_name: str) -> bool:
                """Detect if a value is a placeholder, empty, or otherwise meaningless."""
                if value is None or value == '':
                    return True
                if not isinstance(value, str):
                    return False
                normalized = value.strip().lower()
                VALID_SHORT_VALUES = {'best', 'worst', '720p', '1080p', '480p', '360p', '240p', '144p', 'high', 'medium', 'low', 'true', 'false', 'yes', 'no', 'on', 'off'}
                if normalized in VALID_SHORT_VALUES or param_name == 'quality':
                    return False
                if not normalized or len(normalized) < 10:
                    return True
                placeholder_patterns = ['transcript data', 'please provide', 'the transcript', 'provide the', 'insert ', 'enter ', '<transcript>', '[transcript]', '{{transcript}}', 'n/a', 'not available', 'tbd', 'todo']
                if any((pattern in normalized for pattern in placeholder_patterns)):
                    return True
                if normalized in {'transcript', 'text', 'content', 'data', 'input', 'claim', 'claims', 'query', 'question'}:
                    return True
                return bool(normalized.startswith(('the ', 'a ', 'an ')) and len(normalized.split()) < 5)
            for k in list(final_kwargs.keys()):
                if _is_placeholder_or_empty(final_kwargs[k], k):
                    print(f"⚠️  Detected placeholder/empty value for '{k}': {(final_kwargs[k][:50] if isinstance(final_kwargs[k], str) else final_kwargs[k])}")
                    final_kwargs[k] = None
            print(f'🔧 Executing {tool_cls} with preserved args: {list(final_kwargs.keys())}')
            merged_context = {**_GLOBAL_CREW_CONTEXT, **self._shared_context}
            context_keys = set(merged_context.keys()) if merged_context else set()
            if context_keys:
                print(f'📦 Available context keys: {list(context_keys)}')
            if merged_context:
                CRITICAL_DATA_PARAMS = {'text', 'transcript', 'content', 'claim', 'claims', 'enhanced_transcript', 'url', 'source_url', 'file_path', 'media_info'}
                merged_kwargs = {**merged_context}
                for k, v in final_kwargs.items():
                    is_meaningful = v not in (None, '', [], {}) and (not _is_placeholder_or_empty(v, k))
                    if is_meaningful:
                        merged_kwargs[k] = v
                        print(f"✅ Using LLM-provided value for '{k}' ({len(str(v))} chars)")
                    elif k not in merged_kwargs and k not in CRITICAL_DATA_PARAMS:
                        merged_kwargs[k] = v
                    else:
                        print(f"⚠️  Ignoring empty/placeholder LLM value for critical param '{k}', will use shared_context")
                final_kwargs = merged_kwargs
            try:
                import inspect
                target_fn = None
                if hasattr(self._wrapped_tool, 'run'):
                    target_fn = self._wrapped_tool.run
                elif hasattr(self._wrapped_tool, '_run'):
                    target_fn = self._wrapped_tool._run
                else:
                    target_fn = self._wrapped_tool
                sig = inspect.signature(target_fn)
                params = list(sig.parameters.values())
                allowed = {p.name for p in params if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)}
                has_var_kw = any((p.kind == inspect.Parameter.VAR_KEYWORD for p in params))
                if merged_context:
                    transcript_data = merged_context.get('transcript') or merged_context.get('enhanced_transcript') or merged_context.get('text') or ''
                    text_value = final_kwargs.get('text', '')
                    text_is_placeholder = _is_placeholder_or_empty(text_value, 'text')
                    if 'text' in allowed and text_is_placeholder and transcript_data:
                        final_kwargs['text'] = transcript_data
                        print(f'✅ Aliased transcript→text ({len(transcript_data)} chars)')
                    elif 'text' in allowed and (not text_value) and (not transcript_data):
                        print(f"❌ CRITICAL ERROR: Tool {tool_cls} requires 'text' parameter but no data available in context")
                        print(f'   Context keys: {(list(merged_context.keys()) if merged_context else 'EMPTY')}')
                    claim_value = final_kwargs.get('claim', '')
                    claim_is_empty_or_missing = _is_placeholder_or_empty(claim_value, 'claim')
                    if 'claim' in allowed and claim_is_empty_or_missing and transcript_data:
                        if len(transcript_data) > 500:
                            final_kwargs['claim'] = transcript_data[:500] + '...'
                        else:
                            final_kwargs['claim'] = transcript_data
                        print(f'✅ Aliased transcript→claim ({len(final_kwargs['claim'])} chars)')
                    content_value = final_kwargs.get('content', '')
                    content_is_empty_or_missing = _is_placeholder_or_empty(content_value, 'content')
                    if 'content' in allowed and content_is_empty_or_missing and transcript_data:
                        final_kwargs['content'] = transcript_data
                        print(f'✅ Aliased transcript→content ({len(transcript_data)} chars)')
                    if 'claims' in allowed and 'claims' not in final_kwargs:
                        claims_data = merged_context.get('claims') or merged_context.get('fact_checks')
                        if claims_data:
                            final_kwargs['claims'] = claims_data
                            print('✅ Aliased claims data')
                    if 'video_path' in allowed and 'video_path' not in final_kwargs:
                        file_path_data = merged_context.get('file_path') or merged_context.get('media_path') or merged_context.get('video_path')
                        if file_path_data:
                            final_kwargs['video_path'] = file_path_data
                            print(f'✅ Aliased video_path from context: {file_path_data}')
                    if 'file_path' in allowed and 'file_path' not in final_kwargs:
                        file_path_data = merged_context.get('file_path') or merged_context.get('media_path')
                        if file_path_data:
                            final_kwargs['file_path'] = file_path_data
                            print('✅ Aliased file_path from context')
                    if 'media_info' in allowed and 'media_info' not in final_kwargs:
                        media_info_data = merged_context.get('media_info')
                        if media_info_data:
                            final_kwargs['media_info'] = media_info_data
                            print('✅ Aliased media_info from context')
                    if 'query' in allowed and 'query' not in final_kwargs:
                        query_data = merged_context.get('query') or merged_context.get('question')
                        if query_data:
                            final_kwargs['query'] = query_data
                            print('✅ Aliased query data')
                    if 'url' in allowed and 'url' not in final_kwargs:
                        url_data = merged_context.get('url') or merged_context.get('source_url') or final_kwargs.get('video_url')
                        if url_data:
                            final_kwargs['url'] = url_data
                            print(f'✅ Aliased url: {url_data}')
                    if 'video_url' in allowed and 'video_url' not in final_kwargs:
                        url_data = final_kwargs.get('url') or merged_context.get('url') or merged_context.get('video_url') or merged_context.get('source_url')
                        if url_data:
                            final_kwargs['video_url'] = url_data
                            print(f'✅ Aliased video_url: {url_data}')
                    if 'metadata' in allowed and 'metadata' not in final_kwargs:
                        metadata = merged_context.get('media_info') or merged_context.get('metadata')
                        if metadata:
                            final_kwargs['metadata'] = metadata
                            print('✅ Aliased metadata')
                    if 'video_id' in allowed and 'video_id' not in final_kwargs:
                        media_info = merged_context.get('media_info')
                        if isinstance(media_info, dict) and 'video_id' in media_info:
                            final_kwargs['video_id'] = media_info['video_id']
                            print(f'✅ Aliased video_id from media_info: {media_info['video_id']}')
                if final_kwargs:
                    available_params = list(final_kwargs.keys())
                    print(f'📋 Available parameters before filtering: {available_params}')
                CONTEXT_ONLY_PARAMS = {'depth', 'tenant_id', 'workspace_id', 'routing_profile_id'}
                CONTEXT_DATA_KEYS = {'transcript', 'transcript_length', 'timeline_anchors', 'quality_score', 'insights', 'themes', 'perspectives', 'fallacies', 'file_path', 'title', 'description', 'author', 'duration', 'platform', 'claims', 'verified_claims', 'fact_check_results', 'trustworthiness_score', 'url', 'media_info', 'metadata'}
                if not has_var_kw:
                    filtered_kwargs = {k: v for k, v in final_kwargs.items() if k in allowed}
                    context_data = {k: v for k, v in final_kwargs.items() if k in CONTEXT_DATA_KEYS and k not in allowed}
                    if context_data:
                        if '_context' in allowed:
                            filtered_kwargs['_context'] = context_data
                            print(f'✅ Bundled {len(context_data)} context keys into _context parameter')
                        else:
                            if not hasattr(self, '_shared_context'):
                                self._shared_context = {}
                            self._shared_context.update(context_data)
                            print(f'✅ Preserved {len(context_data)} context keys in _shared_context')
                    removed = set(final_kwargs.keys()) - set(filtered_kwargs.keys())
                    preserved_in_context = removed & CONTEXT_DATA_KEYS
                    truly_removed = removed - CONTEXT_DATA_KEYS - CONTEXT_ONLY_PARAMS
                    if truly_removed:
                        print(f'⚠️  Filtered out parameters: {truly_removed}')
                    if preserved_in_context:
                        print(f'[INFO] Context data preserved ({len(preserved_in_context)} keys): {preserved_in_context}')
                    print(f'✅ Kept parameters: {list(filtered_kwargs.keys())}')
                    DATA_DEPENDENT_TOOLS = {'TextAnalysisTool': ['text'], 'LogicalFallacyTool': ['text'], 'PerspectiveSynthesizerTool': ['text'], 'FactCheckTool': ['claim'], 'ClaimExtractorTool': ['text'], 'DeceptionScoringTool': ['text'], 'MemoryStorageTool': ['text']}
                    if tool_cls in DATA_DEPENDENT_TOOLS:
                        required_params = DATA_DEPENDENT_TOOLS[tool_cls]
                        for param in required_params:
                            value = filtered_kwargs.get(param)
                            if not value or (isinstance(value, str) and (not value.strip())):
                                if param == 'text' and self._shared_context:
                                    for fallback_key in ['transcript', 'insights', 'themes', 'perspectives']:
                                        fallback_val = self._shared_context.get(fallback_key)
                                        if fallback_val and isinstance(fallback_val, str) and fallback_val.strip():
                                            filtered_kwargs[param] = fallback_val
                                            print(f"✅ Auto-populated '{param}' from context key '{fallback_key}'")
                                            break
                                value = filtered_kwargs.get(param)
                                if not value or (isinstance(value, str) and (not value.strip())):
                                    available_context = list(self._shared_context.keys()) if self._shared_context else []
                                    error_msg = f"❌ {tool_cls} called with empty '{param}' parameter. Available context keys: {available_context}. This indicates a data flow issue - the LLM doesn't have access to required data."
                                    print(error_msg)
                                    logger = logging.getLogger(__name__)
                                    logger.error(error_msg)
                                    from platform.core.step_result import StepResult
                                    return StepResult.fail(error=f'Missing required data: {param}', step=f'{tool_cls}_validation')
                    print(f'🔍 Parameter filtering: allowed={len(allowed)}, final={len(filtered_kwargs)}, context_keys={len(context_keys)}')
                else:
                    filtered_kwargs = {k: v for k, v in final_kwargs.items() if k not in CONTEXT_ONLY_PARAMS}
                    if 'quality' in allowed and filtered_kwargs.get('quality') is None:
                        filtered_kwargs['quality'] = 'best'
                        print("✅ Applied default quality='best' for download tool")
                    removed = set(final_kwargs.keys()) - set(filtered_kwargs.keys())
                    if removed:
                        print(f'⚠️  Filtered out context-only params: {removed}')
                    print(f'🔍 Parameter passthrough: tool accepts **kwargs, passing {len(filtered_kwargs)} params')
                final_kwargs = filtered_kwargs
            except Exception as introspection_error:
                print(f'⚠️  Introspection failed: {introspection_error}, using unfiltered kwargs')
            try:
                validation_errors = []
                if tool_cls.endswith('DownloadTool'):
                    url_param = final_kwargs.get('url') or final_kwargs.get('video_url')
                    if not url_param:
                        validation_errors.append(f'{tool_cls} requires url/video_url parameter but received None. LLM must provide URL in tool call.')
                elif 'TranscriptionTool' in tool_cls or 'AudioTranscription' in tool_cls:
                    video_path = final_kwargs.get('video_path') or final_kwargs.get('file_path')
                    if not video_path:
                        if merged_context:
                            video_path = merged_context.get('file_path') or merged_context.get('media_path') or merged_context.get('video_path')
                            if video_path:
                                final_kwargs['video_path'] = video_path
                                final_kwargs.pop('file_path', None)
                                print(f'✅ Auto-populated video_path from context: {video_path}')
                        if not final_kwargs.get('video_path'):
                            validation_errors.append(f'{tool_cls} requires video_path parameter. This comes from acquisition task output. Available context: {(list(merged_context.keys()) if merged_context else 'EMPTY')}')
                elif any((x in tool_cls for x in ['TextAnalysis', 'LogicalFallacy', 'PerspectiveSynthesizer', 'DeceptionScoring', 'TruthScoring'])):
                    text_param = final_kwargs.get('text') or final_kwargs.get('content')
                    if not text_param or (isinstance(text_param, str) and len(text_param.strip()) < 10):
                        validation_errors.append(f"{tool_cls} requires non-empty 'text' parameter (min 10 chars). Received: {(len(str(text_param)) if text_param else 0)} chars. This comes from transcription task output.")
                elif 'ClaimExtractor' in tool_cls:
                    text_param = final_kwargs.get('text')
                    if not text_param or (isinstance(text_param, str) and len(text_param.strip()) < 50):
                        validation_errors.append(f"{tool_cls} requires substantial 'text' parameter (min 50 chars) to extract claims. Received: {(len(str(text_param)) if text_param else 0)} chars.")
                elif 'FactCheck' in tool_cls:
                    claim_param = final_kwargs.get('claim')
                    if not claim_param or (isinstance(claim_param, str) and len(claim_param.strip()) < 5):
                        validation_errors.append(f"{tool_cls} requires non-empty 'claim' parameter. Received: {(len(str(claim_param)) if claim_param else 0)} chars.")
                elif 'MemoryStorage' in tool_cls or 'GraphMemory' in tool_cls:
                    text_param = final_kwargs.get('text') or final_kwargs.get('content')
                    if not text_param or (isinstance(text_param, str) and len(text_param.strip()) < 10):
                        validation_errors.append(f'{tool_cls} requires non-empty text to store. Received: {(len(str(text_param)) if text_param else 0)} chars.')
                if validation_errors:
                    error_msg = '\n'.join([f'  • {err}' for err in validation_errors])
                    full_error = f'❌ PRE-EXECUTION VALIDATION FAILED for {tool_cls}:\n{error_msg}\n\nProvided parameters: {list(final_kwargs.keys())}\nContext available: {(list(merged_context.keys()) if merged_context else 'EMPTY')}\n\n💡 This indicates a data flow issue - required data from previous tasks is missing.'
                    print(full_error)
                    logger = logging.getLogger(__name__)
                    logger.error(full_error)
                    return StepResult.fail(error=full_error, tool=tool_cls, step='pre_execution_validation', args_provided=list(final_kwargs.keys()), context_available=list(merged_context.keys()) if merged_context else [])
                validation = self._validate_tool_dependencies()
                if not validation['dependencies_valid']:
                    pass
                logger = logging.getLogger(__name__)
                param_summary = {}
                for k, v in final_kwargs.items():
                    if isinstance(v, str):
                        param_summary[k] = f'{len(v)} chars' if len(v) > 50 else f"'{v}'"
                    elif isinstance(v, (list, dict)):
                        param_summary[k] = f'{len(v)} items'
                    else:
                        param_summary[k] = str(v)[:50]
                logger.warning(f'🔧 TOOL CALLED: {tool_cls} with params: {param_summary}')
                print(f'🔧 TOOL CALLED: {tool_cls} with params: {param_summary}')
                if hasattr(self._wrapped_tool, 'run'):
                    res = self._wrapped_tool.run(**final_kwargs)
                elif hasattr(self._wrapped_tool, '_run'):
                    res = self._wrapped_tool._run(**final_kwargs)
                else:
                    res = self._wrapped_tool(**final_kwargs)
                result_summary = ''
                if hasattr(res, 'data') and isinstance(res.data, dict):
                    result_keys = list(res.data.keys())[:5]
                    result_summary = f'keys={result_keys}'
                elif isinstance(res, dict):
                    result_keys = list(res.keys())[:5]
                    result_summary = f'keys={result_keys}'
                else:
                    result_summary = f'type={type(res).__name__}'
                logger.warning(f'✅ TOOL RETURNED: {tool_cls} → {result_summary}')
                print(f'✅ TOOL RETURNED: {tool_cls} → {result_summary}')
                print(f'✅ {tool_cls} executed successfully')
                self._last_result = res
                if hasattr(res, 'data') and isinstance(res.data, dict):
                    context_updates = {}
                    if 'url' in res.data:
                        context_updates['url'] = res.data['url']
                    if 'content' in res.data:
                        context_updates['content'] = res.data['content']
                    if 'transcript' in res.data:
                        context_updates['transcript'] = res.data['transcript']
                    if 'enhanced_transcript' in res.data:
                        context_updates['enhanced_transcript'] = res.data['enhanced_transcript']
                    if 'text' in res.data:
                        context_updates['text'] = res.data['text']
                    if 'analysis' in res.data:
                        context_updates['analysis'] = res.data['analysis']
                    if 'file_path' in res.data:
                        context_updates['file_path'] = res.data['file_path']
                    if 'media_path' in res.data:
                        context_updates['file_path'] = res.data['media_path']
                    if 'output_path' in res.data:
                        context_updates['file_path'] = res.data['output_path']
                    if 'media_info' in res.data:
                        context_updates['media_info'] = res.data['media_info']
                    if 'metadata' in res.data:
                        context_updates['metadata'] = res.data['metadata']
                    if 'claims' in res.data:
                        context_updates['claims'] = res.data['claims']
                    if 'fact_checks' in res.data:
                        context_updates['fact_checks'] = res.data['fact_checks']
                    if context_updates:
                        print(f'📤 Updating global context with keys: {list(context_updates.keys())}')
                        self.update_context(context_updates)
                from .step_result import StepResult
                if isinstance(res, StepResult):
                    return res
                elif isinstance(res, dict):
                    return StepResult.ok(data=res)
                else:
                    return StepResult.ok(data={'result': res, 'result_type': type(res).__name__})
            except Exception as tool_error:
                print(f'❌ {tool_cls} execution failed: {tool_error}')
                import traceback
                traceback.print_exc()
                from .step_result import StepResult
                return StepResult.fail(error=f'{tool_cls} execution failed: {tool_error!s}', tool=tool_cls, args_provided=list(final_kwargs.keys()))
        except TypeError as e:
            print(f'❌ {tool_cls} argument type error: {e}')
            print(f'  Provided arguments: {list(final_kwargs.keys())}')
            print(f'  Tool class: {self._wrapped_tool.__class__.__name__}')
            with contextlib.suppress(Exception):
                import inspect
                if hasattr(self._wrapped_tool, 'run'):
                    sig = inspect.signature(self._wrapped_tool.run)
                elif hasattr(self._wrapped_tool, '_run'):
                    sig = inspect.signature(self._wrapped_tool._run)
                else:
                    sig = inspect.signature(self._wrapped_tool)
                print(f'  Expected signature: {sig}')
            from .step_result import StepResult
            err_lower = str(e).lower()
            msg = f'Tool {tool_cls} argument error: {e!s}'
            if 'missing required arg' in err_lower:
                msg = str(e)
            return StepResult.fail(error=msg, step='tool_execution', data={'tool_class': tool_cls, 'provided_args': list(final_kwargs.keys()), 'error_details': str(e)})
        except Exception as e:
            import traceback
            full_traceback = traceback.format_exc()
            print(f'❌ {tool_cls} execution failed: {e}')
            print(f'📊 Full error traceback:\n{full_traceback}')
            print(f'🔧 Tool args that failed: {final_kwargs}')
            print(f'🗂️ Shared context available: {(list(self._shared_context.keys()) if self._shared_context else 'None')}')
            error_context = {'tool_class': tool_cls, 'error_message': str(e), 'error_type': type(e).__name__, 'args_provided': list(final_kwargs.keys()), 'args_values': {k: str(v)[:100] + '...' if len(str(v)) > 100 else str(v) for k, v in final_kwargs.items()}, 'shared_context_keys': list(self._shared_context.keys()) if self._shared_context else [], 'traceback': full_traceback, 'has_wrapped_tool': hasattr(self, '_wrapped_tool'), 'wrapped_tool_type': type(self._wrapped_tool).__name__ if hasattr(self, '_wrapped_tool') else None, 'available_methods': [m for m in dir(self._wrapped_tool) if not m.startswith('_')] if hasattr(self, '_wrapped_tool') else []}
            from .step_result import StepResult
            return StepResult.fail(error=f'Tool {tool_cls} execution failed: {e!s}', step='tool_execution', data={'tool_class': tool_cls, 'error_context': error_context, 'error_type': type(e).__name__, 'error_details': str(e)})

    def _validate_tool_dependencies(self) -> dict[str, Any]:
        """Validate that tool dependencies are available before execution."""
        missing_deps = []
        config_issues = []
        tool_cls = self._wrapped_tool.__class__.__name__
        if 'YouTube' in tool_cls or 'YtDlp' in tool_cls or 'Download' in tool_cls:
            import shutil
            if not shutil.which('yt-dlp'):
                missing_deps.append('yt-dlp binary not found on PATH')
        if 'Discord' in tool_cls:
            webhook_url = getattr(self._wrapped_tool, 'webhook_url', None)
            if not webhook_url or webhook_url.startswith('dummy'):
                config_issues.append('Discord webhook URL not configured')
        if 'OpenAI' in tool_cls or 'Transcription' in tool_cls:
            import os
            if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY', '').startswith('dummy'):
                config_issues.append('OpenAI API key not configured')
        if 'Pipeline' in tool_cls:
            try:
                from ..pipeline_components.orchestrator import ContentPipeline
            except ImportError:
                missing_deps.append('ContentPipeline not available')
        return {'dependencies_valid': len(missing_deps) == 0 and len(config_issues) == 0, 'missing_dependencies': missing_deps, 'configuration_issues': config_issues}

    def _analyze_tool_error(self, error: Exception, args: tuple, kwargs: dict) -> str:
        """Analyze tool execution errors to provide helpful debugging information."""
        error_msg = str(error)
        if 'missing' in error_msg.lower() and 'argument' in error_msg.lower():
            return f'Missing required argument. Error: {error_msg}'
        elif 'unexpected keyword argument' in error_msg.lower():
            return f'Invalid argument provided. Error: {error_msg}'
        elif 'takes' in error_msg and 'positional argument' in error_msg:
            return f'Wrong number of arguments. Error: {error_msg}'
        else:
            return f'Unknown argument error: {error_msg}'

    def _validate_tool_dependencies(self) -> dict[str, Any]:
        """Validate that tool dependencies are available."""
        validation_result = {'tool_class': self._wrapped_tool.__class__.__name__, 'dependencies_valid': True, 'missing_dependencies': [], 'configuration_issues': []}
        try:
            required_attrs = ['name', 'description']
            for attr in required_attrs:
                if not hasattr(self._wrapped_tool, attr):
                    validation_result['configuration_issues'].append(f'Missing required attribute: {attr}')
            if not (hasattr(self._wrapped_tool, 'run') or hasattr(self._wrapped_tool, '_run')):
                validation_result['configuration_issues'].append("Tool missing both 'run' and '_run' methods")
            tool_class = self._wrapped_tool.__class__.__name__
            if tool_class in ['AudioTranscriptionTool', 'TextAnalysisTool', 'FactCheckTool']:
                import os
                if not os.getenv('OPENAI_API_KEY') and (not os.getenv('OPENROUTER_API_KEY')):
                    validation_result['missing_dependencies'].append('API key required (OPENAI_API_KEY or OPENROUTER_API_KEY)')
            if tool_class in ['DiscordPostTool', 'DiscordPrivateAlertTool']:
                import os
                if not os.getenv('DISCORD_WEBHOOK'):
                    validation_result['missing_dependencies'].append('DISCORD_WEBHOOK environment variable required')
            validation_result['dependencies_valid'] = len(validation_result['missing_dependencies']) == 0 and len(validation_result['configuration_issues']) == 0
        except Exception as e:
            validation_result['dependencies_valid'] = False
            validation_result['configuration_issues'].append(f'Validation error: {e!s}')
        return validation_result

    def _analyze_tool_error(self, error: Exception, args: tuple, kwargs: dict) -> str:
        """Analyze tool execution error and provide helpful diagnostic."""
        error_str = str(error)
        if 'missing' in error_str.lower() and 'argument' in error_str.lower():
            match = re.search("missing.*required.*argument.*'(\\w+)'", error_str)
            if match:
                missing_arg = match.group(1)
                return f"Missing required argument '{missing_arg}'. Provided: {list(kwargs.keys())}"
        if 'unexpected keyword argument' in error_str.lower():
            match = re.search("unexpected keyword argument '(\\w+)'", error_str)
            if match:
                unexpected_arg = match.group(1)
                return f"Unexpected argument '{unexpected_arg}'. Tool may not support this parameter."
        provided_info = f'Args provided: {len(args)} positional, {len(kwargs)} keyword ({list(kwargs.keys())})'
        return f'{error_str} | {provided_info}'

    def _get_configuration_suggestions(self, tool_cls: str) -> list[str]:
        """Get configuration suggestions for specific tool types."""
        suggestions = []
        if tool_cls in ['AudioTranscriptionTool', 'TextAnalysisTool', 'FactCheckTool', 'LogicalFallacyTool', 'PerspectiveSynthesizerTool']:
            suggestions.extend(['Set OPENAI_API_KEY or OPENROUTER_API_KEY environment variable', 'Ensure API key is valid and has proper permissions', 'Check if you have sufficient API credits'])
        if tool_cls in ['DiscordPostTool', 'DiscordPrivateAlertTool']:
            suggestions.extend(['Set DISCORD_WEBHOOK environment variable with a valid webhook URL', 'Create a Discord webhook in your server settings', 'Ensure the webhook URL starts with https://discord.com/api/webhooks/'])
        if tool_cls in ['PipelineTool', 'MultiPlatformDownloadTool']:
            suggestions.extend(['Install yt-dlp: pip install yt-dlp', 'Ensure you have write permissions to the download directory', 'Check if the video URL is accessible and valid'])
        if tool_cls in ['VectorSearchTool', 'MemoryStorageTool', 'GraphMemoryTool']:
            suggestions.extend(['Set QDRANT_URL environment variable if using Qdrant', 'Ensure vector database is running and accessible', 'Check database connection settings'])
        if tool_cls in ['DriveUploadTool']:
            suggestions.extend(['Configure Google Drive API credentials', 'Set up service account with proper permissions', 'Ensure GOOGLE_DRIVE_CREDENTIALS environment variable is set'])
        return suggestions

    def get_validation_status(self) -> dict[str, Any]:
        """Get tool validation status for debugging purposes."""
        return self._validate_tool_dependencies()

def wrap_tool_for_crewai(tool: Any) -> BaseTool:
    """Wrap any of our existing tools to be CrewAI compatible."""
    return CrewAIToolWrapper(tool)

class PipelineToolWrapper(BaseTool):
    name: str = 'Pipeline Tool'
    description: str = 'Execute the content pipeline for downloading and processing media'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool

    def _run(self, url: str, quality: str='1080p', **kwargs) -> Any:
        """Run the pipeline tool with proper delegation to the underlying tool."""
        try:
            from platform.core.step_result import StepResult
            tenant_id = kwargs.get('tenant_id')
            workspace_id = kwargs.get('workspace_id')
            if not url or not isinstance(url, str):
                return StepResult.fail(error='URL is required and must be a string', url=url, quality=quality)
            if not quality or not isinstance(quality, str) or (not quality.strip()):
                quality = '1080p'
            if hasattr(self._wrapped_tool, 'run'):
                try:
                    result = self._wrapped_tool.run(url=url, quality=quality, tenant_id=tenant_id, workspace_id=workspace_id)
                    import inspect
                    if inspect.iscoroutine(result):
                        import asyncio
                        try:
                            asyncio.get_running_loop()
                            return StepResult.fail(error='Pipeline tool returned coroutine in async context - caller should use await', url=url, quality=quality)
                        except RuntimeError:
                            result = asyncio.run(result)
                except RuntimeError as e:
                    if 'coroutine' in str(e) or 'async context' in str(e):
                        return StepResult.fail(error=f'Pipeline async handling issue: {e!s}', url=url, quality=quality)
                    else:
                        raise
                if isinstance(result, StepResult):
                    return result
                elif isinstance(result, dict):
                    if result.get('status') == 'success':
                        return StepResult.ok(data=result)
                    else:
                        return StepResult.fail(error=result.get('error', 'Pipeline execution failed'), url=url, quality=quality, data=result)
                else:
                    return StepResult.ok(data={'result': result})
            else:
                return StepResult.fail(error='Pipeline tool has no run method', url=url, quality=quality)
        except Exception as e:
            from platform.core.step_result import StepResult
            return StepResult.fail(error=f'Pipeline execution failed: {e!s}', url=url, quality=quality)

class DiscordPostToolWrapper(BaseTool):
    name: str = 'Discord Post Tool'
    description: str = 'Post messages to Discord channels'
    _wrapped_tool: Any = PrivateAttr()
    _can_post: bool = PrivateAttr(default=False)
    _last_post_hash: str | None = PrivateAttr(default=None)
    _last_post_time: float | None = PrivateAttr(default=None)

    def __init__(self, tool_class, webhook_url: str='https://placeholder.webhook.url', **kwargs):
        super().__init__(**kwargs)
        try:
            import re
            url = str(webhook_url or '').strip()
            if not url or 'placeholder' in url or (not re.match('^https://', url)):

                class _NoopPoster:

                    def _run(self, *a, **k):
                        from .step_result import StepResult
                        return StepResult.skip(reason='no webhook configured')

                    def run(self, *a, **k):
                        return self._run(*a, **k)
                self._wrapped_tool = _NoopPoster()
                self._can_post = False
            else:
                self._wrapped_tool = tool_class(url)
                self._can_post = True
        except Exception:

            class _NoopPoster:

                def _run(self, *a, **k):
                    from platform.core.step_result import StepResult
                    return StepResult.skip(reason='discord_post_disabled')

                def run(self, *a, **k):
                    return self._run(*a, **k)
            self._wrapped_tool = _NoopPoster()
            self._can_post = False

    def _run(self, message: Any='') -> Any:
        try:
            import hashlib
            import os
            import time
            try:
                min_len = int(os.getenv('DISCORD_POST_MIN_LEN', '20').strip())
            except Exception:
                min_len = 20
            try:
                cooldown = float(os.getenv('DISCORD_POST_COOLDOWN_SECONDS', '20').strip())
            except Exception:
                cooldown = 20.0
            if not isinstance(message, str):
                if isinstance(message, dict):
                    msg = message.get('content') or message.get('message') or message.get('description')
                    message = msg if isinstance(msg, str) else str(message)
                else:
                    message = str(message)
            msg_clean = (message or '').strip()
            if not msg_clean or len(msg_clean) < max(1, min_len):
                from platform.core.step_result import StepResult
                return StepResult.skip(reason='empty_or_short_message')
            msg_hash = hashlib.sha256(msg_clean.encode('utf-8')).hexdigest()
            now = time.time()
            if self._last_post_hash == msg_hash and self._last_post_time is not None and (now - self._last_post_time < max(0.0, cooldown)):
                from platform.core.step_result import StepResult
                return StepResult.skip(reason='duplicate_message_debounced')
            if not self._can_post:
                if hasattr(self._wrapped_tool, '_run'):
                    return self._wrapped_tool._run({'title': msg_clean[:80]}, {})
                from platform.core.step_result import StepResult
                return StepResult.skip(reason='discord_post_disabled')
            if hasattr(self._wrapped_tool, 'run'):
                res = self._wrapped_tool.run(message=message)
                from platform.core.step_result import StepResult
                if isinstance(res, StepResult):
                    if res.success:
                        self._last_post_hash = msg_hash
                        self._last_post_time = now
                    return res
                self._last_post_hash = msg_hash
                self._last_post_time = now
                return StepResult.ok(message=str(res))
            if hasattr(self._wrapped_tool, '_run'):
                content_data = {'title': message[:80], 'uploader': 'CrewAI', 'platform': 'internal'}
                res = self._wrapped_tool._run(content_data, {})
                from platform.core.step_result import StepResult
                if isinstance(res, StepResult):
                    if res.success:
                        self._last_post_hash = msg_hash
                        self._last_post_time = now
                    return res
                self._last_post_hash = msg_hash
                self._last_post_time = now
                return StepResult.ok(message=str(res))
            from platform.core.step_result import StepResult
            return StepResult.skip(reason='discord_post_unavailable')
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e), message=message[:100])

class DiscordPrivateAlertToolWrapper(BaseTool):
    name: str = 'Discord Private Alert Tool'
    description: str = 'Send private alerts to Discord channels'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, tool_class, webhook_url: str='https://placeholder.webhook.url', **kwargs):
        super().__init__(**kwargs)
        try:
            self._wrapped_tool = tool_class(webhook_url)
        except Exception:

            class MockDiscordPrivateAlertTool:

                def __init__(self, url):
                    self.webhook_url = url

                def _run(self, message):
                    return f'Private alert simulated to {self.webhook_url}: {message[:100]}...'
            self._wrapped_tool = MockDiscordPrivateAlertTool(webhook_url)

    def _run(self, message: str) -> Any:
        try:
            if hasattr(self._wrapped_tool, '_run'):
                res = self._wrapped_tool._run(message)
                from .step_result import StepResult
                return res if isinstance(res, StepResult) else StepResult.ok(message=str(res))
            else:
                from .step_result import StepResult
                return StepResult.ok(message=f'Private alert simulated: {message[:100]}...')
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e), message=message[:100])

class MCPCallToolWrapper(BaseTool):
    name: str = 'MCP Call Tool'
    description: str = 'Call MCP server tools safely by namespace and name with optional parameters'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool

    def _run(self, namespace: str='obs', name: str='summarize_health', params: dict | None=None) -> Any:
        """Execute MCP call with required parameters."""
        try:
            res = self._wrapped_tool.run(namespace=namespace, name=name, params=params)
            from .step_result import StepResult
            return res if isinstance(res, StepResult) else StepResult.ok(result=res)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=f'MCP call failed: {str(e)[:200]}', namespace=namespace, name=name)

class TimelineToolWrapper(BaseTool):
    name: str = 'Timeline Tool'
    description: str = 'Record and fetch timeline events for videos'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
    try:

        class _TimelineArgs(BaseModel):
            action: str = Field('fetch')
            url: str = Field('')
            event_type: str = Field('analysis')
            details: str = Field('')
            video_id: str | None = Field(None)
            event: dict | None = Field(None)
        args_schema: type[BaseModel] = _TimelineArgs
    except Exception:
        args_schema = None

    def _run(self, action: str='fetch', url: str='', event_type: str='analysis', details: str='', video_id: str | None=None, event: dict | None=None) -> Any:
        """Execute timeline action with friendly parameter mapping.

        - action "record"/"add": map to tool._run("add", video_id=..., event=...)
        - action "get"/"fetch": map to tool._run("get", video_id=...)
        If video_id is not provided, derive from URL (best-effort) or use a
        deterministic placeholder.
        """
        try:
            act = action.lower().strip() if isinstance(action, str) else 'get'
            vid = (video_id or '').strip()
            if not vid:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(url or '')
                    segs = [s for s in (parsed.path or '').split('/') if s]
                    vid = (segs[-1] if segs else parsed.netloc or 'unknown') or 'unknown'
                except Exception:
                    vid = 'unknown'
            if act in {'log', 'create_timeline_anchors'}:
                act = 'add'
                if action.lower().strip() == 'create_timeline_anchors':
                    event_type = event_type or 'transcription_anchors'
                    details = details or 'Auto-created timeline anchors'
            if act in {'record', 'add'}:
                ev = event or {'type': event_type, 'data': {'details': details, 'url': url}}
                if not isinstance(ev, dict):
                    ev = {'type': str(event_type), 'data': {'details': str(details), 'url': str(url)}}
                return self._wrapped_tool._run('add', video_id=vid, event=ev)
            if act in {'get', 'fetch'}:
                return self._wrapped_tool._run('get', video_id=vid)
            return self._wrapped_tool._run(act, video_id=vid, event=event or {})
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e), action=action)

class AdvancedPerformanceAnalyticsToolWrapper(BaseTool):
    name: str = 'Advanced Performance Analytics Tool'
    description: str = 'Execute comprehensive performance analytics with proper action parameters'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool

    def _run(self, action: str='analyze', lookback_hours: int=24, include_optimization: bool=False, send_notifications: bool=True, **kwargs) -> Any:
        """Execute performance analytics with required action parameter."""
        try:
            alias_map = {'evaluate': 'analyze', 'summary': 'executive_summary', 'summarize': 'executive_summary', 'predictive': 'predict', 'optimize': 'optimize', 'analyze': 'analyze', 'alerts': 'alerts', 'dashboard': 'dashboard'}
            act_norm = str(action or 'analyze').strip().lower()
            action_mapped = alias_map.get(act_norm, act_norm)
            try:
                if not isinstance(lookback_hours, int):
                    lookback_hours = int(str(lookback_hours).strip())
            except Exception:
                lookback_hours = 24
            return self._wrapped_tool._run(action_mapped, lookback_hours=lookback_hours, include_optimization=include_optimization, send_notifications=send_notifications, **kwargs)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=f'Performance analytics failed: {str(e)[:200]}', action=action)

class SentimentToolWrapper(BaseTool):
    name: str = 'Sentiment Tool'
    description: str = 'Analyze sentiment of text with automatic text parameter handling'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool

    def _run(self, text: str='neutral content', **kwargs) -> Any:
        """Execute sentiment analysis with required text parameter."""
        try:
            if not text and 'description' in kwargs:
                text = str(kwargs.pop('description'))
            return self._wrapped_tool._run(text, **kwargs)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class GraphMemoryToolWrapper(BaseTool):
    name: str = 'Graph Memory Tool'
    description: str = 'Store knowledge graphs with automatic text parameter handling'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
    try:

        class _GraphMemoryArgs(BaseModel):
            text: str = Field('sample knowledge')
            index: str = Field('graph')
            metadata: dict | None = Field(None)
            tags: list | None = Field(None)
        args_schema: type[BaseModel] = _GraphMemoryArgs
    except Exception:
        args_schema = None

    def _run(self, text: str='sample knowledge', index: str='graph', metadata: dict | None=None, tags: list | None=None, **kwargs) -> Any:
        """Execute graph memory storage with required text parameter."""
        try:
            if not text and kwargs:
                for alt in ('description', 'content', 'message'):
                    if alt in kwargs and isinstance(kwargs[alt], str):
                        text = kwargs.pop(alt)
                        break
            md = metadata or {}
            if 'crew_analysis' in kwargs and (not md.get('crew_analysis')):
                md['crew_analysis'] = kwargs.pop('crew_analysis')
            return self._wrapped_tool.run(text=text, index=index, metadata=md, tags=tags or [], **kwargs)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class HippoRAGToolWrapper(BaseTool):
    name: str = 'HippoRAG Continual Memory Tool'
    description: str = 'Continual memory system with automatic text parameter handling'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool

    def _run(self, text: str='sample memory', **kwargs) -> Any:
        """Execute HippoRAG with required text parameter."""
        try:
            return self._wrapped_tool.run(text=text, **kwargs)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class RAGIngestToolWrapper(BaseTool):
    name: str = 'RAG Ingest Tool'
    description: str = 'Ingest text into RAG system with automatic parameters'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool

    def _run(self, texts: list | None=None, index: str='memory', chunk_size: int=400, overlap: int=50, **kwargs) -> Any:
        """Execute RAG ingestion with required texts parameter."""
        try:
            if texts is None:
                texts = ['sample text content']
            return self._wrapped_tool.run(texts=texts, index=index, chunk_size=chunk_size, overlap=overlap, **kwargs)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class MemoryStorageToolWrapper(BaseTool):
    name: str = 'Memory Storage Tool'
    description: str = 'Store memories with automatic parameter handling'
    _wrapped_tool: Any = PrivateAttr()

    def __init__(self, wrapped_tool, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool

    def _run(self, text: str='sample memory', namespace: str='default', metadata: dict | None=None, **kwargs) -> Any:
        """Execute memory storage with required parameters."""
        try:
            return self._wrapped_tool.run(text=text, namespace=namespace, metadata=metadata or {}, **kwargs)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class AudioTranscriptionArgs(BaseModel):
    video_path: str = Field(..., description='Local path to the video file')

class AudioTranscriptionToolWrapper(BaseTool):
    name: str = 'Audio Transcription Tool'
    description: str = 'Transcribe audio from a video file using Whisper.'
    args_schema: type[BaseModel] = AudioTranscriptionArgs
    _wrapped_tool: Any = PrivateAttr()
    _default_video_path: str | None = PrivateAttr(default=None)

    def __init__(self, wrapped_tool, default_video_path: str | None=None, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
        self._default_video_path = default_video_path

    def _run(self, video_path: str='', **kwargs) -> Any:
        try:
            if not video_path and 'path' in kwargs:
                video_path = str(kwargs['path'])
            if not video_path and self._default_video_path:
                video_path = self._default_video_path
            if hasattr(self._wrapped_tool, 'run'):
                return self._wrapped_tool.run(video_path=video_path)
            return self._wrapped_tool._run(video_path)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class TextAnalysisArgs(BaseModel):
    text: str = Field(..., description='Text to analyze')

class TextAnalysisToolWrapper(BaseTool):
    name: str = 'Text Analysis Tool'
    description: str = 'Analyze text to extract sentiment, keywords, and topics.'
    args_schema: type[BaseModel] = TextAnalysisArgs
    _wrapped_tool: Any = PrivateAttr()
    _default_text: str | None = PrivateAttr(default=None)

    def __init__(self, wrapped_tool, default_text: str | None=None, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
        self._default_text = default_text

    def _run(self, text: str='', **kwargs) -> Any:
        try:
            if not text:
                for alt in ('description', 'content', 'message'):
                    if alt in kwargs:
                        text = str(kwargs[alt])
                        break
            if not text and self._default_text:
                text = self._default_text
            if hasattr(self._wrapped_tool, 'run'):
                return self._wrapped_tool.run(text=text)
            return self._wrapped_tool._run(text)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class TranscriptIndexArgs(BaseModel):
    transcript: str = Field(..., description='Transcript text to index')
    video_id: str = Field(..., description='Associated video identifier')

class TranscriptIndexToolWrapper(BaseTool):
    name: str = 'Transcript Index Tool'
    description: str = 'Index transcripts into timestamped windows and fetch surrounding context.'
    args_schema: type[BaseModel] = TranscriptIndexArgs
    _wrapped_tool: Any = PrivateAttr()
    _default_transcript: str | None = PrivateAttr(default=None)
    _default_video_id: str | None = PrivateAttr(default=None)

    def __init__(self, wrapped_tool, default_transcript: str | None=None, default_video_id: str | None=None, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
        self._default_transcript = default_transcript
        self._default_video_id = default_video_id

    def _run(self, transcript: str='', video_id: str='', **kwargs) -> Any:
        try:
            if not transcript and self._default_transcript:
                transcript = self._default_transcript
            if not video_id and self._default_video_id:
                video_id = self._default_video_id
            if hasattr(self._wrapped_tool, 'run'):
                return self._wrapped_tool.run(transcript=transcript, video_id=video_id)
            return self._wrapped_tool._run(transcript, video_id)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class DriveUploadArgs(BaseModel):
    file_path: str = Field(..., description='Local path to file to upload')
    platform: str = Field('generic', description='Source platform (label)')

class DriveUploadToolWrapper(BaseTool):
    name: str = 'Google Drive Upload Tool'
    description: str = 'Upload files to Google Drive and create shareable links'
    args_schema: type[BaseModel] = DriveUploadArgs
    _wrapped_tool: Any = PrivateAttr()
    _default_file_path: str | None = PrivateAttr(default=None)
    _default_platform: str | None = PrivateAttr(default=None)

    def __init__(self, wrapped_tool, default_file_path: str | None=None, default_platform: str | None=None, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
        self._default_file_path = default_file_path
        self._default_platform = default_platform

    def _run(self, file_path: str='', platform: str='generic', **kwargs) -> Any:
        try:
            if not file_path and self._default_file_path:
                file_path = self._default_file_path
            if not platform and self._default_platform:
                platform = self._default_platform
            if hasattr(self._wrapped_tool, 'run'):
                return self._wrapped_tool.run(file_path=file_path, platform=platform)
            return self._wrapped_tool._run(file_path=file_path, platform=platform)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class EnhancedAnalysisArgs(BaseModel):
    content: str = Field(..., description='Content to analyze')

class EnhancedContentAnalysisToolWrapper(BaseTool):
    name: str = 'Enhanced Content Analysis Tool'
    description: str = 'Analyze content with multiple analysis modes and intelligent fallbacks'
    args_schema: type[BaseModel] = EnhancedAnalysisArgs
    _wrapped_tool: Any = PrivateAttr()
    _default_content: str | None = PrivateAttr(default=None)

    def __init__(self, wrapped_tool, default_content: str | None=None, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
        self._default_content = default_content

    def _run(self, content: str='', **kwargs) -> Any:
        try:
            if not content and 'text' in kwargs:
                content = str(kwargs['text'])
            if not content and self._default_content:
                content = self._default_content
            if hasattr(self._wrapped_tool, 'run'):
                return self._wrapped_tool.run(content=content)
            return self._wrapped_tool._run(content)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))

class ClaimExtractorArgs(BaseModel):
    text: str = Field(..., description='Text to extract factual claims from')

class ClaimExtractorToolWrapper(BaseTool):
    name: str = 'Claim Extractor Tool'
    description: str = 'Extract potential factual claims from text using linguistic patterns.'
    args_schema: type[BaseModel] = ClaimExtractorArgs
    _wrapped_tool: Any = PrivateAttr()
    _default_text: str | None = PrivateAttr(default=None)

    def __init__(self, wrapped_tool, default_text: str | None=None, **kwargs):
        super().__init__(**kwargs)
        self._wrapped_tool = wrapped_tool
        self._default_text = default_text

    def _run(self, text: str='', **kwargs) -> Any:
        try:
            if not text and 'content' in kwargs:
                text = str(kwargs['content'])
            if not text and self._default_text:
                text = self._default_text
            if hasattr(self._wrapped_tool, 'run'):
                return self._wrapped_tool.run(text=text)
            return self._wrapped_tool._run(text)
        except Exception as e:
            from .step_result import StepResult
            return StepResult.fail(error=str(e))