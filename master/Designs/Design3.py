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
		self.N=np.cross(C-A,B-A)

triangles = []
def addTriangle(tr):
	triangles.append(tr)

#construct some triangles here
addTriangle(Triangle3(vec3(1,0,0),vec3(0,1,0),vec3(0,0,1)))





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

commit(scene=""" 
	//in the future, fragment shaders will go here

""")
