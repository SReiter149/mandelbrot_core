
def plot_vector_field(G, C, tick, convergent_points, divergent_points, misc_points, r_boundaries = [-2,2], i_boundaries = [-2,2] ):
    """
    vector field + fixed points + point classification
    """
    G = add_vector_field(
        G,C,
        r_boundaries=r_boundaries,
        i_boundaries=i_boundaries,
        tick = tick,
        vector_length = tick * 0.75)


    G = add_convergent_points(G, convergent_points, size = 5)
    G = add_divergent_points(G, divergent_points, size = 5)
    G = add_misc_points(G, misc_points, size = 5)

    fp1,fp2 = get_fixed_points(C)
    G = add_points(G, (fp1,fp2), color = "purple", size = 15)

    # CONVERTS TO MATPLOTLIB
    fig = G.matplotlib(figsize=(10, 8), aspect_ratio=1)
    ax = fig.axes[0]

    cmap = LinearSegmentedColormap.from_list(
        "green_to_blue",
        ["#00ff00", "#0000ff"]
    )

    scale = ScalarMappable(
            norm=Normalize(vmin=0, vmax=10),
            cmap=cmap
        )
    scale.set_array([])

    fig.colorbar(
            scale,
            ax=ax,
            label="Vector length"
        )
    ax.set_title(f"Vector Field for P(x) = x^2 + {str(C)}")
    return fig

def analysis_vector_field_rect(C, images_dir, iterations = 20, r_boundaries = [-2, 2], i_boundaries = [-2, 2], tick = 0.1): 
    (
        convergent_points, 
        convergent_paths, 
        divergent_points, 
        divergent_paths, 
        misc_points, 
        misc_paths
    ) = get_paths_and_convergence_over_rect(
        C, 
        iterations = iterations, 
        r_boundaries = r_boundaries, 
        i_boundaries = i_boundaries, 
        tick = tick
    ) 
    G = Graphics()
    fig = plot_vector_field(
        G, 
        C, 
        tick, 
        convergent_points, 
        divergent_points, 
        misc_points,
        r_boundaries = r_boundaries, 
        i_boundaries = i_boundaries
    )
    save_mpl_plot(fig, f"vector field",images_dir)
    return (
        convergent_points, 
        convergent_paths, 
        divergent_points, 
        divergent_paths, 
        misc_points, 
        misc_paths
    )


def analysis_vector_field_polar(C, images_dir, iterations = 20, r_boundaries = [-2, 2], i_boundaries = [-2, 2], centers = [CC(0)], r_max = 3, r_tick = 0.1, t_tick = 0.05):
    convergent_points = []
    convergent_paths = []
    divergent_points = []
    divergent_paths = []
    misc_points = []
    misc_paths = []

    for center in centers:
        (
            c_points,
            c_paths ,
            d_points,
            d_paths ,
            m_points,
            m_paths,
        ) = get_paths_and_convergence_over_polar(
            C,
            iterations = iterations,
            center = center,
            r_max = r_max,
            r_tick = r_tick,
            t_tick = t_tick
        )
        convergent_points.extend(c_points)
        convergent_paths.extend(c_paths)
        divergent_points.extend(d_points)
        divergent_paths.extend(d_paths)
        misc_points.extend(m_points)
        misc_paths.extend(m_paths)

    G = Graphics()
    fig = plot_vector_field(
        G,
        C,
        r_tick,
        convergent_points,
        divergent_points,
        misc_points,
        r_boundaries = r_boundaries,
        i_boundaries = i_boundaries
    )
    save_mpl_plot(fig, "vector field polar", images_dir)
    return (
        convergent_points,
        convergent_paths,
        divergent_points,
        divergent_paths,
        misc_points,
        misc_paths
    )

