"""Ensure project root is on sys.path for `from models`, `rag_engine`, etc."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_root_str = str(_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)
