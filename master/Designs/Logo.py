from DesignCSG import *
from designlibrary import *
from fontTools.pens.ttGlyphPen import TTGlyphPen

define_auxillary_function("""

#define AXES_XYZ -1
#define AXES_XY 0
#define AXES_YZ 1
#define AXES_ZX 2

#define Vector3f(x,y,z) ((float3)(x,y,z))
#define toVector3f(v) (Vector3f(v.x,v.y,v.z))
float3 scaledVector3f(float s,float3 v) {
	return Vector3f(s*v.x,s*v.y,s*v.z);
}
float box(float3 v){
	
	return T_max(fabs(v.x)-0.5,T_max(fabs(v.y)-0.5,fabs(v.z)-0.5));

}


float3 quadraticBezierCurve(float3 A, float3 B, float3 C, float t){
		return scaledVector3f(1.0-t,scaledVector3f(1.0-t,A)+scaledVector3f(t,B)) + scaledVector3f(t,scaledVector3f(1.0-t,B)+scaledVector3f(t,C));


}

float quadraticBezierSDF(float3 v,float3 A, float3 B, float3 C, float thickness,int axesTag,int N){

	float d = MAX_DISTANCE;

	for(int i=0;i < N;i++){
		float t = (float)i/(float)N;
		float3 p = quadraticBezierCurve(A,B,C,t);

		switch(axesTag){
			case AXES_XY:
				p.z=0;
				v.z = 0;
			break;
			case AXES_YZ:
				p.x = 0;
				v.x = 0;	
			break;
			case AXES_ZX:
				p.y=0;
				v.y=0;
			break;
			default:
				//Do nothing.
			break;
		}


		float dist = length(p-toVector3f(v));
		if(dist<d){
			d = dist;
		}

	}

	return d-thickness;

}



""")

scene_brush = define_brush(body="""


int numCurves = (int)getAD(AD_NUMCURVES,0);
float d = MAX_DISTANCE;

for(int i=0;i<numCurves;i++){

	int offs = i*11;
	d = T_min(d,quadraticBezierSDF(toVector3f(v),
		Vector3f(getAD(AD_CURVEDATA,offs+0),getAD(AD_CURVEDATA,offs+1),getAD(AD_CURVEDATA,offs+2)),
		Vector3f(getAD(AD_CURVEDATA,offs+3),getAD(AD_CURVEDATA,offs+4),getAD(AD_CURVEDATA,offs+5)),
		Vector3f(getAD(AD_CURVEDATA,offs+6),getAD(AD_CURVEDATA,offs+7),getAD(AD_CURVEDATA,offs+8)),
		getAD(AD_CURVEDATA,offs+9),(int)getAD(AD_CURVEDATA,offs+10),250
	));

}

return d;


""")

def vec3(x,y,z):
	return np.array([x,y,z])

# ######
#Courtesy of everestial007 on StackOverflow
#https://stackoverflow.com/a/42815781/5166365
from fontTools.ttLib import TTFont
font = TTFont('Designs/Roboto-Black.ttf')
# ######

cmap = font.getBestCmap()
glyphSet = font.getGlyphSet()


draw(scene_brush,Transform.initial(
	position=vec3(0.0,0.0,0.0),
	yaw=0,
	pitch=0,
	roll=0,
	scale=vec3(1.0,1.0,1.0)
))

curves = []

AXES_XYZ  = -1
AXES_XY = 0
AXES_YZ = 1
AXES_ZX = 2

class Curve:

	def __init__(self,A,B,C,thickness = 0.05,axesTag=AXES_XYZ):
		self.A = A
		self.B = B
		self.C = C
		self.thickness = thickness
		self.axesTag =axesTag
		
def addCurve(curve):
	curves.append(curve)


#render ttf here

def getFontData(chr):
	pen = TTGlyphPen(glyphSet)
	g = glyphSet[cmap[ord(chr)]]
	g.draw(pen)
	g=pen.glyph()
	return g.getCoordinates(glyphSet._glyphs)
	

for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
	print(letter,getFontData(letter))


addCurve(Curve(A=vec3(-1.0,0.0,0.0),B=vec3(0.0,1.0,0.0),C=vec3(1.0,0.0,0.0),thickness=0.05,axesTag=AXES_XYZ))
addCurve(Curve(A=vec3(0.0,0.0,-1.0),B=vec3(0.0,1.0,0.0),C=vec3(0.0,0.0,1.0),thickness=0.05,axesTag=AXES_XYZ))
addCurve(Curve(A=vec3(1.0,0.0,0.0),B=vec3(0.0,1.0,0.0),C=vec3(0.0,0.0,1.0),thickness=0.05,axesTag=AXES_XYZ))


addArbitraryData("NUMCURVES",[float(len(curves))])
curvedata = []
for curve in curves:
	curvedata.extend(list(curve.A))
	curvedata.extend(list(curve.B))
	curvedata.extend(list(curve.C))
	curvedata.append(curve.thickness)
	curvedata.append(curve.axesTag)
addArbitraryData("CURVEDATA",curvedata)
commit()
