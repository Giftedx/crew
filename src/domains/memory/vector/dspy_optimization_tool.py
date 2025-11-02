"""Tool to drive DSPy optimization workflows for agents.

Actions:
- optimize: Compile an optimized module for a given signature and training set; optional save.
- load: Verify a previously optimized module exists and is loadable.
- compare: A/B test an optimized module against a baseline.
- metric: Compute a metric over a module and a test set.
"""

from __future__ import annotations

import json
from pathlib import Path
from platform.core.step_result import StepResult
from platform.observability.metrics import get_metrics
from typing import Any, Literal

from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.settings import Settings

from ._base import BaseTool


SignatureName = Literal[
    "DebateAnalysisSignature",
    "FactCheckingSignature",
    "ClaimExtractionSignature",
    "SentimentAnalysisSignature",
    "SummaryGenerationSignature",
]


class DSPyOptimizationSchema(BaseModel):
    action: Literal["optimize", "load", "compare", "metric"] = Field(..., description="Operation to perform")
    signature: SignatureName | None = Field(None, description="DSPy signature name to optimize/evaluate")
    optimization_level: Literal["light", "medium", "heavy"] | None = Field(
        "medium", description="Optimization intensity for DSPy"
    )
    training_data_path: str | None = Field(None, description="Path to JSON training set (from generator script)")
    test_data_path: str | None = Field(None, description="Path to JSON test set for evaluation/compare")
    data_limit: int | None = Field(50, description="Limit number of examples loaded from dataset")
    agent_name: str | None = Field(None, description="Logical agent name for saving/loading modules")
    version: str | None = Field(None, description="Version tag to save or load an optimized module")
    baseline_version: str | None = Field(None, description="Baseline version to compare against")


