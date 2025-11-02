"""Tests for dynamic context trimming functionality."""
import os
from unittest.mock import patch
from platform.prompts.engine import PromptEngine

def enable_compression():
    """Enable prompt compression for testing."""
    os.environ['ENABLE_PROMPT_COMPRESSION'] = '1'

def disable_compression():
    """Disable prompt compression for testing."""
    os.environ.pop('ENABLE_PROMPT_COMPRESSION', None)

def test_dynamic_context_trimming_basic():
    """Test basic dynamic context trimming functionality."""
    enable_compression()
    engine = PromptEngine()
    prompt = '\n    This is the main instruction.\n\n    Context section with important information:\n    ERROR: Something critical happened\n    WARNING: Pay attention to this\n    IMPORTANT: This must be preserved\n\n    Some repetitive content:\n    Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n    Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n    Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n\n    Additional verbose content:\n    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.\n\n    QUESTION: What should we do?\n    ANSWER: Process the request carefully.\n    '
    original_tokens = engine.count_tokens(prompt)
    optimized = engine.optimise(prompt, target_token_reduction=0.15)
    optimized_tokens = engine.count_tokens(optimized)
    reduction = 1.0 - optimized_tokens / original_tokens
    assert reduction >= 0.1, f'Expected at least 10% reduction, got {reduction * 100:.1f}%'
    assert reduction <= 0.5, f'Reduction too aggressive: {reduction * 100:.1f}%'
    assert 'ERROR:' in optimized
    assert 'WARNING:' in optimized
    assert 'IMPORTANT:' in optimized
    assert 'QUESTION:' in optimized
    assert 'ANSWER:' in optimized

def test_max_token_limit():
    """Test hard token limit enforcement."""
    enable_compression()
    engine = PromptEngine()
    long_prompt = 'This is a test sentence. ' * 100
    limited = engine.optimise(long_prompt, max_tokens=50)
    limited_tokens = engine.count_tokens(limited)
    assert limited_tokens <= 50, f'Expected ≤50 tokens, got {limited_tokens}'
    assert len(limited) > 0, 'Output should not be empty'

def test_backwards_compatibility():
    """Test that old interface still works."""
    enable_compression()
    engine = PromptEngine()
    prompt = 'Test prompt\n\n\nWith extra spacing\nWith extra spacing'
    optimized = engine.optimise(prompt)
    assert optimized.count('With extra spacing') <= 2
    assert '\n\n\n' not in optimized

def test_compression_disabled():
    """Test that compression can be disabled."""
    disable_compression()
    engine = PromptEngine()
    prompt = 'Test prompt\n\n\nWith extra spacing\nWith extra spacing'
    result = engine.optimise(prompt, target_token_reduction=0.5)
    assert result == prompt.strip()

def test_line_value_scoring():
    """Test that important lines are preserved over low-value ones."""
    enable_compression()
    engine = PromptEngine()
    prompt = '\n    Short line.\n    ERROR: This is a critical error that must be preserved at all costs.\n    x\n    IMPORTANT: Another high-value line with essential information.\n    ....................\n    WARNING: Security alert that should be kept.\n    A line with some moderate content here.\n    '
    optimized = engine.optimise(prompt, target_token_reduction=0.7)
    high_value_count = sum((1 for marker in ['ERROR:', 'IMPORTANT:', 'WARNING:'] if marker in optimized))
    assert high_value_count >= 2, f'Expected at least 2 high-value markers, got {high_value_count}'
    assert 'x' not in optimized or '....................' not in optimized

def test_zero_token_edge_case():
    """Test edge case with very short prompts."""
    enable_compression()
    engine = PromptEngine()
    short_prompt = 'Hi'
    result = engine.optimise(short_prompt, target_token_reduction=0.5, max_tokens=1)
    assert isinstance(result, str)
    if len(result) == 0:
        pass
    else:
        tokens = engine.count_tokens(result)
        assert tokens <= 1

def test_emergency_truncation():
    """Test emergency truncation for extreme token limits."""
    enable_compression()
    engine = PromptEngine()
    long_prompt = 'This is a detailed sentence with many words. ' * 50
    result = engine.optimise(long_prompt, max_tokens=10)
    result_tokens = engine.count_tokens(result)
    assert result_tokens <= 10
    assert len(result) > 0
    assert '...' in result or 'omitted' in result

