
from pathlib import Path

root = Path(__file__).resolve().parent.parent
# saves_directory = imageLocation = root / "tests" / "saves"

def generate_psi_coeffs(n, saves_directory = None, batch_size = 20):
    """
    n is the number of iterates we are approximating to
    you will get 2*2^(n-1) terms in the taylor expansion of psi
    psi: dynamic plane -> parameter plane

    returns the path to the save file
    """
    assert isinstance(n, (int, Integer)), "n must be an integer"
    b_variable_names = [f"b{i}" for i in range(0, 2* (2^n - 1))]
    B = PolynomialRing(base_ring = QQ, names = b_variable_names)
    b_variables = list(B.gens())
    L.<w> = AsymptoticRing(growth_group = 'w^QQ', coefficient_ring=B)

    T = LaurentSeriesRing(B, 't')
    t = T.gen()

    # v,c = var("v c")

    # b_variables = [b0, b1, b2, b3, b4, b5, b6, b7, b8]

    b_values = []
    for iteration in range(1, n+1):

        save_path = saves_directory / "psi_coefficients.sobj"
        save_path_i = saves_directory / f"psi_coefficients_{iteration}.sobj"

        if (saves_directory / f"psi_coefficients_{iteration}.sobj").exists():
            psi, b_values = load_psi(saves_directory / f"psi_coefficients_{iteration}.sobj")
        
        else: 
            base_psi = w
            for i in range(len(b_values)):
                base_psi += b_values[i] * w^(-i)
            
            for batch_start in range(len(b_values), 2*(2^iteration - 1), batch_size):
                batch_end = min(batch_start + batch_size, 2*(2^iteration - 1))
                for j in range(batch_start, batch_end):
                    base_psi += b_variables[j] * w^(-j)
 
                psi = base_psi + O(w^-(2 * (2^iteration) - 1))
            
                psi_t = T(
                    [B(1)] + b_values + b_variables[batch_start:batch_end],
                    prec = (2*(2^iteration) - 1) + 1
                ) * t^(-1)

                An_t = psi_t
                for i in range(iteration):
                    An_t = An_t * An_t + psi_t

                An = sum(
                    (
                        An_t[j] * w^(-j)
                        for j in range(int(An_t.valuation()), int(An_t.prec()))
                        if An_t[j]
                    ),
                    L(0)
                ) + O(w^(-int(An_t.prec())))

                print(f"A_{batch_end} has been generated")
            
                for b_index in range(batch_start, batch_end):
                    b_values.append(
                        solve(
                            [SR(An.monomial_coefficient(w^(2^iteration - (b_index+1)))) == 0],
                            SR(b_variables[b_index])
                        )[0].rhs()
                    ) #for n = 1, it was 1
                    An = An.map_coefficients(
                        lambda a: a.subs({b_variables[b_index]: B(b_values[-1])})
                    )

                    base_psi = base_psi.map_coefficients(
                        lambda a: a.subs({b_variables[b_index]: B(b_values[-1])})
                    )
                    
                    print()
                    # print(f"An is now {An}")
                    print(f"b_variables{b_index} value: {b_values[-1]}")

                print(f"psi is now {psi}")
                if saves_directory:

                    save(b_values, str(save_path))
                    save(b_values, str(save_path_i))
                    print(f"saved to both {save_path}, and {save_path_i}")


    print(f"here are all the b_variables values: {b_values}")
    print(f"their numberators are: {[b_values[i].numerator() for i in range(len(b_values))]}")
    print(f"their denominators are 2^: {[log(b_values[i].denominator(), 2) for i in range(len(b_values))]}")


    return b_values

def load_psi(path):
    path = str(path)
    b_values = load(path)

    w = var('w')
    psi = w
    for i in range(len(b_values)):
        psi += b_values[i] * w^(-i)

    w_sym = SR.var('w')
    psi_func = SR(psi).function(w_sym)
    return psi_func, b_values
