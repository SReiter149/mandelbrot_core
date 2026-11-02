'''
GET SPECIFIC POINTS
'''

def rect_point_sampler(r_boundaries, i_boundaries, tick):
    for y in srange(i_boundaries[0], i_boundaries[1], tick):
        for x in srange(r_boundaries[0], r_boundaries[1], tick):
            yield CC(x + y*I)

def polar_point_sampler(center, r_max, r_tick, t_tick):
    yield CC(center)
    for r in srange(r_tick, r_max + r_tick, r_tick):
        # t is a fraction of one full turn; e.g. t_tick=0.25 gives 4 angles.
        for t in srange(0, 1, t_tick):
            point = CC(r*e^(t * 2 * pi * I) + center)
            yield point

def get_fixed_points(c):
    return ((1 - (1 - 4*c)**0.5)/2, (1 + (1 - 4*c)**0.5)/2)

def quadratic(z, c):
    return z**2 + c

def iterate_quadratic(z,c,iterations = 10, convergence_threshold = 10e-8):
    """
    iterates the function z^2 + c given the starting point z and the constant c.
    returns a list of `iterations` results.
    """
    previous_results = [CC(z)]
    yield previous_results[-1]
    for i in range(iterations):
        result = quadratic(z, c)
        if (abs(result) > 1/convergence_threshold) or (norm(result - previous_results[-1]) < convergence_threshold):
            break
        yield result
        if result in previous_results:
            break
        previous_results.append(result)

'''
VECTOR FIELD
'''
def get_vector_field(start_points, func):
    vector_field = []
    for z in start_points:
        vector_field.append([z, func(z)])
    return vector_field

'''
PATHS AND CONVERGENCE
'''
def get_path(start_point, func, iterations = 10, convergence_threshold = 10e-8):
    path = [start_point]
    for i in range(iterations):
        new_point = func(path[-1])
        distances = [abs(p - new_point) for p in path]
        path.append(new_point)
        if (
            min(distances) < convergence_threshold or 
            max(distances) > 1/convergence_threshold
        ):     
            return path

    return path


def get_paths(start_points, func, iterations = 10, convergence_threshold = 10e-8):
    paths = []
    for start_point in start_points:
        paths.append(
            get_path(
                start_point, 
                func = func, iterations = iterations, convergence_threshold=convergence_threshold
            )
        )
    return paths

def classify_paths(paths, fixed_points, convergence_threshold = 10e-8):
    convergent_points = []
    convergent_paths = []
    divergent_points = []
    divergent_paths = []
    cycle_points = []
    cycle_paths = []
    misc_points = []
    misc_paths = []

    for path in paths:
        if path[-1] in path[ :-1]:
            cycle_points.append(path[0])
            cycle_paths.append(path)

        distances = [abs(path[-1] - fp) for fp in fixed_points]
        if min(distances) < convergence_threshold:
            convergent_points.append(path[0])
            convergent_paths.append(path)
        elif max(distances)> 1/convergence_threshold:
            divergent_points.append(path[0])
            divergent_paths.append(path)
        else:
            misc_points.append(path[0])
            misc_paths.append(path)  
    return (
        convergent_points, 
        convergent_paths, 
        divergent_points, 
        divergent_paths, 
        cycle_points, 
        cycle_paths,
        misc_points, 
        misc_paths
    )


def get_paths_and_convergence_over_polar(c, iterations = 10, convergence_threshold = 10e-8, center = CC(0), r_max = 3, r_tick = 0.1, t_tick = 0.05):
    complex_field = CC(0)
    fixed_points = get_fixed_points(c)

    paths = []
    for start_point in polar_point_sampler(center, r_max, r_tick, t_tick):
        paths.append(get_path(c, start_point, iterations, convergence_threshold))

    return classify_paths(paths, fixed_points, convergence_threshold = convergence_threshold)


def get_paths_and_convergence_over_rect(c, iterations = 10, convergence_threshold = 10e-8, r_boundaries = (-2, 2), i_boundaries = (-2, 2), tick = 0.1):
    complex_field = CC(0)
    fixed_points = get_fixed_points(c)

    paths = []
    for start_point in rect_point_sampler(r_boundaries, i_boundaries, tick):
        paths.append(get_path(c, start_point, iterations, convergence_threshold))

    return classify_paths(paths, fixed_points, convergence_threshold = convergence_threshold)


'''
PULL BACK STUFF
'''

def get_pullback_paths(c, target, iterations = 10):
    seen = {target}
    frontier = {target}

    for _ in range(iterations):
        next_frontier = set()
        for point in frontier:
            next_points = (point - c).nth_root(2, all=True)
            next_frontier.update(next_points)

        next_frontier.difference_update(seen)
        if  len(next_frontier) == 0:
            return seen
        seen.update(next_frontier)
        frontier = next_frontier
    return seen

'''
MOBIUS TRANFORMATIONS
'''

def mobius(z, p = 1, q = 0, r = 0, s = 1):

    if p*s - r * q == 0:
        raise ValueError(f"Degenerate Mobius transformation: {p}, {q}, {r}, {s}")
    if z == Infinity:
        if r == 0:
            return Infinity
        return p/r
    if r != 0:
        if z == s/r:
            return Infinity

    return (p * z + q) / (r * z + s)

def mobius_inv(z, p = 1, q = 0, r = 0, s = 1):
    if p*s - r * q == 0:
        raise ValueError(f"Degenerate Mobius transformation: {p}, {q}, {r}, {s}")
    if z == Infinity:
        if r == 0:
            return Infinity
        return s/(-1 * r)
    if r != 0:
        if z == p/(-1 * r):
            return Infinity
    return (1/(p*s - r * q)) * (s * z - q) / ((-1 * r) * z + p)
  
def get_mobius_fixed_points(c, p,q,r,s):
    fixed_points = [mobius(z, p,q,r,s) for z in get_fixed_points(c)]
    if r != 0:
        fixed_points.append(p/r)
    return fixed_points

def mobius_transform_on_path(path, p,q,r,s):
    return [mobius(z, p,q,r,s) for z in path]

def mobius_transform_on_vector_field(vector_field, p,q,r,s):
    m = lambda z: mobius(z, p,q,r,s)
    transformed_field = []
    for vector in vector_field:
        new_vector = [m(z) for z in vector]
        transformed_field.append(new_vector)
    return transformed_field