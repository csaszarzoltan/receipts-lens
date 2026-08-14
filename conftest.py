# conftest.py — ensure src/ layout works if needed
import sys
from pathlib import Path

# Add project root to path for app imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Lightweight async-test runner keeps the repository self-contained when
# pytest-asyncio is unavailable in minimal CI images.
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: run an async test in an event loop")

def pytest_pyfunc_call(pyfuncitem):
    import asyncio
    import inspect
    if inspect.iscoroutinefunction(pyfuncitem.obj):
        kwargs={name:pyfuncitem.funcargs[name] for name in inspect.signature(pyfuncitem.obj).parameters}
        asyncio.run(pyfuncitem.obj(**kwargs))
        return True
    return None
