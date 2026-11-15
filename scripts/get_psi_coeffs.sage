from pathlib import Path

root = Path(__file__).resolve().parent.parent
load(str(root / "load_core.sage"))

save_dir = root  / 'saves' / 'psi_coeffs'
save_dir.mkdir(parents = True, exist_ok = True)

generate_psi_coeffs(9, save_dir, batch_size = 30)