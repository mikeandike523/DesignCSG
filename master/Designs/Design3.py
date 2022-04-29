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
segments =32
for I in range(segments):
	t1 = 2.0*np.pi*I/segments
	t2 = 2.0*np.pi*(I+1)/segments
	dy = vec3(0.0,-aspect[1],0.0)
	A = dy
	B = dy + R*vec3(cos(t1),0.0,sin(t1))
	C = dy + R*vec3(cos(t2),0.0,sin(t2))
	addTriangle(Triangle3(A,B,C))
			

R=max(aspect[0],aspect[2])*1.0
segments =32
center  = 2.0*aspect
ydir = normalize(aspect)
r=normalize(vec3(ydir[0],0.0,ydir[2]))
d=np.dot(ydir,r)
h=ydir[1]
dnew = -h
hnew = d
xdir = dnew*r + hnew*vec3(0.0,1.0,0.0)
zdir = normalize(cross(xdir,ydir))

for I in range(segments):
	t1 = 2.0*np.pi*I/segments
	t2 = 2.0*np.pi*(I+1)/segments
	A = center
	B = center+ toCoordinates(R*vec3(cos(t1),0.0,sin(t1)),xdir,ydir,zdir)
	C = center+ toCoordinates(R*vec3(cos(t2),0.0,sin(t2)),xdir,ydir,zdir)
	addLightingTriangle(Triangle3(A,B,C))
	

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
//	return Vector3f(0.5,0.2,1.0);
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
	//return vy;
//	return toLocal(reflected);

	float lightIntensity=1.0;

	of3_t intersection = raycast(gv,reflected,AD_NUM_LIGHT_TRIANGLES,AD_LIGHT_TRIANGLE_DATA);
	if(intersection.hit!=-1){
		//float3 hitPoint = intersection.hitPoint;
		gv = gv+bias*gn;
		intersection = raycast(gv,reflected,AD_NUM_TRIANGLES,AD_TRIANGLE_DATA);
		if(intersection.hit==-1){
		//L += lightIntensity/d2;
		L+=lightIntensity;
		}
	}
	return f2f3(L);
	
}
Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}
""".replace("<{R}>",str(R)).replace("<{H}>",str(2.0*aspect[1])))

commit()