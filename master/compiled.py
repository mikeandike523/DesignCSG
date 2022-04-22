from DesignCSG import *
from designlibrary import *

define_auxillary_function("""
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

float quadraticBezierSDF(float3 v,float3 A, float3 B, float3 C, float thickness, int N){

	float d = MAX_DISTANCE;

	for(int i=0;i < N;i++){
		float t = (float)i/(float)N;
		float3 p = quadraticBezierCurve(A,B,C,t);
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

	int offs = i*10;
	d = T_min(d,quadraticBezierSDF(toVector3f(v),
		Vector3f(getAD(AD_CURVEDATA,offs+0),getAD(AD_CURVEDATA,offs+1),getAD(AD_CURVEDATA,offs+2)),
		Vector3f(getAD(AD_CURVEDATA,offs+3),getAD(AD_CURVEDATA,offs+4),getAD(AD_CURVEDATA,offs+5)),
		Vector3f(getAD(AD_CURVEDATA,offs+6),getAD(AD_CURVEDATA,offs+7),getAD(AD_CURVEDATA,offs+8)),
		getAD(AD_CURVEDATA,offs+9),250
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

draw(scene_brush,Transform.initial(
	position=vec3(0.0,0.0,0.0),
	yaw=0,
	pitch=0,
	roll=0,
	scale=vec3(1.0,1.0,1.0)
))

curves = []

class Curve:
	def __init__(self,A,B,C,thickness = 0.05):
		self.A = A
		self.B = B
		self.C = C
		self.thickness = thickness
		
def addCurve(curve):
	curves.append(curve)


#render ttf here
addCurve(Curve(A=vec3(-1.0,0.0,0.0),B=vec3(0.0,1.0,0.0),C=vec3(1.0,0.0,0.0),thickness=0.05))
addCurve(Curve(A=vec3(0.0,0.0,-1.0),B=vec3(0.0,1.0,0.0),C=vec3(0.0,0.0,1.0),thickness=0.05))
addCurve(Curve(A=vec3(1.0,0.0,0.0),B=vec3(0.0,1.0,0.0),C=vec3(0.0,0.0,1.0),thickness=0.05))


addArbitraryData("NUMCURVES",[float(len(curves))])
curvedata = []
for curve in curves:
	curvedata.extend(list(curve.A))
	curvedata.extend(list(curve.B))
	curvedata.extend(list(curve.C))
	curvedata.append(curve.thickness)
addArbitraryData("CURVEDATA",curvedata)
commit()
