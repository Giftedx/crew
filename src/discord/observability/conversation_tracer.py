"""
Conversation tracing and analysis for Discord AI chatbot.

This module provides detailed conversation tracing, context analysis,
and conversation flow tracking for debugging and optimization.
"""
from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from platform.core.step_result import StepResult

@dataclass
class ConversationStep:
    """Represents a single step in a conversation."""
    step_id: str
    timestamp: float
    step_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = True
    parent_step_id: str | None = None
    child_step_ids: list[str] = field(default_factory=list)

@dataclass
class ConversationTrace:
    """Complete trace of a conversation flow."""
    trace_id: str
    conversation_id: str
    user_id: str
    guild_id: str
    channel_id: str
    start_time: float
    end_time: float | None = None
    steps: list[ConversationStep] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    summary: str = ''
    performance_metrics: dict[str, float] = field(default_factory=dict)

@dataclass
class ConversationContext:
    """Context information for conversation analysis."""
    user_history: list[dict[str, Any]] = field(default_factory=list)
    channel_context: dict[str, Any] = field(default_factory=dict)
    guild_context: dict[str, Any] = field(default_factory=dict)
    personality_state: dict[str, float] = field(default_factory=dict)
    memory_context: dict[str, Any] = field(default_factory=dict)
    system_state: dict[str, Any] = field(default_factory=dict)

