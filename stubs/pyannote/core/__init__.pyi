"""Type stubs for pyannote.core package."""

class Segment:
    start: float
    end: float

    def __init__(self, start: float, end: float) -> None: ...

class Timeline:
    def __init__(self, segments: list[Segment] | None = None) -> None: ...

class Annotation:
    def __init__(self) -> None: ...
