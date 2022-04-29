from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin

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
	addLightingTriangle(tr)

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

	const float bias = 0.005;
	float L = 0.0;
	int numLightingTriangles = (int)getNumTriangles(AD_NUM_LIGHT_TRIANGLES);
	float3 ln = getTriangleN(it,AD_TRIANGLE_DATA);	
	float3 gn = toGlobal(ln);
	float3 lAB = normalize(getTriangleB(it,AD_TRIANGLE_DATA)-getTriangleA(it,AD_TRIANGLE_DATA));
	float3 gAB = toGlobal(lAB);
	float3 vx = gAB;
	float3 vy=normalize(gn);
	float3 incident=normalize(gv-camera_g);
	if(dot(vy,incident)>=0.0)
		vy=normalize(toGlobal(-ln));
	float3 vz =normalize(-cross(vx,vy));
	float axz = rand(rand_counter_p)*M_PI*2.0;
	float ary = rand(rand_counter_p)*M_PI/2.0;
	float3 reflected = cos(axz)*cos(ary)*vx+sin(axz)*cos(ary)*vz+sin(ary)*vy;
	float lightIntensity=1.0;
	of3_t intersection = raycast(gv,reflected,AD_NUM_LIGHT_TRIANGLES,AD_LIGHT_TRIANGLE_DATA);
	if(intersection.hit!=-1){
		gv = gv+bias*gn;
		intersection = raycast(gv,reflected,AD_NUM_TRIANGLES,AD_TRIANGLE_DATA);
		if(intersection.hit==-1){
		L+=lightIntensity;
		}
	}
	return f2f3(L);
	
}

Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}

""".replace("<{R}>",str(R)).replace("<{H}>",str(2.0*aspect[1])))

commit()