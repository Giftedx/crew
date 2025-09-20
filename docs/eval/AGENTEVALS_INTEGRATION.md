# AgentEvals Integration (Optional)

This repository includes an optional integration with the `agentevals` trajectory evaluators to score agent trajectories using an LLM-as-judge or trajectory match evaluators.

## Feature flags

- ENABLE_TRAJECTORY_EVALUATION=1  # master switch for trajectory evaluation paths
- ENABLE_AGENT_EVALS=1            # enables agentevals-backed evaluator (optional)
- AGENTEVALS_MODEL=openai:o3-mini # optional; model identifier for agentevals judge

By default, if ENABLE_AGENT_EVALS is not set, the system falls back to an internal heuristic evaluator.

## Where it lives

- Code: `src/eval/trajectory_evaluator.py`
  - Uses `_to_agentevals_messages()` to convert internal trajectories into the agentevals message schema.
  - Returns results via `StepResult.ok(...)` preserving the repository-wide contract.

## Usage

1) Enable feature flags in your environment:

```bash
export ENABLE_TRAJECTORY_EVALUATION=1
export ENABLE_AGENT_EVALS=1
export AGENTEVALS_MODEL=openai:o3-mini
```

1) Execute a Crew run that records execution steps. `EnhancedCrewEvaluator` will extract a trajectory and call the trajectory evaluator.

1) If agentevals is installed, results will include `evaluator="AgentEvals"`; otherwise `evaluator="LLMHeuristic"`.

## Fallbacks

- If the agentevals package is missing or errors occur at runtime, the evaluator records a degradation metric and gracefully falls back to the heuristic evaluator without raising.

## Testing

- A lightweight adapter test is in `tests/test_trajectory_evaluator_agentevals.py`.
- Quick CI sweep continues to pass without requiring agentevals installation.
