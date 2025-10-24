"""Deception scoring tool.

Computes a quantitative deception risk score based on fact-check outcomes
and reasoning quality signals (e.g., logical fallacies). The score is a
float in [0, 1], where higher means greater risk of deception (by either
the content's originator or its subject).

Inputs (flexible dict):
- factchecks: list of {verdict: str, confidence: float, claim?: str, source?: str,
               source_trust?: float (0..1), salience?: float (0..1)}
- fallacies: list or dict with key "fallacies" (optional)
- weights: optional {false: float, likely_false: float, uncertain: float, fallacy: float}
- source_trust: optional mapping {source_name: float (0..1)} used when items include "source"

Returns StepResult with:
- score: float in [0, 1]
- components: dict of partial contributions
- summary: human-readable short description
 - claims: per-claim breakdown [{claim, score, adverse_count}]
"""

from __future__ import annotations

from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


class _DeceptionInputs(TypedDict, total=False):
    factchecks: list[dict]
    fallacies: list[dict] | dict
    weights: dict
    source_trust: dict[str, float]


class DeceptionScoringTool(BaseTool[StepResult]):
    name = "Deception Scoring Tool"
    description = "Quantify deception risk from fact-checks and fallacy signals."

    def __init__(self) -> None:
        self._metrics = get_metrics()

    def run(self, payload: _DeceptionInputs | None = None, /, **kwargs: Any) -> StepResult:
        try:
            data = payload or {}
            factchecks = data.get("factchecks") or kwargs.get("factchecks") or []
            fallacies = data.get("fallacies") or kwargs.get("fallacies") or []
            source_trust_map = data.get("source_trust") or kwargs.get("source_trust") or {}
            weights = {
                "false": 1.0,
                "likely_false": 0.7,
                "uncertain": 0.4,
                "fallacy": 0.15,  # each distinct fallacy adds this capped contribution
                "fallacy_cap": 0.3,  # cap cumulative fallacy contribution
            }
            # allow custom weights override
            w_override = data.get("weights") or kwargs.get("weights") or {}
            if isinstance(w_override, dict):
                weights.update(
                    {k: float(v) for k, v in w_override.items() if k in weights and isinstance(v, (int, float))}
                )

            # Normalize and score fact-checks
            def _norm_verdict(v: Any) -> str:
                if isinstance(v, str):
                    return v.strip().lower()
                return ""

            total_weight = 0.0
            contribution = 0.0
            fc_items: list[dict] = []
            # Per-claim aggregation containers
            per_claim_sum: dict[str, float] = {}
            per_claim_w: dict[str, float] = {}
            per_claim_adverse: dict[str, int] = {}
            if isinstance(factchecks, list):
                for fc in factchecks:
                    try:
                        # Accept both flat and nested dict shapes
                        verdict = fc.get("verdict")
                        if verdict is None and isinstance(fc.get("data"), dict):
                            verdict = fc["data"].get("verdict")
                        confidence = fc.get("confidence")
                        if confidence is None and isinstance(fc.get("data"), dict):
                            confidence = fc["data"].get("confidence")
                        claim_text = fc.get("claim") or ""
                        source_name = fc.get("source") or None
                        # Source trust can be provided per-item or via map
                        src_trust = fc.get("source_trust")
                        if not isinstance(src_trust, (int, float)):
                            if isinstance(source_trust_map, dict) and isinstance(source_name, str):
                                st = source_trust_map.get(source_name)
                                src_trust = float(st) if isinstance(st, (int, float)) else 1.0
                            else:
                                src_trust = 1.0
                        else:
                            src_trust = float(src_trust)
                        conf = float(confidence) if isinstance(confidence, (int, float, str)) else 0.5
                        try:
                            # tolerate str values for confidence
                            conf = float(conf)
                        except Exception:
                            conf = 0.5
                        # Clamp weights
                        conf_w = max(0.5, min(conf, 1.0))
                        src_w = max(0.0, min(float(src_trust), 1.0)) if isinstance(src_trust, (int, float)) else 1.0
                        sal = fc.get("salience")
                        sal_w = float(sal) if isinstance(sal, (int, float, str)) else 1.0
                        try:
                            sal_w = float(sal_w)
                        except Exception:
                            sal_w = 1.0
                        sal_w = max(0.5, min(sal_w, 1.0))
                        v = _norm_verdict(verdict)
                        base = 0.0
                        if v == "false":
                            base = weights["false"]
                        elif v == "likely false":
                            base = weights["likely_false"]
                        elif v in {
                            "uncertain",
                            "needs context",
                            "requires further research",
                            "insufficient evidence",
                        }:
                            base = weights["uncertain"]
                        else:
                            base = 0.0  # true/likely true reduce risk implicitly by not adding
                        # Composite item weight (bounded)
                        item_w = conf_w * src_w * sal_w
                        contribution += base * item_w
                        total_weight += item_w
                        fc_items.append(
                            {
                                "verdict": v,
                                "confidence": conf_w,
                                "source_trust": src_w,
                                "salience": sal_w,
                                "base": base,
                                "claim": claim_text or None,
                                "source": source_name,
                                "weight": item_w,
                            }
                        )
                        # Per-claim roll-up
                        if claim_text:
                            per_claim_sum[claim_text] = per_claim_sum.get(claim_text, 0.0) + (base * item_w)
                            per_claim_w[claim_text] = per_claim_w.get(claim_text, 0.0) + item_w
                            if base > 0:
                                per_claim_adverse[claim_text] = per_claim_adverse.get(claim_text, 0) + 1
                    except Exception:
                        continue

            # Fallacy contribution (distinct types)
            fallacy_types: set[str] = set()
            if isinstance(fallacies, dict):
                cand = fallacies.get("fallacies")
                if isinstance(cand, list):
                    fallacies = cand
            if isinstance(fallacies, list):
                for f in fallacies:
                    if isinstance(f, dict):
                        t = (f.get("type") or f.get("name") or "").strip().lower()
                        if t:
                            fallacy_types.add(t)

            fallacy_contrib = min(
                len(fallacy_types) * float(weights["fallacy"]),
                float(weights["fallacy_cap"]),
            )

            # Aggregate score
            # If there are no fact-checks, base score derives only from fallacies
            if total_weight > 0:
                fc_score = contribution / max(total_weight, 1e-9)  # 0..1 normalized risk from fact-checks
            else:
                fc_score = 0.0

            score = max(0.0, min(1.0, fc_score + fallacy_contrib))

            # Classification buckets for UI
            if score >= 0.7:
                label = "high"
            elif score >= 0.4:
                label = "moderate"
            else:
                label = "low"

            # Build per-claim breakdown (top 3 by score)
            claim_breakdown: list[dict[str, Any]] = []
            try:
                for c, ssum in per_claim_sum.items():
                    w = per_claim_w.get(c, 0.0) or 1.0
                    cscore = max(0.0, min(1.0, ssum / max(w, 1e-9)))
                    claim_breakdown.append(
                        {
                            "claim": c,
                            "score": cscore,
                            "adverse_count": per_claim_adverse.get(c, 0),
                        }
                    )
                claim_breakdown.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                claim_breakdown = claim_breakdown[:3]
            except Exception:
                claim_breakdown = []

            # Summary string keeps low-cardinality counters only
            summary = (
                f"Deception risk: {label} (score={score:.2f}). "
                f"Signals: {len([i for i in fc_items if i['base'] > 0])} adverse fact-checks, "
                f"{len(fallacy_types)} fallacy types."
            )

            # Metrics (best-effort)
            try:
                self._metrics.histogram("deception_score", score, labels={"bucket": label}).observe(score)  # type: ignore[attr-defined]
            except Exception:
                pass

            return StepResult.ok(
                score=score,
                label=label,
                components={
                    "factcheck_score": fc_score,
                    "fallacy_contribution": fallacy_contrib,
                    "factchecks": fc_items,
                    "fallacies": sorted(fallacy_types),
                    "claims": claim_breakdown,
                },
                summary=summary,
            )
        except Exception as e:  # pragma: no cover - defensive path
            return StepResult.fail(error=str(e))


__all__ = ["DeceptionScoringTool"]
