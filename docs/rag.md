# Retrieval Augmented Generation (RAG)

Chunks written to the vector store include source URLs and timestamp
ranges.  Queries embed the text and perform a cosine search within the
appropriate namespace: `tenant:workspace:creator`.

The `/context` command uses this information to return answers with
inline citations.  CDN links are not stored directly; only the episode
URL and the start timestamp are required to reconstruct a reference of
the form `https://example.com/watch?v=ID&t=MMSS`.
