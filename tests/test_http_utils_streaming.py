
from core.http_utils import resilient_get


def test_resilient_get_streaming_forwards_flag_and_iter_content():
    captured = {}

    class StreamResponse:
        status_code = 200
        text = "ok"

        def __init__(self):
            self._chunks = [b"a", b"b", b""]

        def iter_content(self, chunk_size=1):  # pragma: no cover - generator
            for c in self._chunks:
                if c:
                    yield c

    def fake(url, params=None, headers=None, timeout=None, stream=None):
        captured["stream"] = stream
        return StreamResponse()

    resp = resilient_get("https://example.com/file.bin", request_fn=fake, stream=True)
    assert resp.status_code == 200
    assert captured["stream"] is True
