"""DSPy-based tool for optimized text analysis."""

import dspy


class OptimizedAnalysisTool(dspy.Module):
    """A DSPy module for generating analysis from a transcript."""

    def __init__(self):
        """Initializes the OptimizedAnalysisTool."""
        super().__init__()
        self.generate_analysis = dspy.ChainOfThought("transcript -> analysis")

    def forward(self, transcript: str) -> dspy.Prediction:
        """
        Generates an analysis for the given transcript.

        Args:
            transcript: The text of the transcript to analyze.

        Returns:
            A dspy.Prediction object containing the analysis.
        """
        return self.generate_analysis(transcript=transcript)
