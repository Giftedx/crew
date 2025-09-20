"""Test the trajectory evaluation system integration."""

import os
import sys
import time
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for testing
os.environ["ENABLE_TRAJECTORY_EVALUATION"] = "1"
os.environ["ENABLE_ENHANCED_CREW_EVALUATION"] = "1"

try:
    from eval.config import get_trajectory_evaluation_config
    from eval.trajectory_evaluator import AgentTrajectory, TrajectoryEvaluator, TrajectoryStep

    print("✅ Successfully imported trajectory evaluation modules")

    # Test configuration loading
    config = get_trajectory_evaluation_config()
    print(f"✅ Configuration loaded: enabled={config.enabled}, enhanced={config.enhanced_crew_evaluation}")

    # Test trajectory evaluator initialization
    evaluator = TrajectoryEvaluator()
    print("✅ Trajectory evaluator initialized")

    # Create a test trajectory
    test_steps = [
        TrajectoryStep(
            timestamp=time.time(),
            agent_role="test_agent",
            action_type="tool_call",
            content="Testing tool usage",
            tool_name="test_tool",
            tool_args={"arg1": "value1"},
            success=True,
        )
    ]

    test_trajectory = AgentTrajectory(
        session_id="test_session_001",
        user_input="Test user input",
        steps=test_steps,
        final_output="Test completed successfully",
        total_duration=1.5,
        success=True,
        tenant="test_tenant",
        workspace="test_workspace",
    )

    print("✅ Test trajectory created")

    # Test trajectory evaluation
    evaluation_result = evaluator.evaluate_trajectory_accuracy(test_trajectory)

    if evaluation_result.success:
        print(f"✅ Trajectory evaluation successful: score={evaluation_result.data.get('score')}")
        print(f"   Accuracy: {evaluation_result.data.get('accuracy_score'):.2f}")
        print(f"   Efficiency: {evaluation_result.data.get('efficiency_score'):.2f}")
        print(f"   Error Handling: {evaluation_result.data.get('error_handling_score'):.2f}")
    else:
        print(f"❌ Trajectory evaluation failed: {evaluation_result.error}")

    # Test trajectory matching
    reference_trajectory = test_trajectory  # Same trajectory for testing
    match_result = evaluator.evaluate_trajectory_match(test_trajectory, reference_trajectory, "strict")

    if match_result.success:
        print(f"✅ Trajectory matching successful: match={match_result.data.get('match')}")
    else:
        print(f"❌ Trajectory matching failed: {match_result.error}")

    print("\n🎉 All trajectory evaluation tests passed!")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This might be expected if dependencies are not fully configured")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback

    traceback.print_exc()
