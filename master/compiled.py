from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin

np.random.seed(1999)

trs1 , aspect1= loadTrianglesFromOBJ("Assets/Model/FullScene/FullScene.obj",scale=1.0,textureScale = 0.5)
#trs1 , aspect1= loadTrianglesFromOBJ("Assets/Model/Car/Car.obj",scale=1.0,textureScale = 0.5)
for tr in trs1:
	addTriangle(tr)

setSamples(256);
setViewportSamples(1);
setRandomTableSize(16384)
setColorPow(0.1)
setMaxBounces(5)
setBlurCount(1)
setBlurPixels(0)
setBias(0.005)
addSkybox("Assets/Skybox/skybox.jpg",2)

commit()