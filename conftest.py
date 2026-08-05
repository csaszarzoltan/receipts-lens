# conftest.py — ensure src/ layout works if needed
import sys
from pathlib import Path

# Add project root to path for app imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
