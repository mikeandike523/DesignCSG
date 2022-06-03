from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin

np.random.seed(1999)

trs1 , aspect1= loadTrianglesFromOBJ("Assets/Model/Car_Decimated_0.25/Car.obj",scale=2.5,textureScale = 0.5)
for tr in trs1:
	addTriangle(tr)

trs2 , aspect2= loadTrianglesFromOBJ("Assets/Model/RoadAsPlane/RoadAsPlane.obj",scale=0.5,textureScale = 0.25)
for I in range(-1,1+1,1):
	for tr in trs2:
		addTriangle(tr.transformed(Transform.eulerX(np.pi/2)).transformed(Transform.translation(vec3(0.0,-aspect1[1]-aspect2[2],0.0))).transformed(Transform.eulerY(np.pi/2)).transformed(Transform.translation(vec3(0.0,0.0,I*2.0*aspect2[1]))))

setSamples(256);
setViewportSamples(1);
setRandomTableSize(16384)
setColorPow(0.25)
setMaxBounces(5)
setBlurCount(1)
setBlurPixels(0)
setBias(0.005)
addSkybox("Assets/Skybox/skybox.jpg",4)

commit()