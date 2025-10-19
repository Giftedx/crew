#!/usr/bin/env python3
"""
Cache Performance Monitoring Script
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.cache.adaptive_semantic_cache import get_adaptive_semantic_cache

    def monitor_cache_performance():
        """Monitor and display cache performance metrics."""

        cache = get_adaptive_semantic_cache()
        stats = cache.get_performance_stats()

        print("📊 Semantic Cache Performance Metrics:")
        print(f"  Current Threshold: {stats['current_threshold']:.3f}")
        print(f"  Hit Rate: {stats['hit_rate']:.1%}")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Cache Hits: {stats['cache_hits']}")
        print(f"  Cache Misses: {stats['cache_misses']}")
        print(f"  Average Similarity: {stats['average_similarity']:.3f}")
        print(f"  Cost Efficiency: ${stats['cost_efficiency']:.4f}/request")
        print(f"  Total Cost Saved: ${stats['total_cost_saved']:.2f}")

        # Performance assessment
        hit_rate = stats['hit_rate']
        if hit_rate > 0.60:
            print("✅ Excellent cache performance!")
        elif hit_rate > 0.40:
            print("⚠️  Good cache performance, room for improvement")
        else:
            print("❌ Low cache performance, consider threshold adjustment")

    if __name__ == "__main__":
        monitor_cache_performance()

except ImportError as e:
    print(f"❌ Error importing adaptive cache: {e}")
    print("Make sure to install dependencies and set up the cache properly.")
