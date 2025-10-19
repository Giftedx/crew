import dspy


class DebateAnalysisSignature(dspy.Signature):
    """Analyzes debate content, extracting key claims and identifying logical fallacies."""

    transcript = dspy.InputField(desc="The full transcript of the debate.")
    claims = dspy.OutputField(desc="A list of the key claims made during the debate.")
    fallacies = dspy.OutputField(
        desc="A list of logical fallacies identified in the arguments."
    )


class FactCheckingSignature(dspy.Signature):
    """Fact-checks a claim against available evidence."""

    claim = dspy.InputField(desc="The claim to fact-check.")
    context = dspy.InputField(desc="Additional context about the claim.")
    verdict = dspy.OutputField(
        desc="The fact-check verdict: 'true', 'false', 'misleading', or 'unverified'."
    )
    confidence = dspy.OutputField(desc="Confidence score from 0.0 to 1.0.")
    evidence = dspy.OutputField(desc="Supporting evidence for the verdict.")


class ClaimExtractionSignature(dspy.Signature):
    """Extracts factual claims from text content."""

    text = dspy.InputField(desc="The text content to extract claims from.")
    claims = dspy.OutputField(
        desc="A list of verifiable factual claims found in the text."
    )
    claim_types = dspy.OutputField(
        desc="Types of claims (statistical, causal, categorical, etc.)."
    )


class SentimentAnalysisSignature(dspy.Signature):
    """Analyzes sentiment and emotional tone of content."""

    text = dspy.InputField(desc="The text content to analyze.")
    sentiment = dspy.OutputField(
        desc="Overall sentiment: 'positive', 'negative', or 'neutral'."
    )
    confidence = dspy.OutputField(desc="Confidence score from 0.0 to 1.0.")
    emotions = dspy.OutputField(
        desc="Specific emotions detected (joy, anger, fear, etc.)."
    )
    intensity = dspy.OutputField(desc="Emotional intensity from 0.0 to 1.0.")


class SummaryGenerationSignature(dspy.Signature):
    """Generates concise summaries of content."""

    content = dspy.InputField(desc="The full content to summarize.")
    max_length = dspy.InputField(desc="Maximum length of the summary in words.")
    summary = dspy.OutputField(desc="A concise summary of the key points.")
    key_points = dspy.OutputField(desc="Bullet-pointed list of key takeaways.")
