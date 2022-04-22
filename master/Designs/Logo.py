from DesignCSG import *
from designlibrary import *

def vec3(x,y,z):
	return np.array([x,y,z])

#Courtesy of everestial007 on StackOverflow
#https://stackoverflow.com/a/42815781/5166365
from fontTools.ttLib import TTFont
font = TTFont('Designs/Roboto-Black.ttf')
#print(font)
#print(dir(font))
#print(font.getBestCmap())

cmap = font.getBestCmap()
charC_mapped = cmap[ord('C')]
print(charC_mapped)

box_brush = define_brush(body="return T_max(fabs(v.x)-0.5,T_max(fabs(v.y)-0.5,fabs(v.z)-0.5));")

draw(box_brush,Transform.initial(
	position=vec3(0.0,0.0,0.0),
	yaw=0,
	pitch=0,
	roll=0,
	scale=vec3(1.0,1.0,1.0)
))

compiler.addArbitraryData("cCurves",[1,2,3,4])

commit()
