"""Type stubs for loguru package."""

from collections.abc import Callable
from typing import Any, TextIO

class Logger:
    def trace(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def info(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def success(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def log(self, level: str | int, message: str, *args: Any, **kwargs: Any) -> None: ...
    def add(
        self,
        sink: TextIO | str | Callable,
        *,
        level: str | int = "DEBUG",
        format: str | Callable = ...,
        filter: str | Callable | None = None,
        colorize: bool | None = None,
        serialize: bool = False,
        backtrace: bool = True,
        diagnose: bool = True,
        enqueue: bool = False,
        catch: bool = True,
        **kwargs: Any,
    ) -> int: ...
    def remove(self, handler_id: int | None = None) -> None: ...
    def complete(self) -> None: ...
    def catch(
        self,
        exception: type[BaseException] | tuple[type[BaseException], ...] = Exception,
        *,
        level: str | int = "ERROR",
        reraise: bool = False,
        onerror: Callable | None = None,
        exclude: type[BaseException] | tuple[type[BaseException], ...] | None = None,
        default: Any = None,
        message: str = "An error has been caught in function '{record[function]}', process '{record[process].name}' ({record[process].id}), thread '{record[thread].name}' ({record[thread].id}):",
    ) -> Callable: ...

logger: Logger
