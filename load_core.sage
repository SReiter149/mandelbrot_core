"""Load the human-written Sage core into a caller's namespace.

In a Sage script: load(str(repository_root / "load_core.sage"))
In Python: sage.repl.load.load(str(entry_point), namespace)
The entry point loads definitions only; it does not run analyses or generate saves.
"""


def load_core(namespace, project_root=None):
    """Load all core helpers in dependency order, without changing caller paths.

    Explicitly pass globals() or a separate dict as namespace. When no project
    root is supplied, locate the checkout relative to the caller's __file__
    (or cwd for interactive sessions), including sibling run_code/ scripts.
    """
    from pathlib import Path
    import sage.all
    from sage.repl.load import load as sage_load

    filenames = (
        "constants.sage", "math.sage", "misc.sage", "external_rays.sage",
        "plot.sage", "mandelbrot.sage", "analysis.sage",
    )
    if project_root is None:
        caller = namespace.get("__file__")
        start = Path(caller).resolve().parent if caller else Path.cwd().resolve()
        candidates = (
            candidate
            for parent in (start, *start.parents)
            for candidate in (parent, parent / "mandelbrot_core",
                              parent / "code" / "mandelbrot_core")
        )
        project_root = next(
            (candidate for candidate in candidates
             if (candidate / "core" / "math.sage").is_file()
             and (candidate / "core" / "plot.sage").is_file()),
            None,
        )
        if project_root is None:
            raise FileNotFoundError("Cannot find mandelbrot_core/core relative to the caller")

    core_dir = Path(project_root).resolve() / "core"
    sources = [core_dir / filename for filename in filenames]
    for source in sources:
        if not source.is_file():
            raise FileNotFoundError(f"Missing core helper: {source}")

    # Sage helpers expect the standard Sage namespace, but callers retain their
    # existing bindings. Do not replace their module identity with sage.all's.
    for name, value in vars(sage.all).items():
        if not name.startswith("__"):
            namespace.setdefault(name, value)

    # Some helpers inspect __file__ and define a global root. Their loading must
    # not redirect the caller's later image/save paths or change its identity.
    missing = object()
    previous = {key: namespace.get(key, missing) for key in ("__file__", "root")}
    try:
        for source in sources:
            namespace["__file__"] = str(source)
            sage_load(str(source), namespace)
    finally:
        for key, value in previous.items():
            if value is missing:
                namespace.pop(key, None)
            else:
                namespace[key] = value
    return namespace


load_core(globals())
