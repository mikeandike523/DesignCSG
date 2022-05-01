from DesignCSG import *
import numpy as np
import itertools
import struct
from math import sqrt,cos,sin

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


setSamples(16);
setRandomTableSize(16384)
setColorPow(0.25)
setMaxBounces(5)
setBlurCount(5)
setBlurPixels(2)
setBias(0.005)

commit()