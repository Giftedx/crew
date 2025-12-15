#!/usr/bin/env python3
"""Benchmark harness for /autointel flag combination validation.

This script runs the 8 flag combinations from Week 3 validation plan,
collecting timing and quality metrics for each combination across 3 iterations.

USAGE:
    # Run all 8 combinations (3 iterations each = 24 total runs)
    python scripts/benchmark_autointel_flags.py --url "https://youtube.com/watch?v=..." --iterations 3

    # Run specific combinations only
    python scripts/benchmark_autointel_flags.py --url "..." --combinations 1 2 3

    # Quick test (1 iteration, combinations 1 and 8 only)
    python scripts/benchmark_autointel_flags.py --url "..." --iterations 1 --combinations 1 8

OUTPUT:
    - JSON results file: benchmarks/flag_validation_results_{timestamp}.json
    - Summary report: benchmarks/flag_validation_summary_{timestamp}.md
    - Per-combination logs: benchmarks/logs/combination_{N}_iter_{M}.log

EXPECTED RUNTIME:
    - Full suite (24 runs): ~4-6 hours (depends on video length)
    - Individual baselines (Combinations 1-4, 3 iterations each): ~2-3 hours
    - Quick test (Combinations 1 + 8, 1 iteration each): ~20-30 min
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.autonomous_orchestrator import (
    AutonomousIntelligenceOrchestrator,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

# The 8 flag combinations
FLAG_COMBINATIONS = {
    1: {
        "name": "sequential_baseline",
        "ENABLE_PARALLEL_MEMORY_OPS": "0",
        "ENABLE_PARALLEL_ANALYSIS": "0",
        "ENABLE_PARALLEL_FACT_CHECKING": "0",
        "expected_savings_min": 0.0,
        "expected_savings_max": 0.0,
        "description": "Original sequential flow (baseline)",
    },
    2: {
        "name": "memory_only",
        "ENABLE_PARALLEL_MEMORY_OPS": "1",
        "ENABLE_PARALLEL_ANALYSIS": "0",
        "ENABLE_PARALLEL_FACT_CHECKING": "0",
        "expected_savings_min": 0.5,
        "expected_savings_max": 1.0,
        "description": "Memory operations parallelization only",
    },
    3: {
        "name": "analysis_only",
        "ENABLE_PARALLEL_MEMORY_OPS": "0",
        "ENABLE_PARALLEL_ANALYSIS": "1",
        "ENABLE_PARALLEL_FACT_CHECKING": "0",
        "expected_savings_min": 1.0,
        "expected_savings_max": 2.0,
        "description": "Analysis subtasks parallelization only",
    },
    4: {
        "name": "fact_checking_only",
        "ENABLE_PARALLEL_MEMORY_OPS": "0",
        "ENABLE_PARALLEL_ANALYSIS": "0",
        "ENABLE_PARALLEL_FACT_CHECKING": "1",
        "expected_savings_min": 0.5,
        "expected_savings_max": 1.0,
        "description": "Fact-checking parallelization only",
    },
    5: {
        "name": "memory_analysis",
        "ENABLE_PARALLEL_MEMORY_OPS": "1",
        "ENABLE_PARALLEL_ANALYSIS": "1",
        "ENABLE_PARALLEL_FACT_CHECKING": "0",
        "expected_savings_min": 1.5,
        "expected_savings_max": 3.0,
        "description": "Memory + Analysis parallelization (combined)",
    },
    6: {
        "name": "memory_fact_checking",
        "ENABLE_PARALLEL_MEMORY_OPS": "1",
        "ENABLE_PARALLEL_ANALYSIS": "0",
        "ENABLE_PARALLEL_FACT_CHECKING": "1",
        "expected_savings_min": 1.0,
        "expected_savings_max": 2.0,
        "description": "Memory + Fact-checking parallelization (combined)",
    },
    7: {
        "name": "analysis_fact_checking",
        "ENABLE_PARALLEL_MEMORY_OPS": "0",
        "ENABLE_PARALLEL_ANALYSIS": "1",
        "ENABLE_PARALLEL_FACT_CHECKING": "1",
        "expected_savings_min": 1.5,
        "expected_savings_max": 3.0,
        "description": "Analysis + Fact-checking parallelization (combined)",
    },
    8: {
        "name": "all_parallel",
        "ENABLE_PARALLEL_MEMORY_OPS": "1",
        "ENABLE_PARALLEL_ANALYSIS": "1",
        "ENABLE_PARALLEL_FACT_CHECKING": "1",
        "expected_savings_min": 2.0,
        "expected_savings_max": 4.0,
        "description": "All parallelizations enabled (full optimization)",
    },
}

# ============================================================================
# MOCK DISCORD INTERACTION
# ============================================================================


def create_mock_interaction():
    """Create a mock Discord interaction for testing."""
    interaction = MagicMock()
    interaction.guild_id = 123456789
    interaction.channel = MagicMock()
    interaction.channel.name = "benchmark-harness"
    interaction.followup = MagicMock()

    # Make followup.send async
    async def mock_send(*args, **kwargs):
        pass

    interaction.followup.send = mock_send
    return interaction


# ============================================================================
# BENCHMARKING FUNCTIONS
# ============================================================================


EXTRA_FLAG_NAMES = [
    # Phase 2 / alternative optimization flags we want to record for analysis
    "ENABLE_SEMANTIC_CACHE",
    "ENABLE_PROMPT_COMPRESSION",
    # Future-proof: harmless to include; present if user experiments manually
    "ENABLE_SEMANTIC_CACHE_SHADOW",
    "ENABLE_SEMANTIC_CACHE_PROMOTION",
    "ENABLE_LLMLINGUA",
    "ENABLE_TRANSCRIPT_COMPRESSION",
]


async def run_single_benchmark(
    combination_id: int,
    iteration: int,
    url: str,
    depth: str,
    output_dir: Path,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Run a single benchmark iteration for a flag combination.

    Args:
        combination_id: Combination number (1-8)
        iteration: Iteration number (1-based)
        url: YouTube URL to process
        depth: Analysis depth (experimental)
        output_dir: Directory for logs/results
        logger: Logger instance

    Returns:
        dict with timing, quality, and metadata
    """
    combo = FLAG_COMBINATIONS[combination_id]
    logger.info(f"Running Combination {combination_id} ({combo['name']}) - Iteration {iteration}")

    run_logs_dir = output_dir / "logs"
    run_logs_dir.mkdir(parents=True, exist_ok=True)
    run_log_path = run_logs_dir / f"combination_{combination_id}_iteration_{iteration}.json"

    # Set core parallelization environment variables for this combination while preserving originals
    env_backup: dict[str, str | None] = {}
    core_flags = [
        "ENABLE_PARALLEL_MEMORY_OPS",
        "ENABLE_PARALLEL_ANALYSIS",
        "ENABLE_PARALLEL_FACT_CHECKING",
    ]
    for flag in core_flags:
        env_backup[flag] = os.environ.get(flag)
        os.environ[flag] = combo[flag]

    # Capture (but do not mutate) extra optimization flags so we can record them
    extra_flag_snapshot: dict[str, str | None] = {name: os.environ.get(name) for name in EXTRA_FLAG_NAMES}

    try:
        # Create orchestrator instance
        orchestrator = AutonomousIntelligenceOrchestrator()

        # Create mock interaction
        interaction = create_mock_interaction()

        # Run benchmark
        start_time = time.time()
        start_datetime = datetime.now()

        logger.info(f"  Starting execution at {start_datetime.isoformat()}")

        # Execute workflow
        await orchestrator.execute_autonomous_intelligence_workflow(interaction=interaction, url=url, depth=depth)

        end_time = time.time()
        end_datetime = datetime.now()
        duration_seconds = end_time - start_time

        logger.info(f"  Completed in {duration_seconds:.2f}s ({duration_seconds / 60:.2f} min)")

        # Collect results (extract from orchestrator state if available)
        # Note: This requires orchestrator to expose results, which may need enhancement
        transcript_length = None
        quality_score = None
        trustworthiness_score = None
        insights_count = None
        verified_claims_count = None

        if hasattr(orchestrator, "last_execution_result") and orchestrator.last_execution_result:
            try:
                task_outputs = orchestrator.last_execution_result.get("task_outputs", {})

                # Extract transcript length
                transcription_output = task_outputs.get("transcription")
                if transcription_output:
                    if hasattr(transcription_output, "transcript_length"):
                         transcript_length = transcription_output.transcript_length
                    elif isinstance(transcription_output, str):
                        transcript_length = len(transcription_output)
                    elif hasattr(transcription_output, "get"): # Dictionary-like
                         transcript_length = transcription_output.get("transcript_length")
                         if not transcript_length and transcription_output.get("transcript"):
                             transcript_length = len(transcription_output.get("transcript"))

                # Extract quality metrics if available (placeholder logic based on available data)
                # We can expand this as more structured output becomes available

            except Exception as e:
                logger.warning(f"Failed to extract metrics from orchestrator result: {e}")

        result = {
            "combination_id": combination_id,
            "combination_name": combo["name"],
            "iteration": iteration,
            "url": url,
            "depth": depth,
            # Record both the controlled (core) flags and passive extra flags state
            "flags": {
                "ENABLE_PARALLEL_MEMORY_OPS": combo["ENABLE_PARALLEL_MEMORY_OPS"],
                "ENABLE_PARALLEL_ANALYSIS": combo["ENABLE_PARALLEL_ANALYSIS"],
                "ENABLE_PARALLEL_FACT_CHECKING": combo["ENABLE_PARALLEL_FACT_CHECKING"],
                **{k: ("" if v is None else v) for k, v in extra_flag_snapshot.items()},
            },
            "timing": {
                "start": start_datetime.isoformat(),
                "end": end_datetime.isoformat(),
                "duration_seconds": duration_seconds,
                "duration_minutes": duration_seconds / 60,
            },
            "expected_savings": {
                "min_minutes": combo["expected_savings_min"],
                "max_minutes": combo["expected_savings_max"],
            },
            # Quality metrics (would need to extract from orchestrator)
            "quality": {
                "transcript_length": transcript_length,
                "quality_score": quality_score,
                "trustworthiness_score": trustworthiness_score,
                "insights_count": insights_count,
                "verified_claims_count": verified_claims_count,
            },
            "success": True,
            "error": None,
        }

        return result

        run_log_path.write_text(
            json.dumps(
                {
                    "logged_at": datetime.now().isoformat(),
                    "combination_id": combination_id,
                    "iteration": iteration,
                    "timing": result["timing"],
                    "flags": result["flags"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    except Exception as e:
        logger.error(f"  ERROR: {e!s}", exc_info=True)
        return {
            "combination_id": combination_id,
            "combination_name": combo["name"],
            "iteration": iteration,
            "url": url,
            "depth": depth,
            "success": False,
            "error": str(e),
            "timing": {"duration_seconds": 0, "duration_minutes": 0},
        }

    finally:
        # Restore environment variables
        for flag, value in env_backup.items():
            if value is None:
                os.environ.pop(flag, None)
            else:
                os.environ[flag] = value


async def run_combination_benchmarks(
    combination_id: int,
    iterations: int,
    url: str,
    depth: str,
    output_dir: Path,
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """Run multiple iterations for a single combination.

    Args:
        combination_id: Combination number (1-8)
        iterations: Number of iterations to run
        url: YouTube URL to process
        depth: Analysis depth
        output_dir: Directory for results
        logger: Logger instance

    Returns:
        List of result dicts (one per iteration)
    """
    results = []

    for i in range(1, iterations + 1):
        result = await run_single_benchmark(combination_id, i, url, depth, output_dir, logger)
        results.append(result)

        # Save intermediate results
        interim_file = output_dir / f"combination_{combination_id}_interim.json"
        with open(interim_file, "w") as f:
            json.dump(results, f, indent=2)

    return results


# ============================================================================
# ANALYSIS & REPORTING
# ============================================================================


def calculate_statistics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate statistical metrics from multiple iterations.

    Args:
        results: List of result dicts from iterations

    Returns:
        dict with mean, median, std, min, max
    """
    successful_results = [r for r in results if r["success"]]

    if not successful_results:
        return {"error": "No successful runs"}

    durations = [r["timing"]["duration_seconds"] for r in successful_results]

    return {
        "count": len(successful_results),
        "mean_seconds": sum(durations) / len(durations),
        "mean_minutes": sum(durations) / len(durations) / 60,
        "min_seconds": min(durations),
        "min_minutes": min(durations) / 60,
        "max_seconds": max(durations),
        "max_minutes": max(durations) / 60,
        "median_seconds": sorted(durations)[len(durations) // 2],
        "median_minutes": sorted(durations)[len(durations) // 2] / 60,
        "std_seconds": (sum((d - sum(durations) / len(durations)) ** 2 for d in durations) / len(durations)) ** 0.5
        if len(durations) > 1
        else 0,
    }


def generate_summary_report(all_results: dict[int, list[dict[str, Any]]], output_file: Path) -> None:
    """Generate a markdown summary report.

    Args:
        all_results: Dict mapping combination_id -> list of results
        output_file: Path to write markdown report
    """
    # Calculate baseline (Combination 1)
    # Baseline (Combination 1). Previous implementation used a static 629s (~10.5 min)
    # fallback which became misleading once true baseline improved (e.g. ~170s).
    # New logic:
    # 1. If combination 1 present with successful runs -> use its mean
    # 2. Else: find earliest successful run across any combination and use that
    # 3. Else: retain conservative 629s sentinel
    baseline_stats = calculate_statistics(all_results.get(1, []))
    baseline_mean: float
    if all_results.get(1) and "mean_seconds" in baseline_stats:
        baseline_mean = float(baseline_stats["mean_seconds"])  # true baseline
    else:
        # Fallback scan for earliest successful duration
        candidate = None
        earliest_ts = None
        for _combo_id, runs in all_results.items():
            for r in runs:
                if r.get("success") and r.get("timing", {}).get("duration_seconds"):
                    # Parse start time if available
                    start_iso = r.get("timing", {}).get("start")
                    duration = r["timing"]["duration_seconds"]
                    if start_iso:
                        try:
                            ts = datetime.fromisoformat(start_iso)
                        except Exception:  # pragma: no cover - defensive
                            ts = None
                    else:
                        ts = None
                    if candidate is None or (ts and earliest_ts and ts < earliest_ts) or (ts and earliest_ts is None):
                        candidate = duration
                        earliest_ts = ts
        baseline_mean = float(candidate) if candidate is not None else 629.0

    report_lines = [
        "# Flag Combination Validation Results",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Baseline Mean:** {baseline_mean:.2f}s ({baseline_mean / 60:.2f} min)",
        "",
        "---",
        "",
        "## Summary Table",
        "",
        "| Combination | Name | Mean Time | vs Baseline | Expected Savings | Actual Savings | Status |",
        "|-------------|------|-----------|-------------|------------------|----------------|--------|",
    ]

    for combo_id in sorted(all_results.keys()):
        combo = FLAG_COMBINATIONS[combo_id]
        stats = calculate_statistics(all_results[combo_id])

        if "error" in stats:
            report_lines.append(f"| {combo_id} | {combo['name']} | ERROR | - | - | - | ❌ |")
            continue

        mean_time = stats["mean_minutes"]
        actual_savings = (baseline_mean / 60) - mean_time
        expected_min = combo["expected_savings_min"]
        expected_max = combo["expected_savings_max"]

        # Determine status
        if combo_id == 1:
            status = "📊 Baseline"
        elif expected_min <= actual_savings <= expected_max * 1.2:  # Allow 20% margin
            status = "✅ Pass"
        elif actual_savings >= expected_min * 0.8:  # Within 80% of target
            status = "⚠️ Partial"
        else:
            status = "❌ Fail"

        report_lines.append(
            f"| {combo_id} | {combo['name']} | {mean_time:.2f} min | "
            f"{actual_savings:+.2f} min | {expected_min:.1f}-{expected_max:.1f} min | "
            f"{actual_savings:.2f} min | {status} |"
        )

    report_lines.extend(
        [
            "",
            "---",
            "",
            "## Detailed Statistics",
            "",
        ]
    )

    for combo_id in sorted(all_results.keys()):
        combo = FLAG_COMBINATIONS[combo_id]
        stats = calculate_statistics(all_results[combo_id])

        report_lines.extend(
            [
                f"### Combination {combo_id}: {combo['name']}",
                "",
                f"**Description:** {combo['description']}",
                "",
                "**Flags:**",
                f"- ENABLE_PARALLEL_MEMORY_OPS: {combo['ENABLE_PARALLEL_MEMORY_OPS']}",
                f"- ENABLE_PARALLEL_ANALYSIS: {combo['ENABLE_PARALLEL_ANALYSIS']}",
                f"- ENABLE_PARALLEL_FACT_CHECKING: {combo['ENABLE_PARALLEL_FACT_CHECKING']}",
                "",
            ]
        )

        if "error" in stats:
            report_lines.append("**Status:** ❌ All runs failed")
            continue

        report_lines.extend(
            [
                "**Statistics:**",
                f"- Iterations: {stats['count']}",
                f"- Mean: {stats['mean_seconds']:.2f}s ({stats['mean_minutes']:.2f} min)",
                f"- Median: {stats['median_seconds']:.2f}s ({stats['median_minutes']:.2f} min)",
                f"- Min: {stats['min_seconds']:.2f}s ({stats['min_minutes']:.2f} min)",
                f"- Max: {stats['max_seconds']:.2f}s ({stats['max_minutes']:.2f} min)",
                f"- Std Dev: {stats['std_seconds']:.2f}s",
                "",
            ]
        )

    # Write report
    with open(output_file, "w") as f:
        f.write("\n".join(report_lines))


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def main():
    """Main benchmark harness execution."""
    parser = argparse.ArgumentParser(description="Benchmark /autointel flag combinations")
    parser.add_argument("--url", required=True, help="YouTube URL to process")
    parser.add_argument(
        "--depth",
        default="experimental",
        choices=["standard", "deep", "comprehensive", "experimental"],
        help="Analysis depth",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Iterations per combination (default: 3)",
    )
    parser.add_argument(
        "--combinations",
        nargs="+",
        type=int,
        default=list(range(1, 9)),
        help="Combinations to run (default: all 1-8)",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks"), help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = args.output_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"benchmark_run_{timestamp}.log"

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Flag Combination Benchmark Harness")
    logger.info("=" * 80)
    logger.info(f"URL: {args.url}")
    logger.info(f"Depth: {args.depth}")
    logger.info(f"Iterations per combination: {args.iterations}")
    logger.info(f"Combinations to run: {args.combinations}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info("=" * 80)

    # Run benchmarks
    all_results: dict[int, list[dict[str, Any]]] = {}

    for combo_id in sorted(args.combinations):
        if combo_id not in FLAG_COMBINATIONS:
            logger.warning(f"Invalid combination ID: {combo_id}, skipping")
            continue

        logger.info(f"\n{'=' * 80}")
        logger.info(f"Starting Combination {combo_id}: {FLAG_COMBINATIONS[combo_id]['name']}")
        logger.info(f"{'=' * 80}\n")

        results = await run_combination_benchmarks(
            combo_id, args.iterations, args.url, args.depth, args.output_dir, logger
        )

        all_results[combo_id] = results

        # Show summary for this combination
        stats = calculate_statistics(results)
        if "error" not in stats:
            logger.info(f"\nCombination {combo_id} Summary:")
            logger.info(f"  Mean: {stats['mean_seconds']:.2f}s ({stats['mean_minutes']:.2f} min)")
            logger.info(f"  Median: {stats['median_seconds']:.2f}s ({stats['median_minutes']:.2f} min)")
            logger.info(f"  Range: {stats['min_seconds']:.2f}s - {stats['max_seconds']:.2f}s")

    # Save full results
    results_file = args.output_dir / f"flag_validation_results_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"\n\nFull results saved to: {results_file}")

    # Generate summary report
    summary_file = args.output_dir / f"flag_validation_summary_{timestamp}.md"
    generate_summary_report(all_results, summary_file)

    logger.info(f"Summary report saved to: {summary_file}")
    logger.info("\n" + "=" * 80)
    logger.info("Benchmark run complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
