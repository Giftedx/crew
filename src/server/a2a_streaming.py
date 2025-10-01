"""Optional streaming demo endpoint for the A2A adapter.

Separated to keep the main router lean. Uses the same ENABLE_A2A_STREAMING_DEMO flag.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from .a2a_tools import is_enabled as _is_enabled


def attach_streaming_demo(router: APIRouter) -> None:
    if not _is_enabled("ENABLE_A2A_STREAMING_DEMO", False):
        return
    try:
        from fastapi.responses import StreamingResponse  # type: ignore
    except Exception:  # pragma: no cover - optional
        StreamingResponse = None  # type: ignore

    if StreamingResponse is not None:  # type: ignore[truthy-bool]

        @router.get("/stream-demo")
        async def stream_demo(text: str = "processing") -> Response:
            async def gen():
                import asyncio

                for i in range(1, 4):
                    yield f"data: step {i}/3: {text}\n\n"
                    await asyncio.sleep(0.05)
                yield "data: done\n\n"

            return StreamingResponse(gen(), media_type="text/event-stream")
    else:

        @router.get("/stream-demo")
        async def stream_demo_fallback(text: str = "processing") -> Response:  # pragma: no cover - fallback
            payload = "".join([f"data: step {i}/3: {text}\n\n" for i in range(1, 4)]) + "data: done\n\n"
            return Response(payload, media_type="text/event-stream")


__all__ = ["attach_streaming_demo"]
