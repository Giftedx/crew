# Knowledge Graph

This repository ships a lightweight knowledge graph for linking entities, claims and media.

## Storage
Nodes and edges are stored in a small SQLite database via `KGStore`. Each node is
namespaced by tenant and can be connected with typed edges. The store offers helper
methods for queries and neighbor traversal.

## Extraction
`kg.extract` performs a minimal pass over text to surface capitalised entities and simple
claim statements. These can be inserted into the graph during ingestion to maintain
cross‑content links.

## Reasoning & Visualisation
`kg.reasoner.timeline` orders events mentioning an entity by timestamp. Subgraphs can
be rendered to Graphviz DOT via `kg.viz.render` for debugging or Discord previews.
