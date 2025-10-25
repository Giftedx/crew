"""LlamaIndex RAG service for enhanced retrieval and generation."""

from __future__ import annotations

import logging
from typing import Any


try:
    from llama_index.core import Document, StorageContext, VectorStoreIndex
    from llama_index.core.node_parser import SimpleNodeParser
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    VectorStoreIndex = None  # type: ignore[assignment,misc]
    StorageContext = None  # type: ignore[assignment,misc]
    Document = None  # type: ignore[assignment,misc]

from src.ultimate_discord_intelligence_bot.step_result import StepResult


_logger = logging.getLogger(__name__)


class LlamaIndexRAGService:
    """LlamaIndex-based RAG service for intelligent retrieval and generation."""

    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "llamaindex_collection",
        openai_api_key: str | None = None,
    ):
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex not available. Install with: pip install llama-index"
            )

        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.openai_api_key = openai_api_key

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=qdrant_url)

        # Initialize embedding model
        self.embed_model = OpenAIEmbedding(api_key=openai_api_key)

        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name,
        )

        # Initialize storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        # Initialize index
        self.index = VectorStoreIndex(
            nodes=[],
            storage_context=self.storage_context,
            embed_model=self.embed_model,
        )

        _logger.info(f"LlamaIndex RAG service initialized with collection: {collection_name}")

    def ingest_documents(
        self,
        texts: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> StepResult:
        """Ingest documents into the RAG system."""
        try:
            documents = []
            metadata_list = metadata or [{}] * len(texts)

            for text, meta in zip(texts, metadata_list, strict=False):
                doc = Document(text=text, metadata=meta)
                documents.append(doc)

            # Parse documents into nodes
            parser = SimpleNodeParser.from_defaults(chunk_size=512, chunk_overlap=20)
            nodes = parser.get_nodes_from_documents(documents)

            # Add nodes to index
            self.index.insert_nodes(nodes)

            _logger.info(f"Ingested {len(documents)} documents into RAG system")

            return StepResult.ok(data={
                "documents_ingested": len(documents),
                "nodes_created": len(nodes),
            })

        except Exception as e:
            _logger.error(f"Error ingesting documents: {e}")
            return StepResult.fail(f"Failed to ingest documents: {e!s}")

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> StepResult:
        """Query the RAG system for relevant content."""
        try:
            # Create query engine
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

            # Execute query
            response = query_engine.query(query_text)

            # Extract results
            results = []
            for node in response.source_nodes:
                results.append({
                    "text": node.text,
                    "score": node.score,
                    "metadata": node.metadata,
                })

            _logger.info(f"Query returned {len(results)} results")

            return StepResult.ok(data={
                "query": query_text,
                "response": str(response),
                "results": results,
                "top_k": top_k,
            })

        except Exception as e:
            _logger.error(f"Error querying RAG system: {e}")
            return StepResult.fail(f"Failed to query RAG system: {e!s}")

    def retrieve_context(
        self,
        query_text: str,
        top_k: int = 3,
    ) -> StepResult:
        """Retrieve relevant context for a query."""
        try:
            # Use retriever for context retrieval
            retriever = self.index.as_retriever(similarity_top_k=top_k)

            # Retrieve nodes
            nodes = retriever.retrieve(query_text)

            # Format context
            context_parts = []
            for node in nodes:
                context_parts.append({
                    "text": node.text,
                    "score": node.score,
                    "metadata": node.metadata,
                })

            _logger.info(f"Retrieved {len(context_parts)} context items")

            return StepResult.ok(data={
                "query": query_text,
                "context": context_parts,
                "top_k": top_k,
            })

        except Exception as e:
            _logger.error(f"Error retrieving context: {e}")
            return StepResult.fail(f"Failed to retrieve context: {e!s}")

    def update_index(self) -> StepResult:
        """Update the index with recent changes."""
        try:
            # Refresh index
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model,
            )

            _logger.info("Index updated successfully")

            return StepResult.ok(data={"status": "index_updated"})

        except Exception as e:
            _logger.error(f"Error updating index: {e}")
            return StepResult.fail(f"Failed to update index: {e!s}")

    def get_stats(self) -> StepResult:
        """Get statistics about the RAG system."""
        try:
            # Get collection info from Qdrant
            collection_info = self.qdrant_client.get_collection(self.collection_name)

            stats = {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "index_status": collection_info.status,
            }

            return StepResult.ok(data=stats)

        except Exception as e:
            _logger.error(f"Error getting stats: {e}")
            return StepResult.fail(f"Failed to get stats: {e!s}")
