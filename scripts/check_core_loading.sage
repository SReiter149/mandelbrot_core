from pathlib import Path
import sys 

this_file = Path(sys.argv[0]).resolve()
root = this_file.parent

# look for load_core.sage
while not (root / "load_core.sage").is_file():
    if root == root.parent:
        raise FileNotFoundError("Could not find load_core.sage")
    root = root.parent

load_file = root / "load_core.sage"
load(str(load_file))