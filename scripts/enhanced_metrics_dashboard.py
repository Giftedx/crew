#!/usr/bin/env python3
"""Enhanced Metrics Dashboard Script.

This script provides a comprehensive web-based dashboard for monitoring
tool performance, system health, and advanced analytics.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ultimate_discord_intelligence_bot.observability.enhanced_metrics_api import (
        run_enhanced_metrics_api,  # type: ignore
    )

    ENHANCED_API_AVAILABLE = True
except ImportError as e:
    ENHANCED_API_AVAILABLE = False
    print(f"⚠️  Enhanced metrics API not available: {e}")


def main():
    """Main entry point for the enhanced metrics dashboard."""
    parser = argparse.ArgumentParser(
        description="Enhanced Metrics Dashboard for Ultimate Discord Intelligence Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/enhanced_metrics_dashboard.py
  python scripts/enhanced_metrics_dashboard.py --host 0.0.0.0 --port 8080
  python scripts/enhanced_metrics_dashboard.py --debug
        """,
    )

    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to (default: 127.0.0.1)")

    parser.add_argument("--port", type=int, default=5002, help="Port to bind the server to (default: 5002)")

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    if not ENHANCED_API_AVAILABLE:
        print("❌ Enhanced metrics API is not available.")
        print("Please ensure Flask is installed and all dependencies are met.")
        print("\nTo install Flask:")
        print("  pip install flask")
        return 1

    print("🚀 Starting Enhanced Metrics Dashboard...")
    print(f"📡 Server will be available at: http://{args.host}:{args.port}")
    print("📊 Dashboard features:")
    print("  • Real-time metrics visualization")
    print("  • Interactive tool performance charts")
    print("  • System health monitoring")
    print("  • Advanced analytics and insights")
    print("  • Export capabilities")
    print("\n🌐 Available endpoints:")
    print("  • GET  / - Main dashboard")
    print("  • GET  /simple - Simple dashboard")
    print("  • GET  /api/metrics/health - Health check")
    print("  • GET  /api/metrics/system - System metrics")
    print("  • GET  /api/metrics/tools - All tool metrics")
    print("  • GET  /api/metrics/tools/<name> - Specific tool metrics")
    print("  • GET  /api/metrics/analytics - Advanced analytics")
    print("  • GET  /api/metrics/export - Export metrics")
    print("\n💡 Tips:")
    print("  • Use Ctrl+C to stop the server")
    print("  • Dashboard auto-refreshes every 30 seconds")
    print("  • Check /api/metrics/health for quick status")
    print("  • Export data via /api/metrics/export")

    try:
        run_enhanced_metrics_api(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 Enhanced Metrics Dashboard stopped.")
        return 0
    except Exception as e:
        print(f"❌ Failed to start enhanced metrics dashboard: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
