#!/usr/bin/env python3
"""
Script to create gold dataset annotations for creator intelligence evaluation.

This script generates ground truth annotations for 10 representative episodes
and calculates inter-annotator agreement metrics to ensure quality.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import logging
from typing import Any

from ultimate_discord_intelligence_bot.services.gold_dataset_annotator import GoldDatasetAnnotator
from ultimate_discord_intelligence_bot.step_result import StepResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_and_validate_gold_dataset(output_path: str = "gold_dataset.json") -> StepResult:
    """Create and validate the gold dataset."""
    print("🏆 Creating Gold Dataset for Creator Intelligence Evaluation")
    print("=" * 70)

    try:
        # Initialize annotator
        annotator = GoldDatasetAnnotator()

        print("📊 Dataset Overview:")
        print(f"  Episodes to annotate: {len(annotator.episodes_data)}")
        print(f"  Annotators: {', '.join(annotator.annotators)}")
        print(f"  Platforms: {set(ep['platform'] for ep in annotator.episodes_data.values())}")
        print(f"  Creators: {set(ep['creator'] for ep in annotator.episodes_data.values())}")

        # Create gold annotations
        print("\n🔨 Generating gold annotations...")
        gold_annotations = annotator.create_gold_annotations()

        print(f"✅ Generated {len(gold_annotations)} gold annotations")

        # Calculate inter-annotator agreement
        print("\n📊 Calculating inter-annotator agreement...")
        agreement = annotator.calculate_agreement_metrics()

        print(f"  Cohen's Kappa: {agreement.cohens_kappa:.3f}")
        print(f"  Fleiss Kappa: {agreement.fleiss_kappa:.3f}")
        print(f"  Overall Agreement: {agreement.overall_agreement:.3f}")
        print(f"  Target Met (≥0.70): {'✅' if agreement.cohens_kappa >= 0.70 else '❌'}")

        # Validate dataset
        print("\n🔍 Validating dataset...")
        validation_result = annotator.validate_gold_dataset(gold_annotations)

        if validation_result.success:
            validation_data = validation_result.data["data"]
            print("✅ Dataset validation passed")
            print(f"  Total segments: {validation_data['annotations_summary']['total_segments']}")
            print(f"  Total topics: {validation_data['annotations_summary']['total_topics']}")
            print(f"  Total claims: {validation_data['annotations_summary']['total_claims']}")
            print(f"  Total highlights: {validation_data['annotations_summary']['total_highlights']}")
        else:
            print(f"❌ Dataset validation failed: {validation_result.error}")
            return validation_result

        # Save dataset
        print(f"\n💾 Saving dataset to {output_path}...")
        save_result = annotator.save_gold_dataset(gold_annotations, output_path)

        if save_result.success:
            save_data = save_result.data["data"]
            print("✅ Dataset saved successfully")
            print(f"  Episodes annotated: {save_data['episodes_annotated']}")
            print(f"  Output path: {save_data['output_path']}")
            print(f"  Total segments: {save_data['total_segments']}")
            print(f"  Total topics: {save_data['total_topics']}")
            print(f"  Total claims: {save_data['total_claims']}")
            print(f"  Total highlights: {save_data['total_highlights']}")
        else:
            print(f"❌ Failed to save dataset: {save_result.error}")
            return save_result

        # Generate comprehensive report
        print("\n📋 Generating annotation report...")
        report = annotator.generate_annotation_report()

        # Save report
        report_path = output_path.replace(".json", "_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Report saved to {report_path}")

        # Display summary
        print("\n🎯 Gold Dataset Summary:")
        print("=" * 50)
        print(f"  Episodes: {len(gold_annotations)}")
        print(f"  Cohen's Kappa: {agreement.cohens_kappa:.3f}")
        print(f"  Target Met: {'✅' if agreement.cohens_kappa >= 0.70 else '❌'}")
        print(
            f"  Avg Confidence: {sum(a.confidence_scores.get('transcript', 0) for a in gold_annotations) / len(gold_annotations):.3f}"
        )
        print(f"  Total Annotations: {sum(len(a.transcript_segments) for a in gold_annotations)} segments")

        # Check acceptance criteria
        print("\n🎯 Acceptance Criteria Check:")
        print(f"  Cohen's Kappa ≥ 0.70: {'✅' if agreement.cohens_kappa >= 0.70 else '❌'}")
        print(f"  10 Episodes Annotated: {'✅' if len(gold_annotations) == 10 else '❌'}")
        print(f"  All Categories Present: {'✅' if validation_result.success else '❌'}")
        print(f"  Dataset Saved Successfully: {'✅' if save_result.success else '❌'}")

        return StepResult.ok(
            data={
                "gold_dataset_path": output_path,
                "report_path": report_path,
                "episodes_annotated": len(gold_annotations),
                "cohens_kappa": agreement.cohens_kappa,
                "target_met": agreement.cohens_kappa >= 0.70,
                "validation_passed": validation_result.success,
            }
        )

    except Exception as e:
        logger.error(f"Failed to create gold dataset: {str(e)}")
        return StepResult.fail(f"Failed to create gold dataset: {str(e)}")


def display_episode_details(annotations: list[Any]) -> None:
    """Display detailed information about each annotated episode."""
    print("\n📋 Episode Details:")
    print("=" * 80)

    for annotation in annotations:
        print(f"\n🎬 {annotation.episode_id}")
        print(f"   Creator: {annotation.creator}")
        print(f"   Platform: {annotation.platform}")
        print(f"   Title: {annotation.title}")
        print(f"   Duration: {annotation.duration_seconds / 60:.1f} minutes")
        print(f"   Upload Date: {annotation.upload_date.strftime('%Y-%m-%d')}")

        print(f"   📝 Transcript Segments: {len(annotation.transcript_segments)}")
        print(f"   🗣️  Speaker Segments: {len(annotation.speaker_segments)}")
        print(f"   📚 Topics: {len(annotation.topics)}")
        print(f"   💬 Claims: {len(annotation.claims)}")
        print(f"   ⭐ Highlights: {len(annotation.highlights)}")

        print("   📊 Confidence Scores:")
        for category, score in annotation.confidence_scores.items():
            print(f"      {category}: {score:.3f}")


def main():
    """Main function to create gold dataset."""
    output_path = "gold_dataset.json"

    print("🏆 Gold Dataset Annotation for Creator Intelligence")
    print("=" * 60)

    # Create and validate gold dataset
    result = create_and_validate_gold_dataset(output_path)

    if result.success:
        data = result.data["data"]

        print("\n✅ Gold Dataset Creation Complete!")
        print(f"📁 Dataset saved to: {data['gold_dataset_path']}")
        print(f"📊 Report saved to: {data['report_path']}")
        print(f"🎯 Cohen's Kappa: {data['cohens_kappa']:.3f}")
        print(f"🏆 Target Met: {'✅' if data['target_met'] else '❌'}")

        # Load and display episode details
        annotator = GoldDatasetAnnotator()
        annotations = annotator.load_gold_dataset(output_path)
        display_episode_details(annotations)

        print("\n🚀 Next Steps:")
        print("  1. Use gold dataset for CreatorEvaluationHarness")
        print("  2. Run automated evaluation metrics")
        print("  3. Set up monitoring dashboard")
        print("  4. Establish baseline performance targets")

        return 0
    else:
        print(f"\n❌ Gold dataset creation failed: {result.error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
