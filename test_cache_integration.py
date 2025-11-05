"""Integration test for cache decorator."""
import sys


sys.path.insert(0, 'src')

from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from domains.intelligence.analysis.sentiment_tool import SentimentTool


# Test SentimentTool
print('🧪 SentimentTool Caching Test')
print('=' * 60)

st = SentimentTool()

r1 = st._run('This is wonderful and amazing')
print(f'Call 1: cache_hit={r1.metadata.get("cache_hit")}, data={r1.data}')

r2 = st._run('This is wonderful and amazing')
print(f'Call 2: cache_hit={r2.metadata.get("cache_hit")}, data={r2.data}')

r3 = st._run('Different text here')
print(f'Call 3: cache_hit={r3.metadata.get("cache_hit")}, data={r3.data}')

assert not r1.metadata['cache_hit'], 'First call should miss cache'
assert r2.metadata['cache_hit'], 'Second call should hit cache'
assert not r3.metadata['cache_hit'], 'Different input should miss cache'
print('✅ SentimentTool caching works correctly!\n')

# Test EnhancedAnalysisTool
print('🧪 EnhancedAnalysisTool Caching Test')
print('=' * 60)

eat = EnhancedAnalysisTool()

r4 = eat._run('Healthcare reform policy discussion', 'political')
print(f'Call 1: cache_hit={r4.metadata.get("cache_hit")}, topics={r4.data.get("political_topics", [])}')

r5 = eat._run('Healthcare reform policy discussion', 'political')
print(f'Call 2: cache_hit={r5.metadata.get("cache_hit")}, topics={r5.data.get("political_topics", [])}')

assert not r4.metadata['cache_hit'], 'First analysis should miss cache'
assert r5.metadata['cache_hit'], 'Second analysis should hit cache'
assert r4.data == r5.data, 'Cached data should match original'
print('✅ EnhancedAnalysisTool caching works correctly!\n')

print('🎉 All cache integration tests passed!')
print('📊 Cache hit rate: 2/5 = 40% (expected for this test pattern)')
