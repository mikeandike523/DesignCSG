from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin
from scenecompiler import createOpenCLClass

print(createOpenCLClass(Triangle3f))

np.random.seed(1999)

trs , aspect= loadTrianglesFromSTL("Assets/Mesh/testfile.stl")

for tr in trs:
	addTriangle(tr)

R=max(aspect[0],aspect[2])*2.0
trs = getCircleTriangles(vec3(0.0,-aspect[1],0.0),R,vec3(1,0,0),vec3(0,1,0),vec3(0,0,1),64)
for tr in trs:
	addTriangle(tr)

R=max(aspect[0],aspect[2])*1.0
center = 2.0*aspect
ydir = normalize(aspect)
r=normalize(vec3(ydir[0],0.0,ydir[2]))
d=np.dot(ydir,r)
h=ydir[1]
dnew = -h
hnew = d
xdir = dnew*r + hnew*vec3(0.0,1.0,0.0)
zdir = normalize(cross(xdir,ydir))

trs = getCircleTriangles(center,R,xdir,ydir,zdir,64)
for tr in trs:
	addTriangle(tr)

setSamples(16);
setRandomTableSize(4096)
setColorPow(0.25)

setShaders(""" 

#define R <{R}>
#define H <{H}>

float3 reflection(float3 ray, float3 normal){

	float normalComponent = dot(normal,ray);
	float3 normalComponentVector = normalComponent*normal;
	float3 orthagonalVector = ray-normalComponentVector;
	float3 reflected = orthagonalVector-normalComponentVector;
	return reflected;
}

float3 fragment(float3 gv, int it, int * rand_counter_p){
	return Vector3f(1.0,0.0,0.86);
}

Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}

""".replace("<{R}>",str(R)).replace("<{H}>",str(2.0*aspect[1])))

commit()