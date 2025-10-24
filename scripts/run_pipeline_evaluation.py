#!/usr/bin/env python3
"""
Pipeline evaluation runner script.

This script runs comprehensive evaluation of the multimodal pipeline on test episodes,
validating WER, DER, cost, and latency criteria.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kg.creator_kg_store import CreatorKGStore
from pipeline.evaluation_harness import PipelineEvaluationHarness
from pipeline.multimodal_pipeline import MultimodalContentPipeline, PipelineConfig
from ultimate_discord_intelligence_bot.step_result import StepResult


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def create_mock_pipeline() -> MultimodalContentPipeline:
    """Create a mock pipeline for testing."""
    config = PipelineConfig(
        enable_diarization=True,
        enable_visual_analysis=True,
        enable_claim_extraction=True,
        max_processing_time=600,  # 10 minutes
        max_audio_duration_hours=3,
    )

    # Create mock KG store
    kg_store = CreatorKGStore(":memory:")  # In-memory SQLite for testing

    return MultimodalContentPipeline(config, kg_store)


async def run_evaluation(output_file: str | None = None, episodes_count: int = 5, verbose: bool = False) -> StepResult:
    """Run the pipeline evaluation."""
    try:
        logger.info("Starting pipeline evaluation...")

        # Create pipeline and KG store
        pipeline = await create_mock_pipeline()
        kg_store = CreatorKGStore(":memory:")

        # Create evaluation harness
        harness = PipelineEvaluationHarness(
            pipeline=pipeline,
            kg_store=kg_store,
            tenant="evaluation",
            workspace="testing",
        )

        # Get test episodes
        episodes = harness.create_test_episodes()
        if episodes_count < len(episodes):
            episodes = episodes[:episodes_count]

        logger.info(f"Evaluating {len(episodes)} episodes...")

        # Run evaluation
        results = await harness.run_evaluation(episodes)

        # Print summary
        summary = results["summary"]
        aggregate = results["aggregate_metrics"]

        print("\n" + "=" * 80)
        print("PIPELINE EVALUATION RESULTS")
        print("=" * 80)

        print(f"\nOverall Status: {summary['overall_status']}")
        print(f"Episodes Evaluated: {aggregate['total_episodes']}")
        print(f"Success Rate: {aggregate['success_rate']:.1%}")

        print("\nPerformance Metrics:")
        print(f"  Average WER: {aggregate['average_wer']:.1%} (target: ≤12%)")
        print(f"  Average DER: {aggregate['average_der']:.1%} (target: ≤20%)")
        print(f"  Average Cost: ${aggregate['average_cost']:.2f} (target: ≤$2.00)")
        print(f"  Average Latency: {aggregate['average_latency']:.1f}s (target: ≤600s)")

        print("\nCriteria Status:")
        for criterion, passed in summary["criteria_met"].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {criterion.upper()}: {status}")

        if summary["criteria_failed"]:
            print("\nFailed Criteria:")
            for criterion, reason in summary["criteria_failed"].items():
                print(f"  {criterion.upper()}: {reason}")

        if summary["recommendations"]:
            print("\nRecommendations:")
            for i, rec in enumerate(summary["recommendations"], 1):
                print(f"  {i}. {rec}")

        print("\nStage Success Rates:")
        for stage, rate in aggregate["stage_success_rates"].items():
            print(f"  {stage}: {rate:.1%}")

        if verbose:
            print("\nDetailed Results:")
            for i, (episode, metrics) in enumerate(zip(results["episodes"], results["metrics"], strict=False), 1):
                print(f"\nEpisode {i}: {episode['title']}")
                print(f"  Creator: {episode['creator']}")
                print(f"  Platform: {episode['platform']}")
                print(f"  WER: {metrics['word_error_rate']:.1%}")
                print(f"  DER: {metrics['diarization_error_rate']:.1%}")
                print(f"  Cost: ${metrics['total_cost']:.2f}")
                print(f"  Latency: {metrics['total_latency']:.1f}s")
                print(f"  Stages Completed: {', '.join(metrics['stages_completed'])}")
                if metrics["stages_failed"]:
                    print(f"  Stages Failed: {', '.join(metrics['stages_failed'])}")

        # Save results if requested
        if output_file:
            save_result = harness.save_results(output_file)
            if save_result.success:
                print(f"\nResults saved to: {output_file}")
            else:
                print(f"\nFailed to save results: {save_result.error}")

        # Return success/failure based on overall status
        if summary["overall_status"] == "PASS":
            return StepResult.ok(data=results)
        else:
            return StepResult.fail(f"Evaluation failed: {len(summary['criteria_failed'])} criteria not met")

    except Exception as e:
        logger.error(f"Evaluation failed: {e!s}")
        return StepResult.fail(f"Evaluation failed: {e!s}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run pipeline evaluation")
    parser.add_argument("--output", "-o", type=str, help="Output file for results (JSON format)")
    parser.add_argument(
        "--episodes",
        "-e",
        type=int,
        default=5,
        help="Number of episodes to evaluate (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed results",
    )

    args = parser.parse_args()

    # Run evaluation
    result = asyncio.run(run_evaluation(output_file=args.output, episodes_count=args.episodes, verbose=args.verbose))

    if result.success:
        print("\n✓ Evaluation completed successfully!")
        sys.exit(0)
    else:
        print(f"\n✗ Evaluation failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
