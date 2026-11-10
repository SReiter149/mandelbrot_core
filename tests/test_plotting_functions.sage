from pathlib import Path

root = Path(__file__).resolve().parent.parent
load(str(root / "core_code" / "external_rays.sage"))
load(str(root / "core_code" / "math_functions.sage"))
load(str(root / "core_code" / "plotting_functions.sage"))
image_location = root / "tests" / "testImages"

def test_add_points_1():
    G = Graphics()
    points = [1, I, 1+I, 1-I, sqrt(2) + sqrt(3) * I]
    G = add_points(G, points[:2], colors = ["green", "red", "purple"])
    G = add_points(G, points[2:], color = "blue")

    save_path = str(image_location / "test_add_points_1.svg")
    save(G, save_path, aspect_ratio = 1)

def test_plot_parametric_1():
    G = Graphics()
    t = var('t')
    equation = e^(t * 2 * pi * I)

    G = plot_parametric(
        G, equation,
        parametric_variable = t,
    )
    save_path = str(image_location / "test_plot_parametric_1.svg")
    G.save(save_path, aspect_ratio=1) 


def test_plot_external_rays_1():
    G = Graphics()
    load_path_n = root / "tests" / "saves" / "psi_coefficients2.sobj"
    if not load_path_n.exists():
        load_path, load_path_n = generate_psi_coeffs(2)  

    r = var('t')
    G = plot_external_rays(
        G, r*e^(1/8 * 2 * pi * I),
        parametric_variable = r,
        psi_coeffs_load_path = load_path_n,
        step_size = 0.1, sample_range = (1.1, 2),
        debug = True
    )
    
    save_path = str(image_location / "test_plot_external_rays_1.svg")
    G.save(save_path, aspect_ratio=1) 

    
if __name__ == "__main__":
    # test_add_points_1()
    # test_plot_parametric_1()
    test_plot_external_rays_1()