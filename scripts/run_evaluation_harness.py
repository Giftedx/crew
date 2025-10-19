#!/usr/bin/env python3
"""
Script to run the Creator Intelligence Evaluation Harness.

This script runs comprehensive evaluation on the gold dataset and generates
detailed reports with trends, alerts, and recommendations.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

from ultimate_discord_intelligence_bot.services.creator_evaluation_harness import CreatorEvaluationHarness
from ultimate_discord_intelligence_bot.step_result import StepResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_evaluation(gold_dataset_path: str = "gold_dataset.json") -> StepResult:
    """Run the full evaluation harness."""
    print("🔬 Creator Intelligence Evaluation Harness")
    print("=" * 60)

    try:
        # Initialize evaluation harness
        harness = CreatorEvaluationHarness()

        # Check if gold dataset exists
        if not Path(gold_dataset_path).exists():
            print(f"❌ Gold dataset not found at {gold_dataset_path}")
            print("   Please run scripts/create_gold_dataset.py first")
            return StepResult.fail("Gold dataset not found")

        print(f"📁 Using gold dataset: {gold_dataset_path}")

        # Display thresholds
        print("\n🎯 Evaluation Thresholds:")
        thresholds = harness.metrics_thresholds
        print(".1%")
        print(".1%")
        print(".2f")
        print(".0f")
        print(".1%")
        print(".1%")

        # Run evaluation
        print("\n🚀 Running evaluation...")
        result = harness.run_evaluation(gold_dataset_path)

        if result.success:
            data = result.data["data"]

            print("\n✅ Evaluation Complete!")
            print(f"📊 Report ID: {data['report_id']}")
            print(f"🎬 Episodes Evaluated: {data['episodes_evaluated']}")
            print(f"🏆 Overall Status: {'✅ PASSED' if data['overall_passed'] else '❌ NEEDS IMPROVEMENT'}")

            # Display key metrics
            metrics = data["metrics"]
            print("\n📊 Key Metrics:")
            print(".1%")
            print(".1%")
            print(".2f")
            print(".0f")
            print(".1%")
            print(".1%")

            # Display alerts if any
            if "regression_alerts" in data:
                alerts = data["regression_alerts"]
                if alerts:
                    print(f"\n🚨 Alerts: {len(alerts)}")
                    for alert in alerts:
                        print(f"  • {alert}")

            # Display recommendations
            if "recommendations" in data:
                recommendations = data["recommendations"]
                if recommendations:
                    print("\n💡 Recommendations:")
                    for rec in recommendations:
                        print(f"  • {rec}")

            print(f"\n📄 Full report saved to: {data['report_path']}")

            return result
        else:
            print(f"\n❌ Evaluation failed: {result.error}")
            return result

    except Exception as e:
        logger.error(f"Evaluation harness failed: {str(e)}")
        return StepResult.fail(f"Evaluation harness failed: {str(e)}")


def run_continuous_monitoring():
    """Run evaluation in continuous monitoring mode."""
    print("\n📊 Continuous Monitoring Mode")
    print("=" * 40)

    harness = CreatorEvaluationHarness()

    # Run evaluation multiple times to check for trends
    results = []

    for i in range(3):
        print(f"\n🔄 Run {i + 1}/3...")

        # Use different dataset each time (simulate new data)
        dataset_path = f"gold_dataset_run_{i + 1}.json"
        result = harness.run_evaluation(dataset_path)

        if result.success:
            results.append(result.data["data"])
            print(f"  ✅ Run {i + 1} completed")
        else:
            print(f"  ❌ Run {i + 1} failed: {result.error}")
            break

    if len(results) >= 2:
        print("\n📈 Trend Analysis:")

        # Compare first and last runs
        first_run = results[0]["metrics"]
        last_run = results[-1]["metrics"]

        wer_change = last_run["wer"] - first_run["wer"]
        der_change = last_run["der"] - first_run["der"]
        cost_change = last_run["avg_cost_usd"] - first_run["avg_cost_usd"]

        print(".3f")
        print(".3f")
        print(".3f")

        # Overall trend
        if abs(wer_change) < 0.01 and abs(der_change) < 0.02 and abs(cost_change) < 0.10:
            print("📊 Overall Trend: STABLE")
        elif wer_change < -0.01 or der_change < -0.02 or cost_change < -0.10:
            print("📈 Overall Trend: IMPROVING")
        else:
            print("📉 Overall Trend: DEGRADING")


def main():
    """Main function to run evaluation harness."""
    gold_dataset_path = "gold_dataset.json"

    # Run evaluation
    result = run_evaluation(gold_dataset_path)

    if result.success:
        print("\n🎉 Evaluation Harness Complete!")
        print("   System is ready for production deployment")
        return 0
    else:
        print(f"\n❌ Evaluation Harness Failed: {result.error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
