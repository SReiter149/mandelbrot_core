from sage.all import CC, QQ, e, pi, I, sqrt

def test_functionality(math_core):
    """
    shows that the roots of e^(1/8 * 2 * pi * I) are
    """
    c = QQ(1)/4 + QQ(1)/4 * I 
    fp1, fp2 = (-1/2*sqrt(-I) + 1/2, 1/2*sqrt(-I) + 1/2)

    assert math_core.get_fixed_points(c) == (fp1, fp2)

def test_regression(math_core):
    """
    regression of the CC(0)**0.5 bug
    """
    c = CC(1)/4
    assert math_core.get_fixed_points(c) == (CC(1)/2, CC(1)/2)