"""Integration test for cache decorator.

Tests Tier 1 tools: SentimentTool, EnhancedAnalysisTool, TextAnalysisTool
Tests Tier 2 tools: Requires full environment setup (EmbeddingService, TranscriptIndexTool, VectorSearchTool)
"""

import subprocess
import sys


# Flush Redis before tests
try:
    subprocess.run(["redis-cli", "FLUSHDB"], check=True, capture_output=True)
    print("🧹 Redis cache flushed")
    print()
except Exception as e:
    print(f"⚠️  Failed to flush Redis: {e}")
    print()

sys.path.insert(0, "src")

from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from domains.intelligence.analysis.sentiment_tool import SentimentTool
from domains.intelligence.analysis.text_analysis_tool import TextAnalysisTool


print("=" * 70)
print("CACHE INTEGRATION TESTS - Tier 1 Tools")
print("=" * 70)
print()

# Test SentimentTool
print("🧪 Test 1: SentimentTool Caching")
print("-" * 70)

st = SentimentTool()

r1 = st._run("This is wonderful and amazing")
print(f"  Call 1: cache_hit={r1.metadata.get('cache_hit')}, sentiment={r1.data.get('sentiment')}")

r2 = st._run("This is wonderful and amazing")
print(f"  Call 2: cache_hit={r2.metadata.get('cache_hit')}, sentiment={r2.data.get('sentiment')}")

r3 = st._run("Different text here")
print(f"  Call 3: cache_hit={r3.metadata.get('cache_hit')}, sentiment={r3.data.get('sentiment')}")

assert not r1.metadata["cache_hit"], "First call should miss cache"
assert r2.metadata["cache_hit"], "Second call should hit cache"
assert not r3.metadata["cache_hit"], "Different input should miss cache"
print("  ✅ PASSED - SentimentTool caching working correctly")
print()

# Test EnhancedAnalysisTool
print("🧪 Test 2: EnhancedAnalysisTool Caching")
print("-" * 70)

eat = EnhancedAnalysisTool()

r4 = eat._run("Healthcare reform policy discussion", "political")
print(f"  Call 1: cache_hit={r4.metadata.get('cache_hit')}, topics={len(r4.data.get('political_topics', []))}")

r5 = eat._run("Healthcare reform policy discussion", "political")
print(f"  Call 2: cache_hit={r5.metadata.get('cache_hit')}, topics={len(r5.data.get('political_topics', []))}")

assert not r4.metadata["cache_hit"], "First analysis should miss cache"
assert r5.metadata["cache_hit"], "Second analysis should hit cache"
assert r4.data == r5.data, "Cached data should match original"
print("  ✅ PASSED - EnhancedAnalysisTool caching working correctly")
print()

# Test TextAnalysisTool
print("🧪 Test 3: TextAnalysisTool Caching")
print("-" * 70)

tat = TextAnalysisTool()

r6 = tat._run("The quick brown fox jumps over the lazy dog")
print(f"  Call 1: cache_hit={r6.metadata.get('cache_hit')}, sentiment={r6.data.get('sentiment')}")

r7 = tat._run("The quick brown fox jumps over the lazy dog")
print(f"  Call 2: cache_hit={r7.metadata.get('cache_hit')}, sentiment={r7.data.get('sentiment')}")

assert not r6.metadata["cache_hit"], "First call should miss cache"
assert r7.metadata["cache_hit"], "Second call should hit cache"
assert r6.data == r7.data, "Cached data should match original"
print("  ✅ PASSED - TextAnalysisTool caching working correctly")
print()

print("=" * 70)
print("🎉 All Tier 1 cache integration tests PASSED!")
print("=" * 70)
print()
print("Summary:")
print("  Total calls: 7")
print("  Cache hits: 3")
print("  Cache misses: 4")
print("  Hit rate: 43% (expected for this test pattern)")
print()
print("Tested Tools:")
print("  ✅ SentimentTool (Tier 1) - 2hr TTL")
print("  ✅ EnhancedAnalysisTool (Tier 1) - 1hr TTL")
print("  ✅ TextAnalysisTool (Tier 1) - 1hr TTL")
print()
print("Note: Tier 2 tools (TranscriptIndexTool, VectorSearchTool) require")
print("      full environment setup. Run `make test` for comprehensive tests.")