class ConversationTracer:
    """
    Advanced conversation tracing and analysis system.

    This tracer provides detailed tracking of conversation flows, decision points,
    and performance metrics for debugging and optimization.
    """

    def __init__(self, max_traces: int=1000, max_steps_per_trace: int=100):
        self.max_traces = max_traces
        self.max_steps_per_trace = max_steps_per_trace
        self._active_traces: dict[str, ConversationTrace] = {}
        self._trace_history: list[ConversationTrace] = []
        self._context_cache: dict[str, ConversationContext] = {}
        self._performance_metrics: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()
        self._stats = {'total_traces': 0, 'active_traces': 0, 'avg_trace_duration_ms': 0.0, 'avg_steps_per_trace': 0.0, 'error_rate': 0.0}

    async def start_trace(self, conversation_id: str, user_id: str, guild_id: str, channel_id: str, initial_context: dict[str, Any] | None=None) -> StepResult:
        """Start tracing a new conversation."""
        try:
            trace_id = str(uuid.uuid4())
            trace = ConversationTrace(trace_id=trace_id, conversation_id=conversation_id, user_id=user_id, guild_id=guild_id, channel_id=channel_id, start_time=time.time(), context=initial_context or {})
            async with self._lock:
                self._active_traces[trace_id] = trace
                self._stats['active_traces'] = len(self._active_traces)
            await self._load_conversation_context(trace_id, user_id, guild_id, channel_id)
            return StepResult.ok(data={'trace_id': trace_id, 'action': 'trace_started'})
        except Exception as e:
            return StepResult.fail(f'Failed to start conversation trace: {e!s}')

    async def add_step(self, trace_id: str, step_type: str, content: str, metadata: dict[str, Any] | None=None, parent_step_id: str | None=None, start_time: float | None=None) -> StepResult:
        """Add a step to an active conversation trace."""
        try:
            async with self._lock:
                if trace_id not in self._active_traces:
                    return StepResult.fail(f'Trace {trace_id} not found')
                trace = self._active_traces[trace_id]
                if len(trace.steps) >= self.max_steps_per_trace:
                    return StepResult.fail('Trace has reached maximum step limit')
                step_id = str(uuid.uuid4())
                current_time = time.time()
                step = ConversationStep(step_id=step_id, timestamp=current_time, step_type=step_type, content=content, metadata=metadata or {}, parent_step_id=parent_step_id)
                if start_time:
                    step.duration_ms = (current_time - start_time) * 1000
                trace.steps.append(step)
                if parent_step_id:
                    for parent_step in trace.steps:
                        if parent_step.step_id == parent_step_id:
                            parent_step.child_step_ids.append(step_id)
                            break
                return StepResult.ok(data={'step_id': step_id, 'step_added': True})
        except Exception as e:
            return StepResult.fail(f'Failed to add step to trace: {e!s}')

    async def end_step(self, trace_id: str, step_id: str, success: bool=True, final_content: str | None=None, error_message: str | None=None) -> StepResult:
        """End a step in a conversation trace."""
        try:
            async with self._lock:
                if trace_id not in self._active_traces:
                    return StepResult.fail(f'Trace {trace_id} not found')
                trace = self._active_traces[trace_id]
                for step in trace.steps:
                    if step.step_id == step_id:
                        step.success = success
                        if final_content:
                            step.content = final_content
                        if error_message:
                            step.metadata['error'] = error_message
                        if step.step_type in self._performance_metrics:
                            self._performance_metrics[step.step_type].append(step.duration_ms)
                        else:
                            self._performance_metrics[step.step_type] = [step.duration_ms]
                        return StepResult.ok(data={'step_ended': True, 'duration_ms': step.duration_ms})
                return StepResult.fail(f'Step {step_id} not found in trace {trace_id}')
        except Exception as e:
            return StepResult.fail(f'Failed to end step: {e!s}')

    async def end_trace(self, trace_id: str, summary: str | None=None, performance_metrics: dict[str, float] | None=None) -> StepResult:
        """End a conversation trace and move to history."""
        try:
            async with self._lock:
                if trace_id not in self._active_traces:
                    return StepResult.fail(f'Trace {trace_id} not found')
                trace = self._active_traces[trace_id]
                trace.end_time = time.time()
                if summary:
                    trace.summary = summary
                if performance_metrics:
                    trace.performance_metrics = performance_metrics
                self._trace_history.append(trace)
                del self._active_traces[trace_id]
                await self._update_trace_stats(trace)
                if len(self._trace_history) > self.max_traces:
                    self._trace_history = self._trace_history[-self.max_traces:]
                self._stats['active_traces'] = len(self._active_traces)
                return StepResult.ok(data={'trace_id': trace_id, 'action': 'trace_ended', 'total_steps': len(trace.steps), 'duration_ms': (trace.end_time - trace.start_time) * 1000})
        except Exception as e:
            return StepResult.fail(f'Failed to end trace: {e!s}')

    async def get_trace(self, trace_id: str) -> StepResult:
        """Get a specific trace by ID."""
        try:
            async with self._lock:
                if trace_id in self._active_traces:
                    return StepResult.ok(data={'trace': self._active_traces[trace_id], 'status': 'active'})
                for trace in self._trace_history:
                    if trace.trace_id == trace_id:
                        return StepResult.ok(data={'trace': trace, 'status': 'completed'})
                return StepResult.fail(f'Trace {trace_id} not found')
        except Exception as e:
            return StepResult.fail(f'Failed to get trace: {e!s}')

    async def get_conversation_traces(self, conversation_id: str) -> StepResult:
        """Get all traces for a specific conversation."""
        try:
            async with self._lock:
                traces = []
                for trace in self._active_traces.values():
                    if trace.conversation_id == conversation_id:
                        traces.append({'trace': trace, 'status': 'active'})
                for trace in self._trace_history:
                    if trace.conversation_id == conversation_id:
                        traces.append({'trace': trace, 'status': 'completed'})
                return StepResult.ok(data={'traces': traces})
        except Exception as e:
            return StepResult.fail(f'Failed to get conversation traces: {e!s}')

    async def analyze_conversation_flow(self, trace_id: str) -> StepResult:
        """Analyze the flow and patterns in a conversation trace."""
        try:
            trace_result = await self.get_trace(trace_id)
            if not trace_result.success:
                return trace_result
            trace = trace_result.data['trace']
            flow_analysis = {'total_steps': len(trace.steps), 'step_types': {}, 'decision_points': [], 'error_points': [], 'performance_bottlenecks': [], 'conversation_pattern': 'unknown', 'complexity_score': 0.0}
            for step in trace.steps:
                step_type = step.step_type
                if step_type in flow_analysis['step_types']:
                    flow_analysis['step_types'][step_type] += 1
                else:
                    flow_analysis['step_types'][step_type] = 1
                if step.step_type == 'bot_decision':
                    flow_analysis['decision_points'].append({'step_id': step.step_id, 'content': step.content, 'metadata': step.metadata})
                if not step.success:
                    flow_analysis['error_points'].append({'step_id': step.step_id, 'error': step.metadata.get('error', 'Unknown error'), 'step_type': step.step_type})
                if step.duration_ms > 5000:
                    flow_analysis['performance_bottlenecks'].append({'step_id': step.step_id, 'step_type': step.step_type, 'duration_ms': step.duration_ms})
            if len(trace.steps) < 5:
                flow_analysis['conversation_pattern'] = 'simple'
            elif len(trace.steps) < 15:
                flow_analysis['conversation_pattern'] = 'moderate'
            else:
                flow_analysis['conversation_pattern'] = 'complex'
            flow_analysis['complexity_score'] = len(trace.steps) * 0.3 + len(flow_analysis['decision_points']) * 0.4 + len(flow_analysis['error_points']) * 0.2 + len(flow_analysis['performance_bottlenecks']) * 0.1
            return StepResult.ok(data={'flow_analysis': flow_analysis})
        except Exception as e:
            return StepResult.fail(f'Failed to analyze conversation flow: {e!s}')

    async def get_performance_insights(self) -> StepResult:
        """Get performance insights from trace data."""
        try:
            async with self._lock:
                insights = {'step_type_performance': {}, 'average_performance': {}, 'performance_trends': {}, 'recommendations': []}
                for step_type, durations in self._performance_metrics.items():
                    if durations:
                        avg_duration = sum(durations) / len(durations)
                        max_duration = max(durations)
                        min_duration = min(durations)
                        insights['step_type_performance'][step_type] = {'avg_duration_ms': avg_duration, 'max_duration_ms': max_duration, 'min_duration_ms': min_duration, 'sample_count': len(durations)}
                if self._trace_history:
                    total_duration = 0
                    total_steps = 0
                    for trace in self._trace_history:
                        if trace.end_time:
                            total_duration += (trace.end_time - trace.start_time) * 1000
                            total_steps += len(trace.steps)
                    if total_steps > 0:
                        insights['average_performance'] = {'avg_conversation_duration_ms': total_duration / len(self._trace_history), 'avg_steps_per_conversation': total_steps / len(self._trace_history), 'avg_step_duration_ms': total_duration / total_steps}
                recommendations = []
                for step_type, perf in insights['step_type_performance'].items():
                    if perf['avg_duration_ms'] > 3000:
                        recommendations.append(f'Consider optimizing {step_type} operations (avg: {perf['avg_duration_ms']:.1f}ms)')
                error_count = sum((1 for trace in self._trace_history for step in trace.steps if not step.success))
                total_steps = sum((len(trace.steps) for trace in self._trace_history))
                if total_steps > 0:
                    error_rate = error_count / total_steps
                    if error_rate > 0.1:
                        recommendations.append(f'High error rate detected: {error_rate:.1%}. Review error handling.')
                insights['recommendations'] = recommendations
                return StepResult.ok(data={'performance_insights': insights})
        except Exception as e:
            return StepResult.fail(f'Failed to get performance insights: {e!s}')

    async def _load_conversation_context(self, trace_id: str, user_id: str, guild_id: str, channel_id: str):
        """Load conversation context for analysis."""
        try:
            context = ConversationContext(user_history=[], channel_context={'channel_id': channel_id}, guild_context={'guild_id': guild_id}, personality_state={}, memory_context={}, system_state={'timestamp': time.time()})
            self._context_cache[trace_id] = context
        except Exception:
            pass

    async def _update_trace_stats(self, trace: ConversationTrace):
        """Update trace statistics."""
        self._stats['total_traces'] += 1
        if trace.end_time:
            duration = trace.end_time - trace.start_time
            total_traces = self._stats['total_traces']
            if self._stats['avg_trace_duration_ms'] == 0:
                self._stats['avg_trace_duration_ms'] = duration * 1000
            else:
                self._stats['avg_trace_duration_ms'] = (self._stats['avg_trace_duration_ms'] * (total_traces - 1) + duration * 1000) / total_traces
        step_count = len(trace.steps)
        if self._stats['avg_steps_per_trace'] == 0:
            self._stats['avg_steps_per_trace'] = step_count
        else:
            self._stats['avg_steps_per_trace'] = (self._stats['avg_steps_per_trace'] * (total_traces - 1) + step_count) / total_traces
        error_steps = sum((1 for step in trace.steps if not step.success))
        total_steps = sum((len(t.steps) for t in self._trace_history))
        if total_steps > 0:
            self._stats['error_rate'] = error_steps / total_steps

    async def get_tracer_stats(self) -> StepResult:
        """Get tracer statistics."""
        try:
            async with self._lock:
                return StepResult.ok(data={'tracer_stats': self._stats, 'active_traces': len(self._active_traces), 'trace_history_size': len(self._trace_history), 'context_cache_size': len(self._context_cache)})
        except Exception as e:
            return StepResult.fail(f'Failed to get tracer stats: {e!s}')

    async def export_trace(self, trace_id: str, fmt: str='json') -> StepResult:
        """Export a trace in the specified format."""
        try:
            trace_result = await self.get_trace(trace_id)
            if not trace_result.success:
                return trace_result
            trace = trace_result.data['trace']
            if fmt.lower() == 'json':
                export_data = {'trace_id': trace.trace_id, 'conversation_id': trace.conversation_id, 'user_id': trace.user_id, 'guild_id': trace.guild_id, 'channel_id': trace.channel_id, 'start_time': trace.start_time, 'end_time': trace.end_time, 'summary': trace.summary, 'performance_metrics': trace.performance_metrics, 'steps': [{'step_id': step.step_id, 'timestamp': step.timestamp, 'step_type': step.step_type, 'content': step.content, 'metadata': step.metadata, 'duration_ms': step.duration_ms, 'success': step.success, 'parent_step_id': step.parent_step_id, 'child_step_ids': step.child_step_ids} for step in trace.steps]}
                return StepResult.ok(data={'export_data': export_data, 'format': format})
            else:
                return StepResult.fail(f'Unsupported export format: {format}')
        except Exception as e:
            return StepResult.fail(f'Failed to export trace: {e!s}')

def create_conversation_tracer(max_traces: int=1000, max_steps_per_trace: int=100) -> ConversationTracer:
    """Create a conversation tracer with the specified configuration."""
    return ConversationTracer(max_traces, max_steps_per_trace)