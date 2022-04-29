#To make a capsule, we can unscale different dimensions by a value known before building the final object
#This system of unscaling may eventually be baked into the scenecompiler, but will first test it manually before incorporating it

import scenecompiler
import numpy as np
import struct
from math import *

compiler = scenecompiler.SceneCompiler()

addArbitraryData = compiler.addArbitraryData

def setSamples(samples):
    compiler.set_samples(samples)
    
define_auxillary_function=compiler.define_auxillary_function
add_preprocessor_define = compiler.add_preprocessor_define
Transform = scenecompiler.Transform
PI=np.pi


def includeCL(filename):
    with open(filename,"r") as fl:
        define_auxillary_function(fl.read())

from stl import mesh
def readSTLData(filepath):
    stlMesh = mesh.Mesh.from_file(filepath)
    numtrs = len(stlMesh.v1)
    normalPlaceholder = np.zeros((len(stlMesh.v1),3),dtype=float)
    data = []
    for A,B,C,N in zip(stlMesh.v0,stlMesh.v1,stlMesh.v2,normalPlaceholder):
        for coord in range(3):
            data.append(N[coord])
        for coord in range(3):
            data.append(A[coord])
        for coord in range(3):
            data.append(B[coord])
        for coord in range(3):
            data.append(C[coord])
    return numtrs,data

def setRandomTableSize(sz):
    compiler.set_random_table_size(sz)

def setColorPow(colorPow):
    compiler.set_color_pow(colorPow)

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

def vectorHasNaN(v):
    if isnan(v[0]): return True
    if isnan(v[1]): return True
    if isnan(v[2]): return True
    return False

class Triangle3:
    def __init__(self,A,B,C):
        self.A=A
        self.B=B
        self.C=C
        self.N=normalize(cross(C-A,B-A))
        
    def hasNan(self):
        return vectorHasNaN(self.A) or vectorHasNaN(self.B) or vectorHasNaN(self.C) or vectorHasNaN(self.N)

triangles = []
lightingTriangles = []

def addTriangle(tr):
    triangles.append(tr)
def addLightingTriangle(tr):
    lightingTriangles.append(tr)

shaders_g = ""
def setShaders(shaders):
    global shaders_g
    shaders_g = shaders

def commit():

    addArbitraryData("NUM_TRIANGLES",[len(triangles)])
    addArbitraryData("NUM_LIGHT_TRIANGLES",[len(lightingTriangles)])
    triangleData=[]
    lightingTriangleData=[]
    for triangle in triangles:
        triangleData.extend(list(triangle.A))
        triangleData.extend(list(triangle.B))
        triangleData.extend(list(triangle.C))
        triangleData.extend(list(triangle.N))
    for triangle in lightingTriangles:
        lightingTriangleData.extend(list(triangle.A))
        lightingTriangleData.extend(list(triangle.B))
        lightingTriangleData.extend(list(triangle.C))
        lightingTriangleData.extend(list(triangle.N))
    addArbitraryData("TRIANGLE_DATA",triangleData)
    addArbitraryData("LIGHT_TRIANGLE_DATA",lightingTriangleData)
    compiler.shaders=shaders_g
    compiler.commit()


def toCoordinates(v,xdir,ydir,zdir):
	return v[0]*xdir+v[1]*ydir+v[2]*zdir

def swapYZ(v):
	temp=v[1]
	v[1]=v[2]
	v[2]=temp
	return v

