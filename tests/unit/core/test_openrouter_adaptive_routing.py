import pytest

from ultimate_discord_intelligence_bot.services.openrouter_service import (
    context as context_module,
)
from ultimate_discord_intelligence_bot.services.openrouter_service import (
    execution as execution_module,
)
from ultimate_discord_intelligence_bot.services.openrouter_service import (
    service as service_module,
)
from ultimate_discord_intelligence_bot.services.openrouter_service.service import (
    OpenRouterService,
)


class DummyConfig:
    def __init__(self) -> None:
        self.openrouter_general_model = "test/general"
        self.openrouter_analysis_model = None
        self.openrouter_api_key = None
        self.enable_cache_global = False
        self.rate_limit_redis_url = None
        self.cache_ttl_llm = 3600
        self.cache_dir = "./cache"

    def get_setting(self, name: str) -> object | None:
        return getattr(self, name, None)


class DummySettings:
    enable_ax_routing = True
    enable_semantic_cache = False
    enable_gptcache = False
    enable_semantic_cache_shadow = False
    enable_semantic_cache_promotion = False
    semantic_cache_threshold = 0.8
    semantic_cache_ttl_seconds = 3600
    semantic_cache_promotion_threshold = 0.9
    reward_cost_weight = 0.5
    reward_latency_weight = 0.5
    reward_latency_ms_window = 2000
    openrouter_referer = None
    openrouter_title = None
    enable_vllm_local = False
    local_llm_url = None


class DummyTokenMeter:
    def __init__(self, *, max_cost_per_request: float = 100.0, estimate: float = 0.05) -> None:
        self.max_cost_per_request = max_cost_per_request
        self._estimate = estimate
        self.model_prices = {"model-a": 0.001, "model-b": 0.001}

    def estimate_cost(self, tokens_in: int, model: str, prices: dict[str, float] | None = None) -> float:
        return self._estimate

    def affordable_model(
        self,
        tokens_in: int,
        models: list[str] | None,
        prices: dict[str, float] | None = None,
    ) -> str | None:
        if not models:
            return None
        return models[0]


class DummyPromptEngine:
    def optimise_with_metadata(self, prompt: str, model: str) -> tuple[str, dict[str, int]]:
        return prompt, {"final_tokens": len(prompt)}

    def count_tokens(self, text: str, model: str) -> int:
        return len(text)


class DummyTracker:
    def __init__(self) -> None:
        self.charges: list[tuple[float, str]] = []

    def can_charge(self, _cost: float, _task_type: str) -> bool:
        return True

    def charge(self, cost: float, task_type: str) -> None:
        self.charges.append((cost, task_type))


class DummyLogger:
    def __init__(self) -> None:
        self.llm_calls: list[tuple] = []
        self.bandit_events: list[dict[str, object]] = []

    def log_llm_call(
        self,
        task: str,
        model: str,
        provider: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        latency_ms: float,
        profile_id: str | None,
        success: bool,
        error: str | None,
    ) -> None:
        self.llm_calls.append(
            (
                task,
                model,
                provider,
                tokens_in,
                tokens_out,
                cost,
                latency_ms,
                profile_id,
                success,
                error,
            )
        )

    def log_bandit_event(self, event: dict[str, object]) -> None:
        self.bandit_events.append(event)


class DummyAdaptiveManager:
    def __init__(self, suggestion: str) -> None:
        self.enabled = True
        self.suggestion = suggestion
        self.suggest_calls: list[tuple[str, list[str], dict[str, object]]] = []
        self.observe_calls: list[tuple[str, int, float, dict[str, object]]] = []
        self._events: list[dict[str, object]] = []

    def suggest(
        self,
        task_type: str,
        candidates: list[str],
        context: dict[str, object],
    ) -> tuple[int, str] | None:
        self.suggest_calls.append((task_type, candidates, context))
        return 1, self.suggestion

    def observe(
        self,
        task_type: str,
        trial_index: int,
        reward: float,
        metadata: dict[str, object],
    ) -> None:
        self.observe_calls.append((task_type, trial_index, reward, metadata))
        event = {
            "task_type": task_type,
            "reward": reward,
            "model": metadata.get("model") or metadata.get("chosen_model") or self.suggestion,
        }
        event.update(metadata)
        self._events.append(event)

    def drain_events(self) -> list[dict[str, object]]:
        events = list(self._events)
        self._events.clear()
        return events


def _build_service(
    monkeypatch: pytest.MonkeyPatch,
    *,
    token_meter: DummyTokenMeter | None = None,
    manager: DummyAdaptiveManager | None = None,
) -> tuple[OpenRouterService, DummyAdaptiveManager, DummyLogger]:
    monkeypatch.delenv("ENABLE_AX_ROUTING", raising=False)
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE", raising=False)
    monkeypatch.delenv("ENABLE_GPTCACHE", raising=False)
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE_SHADOW", raising=False)
    monkeypatch.delenv("ENABLE_SEMANTIC_CACHE_PROMOTION", raising=False)

    config = DummyConfig()
    settings = DummySettings()
    monkeypatch.setattr(service_module, "get_config", lambda: config)
    monkeypatch.setattr(service_module, "get_settings", lambda: settings)
    monkeypatch.setattr(execution_module, "get_settings", lambda: settings)
    monkeypatch.setattr(context_module, "_crt", lambda: DummyTracker())

    logger = DummyLogger()
    tm = token_meter or DummyTokenMeter()
    svc = OpenRouterService(
        models_map={"general": ["model-a", "model-b"]},
        api_key=None,
        token_meter=tm,
        logger=logger,
    )
    svc.prompt_engine = DummyPromptEngine()
    svc.token_meter = tm
    mgr = manager or DummyAdaptiveManager("model-b")
    svc.adaptive_routing = mgr
    return svc, mgr, logger


def test_adaptive_routing_success_records_reward(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, manager, logger = _build_service(monkeypatch)

    result = service.route("hello world", task_type="general")

    assert result["status"] == "success"
    assert result["model"] == manager.suggestion
    assert manager.suggest_calls and manager.observe_calls
    _, _, reward, metadata = manager.observe_calls[0]
    assert metadata["status"] == "success"
    assert metadata["execution_mode"] == "offline"
    assert reward > 0.0
    assert logger.bandit_events
    event = logger.bandit_events[0]
    assert event["status"] == "success"
    assert event["model"] == manager.suggestion


def test_adaptive_routing_budget_rejection_records_observation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token_meter = DummyTokenMeter(max_cost_per_request=0.01, estimate=1.0)
    service, manager, logger = _build_service(monkeypatch, token_meter=token_meter)

    result = service.route("hi", task_type="general")

    assert result["status"] == "error"
    assert "projected cost" in str(result["error"])
    assert manager.observe_calls
    _, _, reward, metadata = manager.observe_calls[0]
    assert reward == 0.0
    assert metadata["status"] == "budget_rejection"
    assert metadata["reason"] == "per_request_limit"
    assert logger.bandit_events
    assert logger.bandit_events[0]["status"] == "budget_rejection"
