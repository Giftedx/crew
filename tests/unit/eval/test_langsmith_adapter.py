"""Tests for the LangSmith evaluation adapter and integration."""
from __future__ import annotations
import time
import pytest
from eval.langsmith_adapter import LangSmithEvaluationAdapter
from eval.trajectory_evaluator import AgentTrajectory, TrajectoryEvaluator, TrajectoryStep
from platform.core.step_result import StepResult

class DisabledSettings:
    enable_langsmith_eval = False
    langsmith_api_key = None
    langsmith_project = 'test-project'
    langsmith_evaluation_dataset = None
    langsmith_evaluation_name = 'trajectory-accuracy'

class EnabledSettings(DisabledSettings):
    enable_langsmith_eval = True
    langsmith_api_key = 'test-key'

@pytest.fixture
def sample_trajectory() -> AgentTrajectory:
    steps = [TrajectoryStep(timestamp=time.time(), agent_role='researcher', action_type='tool_call', content='used the search tool', tool_name='search', tool_args={'query': 'ai', 'model_id': 'gpt-4'}, success=True), TrajectoryStep(timestamp=time.time() + 1, agent_role='researcher', action_type='response', content='analysis complete', success=True)]
    return AgentTrajectory(session_id='traj-123', user_input='Find AI info', steps=steps, final_output='All good', total_duration=2.0, success=True, tenant='tenant-a', workspace='workspace-a')

def test_adapter_skip_when_disabled(sample_trajectory: AgentTrajectory) -> None:
    adapter = LangSmithEvaluationAdapter(settings=DisabledSettings(), evaluate_fn=lambda **_: {})
    result = adapter.evaluate(sample_trajectory)
    assert result.skipped
    assert result.metadata == {}

def test_adapter_successfully_processes_response(sample_trajectory: AgentTrajectory) -> None:

    def _fake_evaluate(**kwargs):
        assert kwargs['evaluation'] == 'trajectory-accuracy'
        return {'id': 'eval-001', 'metrics': {'score': True, 'reasoning': 'Great trajectory', 'accuracy_score': 0.91, 'efficiency_score': 0.87, 'error_handling_score': 0.9}}
    adapter = LangSmithEvaluationAdapter(settings=EnabledSettings(), evaluate_fn=_fake_evaluate)
    result = adapter.evaluate(sample_trajectory)
    assert result.success
    assert not result.skipped
    assert result.data['accuracy_score'] == pytest.approx(0.91)
    assert result.metadata['langsmith_evaluation_id'] == 'eval-001'
    assert result.metadata['evaluator'] == 'LangSmith'

def test_trajectory_evaluator_uses_langsmith_when_available(sample_trajectory: AgentTrajectory, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('ENABLE_TRAJECTORY_EVALUATION', '1')
    evaluator = TrajectoryEvaluator(router=None, learning_engine=None, rl_model_router=None)

    class _FakeLangSmithAdapter:

        def evaluate(self, trajectory: AgentTrajectory) -> StepResult:
            result = StepResult.ok(score=True, reasoning='LangSmith approves', accuracy_score=0.93, efficiency_score=0.88, error_handling_score=0.9, evaluation_id='ls-777', raw_metrics={'score': 1.0})
            result.metadata['langsmith_evaluation_id'] = 'ls-777'
            return result
    evaluator.langsmith_adapter = _FakeLangSmithAdapter()
    monkeypatch.setattr(evaluator, '_simulate_llm_evaluation', lambda *_args, **_kwargs: {'score': False})
    result = evaluator.evaluate_trajectory_accuracy(sample_trajectory)
    assert result.success
    assert result.data['evaluator'] == 'LangSmith'
    assert result.data['accuracy_score'] == pytest.approx(0.93)
    assert result.metadata['langsmith_adapter_status'] == 'success'
    assert result.metadata['langsmith_evaluation_id'] == 'ls-777'

def test_trajectory_evaluator_falls_back_when_langsmith_fails(sample_trajectory: AgentTrajectory, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('ENABLE_TRAJECTORY_EVALUATION', '1')
    evaluator = TrajectoryEvaluator(router=None, learning_engine=None, rl_model_router=None)

    class _FailingLangSmithAdapter:

        def evaluate(self, trajectory: AgentTrajectory) -> StepResult:
            return StepResult.with_context(success=False, error='adapter failure')
    evaluator.langsmith_adapter = _FailingLangSmithAdapter()
    heuristic_response = {'score': True, 'reasoning': 'fallback heuristic', 'accuracy_score': 0.8, 'efficiency_score': 0.75, 'error_handling_score': 0.7}
    monkeypatch.setattr(evaluator, '_simulate_llm_evaluation', lambda *_: heuristic_response)
    result = evaluator.evaluate_trajectory_accuracy(sample_trajectory)
    assert result.success
    assert result.data['evaluator'] == 'LLMHeuristic'
    assert result.metadata['langsmith_adapter_status'] == 'error'
    assert 'adapter failure' in result.metadata['langsmith_adapter_error']
    assert result.metadata['fallback_model'] == 'heuristic_default'
    assert result.metadata['fallback_reason'].startswith('adapter failure')
    assert isinstance(result.metadata['fallback_latency_ms'], float)
    assert result.metadata['fallback_latency_ms'] >= 0.0