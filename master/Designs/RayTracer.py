from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin

np.random.seed(1999)

print("TRS1")
trs1 , aspect1= loadTrianglesFromOBJ("Assets/Model/Car/10600_RC_ Car_SG_v2_L3.obj",scale=5.0,textureScale = 0.5)
for tr in trs1:
	addTriangle(tr)
print("TRS2")
trs2 , aspect2= loadTrianglesFromOBJ("Assets/Model/Road2/10563_RoadSectionStraight_v1-L3.obj",scale=1.0,textureScale = 0.125)
for tr in trs2:
	addTriangle(tr.transformed(Transform.translation(vec3(0.0,-aspect2[1],0.0))).transformed(Transform.eulerY(np.pi/2)))

setSamples(256);
setViewportSamples(1);
setRandomTableSize(16384)
setColorPow(0.25)
setMaxBounces(5)
setBlurCount(1)
setBlurPixels(0)
setBias(0.005)
addSkybox("Assets/Skybox/skybox.jpg",1)

commit()