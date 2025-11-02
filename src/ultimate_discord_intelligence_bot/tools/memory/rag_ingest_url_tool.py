"""RAG URL ingestion tool: fetch HTTPS pages, strip HTML, chunk and upsert.

Uses core.http_utils wrappers (validate_public_https_url, cached_get) to fetch
content safely. Offline CI remains unaffected because this tool only runs when
invoked and will be guarded by a feature flag when wired into the router.

Contract:
- run(urls: list[str], index: str = "memory", chunk_size: int = 400, overlap: int = 50, max_bytes: int = 500_000)
  -> StepResult with data: { fetched: int, inserted: int, chunks: int, index: str, tenant_scoped: bool }
"""

from __future__ import annotations
import contextlib
import html
import re
from platform.http.http_utils import REQUEST_TIMEOUT_SECONDS, cached_get, validate_public_https_url
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool


def _strip_html_to_text(content: str) -> str:
    content = re.sub("<script[\\s\\S]*?</script>", " ", content, flags=re.IGNORECASE)
    content = re.sub("<style[\\s\\S]*?</style>", " ", content, flags=re.IGNORECASE)
    content = re.sub("<[^>]+>", " ", content)
    content = html.unescape(content)
    content = re.sub("\\s+", " ", content).strip()
    return content


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunk_size = max(50, int(chunk_size))
    overlap = max(0, min(int(overlap), max(0, chunk_size - 1)))
    out: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        out.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
    return out


class RagIngestUrlTool(BaseTool[StepResult]):
    name: str = "RAG Ingest URL Tool"
    description: str = "Fetch HTTPS URLs, strip HTML, chunk and upsert into tenant-scoped VectorStore."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _fetch_text(self, url: str, max_bytes: int) -> str:
        validate_public_https_url(url)
        resp = cached_get(url, timeout_seconds=REQUEST_TIMEOUT_SECONDS)
        txt = getattr(resp, "text", "")
        if not isinstance(txt, str):
            txt = str(txt)
        if max_bytes > 0 and len(txt) > max_bytes:
            txt = txt[:max_bytes]
        return _strip_html_to_text(txt)

    def run(
        self,
        *,
        urls: list[str],
        index: str = "memory",
        chunk_size: int = 400,
        overlap: int = 50,
        max_bytes: int = 500000,
    ) -> StepResult:
        if not isinstance(urls, list) or any((not isinstance(u, str) for u in urls)):
            return StepResult.fail("Invalid params: urls must be a list of strings")
        fetched = 0
        inserted = 0
        chunks_total = 0
        tenant_scoped = False
        try:
            try:
                from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns

                ctx = current_tenant()
                namespace = mem_ns(ctx, index) if ctx else index
                tenant_scoped = ctx is not None
            except Exception:
                namespace = index
                tenant_scoped = False
            from memory import embeddings
            from memory.vector_store import VectorRecord, VectorStore

            vstore = VectorStore()
            to_upsert: list[VectorRecord] = []
            for u in urls:
                try:
                    text = self._fetch_text(u, max_bytes)
                except Exception:
                    continue
                if not text:
                    continue
                fetched += 1
                chunks = _chunk_text(text, chunk_size, overlap)
                chunks_total += len(chunks)
                if not chunks:
                    continue
                vecs = embeddings.embed(chunks)
                for chunk, vec in zip(chunks, vecs, strict=False):
                    to_upsert.append(VectorRecord(vector=vec, payload={"text": chunk, "source_url": u}))
            if to_upsert:
                vstore.upsert(namespace, to_upsert)
                inserted = len(to_upsert)
            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={
                        "tool": "rag_ingest_url",
                        "outcome": "success",
                        "tenant_scoped": str(tenant_scoped).lower(),
                    },
                ).inc()
            return StepResult.ok(
                data={
                    "fetched": fetched,
                    "inserted": inserted,
                    "chunks": chunks_total,
                    "index": namespace,
                    "tenant_scoped": tenant_scoped,
                }
            )
        except Exception as exc:
            with contextlib.suppress(Exception):
                self._metrics.counter(
                    "tool_runs_total",
                    labels={"tool": "rag_ingest_url", "outcome": "error", "tenant_scoped": str(tenant_scoped).lower()},
                ).inc()
            return StepResult.fail(
                str(exc),
                data={
                    "fetched": fetched,
                    "inserted": inserted,
                    "chunks": chunks_total,
                    "index": index,
                    "tenant_scoped": tenant_scoped,
                },
            )


__all__ = ["RagIngestUrlTool"]
