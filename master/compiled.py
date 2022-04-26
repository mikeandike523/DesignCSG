from DesignCSG import *
import numpy as np

includeCL("LinAlg.cl")

def vec3(x,y,z):
	return np.array([x,y,z],dtype=float)

def normalize(v):
	return v/np.linalg.norm(v)

class Triangle3:
	def __init__(self,A,B,C):
		self.A=A
		self.B=B
		self.C=C
		self.N=normalize(np.cross(C-A,B-A))

triangles = []
def addTriangle(tr):
	triangles.append(tr)

#construct some triangles here
A=vec3(-1,1,0)
B=vec3(1,1,0)
C=vec3(1,-1,0)
D=vec3(-1,-1,0)
addTriangle(Triangle3(A,B,C))
addTriangle(Triangle3(C,D,A))
A=vec3(-1,0,1)
B=vec3(1,0,1)
C=vec3(1,0,-1)
D=vec3(-1,0,-1)
addTriangle(Triangle3(A,B,C))
addTriangle(Triangle3(C,D,A))





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

commit(shaders=""" 
float3 getTriangleN(int it);
float3 fragment(float3 gv, int it){
	return fabs(getTriangleN(it));
}
Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}
""")
