from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin

includeCL("LinAlg.cl")

def vec3(x,y,z):
	return np.array([x,y,z],dtype=float)

def normalize(v):
	return v/sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])

def cross(A,B):
	C = vec3(0.0,0.0,0.0)
	C[0] = A[1]*B[2]-A[2]*B[1]
	C[1]=-(A[0]*B[2]-A[2]*B[0])
	C[2]=(A[0]*B[1]-A[1]*B[0])
	return C 

class Triangle3:
	def __init__(self,A,B,C):
		self.A=A
		self.B=B
		self.C=C
		self.N=normalize(cross(C-A,B-A))

triangles = []
def addTriangle(tr):
	triangles.append(tr)

numtrs,data = readSTLData("Assets/Mesh/Flower.stl")
def swapYZ(v):
	temp=v[1]
	v[1]=v[2]
	v[2]=temp
	return v

Apoints = []
Bpoints = []
Cpoints = []


for it in range(numtrs):
	A=vec3(data[it*12+3+0],data[it*12+3+1],data[it*12+3+2])
	B=vec3(data[it*12+6+0],data[it*12+6+1],data[it*12+6+2])
	C=vec3(data[it*12+9+0],data[it*12+9+1],data[it*12+9+2])
	A=swapYZ(A)
	B=swapYZ(B)
	C=swapYZ(C)
	Apoints.append(A)
	Bpoints.append(B)
	Cpoints.append(C)



print(len(Apoints),len(Bpoints),len(Cpoints))


minX = float("+inf")
maxX = float("-inf")
minY =float("+inf")
maxY=float("-inf")
minZ=float("+inf")
maxZ=float("-inf")

for point in itertools.chain(Apoints,Bpoints,Cpoints):
	minX = min(minX,point[0])
	maxX = max(maxX,point[0])
	minY = min(minY,point[1])
	maxY = max(maxY,point[1])
	minZ = min(minZ,point[2])
	maxZ = max(maxZ,point[2])

print(minX,maxX,minY,maxY,minZ,maxZ)

aspect = np.array([maxX-minX,maxY-minY,maxZ-minZ],dtype=float)
minaspect = np.min(aspect)
aspect/=minaspect

S=1.0

rescaleX = lambda x: (-1.0*S + 2.0*S * (x-minX)/(maxX-minX))*aspect[0]
rescaleY= lambda y: (-1.0 *S+ 2.0 *S* (y-minY)/(maxY-minY))*aspect[1]
rescaleZ = lambda z: (-1.0 *S+ 2.0 *S* (z-minZ)/(maxZ-minZ))*aspect[2]

rescaleVector  = lambda v: vec3(rescaleX(v[0]),rescaleY(v[1]),rescaleZ(v[2]))

for A,B,C in zip(Apoints,Bpoints,Cpoints):
	addTriangle(Triangle3(rescaleVector(A),rescaleVector(B),rescaleVector(C)))


R=max(aspect[0],aspect[2])*2.0
segments = 256
for I in range(segments):
	t1 = 2.0*np.pi*I/segments
	t2 = 2.0*np.pi*(I+1)/segments
	dy = vec3(0.0,-aspect[1],0.0)
	A = dy
	B = dy + R*vec3(cos(t1),0.0,sin(t1))
	C = dy + R*vec3(cos(t2),0.0,sin(t2))
	addTriangle(Triangle3(A,B,C))
		
	
			
data_num_triangles = [len(triangles)]
addArbitraryData("NUM_TRIANGLES",data_num_triangles)
data_triangles = []
for triangle in triangles:
	for coord in range(3):
		data_triangles.append(triangle.A[coord])
	for coord in range(3):
		data_triangles.append(triangle.B[coord])
	for coord in range(3):
		data_triangles.append(triangle.C[coord])
	for coord in range(3):
		data_triangles.append(triangle.N[coord])

addArbitraryData("TRIANGLE_DATA",data_triangles)

lightingTriangles = []
R=max(aspect[0],aspect[2])*3.0
segments = 256
for I in range(segments):
	t1 = 2.0*np.pi*I/segments
	t2 = 2.0*np.pi*(I+1)/segments
	dy = vec3(0.0,aspect[1]*2.5,0.0)
	A = dy
	B = dy + R*vec3(cos(t1),0.0,sin(t1))
	C = dy + R*vec3(cos(t2),0.0,sin(t2))
	lightingTriangles.append(Triangle3(A,B,C))
	
data_num_triangles = [len(lightingTriangles)]
addArbitraryData("NUM_LIGHT_TRIANGLES",data_num_triangles)
data_triangles = []
for triangle in lightingTriangles:
	for coord in range(3):
		data_triangles.append(triangle.A[coord])
	for coord in range(3):
		data_triangles.append(triangle.B[coord])
	for coord in range(3):
		data_triangles.append(triangle.C[coord])
	for coord in range(3):
		data_triangles.append(triangle.N[coord])

addArbitraryData("LIGHT_TRIANGLE_DATA",data_triangles)	

setSamples(4);

commit(shaders=""" 
#define R <{R}>
#define H <{H}>

float3 reflection(float3 ray, float3 normal){
	float normalComponent = dot(normal,ray);
	float3 normalComponentVector = normalComponent*normal;
	float3 orthagonalVector = ray-normalComponentVector;
	float3 reflected = orthagonalVector-normalComponentVector;
	return reflected;
}
float3 fragment(float3 gv, int it){

	float L = 0.0;
	int numLightingTriangles = (int)getNumTriangles(AD_NUM_LIGHT_TRIANGLES);
	float3 ln = getTriangleN(it,AD_TRIANGLE_DATA);
	float3 gn = toGlobal(ln);
	float3 incident = normalize(gv-camera_g);
	float3 reflected = reflection(incident,gn);
	of3_t intersection = raycast(gv,reflected,AD_LIGHT_TRIANGLE_DATA);
	if(intersection.hit!=-1){
		L += 1.0;
	}
	return f2f3(L);
	
}
Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}
""".replace("<{R}>",str(R)).replace("<{H}>",str(2.0*aspect[1])))

			