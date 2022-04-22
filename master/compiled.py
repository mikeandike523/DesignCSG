from DesignCSG import *
from designlibrary import *

define_auxillary_function("""
#define Vector3f(x,y,z) (float3)((float)(x),(float)(y),(float)(z))
float box(float3 v){
	
	return T_max(fabs(v.x)-0.5,T_max(fabs(v.y)-0.5,fabs(v.z)-0.5));

}

""")

scene_brush = define_brush(body="""
	return box(Vector3f(v.x,v.y-getAD(AD_DT2,1),v.z));
""")

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

draw(scene_brush,Transform.initial(
	position=vec3(0.0,0.0,0.0),
	yaw=0,
	pitch=0,
	roll=0,
	scale=vec3(1.0,1.0,1.0)
))

addArbitraryData("DT1",[1,2,3,4])
addArbitraryData("DT2",[1,-2,4,3])
commit()
