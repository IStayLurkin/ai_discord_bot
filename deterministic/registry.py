# deterministic/registry.py
from typing import Callable, List, Tuple, Optional

Handler = Callable[[str], Optional[str]]

_handlers: List[Tuple[int, Handler]] = []  # (priority, fn)


def register_handler(priority: int = 100):
    """
    Decorator to register a deterministic handler.

    Each handler takes (text: str) -> Optional[str].
    If it returns a non-empty string, that response is used and we STOP.
    Lower priority number = tried earlier.
    """
    def deco(fn: Handler) -> Handler:
        _handlers.append((priority, fn))
        _handlers.sort(key=lambda x: x[0])
        return fn
    return deco


def try_deterministic_tools(text: str) -> Optional[str]:
    for _, fn in _handlers:
        resp = fn(text)
        if resp:
            return resp
    return None