class DSPyOptimizationTool(BaseTool[dict]):
    """Manage DSPy optimization lifecycle (optimize, load, compare, metric)."""

    name: str = "dspy_optimization_tool"
    description: str = "Compile and evaluate DSPy-optimized modules for specific agent signatures."
    args_schema: type[BaseModel] = DSPyOptimizationSchema

    def __init__(self) -> None:
        super().__init__()
        self.settings = Settings()

    @staticmethod
    def _import_signatures() -> dict[str, Any]:
        try:
            from ..services.dspy_components.signature import (
                ClaimExtractionSignature,
                DebateAnalysisSignature,
                FactCheckingSignature,
                SentimentAnalysisSignature,
                SummaryGenerationSignature,
            )

            return {
                "DebateAnalysisSignature": DebateAnalysisSignature,
                "FactCheckingSignature": FactCheckingSignature,
                "ClaimExtractionSignature": ClaimExtractionSignature,
                "SentimentAnalysisSignature": SentimentAnalysisSignature,
                "SummaryGenerationSignature": SummaryGenerationSignature,
            }
        except Exception:
            return {}

    def _resolve_signature(self, signature_name: SignatureName | None) -> Any:
        mapping = self._import_signatures()
        default_sig = mapping.get("DebateAnalysisSignature")
        if not signature_name:
            return default_sig
        return mapping.get(signature_name, default_sig)

    @staticmethod
    def _default_metric(example: Any, prediction: Any, trace: Any | None = None) -> float:
        """Very permissive metric to enable compilation in generic contexts."""
        try:
            text = str(getattr(prediction, "__dict__", prediction))
            return 1.0 if text and len(text) > 0 else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _load_examples(json_path: str, signature: Any, limit: int | None) -> list[Any]:
        p = Path(json_path)
        if not p.exists():
            return []
        try:
            raw = json.loads(p.read_text())
        except Exception:
            return []
        try:
            import dspy
        except Exception:
            return []
        examples: list[Any] = []
        for rec in raw if isinstance(raw, list) else []:
            try:
                sig_name = getattr(signature, "__name__", None)
                if sig_name == "DebateAnalysisSignature":
                    transcript = (
                        rec.get("transcript")
                        or rec.get("context")
                        or rec.get("content")
                        or rec.get("text")
                        or rec.get("question")
                        or ""
                    )
                    ex = dspy.Example(transcript=str(transcript)).with_inputs("transcript")
                elif sig_name in ("SentimentAnalysisSignature", "ClaimExtractionSignature"):
                    text = rec.get("text") or rec.get("context") or rec.get("content") or rec.get("question") or ""
                    ex = dspy.Example(text=str(text)).with_inputs("text")
                elif sig_name == "FactCheckingSignature":
                    claim = rec.get("claim") or rec.get("question") or ""
                    ctx = rec.get("context") or rec.get("text") or rec.get("content") or ""
                    ex = dspy.Example(claim=str(claim), context=str(ctx)).with_inputs("claim", "context")
                else:
                    content = rec.get("content") or rec.get("context") or rec.get("text") or ""
                    ex = dspy.Example(content=str(content), max_length=150).with_inputs("content", "max_length")
                examples.append(ex)
            except Exception:
                continue
            if limit and len(examples) >= limit:
                break
        return examples

    def _run(
        self,
        action: Literal["optimize", "load", "compare", "metric"],
        signature: SignatureName | None = None,
        optimization_level: Literal["light", "medium", "heavy"] | None = "medium",
        training_data_path: str | None = None,
        test_data_path: str | None = None,
        data_limit: int | None = 50,
        agent_name: str | None = None,
        version: str | None = None,
        baseline_version: str | None = None,
    ) -> StepResult:
        if not getattr(self.settings, "enable_dspy_optimization", False):
            return StepResult.skip(step=self.name, reason="DSPy optimization disabled in settings")
        try:
            from ..services.dspy_optimization_service import AgentOptimizer
        except Exception:
            return StepResult.skip(step=self.name, reason="DSPy runtime not available")
        sig_cls = self._resolve_signature(signature)
        if sig_cls is None:
            return StepResult.fail("Unable to resolve DSPy signature; ensure dspy is installed")
        try:
            with get_metrics().tool_timer(self.name):
                if action == "optimize":
                    if not training_data_path:
                        return StepResult.fail("training_data_path is required for optimize")
                    train = self._load_examples(training_data_path, sig_cls, data_limit or 50)
                    if not train:
                        return StepResult.fail("No training examples loaded from training_data_path")
                    metric = self._default_metric
                    optimizer = AgentOptimizer()
                    res = optimizer.optimize_agent_prompt(
                        agent_signature=sig_cls,
                        training_examples=train,
                        metric=metric,
                        optimization_level=optimization_level or "medium",
                    )
                    if not res.success:
                        return res
                    saved_to: str | None = None
                    if agent_name and version:
                        sv = optimizer.save_optimized_module(res.data, agent_name=agent_name, version=version)
                        if not sv.success:
                            return sv
                        saved_to = sv.data.get("saved_to") if isinstance(sv.data, dict) else None
                    get_metrics().counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
                    return StepResult.ok(
                        data={"optimized": True, "saved_to": saved_to, "agent": agent_name, "version": version}
                    )
                if action == "load":
                    if not agent_name or not version:
                        return StepResult.fail("agent_name and version are required for load")
                    optimizer = AgentOptimizer()
                    lr = optimizer.load_optimized_module(agent_name=agent_name, version=version, signature=sig_cls)
                    if not lr.success:
                        return lr
                    return StepResult.ok(data={"loaded": True, "agent": agent_name, "version": version})
                if action == "compare":
                    if not all([agent_name, version, baseline_version, test_data_path]):
                        return StepResult.fail(
                            "agent_name, version, baseline_version, and test_data_path are required for compare"
                        )
                    optimizer = AgentOptimizer()
                    lr_opt = optimizer.load_optimized_module(agent_name=agent_name, version=version, signature=sig_cls)
                    lr_base = optimizer.load_optimized_module(
                        agent_name=agent_name, version=baseline_version, signature=sig_cls
                    )
                    if not lr_opt.success:
                        return lr_opt
                    if not lr_base.success:
                        return lr_base
                    test = self._load_examples(test_data_path, sig_cls, data_limit or 50)
                    if not test:
                        return StepResult.fail("No test examples loaded from test_data_path")
                    cmp_res = optimizer.compare_optimized_vs_baseline(
                        optimized_module=lr_opt.data,
                        baseline_module=lr_base.data,
                        test_examples=test,
                        metric=self._default_metric,
                    )
                    return cmp_res
                if action == "metric":
                    if not test_data_path:
                        return StepResult.fail("test_data_path is required for metric")
                    optimizer = AgentOptimizer()
                    module_res: StepResult | None = None
                    if agent_name and version:
                        module_res = optimizer.load_optimized_module(
                            agent_name=agent_name, version=version, signature=sig_cls
                        )
                        if not module_res.success:
                            return module_res
                    else:
                        return StepResult.fail("agent_name and version are required for metric")
                    test = self._load_examples(test_data_path, sig_cls, data_limit or 50)
                    if not test:
                        return StepResult.fail("No test examples loaded from test_data_path")
                    return optimizer.calculate_metric(
                        module=module_res.data, examples=test, metric=self._default_metric
                    )
                return StepResult.fail(f"Unknown action: {action}")
        except Exception as e:
            get_metrics().counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            return StepResult.fail(error=str(e), step=self.name)
