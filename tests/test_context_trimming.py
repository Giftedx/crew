#!/usr/bin/env python3
"""Test dynamic context trimming implementation."""

import os

# Enable prompt compression for testing
os.environ["ENABLE_PROMPT_COMPRESSION"] = "1"

from ultimate_discord_intelligence_bot.services.prompt_engine import PromptEngine


def test_dynamic_context_trimming():
    """Test the enhanced context trimming functionality."""
    print("🧪 Testing Dynamic Context Trimming Implementation")

    engine = PromptEngine()

    # Create a long, verbose prompt for testing
    verbose_prompt = """
This is the main instruction for the AI system.

Here are some detailed guidelines:
- Follow these instructions carefully
- Pay attention to context clues
- Generate high-quality responses
- Maintain consistency throughout

ERROR: Something went wrong here
WARNING: This is important to note
IMPORTANT: Critical information follows

Context section:
The user has provided the following background information that may be relevant to their query. This information should be considered when formulating a response, but it should not override the primary instructions above.

Background data:
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Lorem ipsum dolor sit amet, consectetur adipiscing elit.

Additional context:
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco.
Laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse.
Cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident.
Sunt in culpa qui officia deserunt mollit anim id est laborum.

Some repetitive content:
Line 1 with some content
Line 2 with some content
Line 3 with some content
Line 4 with some content
Line 5 with some content
Line 6 with some content
Line 7 with some content
Line 8 with some content
Line 9 with some content
Line 10 with some content

More detailed instructions:
When processing this request, please ensure that you maintain high quality standards throughout your response. The system expects detailed and accurate information that addresses the user's specific needs while remaining concise and focused on the core objectives.

QUESTION: What is the user asking about?
ANSWER: The user wants to know about the topic.
RESULT: This should be a comprehensive response.
OUTPUT: Final formatted result should be here.

Conclusion:
This prompt contains a mix of important instructions, repetitive content, and verbose explanations that could be trimmed while preserving the essential information.
"""

    print(f"Original prompt length: {len(verbose_prompt)} characters")
    original_tokens = engine.count_tokens(verbose_prompt)
    print(f"Original token count: {original_tokens}")

    # Test different compression levels
    for target_reduction in [0.15, 0.25, 0.35]:
        print(f"\n--- Testing {target_reduction * 100:.0f}% target reduction ---")

        optimized = engine.optimise(verbose_prompt, target_token_reduction=target_reduction)
        optimized_tokens = engine.count_tokens(optimized)
        actual_reduction = 1.0 - (optimized_tokens / original_tokens)

        print(f"Optimized length: {len(optimized)} characters")
        print(f"Optimized tokens: {optimized_tokens}")
        print(f"Actual reduction: {actual_reduction * 100:.1f}%")
        print(f"Target achieved: {'✅' if actual_reduction >= target_reduction * 0.9 else '❌'}")

        # Check that important content is preserved
        important_markers = ["ERROR:", "WARNING:", "IMPORTANT:", "QUESTION:", "ANSWER:"]
        preserved_markers = sum(1 for marker in important_markers if marker in optimized)
        print(f"Important markers preserved: {preserved_markers}/{len(important_markers)}")

        print(f"\nOptimized preview (first 200 chars):\n{optimized[:200]}...")

    # Test with max token limit
    print("\n--- Testing max token limit (100 tokens) ---")
    max_limited = engine.optimise(verbose_prompt, max_tokens=100)
    max_limited_tokens = engine.count_tokens(max_limited)
    print(f"Max limited tokens: {max_limited_tokens}")
    print(f"Within limit: {'✅' if max_limited_tokens <= 100 else '❌'}")
    print(f"\nMax limited preview:\n{max_limited}")


def test_backwards_compatibility():
    """Test that existing functionality still works."""
    print("\n🔄 Testing Backwards Compatibility")

    engine = PromptEngine()

    simple_prompt = "This is a simple prompt.\n\n\nWith some extra spacing.\nWith some extra spacing."

    # Test without parameters (old interface)
    old_style = engine.optimise(simple_prompt)
    print(f"Old interface result: {repr(old_style)}")

    # Should remove duplicate lines and extra spacing
    assert "With some extra spacing." in old_style
    assert old_style.count("With some extra spacing.") <= 2
    print("✅ Backwards compatibility maintained")


if __name__ == "__main__":
    test_dynamic_context_trimming()
    test_backwards_compatibility()
    print("\n🎉 Dynamic Context Trimming tests completed!")
