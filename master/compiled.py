from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin
from scenecompiler import createOpenCLClass

np.random.seed(1999)

trs , aspect= loadTrianglesFromSTL("Assets/Mesh/testfile.stl")

for tr in trs:

	tr.Specular = 0.0
	tr.Color =vec3(1,1,1)

	addTriangle(tr)

R=max(aspect[0],aspect[2])*2.0
trs = getCircleTriangles(vec3(0.0,-aspect[1],0.0),R,vec3(1,0,0),vec3(0,1,0),vec3(0,0,1),64)
for tr in trs:

	tr.Specular=1.0
	tr.Color = vec3(0.0,0.0,0.0)


	addTriangle(tr)


for I in range(3):

	

	angle = 2.0*np.pi*I/3
	rx = vec3(cos(angle),0.0,sin(angle))
	rz = vec3(cos(angle+np.pi/2),0.0,sin(angle+np.pi/2))
	ry=vec3(0.0,1.0,0.0)

	R=max(aspect[0],aspect[2])*1.5
	center = 2.0*aspect
	ydir = normalize(aspect)
	r=normalize(vec3(ydir[0],0.0,ydir[2]))
	d=np.dot(ydir,r)
	h=ydir[1]
	dnew = -h
	hnew = d
	xdir = dnew*r + hnew*vec3(0.0,1.0,0.0)
	zdir = normalize(cross(xdir,ydir))

	xdir = toCoordinates(xdir,rx,ry,rz)
	ydir = toCoordinates(ydir,rx,ry,rz)
	zdir = toCoordinates(zdir,rx,ry,rz)
	center=toCoordinates(center,rx,ry,rz)

	trs = getCircleTriangles(center,R,xdir,ydir,zdir,64)
	for tr in trs:
		tr.Emmissive = 1.0
		tr.Color = [vec3(1.0,0.0,0.0),vec3(0.0,1.0,0.0),vec3(0.0,0.0,1.0)][I]
		addTriangle(tr)



setSamples(64);
setRandomTableSize(4096*4)
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

float3 fragment(float3 gv, int it, int * rand_counter_p, int * bounces_p){

	Triangle3f_t tr = getTriangle3f(AD_TRIANGLE_DATA,it);

	const int maxBounces = 3;
	const float bias = 0.005;


	int bounces = 0;
	float3 bounced = (float3)(1.0,1.0,1.0);
	float3 hitPoint = gv;
	float3 oldPoint = camera_g;
	int hitLightSource = 0;


	while(bounces<maxBounces){

		if(tr.Emmissive==1.0) return termProduct(bounced,tr.Color);
		else{
			
			bounced = termProduct(bounced,scaledVector3f(1.0-tr.Specular,tr.Color)+scaledVector3f(tr.Specular,Vector3f(1.0,1.0,1.0)));
		}
		
		float3 n = toGlobal(tr.N);
		float3 AB = toGlobal(tr.B-tr.A);
		
		float3 xdir=normalize(AB);
		float3 ydir=n;
		float3 zdir = normalize(-cross(xdir,ydir));

		float3 incident = normalize(hitPoint-oldPoint);
		if(dot(incident,ydir)>0.0) ydir = -ydir;

		float t1 = rand(rand_counter_p)*M_PI*2.0;
		float t2= rand(rand_counter_p)*M_PI/2.0;
		float3 diffuseReflection = scaledVector3f(cos(t2)*cos(t1),xdir) + scaledVector3f(cos(t2)*sin(t1),zdir) + scaledVector3f(sin(t2),ydir);
		float3 specularReflection = reflection(incident,ydir);
		float3 reflection = normalize(scaledVector3f(tr.Specular,specularReflection)+scaledVector3f(1.0-tr.Specular,diffuseReflection));

		of3_t intersection=raycast(hitPoint+bias*n,reflection,AD_NUM_TRIANGLES,AD_TRIANGLE_DATA);
		if(intersection.hit==-1) {
			bounces++;
			*bounces_p=bounces;
			return (float3)(0.0,0.0,0.0);
		}
		else{
			
			oldPoint=hitPoint;
			hitPoint = intersection.hitPoint;
			tr=getTriangle3f(AD_TRIANGLE_DATA,intersection.hit);
			bounces++;
			*bounces_p=bounces;
		}
	
	}


	return (float3)(0.0,0.0,0.0);
}

Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}

""".replace("<{R}>",str(R)).replace("<{H}>",str(2.0*aspect[1])))

commit()