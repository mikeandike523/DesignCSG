from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin

np.random.seed(1999)

trs , aspect= loadTrianglesFromOBJ("Assets/Model/10600_RC_ Car_SG_v2_L3.obj",scale=5.0)
for tr in trs:
	addTriangle(tr)

R=3.0
trs = getCircleTriangles(vec3(0.0,-aspect[1],0.0),R,vec3(1,0,0),vec3(0,1,0),vec3(0,0,1),64)
for tr in trs:
	tr.Specular=1.0
	addTriangle(tr)

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