from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
from matplotlib.cm import ScalarMappable


def save_sage_plot(G, label, images_dir, r_boundaries = None, i_boundaries = None):
    label_stripped = str(label).replace("/", "over")
    output_path = images_dir / f"{label_stripped}.svg"
    G.save(str(output_path))
    if r_boundaries or i_boundaries:
        G = set_boundaries(G, r_boundaries, i_boundaries)
    print(f"saved to '{output_path}'")

def save_mpl_plot(fig, label, images_dir):
    label_stripped = str(label).replace("/", "over")
    output_path = images_dir / f"{label_stripped}.svg"
    fig.savefig(str(output_path))
    print(f"saved to '{output_path}'")

def set_boundaries(G, r_boundaries = None, i_boundaries = None):
    if r_boundaries:
        G.set_axes_range(
            xmin=r_boundaries[0],
            xmax=r_boundaries[1]
        )
    if i_boundaries:
        G.set_axes_range(
            ymin=i_boundaries[0],
            ymax=i_boundaries[1]
        )
    return G

# PATHS

def add_path(G, path, size = 10, color = 'black', arrow_alpha = 0.30, arrows = True):
    if len(path) == 1:
        G = add_point(G, path[0], size = size, color = color)
        return G
    if len(path) == 2:
        G += arrow(
            path[0], path[1],
            width = 0.5, arrowsize = 1, thickness = 0.5,
            color = color, head = 1)
        G += point((path[0].real(), path[0].imag()), size = size, color = color, zorder = 2)
        G += point((path[1].real(), path[1].imag()), size = size, color = color, zorder = 2)
        return G
    if arrows:
        for a, b in zip(path[:-1], path[1:]):
            start = (a.real(), a.imag())
            end = (b.real(), b.imag())
            if start != end:
                G += arrow(
                    start, end,
                    width = 0.5, arrowsize = 1, thickness = 0.5,
                    color = color)

    for j, z in enumerate(path):
        location = (z.real(), z.imag())
        G += point(location, size=size, color=color, zorder = 2)

    return G

def add_paths(G, paths, size = 10, color = 'black', colors = None, arrow_alpha = 0.30):
    if colors != None:
        assert len(colors) >= len(paths), f"the number of colors ({len(colors)}) must be greater than paths ({len(paths)})"
    else:
        colors = [color] * len(paths)
    if paths:
        for i, path in enumerate(paths):
            G = add_path(
                G, path, size = size, color = colors[i],
                arrow_alpha = arrow_alpha)

    return G

def add_convergent_paths(G, convergent_paths, size = 10):
    return add_paths(G, convergent_paths, color = 'green')
    
def add_divergent_paths(G, divergent_paths, size = 10):
    return add_paths(G, divergent_paths, color = 'red')

def add_misc_paths(G, misc_paths, size = 10):
    return add_paths(G, misc_paths, color = "#b79f27")

# POINTS
def add_point(G, p, color = "black", size = 10, zorder = 4, alpha = 1):
    G += point((p.real(), p.imag()), size=size, color=color, zorder = zorder, alpha = alpha)
    return G

def add_points(G, points, color = "black", size = 10, zorder = 4, alpha = 1):
    if points:
        for p in points:
            G = add_point(G, p, color, size, zorder = zorder, alpha = alpha)
    return G

def add_convergent_points(G, convergent_points, size = 2, zorder = 4):
    return add_points(G, convergent_points, size = size, color = "green",zorder = zorder)

def add_divergent_points(G, divergent_points, size = 2, zorder = 4):
    return add_points(G, divergent_points, size = size, color = "red",zorder = zorder)

def add_misc_points(G, misc_points, size = 2, zorder = 4):
    return add_points(G, misc_points, size = size, color = "yellow",zorder = zorder)

# VECTOR FIELD
def add_vector_field(G, vector_field, vector_length = 0.05, max_length_for_coloring = 10):
    for vec in vector_field:
        if vec[0] == Infinity:
            vec[0] = INFINITY
        if vec[1] == Infinity:
            vec[1] = INFINITY
        length = abs(vec[1] - vec[0])
        unit_vector = (vec[1] - vec[0]) / length
        end_vector = vec[0] + vector_length * unit_vector

        t = min(1, length / max_length_for_coloring)
        color = (0, 1-t, t)
        G += arrow(
            (vec[0].real(), vec[0].imag()),
            (end_vector.real(), end_vector.imag()),
            width = 0.2,
            arrowsize = 0.3,
            thickness = 0.1,
            color = color,
            zorder = 1
        )
    return G
