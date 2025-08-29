from __future__ import annotations

"""Simple multi-agent debate panel."""

from collections.abc import Callable
from dataclasses import dataclass, field

from core.learning_engine import LearningEngine
from core.router import Router
from obs import tracing


@dataclass
class PanelConfig:
    """Configuration for a debate panel."""

    roles: list[str]
    routing_profiles: list[str] | None = None
    n_rounds: int = 1
    aggregation_strategy: str = "vote"


@dataclass
class AgentResult:
    role: str
    model: str
    output: str
    confidence: float = 0.0


@dataclass
class DebateReport:
    agents: list[AgentResult]
    final: str
    votes: dict[str, str] = field(default_factory=dict)


@tracing.trace_call("debate.run_panel")
def run_panel(
    query: str,
    router: Router,
    call_model: Callable[[str, str], str],
    config: PanelConfig,
    engine: LearningEngine | None = None,
    reward: float = 0.0,
) -> DebateReport:
    """Run a debate panel.

    Parameters
    ----------
    query: str
        User question or prompt.
    router: Router
        Model router used to pick models per role.
    call_model: Callable[[str, str], str]
        Function invoked as ``call_model(model, prompt)``.
    config: PanelConfig
        Panel configuration specifying roles and rounds.
    engine: LearningEngine, optional
        RL engine used to record rewards. If ``None`` the panel runs
        without recording.
    """

    agents: list[AgentResult] = []

    for role in config.roles:
        model = router.route(
            task="debate",
            candidates=config.routing_profiles or ["gpt-3.5-turbo"],
            context={"role": role, "prompt": query},
        )
        output = call_model(model, f"{role}: {query}")
        agents.append(AgentResult(role=role, model=model, output=output))

    votes: dict[str, str] = {}
    if config.aggregation_strategy == "vote":
        for agent in agents:
            votes[agent.role] = agent.role
        final = agents[0].output
    else:
        final = "\n".join(a.output for a in agents)

    if engine:
        for agent in agents:
            engine.record("debate", {}, agent.role, agent.confidence)
        engine.record("debate", {}, "panel", reward)

    return DebateReport(agents=agents, final=final, votes=votes)


__all__ = ["PanelConfig", "run_panel", "DebateReport", "AgentResult"]