def test_line_truncation():
    """Test intelligent line truncation."""
    enable_compression()
    engine = PromptEngine()
    test_line = 'This is a very long line with many words that should be truncated intelligently while preserving meaning.'
    truncated = engine._truncate_line_to_tokens(test_line, 10)
    truncated_tokens = engine.count_tokens(truncated)
    assert truncated_tokens <= 10
    assert len(truncated) > 0
    if truncated != test_line:
        assert '...' in truncated

def test_context_aware_section_detection():
    """Test that the trimming preserves context structure."""
    enable_compression()
    engine = PromptEngine()
    prompt = '\n    System: You are a helpful assistant.\n\n    Context: The user is asking about Python programming.\n\n    Previous conversation:\n    User: How do I create a list?\n    Assistant: You can create a list using square brackets.\n    User: What about dictionaries?\n    Assistant: Dictionaries use curly braces with key-value pairs.\n\n    Current question: Can you explain functions?\n\n    Instructions: Provide a clear, helpful response.\n    '
    optimized = engine.optimise(prompt, target_token_reduction=0.3)
    assert 'System:' in optimized or 'Context:' in optimized
    assert 'Current question:' in optimized
    assert 'Instructions:' in optimized

def test_metrics_emission():
    """Test that compression metrics are emitted correctly."""
    enable_compression()
    with patch('ultimate_discord_intelligence_bot.services.prompt_engine.metrics') as mock_metrics:
        mock_metrics.label_ctx.return_value = {'tenant': 'test', 'workspace': 'main'}
        mock_ratio_metric = mock_metrics.PROMPT_COMPRESSION_RATIO
        engine = PromptEngine()
        prompt = 'Test prompt with some content to compress.'
        engine.optimise(prompt, target_token_reduction=0.2)
        mock_ratio_metric.labels.assert_called()
        mock_ratio_metric.labels().observe.assert_called()

def test_edge_case_token_limits():
    """Test edge case with very short prompts and extreme limits."""
    enable_compression()
    engine = PromptEngine()
    short_prompt = 'Hi'
    result = engine.optimise(short_prompt, target_token_reduction=0.5, max_tokens=1)
    assert isinstance(result, str)
    if len(result) == 0:
        pass
    else:
        tokens = engine.count_tokens(result)
        assert tokens <= 1

def test_empty_prompt_edge_case():
    """Test edge case with empty prompt."""
    enable_compression()
    engine = PromptEngine()
    result = engine.optimise('', target_token_reduction=0.5, max_tokens=10)
    assert result == ''
if __name__ == '__main__':
    test_dynamic_context_trimming_basic()
    test_max_token_limit()
    test_backwards_compatibility()
    test_compression_disabled()
    test_line_value_scoring()
    test_emergency_truncation()
    test_line_truncation()
    test_context_aware_section_detection()
    test_metrics_emission()
    test_edge_case_token_limits()
    test_empty_prompt_edge_case()
    print('All dynamic context trimming tests passed!')

def test_alternative_zero_token_edge_case():
    """Test edge case with very short prompts."""
    enable_compression()
    engine = PromptEngine()
    short_prompt = 'Hi'
    result = engine.optimise(short_prompt, target_token_reduction=0.5, max_tokens=1)
    assert isinstance(result, str)
    if len(result) == 0:
        pass
    else:
        tokens = engine.count_tokens(result)
        assert tokens <= 1

def test_empty_prompt_edge_case():
    """Test edge case with empty prompt."""
    enable_compression()
    engine = PromptEngine()
    result = engine.optimise('', target_token_reduction=0.5, max_tokens=10)
    assert result == ''
if __name__ == '__main__':
    test_dynamic_context_trimming_basic()
    test_max_token_limit()
    test_backwards_compatibility()
    test_compression_disabled()
    test_line_value_scoring()
    test_emergency_truncation()
    test_line_truncation()
    test_context_aware_section_detection()
    test_metrics_emission()
    test_zero_token_edge_case()
    test_empty_prompt_edge_case()
    print('All dynamic context trimming tests passed!')