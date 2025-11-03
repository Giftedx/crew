"""Test dynamic context trimming implementation."""

import os


os.environ["ENABLE_PROMPT_COMPRESSION"] = "1"
from platform.prompts.engine import PromptEngine


def test_dynamic_context_trimming():
    """Test the enhanced context trimming functionality."""
    print("🧪 Testing Dynamic Context Trimming Implementation")
    engine = PromptEngine()
    verbose_prompt = "\nThis is the main instruction for the AI system.\n\nHere are some detailed guidelines:\n- Follow these instructions carefully\n- Pay attention to context clues\n- Generate high-quality responses\n- Maintain consistency throughout\n\nERROR: Something went wrong here\nWARNING: This is important to note\nIMPORTANT: Critical information follows\n\nContext section:\nThe user has provided the following background information that may be relevant to their query. This information should be considered when formulating a response, but it should not override the primary instructions above.\n\nBackground data:\nLorem ipsum dolor sit amet, consectetur adipiscing elit.\nLorem ipsum dolor sit amet, consectetur adipiscing elit.\nLorem ipsum dolor sit amet, consectetur adipiscing elit.\nLorem ipsum dolor sit amet, consectetur adipiscing elit.\nLorem ipsum dolor sit amet, consectetur adipiscing elit.\n\nAdditional context:\nSed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\nUt enim ad minim veniam, quis nostrud exercitation ullamco.\nLaboris nisi ut aliquip ex ea commodo consequat.\nDuis aute irure dolor in reprehenderit in voluptate velit esse.\nCillum dolore eu fugiat nulla pariatur.\nExcepteur sint occaecat cupidatat non proident.\nSunt in culpa qui officia deserunt mollit anim id est laborum.\n\nSome repetitive content:\nLine 1 with some content\nLine 2 with some content\nLine 3 with some content\nLine 4 with some content\nLine 5 with some content\nLine 6 with some content\nLine 7 with some content\nLine 8 with some content\nLine 9 with some content\nLine 10 with some content\n\nMore detailed instructions:\nWhen processing this request, please ensure that you maintain high quality standards throughout your response. The system expects detailed and accurate information that addresses the user's specific needs while remaining concise and focused on the core objectives.\n\nQUESTION: What is the user asking about?\nANSWER: The user wants to know about the topic.\nRESULT: This should be a comprehensive response.\nOUTPUT: Final formatted result should be here.\n\nConclusion:\nThis prompt contains a mix of important instructions, repetitive content, and verbose explanations that could be trimmed while preserving the essential information.\n"
    print(f"Original prompt length: {len(verbose_prompt)} characters")
    original_tokens = engine.count_tokens(verbose_prompt)
    print(f"Original token count: {original_tokens}")
    for target_reduction in [0.15, 0.25, 0.35]:
        print(f"\n--- Testing {target_reduction * 100:.0f}% target reduction ---")
        optimized = engine.optimise(verbose_prompt, target_token_reduction=target_reduction)
        optimized_tokens = engine.count_tokens(optimized)
        actual_reduction = 1.0 - optimized_tokens / original_tokens
        print(f"Optimized length: {len(optimized)} characters")
        print(f"Optimized tokens: {optimized_tokens}")
        print(f"Actual reduction: {actual_reduction * 100:.1f}%")
        print(f"Target achieved: {('✅' if actual_reduction >= target_reduction * 0.9 else '❌')}")
        important_markers = ["ERROR:", "WARNING:", "IMPORTANT:", "QUESTION:", "ANSWER:"]
        preserved_markers = sum(1 for marker in important_markers if marker in optimized)
        print(f"Important markers preserved: {preserved_markers}/{len(important_markers)}")
        print(f"\nOptimized preview (first 200 chars):\n{optimized[:200]}...")
    print("\n--- Testing max token limit (100 tokens) ---")
    max_limited = engine.optimise(verbose_prompt, max_tokens=100)
    max_limited_tokens = engine.count_tokens(max_limited)
    print(f"Max limited tokens: {max_limited_tokens}")
    print(f"Within limit: {('✅' if max_limited_tokens <= 100 else '❌')}")
    print(f"\nMax limited preview:\n{max_limited}")


def test_backwards_compatibility():
    """Test that existing functionality still works."""
    print("\n🔄 Testing Backwards Compatibility")
    engine = PromptEngine()
    simple_prompt = "This is a simple prompt.\n\n\nWith some extra spacing.\nWith some extra spacing."
    old_style = engine.optimise(simple_prompt)
    print(f"Old interface result: {old_style!r}")
    assert "With some extra spacing." in old_style
    assert old_style.count("With some extra spacing.") <= 2
    print("✅ Backwards compatibility maintained")


if __name__ == "__main__":
    test_dynamic_context_trimming()
    test_backwards_compatibility()
    print("\n🎉 Dynamic Context Trimming tests completed!")
