def test_load_core(tmp_path):
    from pathlib import Path
    import shutil
    import subprocess

    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "check_core_loading.sage"

    sage = shutil.which("sage")
    assert sage is not None, "Sage executable was not found on PATH"

    result = subprocess.run(
        [sage, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"Sage loading failed:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )