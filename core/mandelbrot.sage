def addMandelBrotSoFar(G):
    G = addCardoid(G)
    G = add2CycleBasin(G)
    G = add3CycleBasin(G)
    return G 
    
def addCardoid(G):
    # e^(I * 2* pi* 0/5)/2 - e^(0/5 * I * 4 * pi)/4
    t = var('t', domain='real')
    G += parametric_plot(
        ((e^(I * t)/2 - e^(I * 2 * t)/4).real(),
        (e^(I * t)/2 - e^(I * 2 * t)/4).imag()),
        (t, 0, 2 * pi)
    )
    return G

def add2CycleBasin(G):
    t = var('t', domain='real')
    G += parametric_plot(
        ((1/4 * e^(I * t) - 1).real(),
        (1/4 * e^(I * t) - 1).imag()),
        (t, 0, 2 * pi)
    )
    return G

def add3CycleBasin(G):
    t = var('t', domain='real')
    colors = ['red', 'green', 'blue']
    # equation1 = -1/32*(1/3)^(2/3)*(-I*sqrt(3) + 1)*(32*e^(I*t) - 253)/(8*sqrt(144*e^(2*I*t) - 6992/3*e^(I*t) + 28279/3)*(e^(I*t) - 8) - 96*e^(2*I*t) + 1488*e^(I*t) - 5763)^(1/3) - 1/32*(1/3)^(1/3)*(8*sqrt(144*e^(2*I*t) - 6992/3*e^(I*t) + 28279/3)*(e^(I*t) - 8) - 96*e^(2*I*t) + 1488*e^(I*t) - 5763)^(1/3)*(I*sqrt(3) + 1) - 1/16
    # equation2 = -1/32*(1/3)^(2/3)*(I*sqrt(3) + 1)*(32*e^(I*t) - 253)/(8*sqrt(144*e^(2*I*t) - 6992/3*e^(I*t) + 28279/3)*(e^(I*t) - 8) - 96*e^(2*I*t) + 1488*e^(I*t) - 5763)^(1/3) - 1/32*(1/3)^(1/3)*(8*sqrt(144*e^(2*I*t) - 6992/3*e^(I*t) + 28279/3)*(e^(I*t) - 8) - 96*e^(2*I*t) + 1488*e^(I*t) - 5763)^(1/3)*(-I*sqrt(3) + 1) - 1/16
    # equation3 = 1/16*(1/3)^(2/3)*(32*e^(I*t) - 253)/(8*sqrt(144*e^(2*I*t) - 6992/3*e^(I*t) + 28279/3)*(e^(I*t) - 8) - 96*e^(2*I*t) + 1488*e^(I*t) - 5763)^(1/3) + 1/16*(1/3)^(1/3)*(8*sqrt(144*e^(2*I*t) - 6992/3*e^(I*t) + 28279/3)*(e^(I*t) - 8) - 96*e^(2*I*t) + 1488*e^(I*t) - 5763)^(1/3) - 1/16

    equation1 = -1/6*(1/2)^(2/3)*(-I*sqrt(3) + 1)*(3*e^(I*t) + 8)/(9*sqrt(9*e^(2*I*t) - 176/3*e^(I*t) + 1472/3)*(e^(I*t) - 8) - 27*e^(2*I*t) + 288*e^(I*t) - 1600)^(1/3) - 1/24*(1/2)^(1/3)*(9*sqrt(9*e^(2*I*t) - 176/3*e^(I*t) + 1472/3)*(e^(I*t) - 8) - 27*e^(2*I*t) + 288*e^(I*t) - 1600)^(1/3)*(I*sqrt(3) + 1) - 2/3
    equation2 = -1/6*(1/2)^(2/3)*(I*sqrt(3) + 1)*(3*e^(I*t) + 8)/(9*sqrt(9*e^(2*I*t) - 176/3*e^(I*t) + 1472/3)*(e^(I*t) - 8) - 27*e^(2*I*t) + 288*e^(I*t) - 1600)^(1/3) - 1/24*(1/2)^(1/3)*(9*sqrt(9*e^(2*I*t) - 176/3*e^(I*t) + 1472/3)*(e^(I*t) - 8) - 27*e^(2*I*t) + 288*e^(I*t) - 1600)^(1/3)*(-I*sqrt(3) + 1) - 2/3
    equation3 = 1/3*(1/2)^(2/3)*(3*e^(I*t) + 8)/(9*sqrt(9*e^(2*I*t) - 176/3*e^(I*t) + 1472/3)*(e^(I*t) - 8) - 27*e^(2*I*t) + 288*e^(I*t) - 1600)^(1/3) + 1/12*(1/2)^(1/3)*(9*sqrt(9*e^(2*I*t) - 176/3*e^(I*t) + 1472/3)*(e^(I*t) - 8) - 27*e^(2*I*t) + 288*e^(I*t) - 1600)^(1/3) - 2/3
    equations = [equation1, equation2, equation3]
    # equations = [equation3]

    for i in range(3):
        equation = equations[i]
        color = colors[i]
        G += parametric_plot(
            (equation.real(), equation.imag()),
            (t, -20*pi, 20 * pi),
            color = color,
            linestyle='',
            marker='.',
            markersize = 1,
            plot_points = 1000
        )
    return G

def mandelbrotApproximation(G, iterations, spacing = 0.05, verbose = False):
    from matplotlib import colormaps
    from matplotlib.colors import Normalize

    points_in = []
    points_out = []
    steps_out = []
    count = 0
    
    for c_sample in uniform_polar_point_sampler(0, 2, spacing):
        if verbose:
            count += 1
            if count % 500 == 0:
                print(f"finished with {count} samples")
        Qc = lambda z: quadratic(z, c_sample)
        path = get_path(0, Qc, iterations = iterations)
        if abs(path[-1]) > 2:
            points_out.append(c_sample)
            steps_out.append(len(path))
        else:
            points_in.append(c_sample)

    normalize_function = Normalize(vmin=log(min(steps_out)), vmax=log(max(steps_out)))
    cmap = colormaps["plasma"]
    out_colors = [cmap(normalize_function(log(float(steps)))) for steps in steps_out]
    G += scatter_plot(
        [(z.real(), z.imag()) for z in points_out],
        facecolor = out_colors,
        alpha = 1,
        markersize = 1,
        edgecolor="none"
    )
    G += scatter_plot(
        [(z.real(), z.imag()) for z in points_in],
        facecolor = "black",
        edgecolor="none",
        markersize = 1
    )


    return G