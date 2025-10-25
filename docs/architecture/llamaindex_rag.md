# LlamaIndex RAG Integration

LlamaIndex provides advanced Retrieval-Augmented Generation (RAG) capabilities for intelligent document retrieval and context-aware generation.

## Overview

The LlamaIndex integration enhances the system with:

- **Intelligent Retrieval**: Semantic search with OpenAI embeddings
- **Context-Aware Generation**: RAG with retrieved context
- **Qdrant Integration**: Scalable vector storage
- **Document Processing**: Automatic chunking and parsing

## Architecture

### Service Components

```
LlamaIndexRAGService
├── ingest_documents()    # Ingest documents into RAG
├── query()               # Query with generation
├── retrieve_context()    # Retrieve relevant context
├── update_index()        # Refresh index
└── get_stats()          # System statistics
```

### Data Flow

```
Documents → Chunking → Embeddings → Qdrant Storage → Retrieval → Generation
```

## Configuration

### Environment Variables

```bash
# OpenAI API Key (for embeddings)
OPENAI_API_KEY=your_openai_api_key

# Qdrant Configuration
QDRANT_URL=http://localhost:6333

# LlamaIndex Collection
LLAMAINDEX_COLLECTION_NAME=llamaindex_collection

# Feature Flag
ENABLE_LLAMAINDEX_RAG=true
```

### Dependencies

```toml
# LlamaIndex packages
llama-index>=0.10.0
llama-index-embeddings-openai>=0.1.0
llama-index-vector-stores-qdrant>=0.1.0
```

## Usage

### Basic Operations

```python
from src.services.rag.llamaindex_service import LlamaIndexRAGService

# Initialize service
rag_service = LlamaIndexRAGService(
    qdrant_url="http://localhost:6333",
    collection_name="debate_knowledge",
    openai_api_key="your_key"
)

# Ingest documents
texts = [
    "Artificial intelligence is transforming society.",
    "Machine learning enables pattern recognition."
]
metadata = [
    {"source": "article1", "date": "2024-01-01"},
    {"source": "article2", "date": "2024-01-02"}
]

result = rag_service.ingest_documents(texts, metadata)
print(f"Ingested {result.data['documents_ingested']} documents")

# Query RAG system
query_result = rag_service.query(
    "What is artificial intelligence?",
    top_k=5,
    similarity_threshold=0.7
)

print(f"Query: {query_result.data['query']}")
print(f"Response: {query_result.data['response']}")
print(f"Results: {len(query_result.data['results'])} relevant documents")

# Retrieve context only
context_result = rag_service.retrieve_context(
    "machine learning applications",
    top_k=3
)

for item in context_result.data['context']:
    print(f"Text: {item['text'][:100]}...")
    print(f"Score: {item['score']}")
```

### Advanced Usage

#### Custom Chunking

```python
from llama_index.core.node_parser import SimpleNodeParser

# Create custom parser
parser = SimpleNodeParser.from_defaults(
    chunk_size=1024,      # Larger chunks
    chunk_overlap=50,    # More overlap
)

# Parse documents
nodes = parser.get_nodes_from_documents(documents)
```

#### Batch Processing

```python
# Process large document sets in batches
batch_size = 100
for i in range(0, len(all_texts), batch_size):
    batch = all_texts[i:i + batch_size]
    batch_metadata = all_metadata[i:i + batch_size]
    
    result = rag_service.ingest_documents(batch, batch_metadata)
    print(f"Processed batch {i // batch_size + 1}")
```

#### Query with Metadata Filtering

```python
# First ingest with rich metadata
texts = ["Document content here"]
metadata = [{
    "episode_id": "episode_123",
    "speaker": "guest_name",
    "date": "2024-01-01",
    "category": "debate"
}]

rag_service.ingest_documents(texts, metadata)

# Query with filtering (via Qdrant)
# LlamaIndex will retrieve relevant documents based on similarity
# You can then filter results by metadata
```

## Use Cases

### 1. Debate Content Analysis

Ingest debate transcripts and query for specific topics:

```python
# Ingest debate transcripts
transcripts = get_debate_transcripts()
result = rag_service.ingest_documents(transcripts)

# Query for specific arguments
query_result = rag_service.query(
    "What are the main arguments about climate change?",
    top_k=10
)

# Analyze retrieved context
for result in query_result.data['results']:
    print(f"Argument: {result['text']}")
    print(f"Source: {result['metadata']}")
```

### 2. Fact-Checking Support

Use RAG to provide supporting evidence:

```python
# Query for fact-check evidence
context = rag_service.retrieve_context(
    "climate change scientific consensus",
    top_k=5
)

# Use retrieved context for fact-checking
fact_check_result = fact_check_tool.check_claim(
    claim="Climate change is real",
    context=context.data['context']
)
```

### 3. Context-Rich Responses

Enhance agent responses with retrieved context:

```python
# User asks about a topic
user_query = "Explain machine learning"

# Retrieve relevant context
context_result = rag_service.retrieve_context(user_query, top_k=3)

# Generate response with context
contexts = [item['text'] for item in context_result.data['context']]
response = generate_with_context(user_query, contexts)
```

## Performance Considerations

### Chunking Strategy

- **Small chunks (256-512)**: Better precision, more fragments
- **Large chunks (1024+)**: Better context, fewer fragments
- **Overlap**: 10-20% typically optimal

### Top-K Selection

- **Small K (3-5)**: Fast, focused results
- **Large K (10-20)**: Comprehensive, more context
- **Adjust based on use case**

### Similarity Threshold

- **High threshold (0.8+)**: Very relevant only
- **Low threshold (0.5-)**: More inclusive
- **Default (0.7)**: Balanced

## Monitoring

### Statistics

```python
# Get system statistics
stats = rag_service.get_stats()

print(f"Collection: {stats.data['collection_name']}")
print(f"Points: {stats.data['points_count']}")
print(f"Vectors: {stats.data['vectors_count']}")
```

### Query Performance

Monitor query latency and retrieval quality:

```python
import time

start = time.time()
result = rag_service.query("test query")
latency = time.time() - start

print(f"Query latency: {latency:.2f}s")
print(f"Results retrieved: {len(result.data['results'])}")
```

## Troubleshooting

### Connection Issues

```bash
# Check Qdrant is running
docker-compose ps qdrant

# View logs
docker-compose logs qdrant

# Test connection
curl http://localhost:6333/health
```

### Embedding Issues

```python
# Verify OpenAI API key
from openai import OpenAI
client = OpenAI(api_key="your_key")
print(client.models.list())
```

### Low Retrieval Quality

1. **Increase chunk overlap**: More context per chunk
2. **Adjust similarity threshold**: Lower for more results
3. **Review chunk size**: May need larger chunks
4. **Ingest more documents**: Expand knowledge base

## Best Practices

1. **Metadata**: Always include rich metadata for filtering
2. **Chunking**: Use appropriate chunk size for content type
3. **Overlap**: Include overlap to prevent context loss
4. **Regular Updates**: Update index with new content
5. **Monitoring**: Track retrieval quality and performance
6. **Testing**: Test with various query types

## See Also

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [Qdrant Integration](https://docs.llamaindex.ai/en/stable/module_guides/vector_stores/vector_stores/)
- [OpenAI Embeddings](https://docs.llamaindex.ai/en/stable/api_reference/embeddings/)
- [Vector Storage Architecture](./vector_storage.md)