def analysis_reversed_paths(C, iterations, plot = True,images_dir = None, r_boundaries = [-2, 2], i_boundaries = [-2, 2]):
    if plot == True:
        assert (images_dir is not None), "analysis reversed paths needs an images_dir"
    fixed_points = get_fixed_points(C)
    start_points_1 = get_pullback_paths(C, fixed_points[0], iterations = iterations)
    start_points_2 = get_pullback_paths(C, fixed_points[1], iterations = iterations)
    print(len(start_points_1), len(start_points_2))

    print(f'a few points which converge to {fixed_points[0]} are {list(start_points_1)[:5]}')
    print(f'a few points which converge to {fixed_points[1]} are {list(start_points_2)[:5]}')

    if plot:
        G = Graphics()
        G = add_points(G, start_points_1, color = 'blue', size = 3)
        G = add_points(G, start_points_2, color = 'green', size = 3)
        G = add_points(G, fixed_points, color = '#ca00af')

        G = set_boundaries(G, r_boundaries = r_boundaries, i_boundaries = i_boundaries)
        save_sage_plot(G, f"start points (steps = {iterations})", images_dir)
    return start_points_1, start_points_2

def make_mobius_frame(G, z,c,p,q,r,s, r_boundaries, i_boundaries, tick, t = None, path_length = 20, arrows = True):
    # get vector field
    def m_func(z, c, p,q,r,s):
        z = mobius_inv(z, p,q,r,s)
        z = quadratic(z, c)
        z = mobius(z, p,q,r,s)
        return z

    mobius_field = get_vector_field(
        rect_point_sampler(r_boundaries, i_boundaries, tick),
        lambda z: m_func(z, c=c, p=p, q=q, r=r, s=s)
    )

    # get and add fixed points
    fixed_points = get_mobius_fixed_points(c, p,q,r,s)
    G = add_points(G, fixed_points, color = "gold", zorder = 6)
     
    # get and add path
    rect_path = get_path(c, z, iterations = path_length)
    mobius_path = mobius_transform_on_path(rect_path, p,q,r,s)
    G = add_path(G, mobius_path, arrows = arrows)
    
    # plot vector field
    G = add_vector_field(G, mobius_field, vector_length = 0.1)

    # Render:
    name = f"Mobius c = {complex_label(c)}, m = {complex_label(p)}z + {complex_label(q)} ÷ {complex_label(r)}z + {complex_label(s)}"
    if t:
        name += "t = {t:.2f}"
    G += text(
            name,
            (0, i_boundaries[1] - 0.3),
            fontsize=10,
            color="black",
            horizontal_alignment="center"
    )

    ## THIS MUST BE LAST!
    G = set_boundaries(
        G,
        r_boundaries,
        i_boundaries,
    )
    return G

def analysis_make_mobius_movie(
    c_func, p_func, q_func, r_func, s_func, 
    t_range = [-3, 3], t_tick = 0.1, 
    r_boundaries = [-5, 5], i_boundaries = [-5, 5], tick = 0.1
    ):
    """
    plots path of 0 and vector field across vector field
    you can use lambda functions for p,q,r,s.
    """

    z = CC(0)

    frames = []

    variable_t = var("t")
    print(f"the determinant is {(p_func(variable_t) * s_func(variable_t) - q_func(variable_t) * r_func(variable_t)).simplify_full()}")
    for t in srange(t_range[0], t_range[1], t_tick):
        print(f"working on frame {t}")
        # Set up
        c = CC(c_func(t))
        p = CC(p_func(t))
        q = CC(q_func(t))
        r = CC(r_func(t))
        s = CC(s_func(t))
        G = Graphics()
        
        G = make_mobius_frame(G, z,c,p,q,r,s, r_boundaries, i_boundaries, tick, t = t)
        frames.append(G)

    movie = animate(frames)

    variable_t = var('t')
    save_name = f"mobius transform c = {c_func(variable_t)}, and p,q,r,s = {p_func(variable_t)},{q_func(variable_t)},{r_func(variable_t)},{s_func(variable_t)}.mp4"
    save_name = safe_string(save_name)
    save_path = str(IMAGES_DIR / "rational functions" / save_name)
    movie.save(save_path)
    print(f"saving to {save_path}")
