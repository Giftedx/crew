# Retrieval Augmented Generation (RAG)

Chunks written to the vector store include source URLs and timestamp
ranges.  Queries embed the text and perform a cosine search within the
appropriate namespace: `tenant:workspace:creator`.

The `/context` command uses this information to return answers with
inline citations.  CDN links are not stored directly; only the episode
URL and the start timestamp are required to reconstruct a reference of
the form `https://example.com/watch?v=ID&t=MMSS`.

## Related Optimizations

- [Prompt Compression](prompt_compression.md): After retrieval, lengthy contextual snippets can be structurally compressed (blank line collapse, dedupe, summarization of oversized blocks) to fit stricter model budgets without discarding grounding anchors.
- [Semantic Cache](semantic_cache.md): When a query (post-normalization) is semantically similar to a prior request, the cached grounded answer can be reused, bypassing an additional retrieval + generation cycle.

Together these reduce both token expenditure and latency: compression trims what must be sent; the semantic cache can avoid sending anything at all for near-duplicate queries.
