"""Small runtime compatibility helpers for Python 3.14+."""
import asyncio


def ensure_event_loop() -> asyncio.AbstractEventLoop:
    """Return a current event loop, creating one when Python has none."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
