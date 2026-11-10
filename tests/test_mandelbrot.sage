from pathlib import Path

root = Path(__file__).resolve().parent.parent
load(str(root / "core_code" / "mandelbrot.sage"))
load(str(root / "core_code" / "math_functions.sage"))
imageLocation = root / "tests" / "testImages"


def testAddCardoid():
    G = Graphics()
    G = addCardoid(G)
    G.save(imageLocation / "testAddCardioid.svg", aspect_ratio=1)

def testAdd2CycleBasin():
    G = Graphics()
    G = add2CycleBasin(G)
    G.save(imageLocation / "testAdd2CycleBasin.svg", aspect_ratio=1)

def testAdd3CycleBasin():
    G = Graphics()
    G = add3CycleBasin(G)
    G.save(imageLocation / "testAdd3CycleBasin.svg", aspect_ratio=1)

def testAddMandelBrotSoFar():
    G = Graphics()
    G = addMandelBrotSoFar(G)
    G.save(imageLocation / "testAddMandelBrotSoFar.svg", aspect_ratio=1) 


def testMandelbrotApproximation():
    G = Graphics()
    G = mandelbrotApproximation(G, 10)
    G.save(imageLocation / "testMandelbrotApproximation.svg", aspect_ratio=1) 
    
if __name__ == "__main__":
    # testAddCardoid()
    # testAdd2CycleBasin()
    # testAdd3CycleBasin()
    # testAddMandelBrotSoFar()
    testMandelbrotApproximation()