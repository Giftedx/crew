import sys
import os
import unittest
# Import platform from stdlib BEFORE adding src to path to avoid shadowing
import platform
from unittest.mock import MagicMock, patch

# Ensure src is in path for local testing
sys.path.insert(0, os.path.abspath("src"))

# Now import the module under test
from ultimate_discord_intelligence_bot.background_intelligence_worker import BackgroundIntelligenceWorker

class TestWorkerExtraction(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MagicMock()
        self.worker = BackgroundIntelligenceWorker(self.orchestrator, storage_dir="/tmp/test_worker_storage")

    def test_pipeline_run_result_extraction(self):
        # Simulate the structure described in the audit
        pipeline_result = {
            "status": "success",
            "download": {"status": "success", "file_path": "/tmp/video.mp4"},
            "transcription": {"status": "success", "transcript": "Hello world"},
            "analysis": {
                "status": "success",
                "sentiment": "positive",
                "keywords": ["test", "audit"],
                "emotions": {"joy": 0.8},
                "topics": {"tech": 0.9}
            },
            "fallacy": {
                "status": "success",
                "fallacies": ["none"],
                "count": 0,
                "confidence_scores": {}
            },
            "perspective": {
                "status": "success",
                "summary": "This is a summary",
                "briefing": "Detailed briefing",
                "claims": ["Claim 1"],
                "fact_checks": ["Check 1"]
            },
            "memory": {"status": "success"},
            "graph_memory": {"status": "success"}
        }

        results = self.worker._extract_crew_results(pipeline_result)

        # Verification
        self.assertEqual(results["sentiment"], "positive")
        self.assertEqual(results["keywords"], ["test", "audit"])
        self.assertEqual(results["summary"], "This is a summary")
        self.assertTrue(results["memory_stored"])
        self.assertTrue(results["graph_created"])
        self.assertEqual(results["claims"], ["Claim 1"])

if __name__ == "__main__":
    unittest.main()
