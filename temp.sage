from pathlib import Path

root = Path(__file__).resolve().parent.parent
load(str(root / "mandelbrot_core" / "load_core.sage"))

image_location = root / "images" / "rays"
saves_location = root / "saves"

c = 1/4 + 1/4 * I

print(get_fixed_points(c))