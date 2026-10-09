"""Helpers for loading the design scripts (hyphenated / duplicate module names)."""

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def load_module(unique_name, relative_path):
    """Import SCRIPTS/<relative_path> under `unique_name`.

    cip/ and logo/ both contain a `core.py` and the generators do
    `from core import ...`, so the module's own directory is put first on
    sys.path and any previously imported `core` is evicted around the import.
    """
    path = SCRIPTS / relative_path
    saved_core = sys.modules.pop("core", None)
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(unique_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
        sys.modules.pop("core", None)
        if saved_core is not None:
            sys.modules["core"] = saved_core
    return module
