from pathlib import Path
from types import ModuleType
import pytest
@pytest.fixture(scope="module")

def math_core():
    import sage.all
    from sage.repl.load import load
    root = Path(__file__).resolve().parents[2]
    source = root / "load_core.sage"
    
    module = ModuleType("math_core")
    module.__dict__.update({
        name: value
        for name, value in vars(sage.all).items()
        if not name.startswith("__")
    })
    module.__file__ = str(source)
    load(str(source), module.__dict__)
    return module