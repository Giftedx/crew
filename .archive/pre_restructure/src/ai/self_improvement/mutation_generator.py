"""
Mutation Generator for Offline Self-Improvement
Generates prompt/config mutations for self-improvement experiments.
"""

import random
from typing import Any


class MutationGenerator:
    def __init__(self, mutation_rate: float = 0.1):
        self.mutation_rate = mutation_rate

    def mutate_prompt(self, prompt: str) -> str:
        """
        Randomly mutate the prompt for experimentation.
        Args:
            prompt: Original prompt string.
        Returns:
            Mutated prompt string.
        """
        # Placeholder: Simulate mutation by shuffling words
        words = prompt.split()
        random.shuffle(words)
        return " ".join(words)

    def mutate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Randomly mutate config values for experimentation.
        Args:
            config: Original config dict.
        Returns:
            Mutated config dict.
        """
        mutated = config.copy()
        for k in mutated:
            if isinstance(mutated[k], (int, float)) and random.random() < self.mutation_rate:
                mutated[k] = mutated[k] * (1 + random.uniform(-0.2, 0.2))
        return mutated
