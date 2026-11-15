from pathlib import Path
import sys 

file = Path(sys.argv[0]).resolve()

root = file.parent.parent
load(str(root / "load_core.sage"))
image_directory = root / "tests" / "testImages"
saves_directory = root / "tests" / "saves"

def test_generate_and_load_psi():
    generate_psi_coeffs(4, saves_directory)
    save_path = saves_directory / "psi_coefficients_2.sobj"
    psi, psi_coeffs = load_psi(save_path)
    print(psi)
    print(psi(2))


if __name__ == "__main__":
    test_generate_and_load_psi()
    # test2()