def addMandelBrotSoFar(G):
    G = addCardoid(G)
    G = add2CycleBasin(G)
    return G 
    
def addCardoid(G):
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

