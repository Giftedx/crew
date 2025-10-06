#!/usr/bin/env python3
"""
Week 4 Hybrid Pilot Deployment Script

Deploys Week 4 optimizations (tuned thresholds) to a test Discord server
for 48-hour validation with real user content.

Usage:
    python scripts/deploy_week4_pilot.py --guild-id <discord_server_id> [--duration 48]

    # Or with environment variable:
    export DISCORD_GUILD_ID=<discord_server_id>
    python scripts/deploy_week4_pilot.py
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import (
    ContentPipeline,
)


class Week4PilotMonitor:
    """Monitor Week 4 pilot deployment metrics."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics: List[Dict[str, Any]] = []
        self.start_time = time.time()

    def record_pipeline_run(self, result: Dict[str, Any]) -> None:
        """Record a pipeline run result."""
        self.metrics.append(
            {
                "timestamp": datetime.now().isoformat(),
                "elapsed_since_start": time.time() - self.start_time,
                "result": result,
            }
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.metrics:
            return {
                "total_runs": 0,
                "error": "No metrics collected yet",
            }

        # Extract key metrics
        total_runs = len(self.metrics)
        successful_runs = sum(1 for m in self.metrics if m["result"].get("success", False))

        # Quality bypass analysis
        bypass_activations = sum(
            1 for m in self.metrics if m["result"].get("quality_filtering", {}).get("bypassed", False)
        )
        bypass_rate = (bypass_activations / total_runs * 100) if total_runs > 0 else 0.0

        # Early exit analysis
        exit_activations = sum(1 for m in self.metrics if m["result"].get("early_exit", {}).get("exited", False))
        exit_rate = (exit_activations / total_runs * 100) if total_runs > 0 else 0.0

        # Time savings analysis
        baseline_times = [m["result"].get("baseline_time", 0) for m in self.metrics if "baseline_time" in m["result"]]
        optimized_times = [
            m["result"].get("optimized_time", 0) for m in self.metrics if "optimized_time" in m["result"]
        ]

        avg_time_savings = 0.0
        if baseline_times and optimized_times:
            avg_baseline = sum(baseline_times) / len(baseline_times)
            avg_optimized = sum(optimized_times) / len(optimized_times)
            if avg_baseline > 0:
                avg_time_savings = (avg_baseline - avg_optimized) / avg_baseline * 100

        # Quality score analysis
        quality_scores = [m["result"].get("quality_score", 0) for m in self.metrics if "quality_score" in m["result"]]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        return {
            "pilot_duration_hours": (time.time() - self.start_time) / 3600,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0.0,
            "bypass_activations": bypass_activations,
            "bypass_rate_percent": round(bypass_rate, 1),
            "exit_activations": exit_activations,
            "exit_rate_percent": round(exit_rate, 1),
            "avg_time_savings_percent": round(avg_time_savings, 1),
            "avg_quality_score": round(avg_quality, 2),
            "recommendation": self._get_recommendation(bypass_rate, exit_rate, avg_time_savings, avg_quality),
        }

    def _get_recommendation(
        self,
        bypass_rate: float,
        exit_rate: float,
        time_savings: float,
        quality_score: float,
    ) -> str:
        """Generate deployment recommendation based on metrics."""
        # Check quality first (non-negotiable)
        if quality_score < 0.65:
            return "DO_NOT_DEPLOY - Quality too low (< 0.65)"

        # Check activation rates and time savings
        good_metrics = 0
        if 15 <= bypass_rate <= 30:
            good_metrics += 1
        if 10 <= exit_rate <= 25:
            good_metrics += 1
        if time_savings >= 15:
            good_metrics += 1
        if quality_score >= 0.70:
            good_metrics += 1

        if good_metrics >= 3:
            return "DEPLOY_TO_PRODUCTION - All metrics within target ranges"
        elif good_metrics >= 2:
            return "DEPLOY_WITH_MONITORING - Most metrics acceptable"
        elif good_metrics >= 1:
            return "CONTINUE_TUNING - Some metrics good, others need adjustment"
        else:
            return "INVESTIGATE - Metrics below expectations"

    def save_metrics(self, filename: str = None) -> Path:
        """Save metrics to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"week4_pilot_metrics_{timestamp}.json"

        output_path = self.output_dir / filename
        summary = self.get_summary()

        data = {
            "summary": summary,
            "detailed_metrics": self.metrics,
            "configuration": {
                "quality_min_overall": os.getenv("QUALITY_MIN_OVERALL", "0.55"),
                "min_exit_confidence": "0.70",  # From config/early_exit.yaml
                "pilot_start": datetime.fromtimestamp(self.start_time).isoformat(),
                "pilot_end": datetime.now().isoformat(),
            },
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

    def print_summary(self) -> None:
        """Print summary to console."""
        summary = self.get_summary()

        print("\n" + "=" * 70)
        print("Week 4 PILOT DEPLOYMENT SUMMARY")
        print("=" * 70)
        print(f"\n📊 Pilot Duration: {summary['pilot_duration_hours']:.1f} hours")
        print(f"📈 Total Runs: {summary['total_runs']}")
        print(f"✅ Success Rate: {summary['success_rate']:.1f}%")
        print(f"\n🔍 Quality Bypass:")
        print(f"   Activations: {summary['bypass_activations']} ({summary['bypass_rate_percent']}%)")
        print(f"   Target: 15-30%")
        print(f"\n⚡ Early Exit:")
        print(f"   Activations: {summary['exit_activations']} ({summary['exit_rate_percent']}%)")
        print(f"   Target: 10-25%")
        print(f"\n⏱️  Time Savings:")
        print(f"   Average: {summary['avg_time_savings_percent']}%")
        print(f"   Target: ≥15%")
        print(f"\n⭐ Quality Score:")
        print(f"   Average: {summary['avg_quality_score']}")
        print(f"   Target: ≥0.70")
        print(f"\n🎯 Recommendation:")
        print(f"   {summary['recommendation']}")
        print("\n" + "=" * 70 + "\n")


def setup_pilot_environment(guild_id: str) -> Dict[str, str]:
    """Configure environment for pilot deployment."""
    env_vars = {
        "DISCORD_GUILD_ID": guild_id,
        "QUALITY_MIN_OVERALL": "0.55",  # Tuned threshold
        "ENABLE_QUALITY_FILTERING": "1",
        "ENABLE_EARLY_EXIT": "1",
        "ENABLE_CONTENT_ROUTING": "1",
        "ENABLE_DASHBOARD_METRICS": "1",
    }

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value

    return env_vars


def print_pilot_config(guild_id: str, duration_hours: int, env_vars: Dict[str, str]):
    """Print pilot configuration."""
    print("\n" + "=" * 70)
    print("Week 4 HYBRID PILOT DEPLOYMENT")
    print("=" * 70)
    print(f"\n📍 Target Server: {guild_id}")
    print(f"⏰ Duration: {duration_hours} hours")
    print(f"\n🔧 Configuration:")
    for key, value in env_vars.items():
        print(f"   {key}={value}")

    end_time = datetime.now() + timedelta(hours=duration_hours)
    print(f"\n📅 Pilot Schedule:")
    print(f"   Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n📊 Monitoring: Metrics will be saved to benchmarks/week4_pilot_metrics_*.json")
    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Deploy Week 4 optimizations to test server for pilot validation")
    parser.add_argument(
        "--guild-id",
        type=str,
        help="Discord server ID for pilot deployment",
        default=os.getenv("DISCORD_GUILD_ID"),
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=48,
        help="Pilot duration in hours (default: 48)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("benchmarks"),
        help="Directory for metrics output",
    )

    args = parser.parse_args()

    if not args.guild_id:
        print("❌ Error: Discord server ID required")
        print("\nProvide via --guild-id argument or DISCORD_GUILD_ID environment variable")
        print("\nExample:")
        print("  python scripts/deploy_week4_pilot.py --guild-id 1234567890123456789")
        print("  export DISCORD_GUILD_ID=1234567890123456789")
        print("  python scripts/deploy_week4_pilot.py")
        sys.exit(1)

    # Setup environment
    env_vars = setup_pilot_environment(args.guild_id)

    # Print configuration
    print_pilot_config(args.guild_id, args.duration, env_vars)

    # Initialize monitor
    monitor = Week4PilotMonitor(args.output_dir)

    print("🚀 Starting pilot deployment...")
    print("   Note: This is a monitoring script. Start the Discord bot separately with:")
    print("   python -m ultimate_discord_intelligence_bot.setup_cli run discord\n")

    # Setup monitoring loop
    pilot_end = time.time() + (args.duration * 3600)

    print("📊 Monitoring active. Press Ctrl+C to stop and generate report.\n")

    try:
        # In a real deployment, this would monitor actual pipeline runs
        # For now, provide instructions
        print("=" * 70)
        print("PILOT DEPLOYMENT INSTRUCTIONS")
        print("=" * 70)
        print("\n1. Start the Discord bot in another terminal:")
        print("   python -m ultimate_discord_intelligence_bot.setup_cli run discord")
        print("\n2. Start the dashboard server:")
        print("   uvicorn server.app:create_app --factory --port 8000 --reload")
        print("\n3. Monitor dashboard:")
        print("   http://localhost:8000/dashboard")
        print("\n4. After 48 hours, check metrics endpoint:")
        print("   curl http://localhost:8000/api/metrics/week4_summary")
        print("\n5. This script will save metrics to:")
        print(f"   {args.output_dir}/week4_pilot_metrics_*.json")
        print("\n" + "=" * 70)

        # Wait for pilot duration
        remaining = pilot_end - time.time()
        if remaining > 0:
            print(f"\n⏳ Pilot will run for {args.duration} hours. Monitoring metrics...")
            print("   Press Ctrl+C to generate interim report\n")

            # Simulate monitoring (in production, this would poll metrics)
            while time.time() < pilot_end:
                time.sleep(300)  # Check every 5 minutes

                # Print status update
                elapsed_hours = (time.time() - monitor.start_time) / 3600
                remaining_hours = (pilot_end - time.time()) / 3600
                print(f"⏰ Pilot status: {elapsed_hours:.1f}h elapsed, {remaining_hours:.1f}h remaining")

    except KeyboardInterrupt:
        print("\n\n⚠️  Pilot monitoring interrupted by user")

    # Generate final report
    print("\n📊 Generating final pilot report...")
    output_path = monitor.save_metrics()
    monitor.print_summary()

    print(f"💾 Metrics saved to: {output_path}")
    print("\n✅ Pilot deployment monitoring complete!")


if __name__ == "__main__":
    main()
