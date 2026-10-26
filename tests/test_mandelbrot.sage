from pathlib import Path

root = Path(__file__).resolve().parent.parent
load(str(root / "core_code" / "mandelbrot.sage"))
imageLocation = root / "tests" / "testImages"


def testAddCardoid():
    G = Graphics()
    G = addCardoid(G)
    G.save(imageLocation / "testAddCardioid.png", aspect_ratio=1)

def testAdd2CycleBasin():
    G = Graphics()
    G = add2CycleBasin(G)
    G.save(imageLocation / "testAdd2CycleBasin.png", aspect_ratio=1)

def testAddMandelBrotSoFar():
    G = Graphics()
    G = addMandelBrotSoFar(G)
    G.save(imageLocation / "testAddMandelBrotSoFar.png", aspect_ratio=1) 
if __name__ == "__main__":
    testAddCardoid()
    testAdd2CycleBasin()
    testAddMandelBrotSoFar()