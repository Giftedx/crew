"""Vector database dependency group definitions."""

# Core vector database dependencies
VECTOR_GROUP: set[str] = {
    "qdrant_client",
    "chromadb",
    "pinecone",
    "weaviate",
    "milvus",
    "faiss",
    "hnswlib",
}

# Optional vector database dependencies
VECTOR_OPTIONAL: set[str] = {
    "elasticsearch",
    "opensearch-py",
    "redis-py",
    "pgvector",
    "annoy",
    "nmslib",
    "scann",
}
