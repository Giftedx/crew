import json
import os
from datetime import datetime

import dspy

# This script is a placeholder for a more sophisticated data extraction process.
# In a real-world scenario, this would connect to a database, log aggregator,
# or another data source to generate high-quality examples for DSPy optimization.


def generate_training_data_from_logs(
    log_directory: str = "crew_data/Logs/traces",
) -> list[dspy.Example]:
    """
    Scans log files to generate a list of dspy.Example objects for training.

    This is a simplified example. A production version would need more robust parsing
    and a method to identify high-quality interactions.
    """
    training_examples = []

    if not os.path.exists(log_directory):
        print(f"⚠️ Log directory not found: {log_directory}")
        return []

    for filename in os.listdir(log_directory):
        if filename.endswith(".json"):
            filepath = os.path.join(log_directory, filename)
            try:
                with open(filepath, "r") as f:
                    trace_data = json.load(f)
                    # This is a heuristic: find a step with a large-ish output
                    # that could be a good example of an answer.
                    for step in trace_data.get("steps", []):
                        if step.get("raw_output_length", 0) > 100:
                            # Heuristic to find a potential question/context
                            # In a real system, you would have structured logs to find this.
                            context = " ".join(
                                [
                                    s.get("raw_output", "")
                                    for s in trace_data["steps"]
                                    if s["step_number"] < step["step_number"]
                                    and s.get("raw_output")
                                ]
                            )

                            if context and step.get("raw_output"):
                                example = dspy.Example(
                                    context=context[
                                        -2000:
                                    ],  # Truncate for context window
                                    question=step.get(
                                        "tool_input", "summarize"
                                    ),  # Placeholder
                                    answer=step.get("raw_output"),
                                ).with_inputs("context", "question")
                                training_examples.append(example)
                                # Limit to a few examples for demonstration
                                if len(training_examples) >= 10:
                                    return training_examples
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON file: {filename}")
            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    return training_examples


def save_training_data(examples: list[dspy.Example], output_path: str):
    """Saves the generated training data to a JSON file."""
    if not examples:
        print("No training data generated, skipping save.")
        return

    # Convert to a serializable format
    serializable_examples = [ex.toDict() for ex in examples]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(serializable_examples, f, indent=2)
    print(f"✅ Saved {len(examples)} training examples to {output_path}")


if __name__ == "__main__":
    print("🚀 Generating training data for DSPy optimization...")

    # 1. Generate examples from logs
    generated_examples = generate_training_data_from_logs()

    # 2. Add some hand-crafted examples for quality
    hand_crafted_examples = [
        dspy.Example(
            context="The mission is to analyze a video about renewable energy.",
            question="What are the key topics?",
            answer="Solar power, wind energy, and battery storage.",
        ).with_inputs("context", "question"),
        dspy.Example(
            context="A user wants to know the sentiment of a recent podcast.",
            question="What is the overall sentiment?",
            answer="The sentiment is largely positive, with some neutral segments.",
        ).with_inputs("context", "question"),
    ]

    all_examples = generated_examples + hand_crafted_examples

    # 3. Save to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"crew_data/training_sets/dspy_training_{timestamp}.json"
    save_training_data(all_examples, output_file)

    print("✨ Training data generation complete.")
