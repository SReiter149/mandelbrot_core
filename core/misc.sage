def display_convergence(results, convergence_point = None):
    if convergence_point:
        print(f'we know the convergence point is {convergence_point}')
        for result in results:
            print(f"location {numerical_approx(result, 10)}, distance from convergence point = {numerical_approx(abs(convergence_point - result), 10)}" )  
    else:
        for result in convergence:
            print(numerical_approx(result, 10))

def complex_label(z, sig=2):
    a = float(z.real())
    b = float(z.imag())

    a_text = f"{a:.{sig}g}"
    if (abs(b)) == 0:
        return a_text
    b_text = f"{abs(b):.{sig}g}"
    sign = "+" if b >= 0 else "-"

    return f"{a_text} {sign} {b_text}i"

def safe_string(string):
    string = string.replace("/", "÷")
    string = string.replace("*", "•")
    return string