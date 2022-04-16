from DesignCSG import *
import numpy as np
from designlibrary import *

def _arr(*args,**kwargs):
	return 5*np.array(*args,**kwargs)

sphere_brush=define_brush(body=""" 

	return length(v)-0.5; 

""")


box_brush=define_brush(body=""" 

	v= fabs(v);
	return T_max(T_max(v.x-0.5,v.y-0.5),v.z-0.5); 

""")




draw(sphere_brush,Transform.initial(
	position=_arr([0.0,-0.0,0.0]),
	yaw=-PI/2,
	pitch=0,
	roll=0,
	scale=_arr([2.0,2.0,2.0])
))

draw(box_brush,Transform.initial(
	position=_arr([0.0,-0.0,0.0]),
	yaw=-PI/2,
	pitch=0,
	roll=0,
	scale=_arr([1.5,1.5,1.5])
))

for _x,_y,_z in np.ndindex((3,3,3)):
	x=_x-1
	y=_y-1
	z=_z-1
	if abs(x)+abs(y)+abs(z)==2:
		erase(sphere_brush,Transform.initial(
			position=_arr([x,y,z]),
			yaw=-PI/2,
			pitch=0,
			roll=0,
			scale=0.75*_arr([1.5,1.5,1.5])
		))

setExportConfig(

	boundingBoxHalfDiameter=10.0,
	minimumOctreeLevel=4,
	maximumOctreeLevel=6,
	gridLevel = 7,
	complexSurfaceThreshold=np.pi/2.0*0.3,
	gradientDescentSteps = 30,
	cacheSubdivision = 16
)

commit()