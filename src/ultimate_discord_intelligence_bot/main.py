import sys
from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew

# This file simply wires CLI commands to the crew. Avoid adding heavy logic.


def run():
    """Kick off the crew with a sample URL."""
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    UltimateDiscordIntelligenceBotCrew().crew().kickoff(inputs=inputs)


def train():
    """Train the crew for a given number of iterations."""
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    UltimateDiscordIntelligenceBotCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)


def replay():
    """Replay the crew execution from a specific task."""
    UltimateDiscordIntelligenceBotCrew().crew().replay(task_id=sys.argv[1])


def test():
    """Test the crew execution and return the results."""
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    UltimateDiscordIntelligenceBotCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
