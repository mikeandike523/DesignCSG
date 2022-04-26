from DesignCSG import *
from designlibrary import *
import numpy as np


def vec3(x,y=None,z=None):
	if isinstance(x,float) and isinstance(y,float) and isinstance(z,float):
		return np.array([x,y,z])
	return np.array(x)

sphere_brush=define_brush(body=""" 
	return length(v)-0.5;
""")


box_brush=define_brush(body=""" 
	v= fabs(v);
	return T_max(T_max(v.x-0.5,v.y-0.5),v.z-0.5);
""")


draw(sphere_brush,Transform.initial(
	position=vec3([0.0,-0.0,0.0]),
	yaw=-PI/2,
	pitch=0,
	roll=0,
	scale=vec3([1.25,1.25,1.25])
))

draw(box_brush,Transform.initial(
	position=vec3([0.0,-0.0,0.0]),
	yaw=-PI/2,
	pitch=0,
	roll=0,
	scale=vec3([0.95,0.95,0.95])
))

for _x,_y,_z in np.ndindex((3,3,3)):
	x=_x-1
	y=_y-1
	z=_z-1
	if abs(x)+abs(y)+abs(z)==3:
		erase(sphere_brush,Transform.initial(
			position=vec3([x,y,z]),
			yaw=-PI/2,
			pitch=0,
			roll=0,
			scale=2.15*vec3([1.0,1.0,1.0])
		))


setExportConfig(

	boundingBoxHalfDiameter=2.0,
	minimumOctreeLevel=5,
	maximumOctreeLevel=7,
	gridLevel = 8,
	complexSurfaceThreshold=np.pi/2.0*0.5,
	gradientDescentSteps = 50,
	cacheSubdivision = 16,
	queriesBeforeGC = 512,
	queriesBeforeFree = 4096
	
)

commit()