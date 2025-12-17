import pytest
from unittest.mock import MagicMock, patch
from domains.ingestion.pipeline import pipeline, models
from domains.memory.unified_graph_store import UnifiedGraphStore, StepResult

class TestPipelineIntegration:
    def test_pipeline_with_unified_graph_store(self):
        # Mock Store
        store = MagicMock(spec=UnifiedGraphStore)
        store.add_node.return_value = StepResult.ok()

        # Mock Job
        job = pipeline.IngestJob(
            source="test_source",
            external_id="123",
            url="http://example.com",
            tenant="default",
            workspace="default",
            tags=["test"]
        )

        # Mock dependencies
        with (
            pipeline.contextlib.ExitStack() as stack
        ):
            # Mock providers
            mock_provider = MagicMock()
            mock_provider.fetch_metadata.return_value = MagicMock(id="test_id", published_at="2023-01-01T00:00:00Z")
            mock_provider.fetch_transcript.return_value = "line 1\nline 2"
            stack.enter_context(patch("domains.ingestion.pipeline.pipeline._get_provider", return_value=(mock_provider, "channel")))

            # Mock segmentation/embedding
            stack.enter_context(patch("domains.intelligence.analysis.segmenter.chunk_transcript", return_value=[
                MagicMock(text="chunk1", start=0, end=1),
                MagicMock(text="chunk2", start=1, end=2)
            ]))
            stack.enter_context(patch("domains.memory.embeddings.embed", return_value=[
                [0.1]*384, [0.2]*384
            ]))
            stack.enter_context(patch("domains.ingestion.pipeline.pipeline.models.connect"))
            stack.enter_context(patch("domains.ingestion.pipeline.pipeline.models.record_provenance"))

            # Run pipeline
            result = pipeline.run(job, store)

            # Verification
            assert result["chunks"] == 2
            assert store.add_node.call_count == 2

            # Verify call args
            calls = store.add_node.call_args_list
            assert calls[0].kwargs["node_id"] == "test_id_chunk_0"
            assert calls[0].kwargs["vector"] == [0.1]*384
