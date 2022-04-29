#To make a capsule, we can unscale different dimensions by a value known before building the final object
#This system of unscaling may eventually be baked into the scenecompiler, but will first test it manually before incorporating it

import scenecompiler
import numpy as np
import struct
from math import *
import itertools

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

def toCoordinates(v,xdir,ydir,zdir):
	return v[0]*xdir+v[1]*ydir+v[2]*zdir

def swapYZ(v):
	temp=v[1]
	v[1]=v[2]
	v[2]=temp
	return v

def loadTrianglesFromSTL(filepath):

    trs=[]

    numtrs,data = readSTLData(filepath)


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

    aspect = np.array([maxX-minX,maxY-minY,maxZ-minZ],dtype=float)
    minaspect = np.min(aspect)
    aspect/=minaspect

    S=1.0

    rescaleX = lambda x: (-1.0*S + 2.0*S * (x-minX)/(maxX-minX))*aspect[0]
    rescaleY= lambda y: (-1.0 *S+ 2.0 *S* (y-minY)/(maxY-minY))*aspect[1]
    rescaleZ = lambda z: (-1.0 *S+ 2.0 *S* (z-minZ)/(maxZ-minZ))*aspect[2]

    rescaleVector  = lambda v: vec3(rescaleX(v[0]),rescaleY(v[1]),rescaleZ(v[2]))

    for A,B,C in zip(Apoints,Bpoints,Cpoints):
        tr=Triangle3(rescaleVector(A),rescaleVector(B),rescaleVector(C))
        if tr.hasNan(): continue
        trs.append(tr)

    return trs, aspect

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


