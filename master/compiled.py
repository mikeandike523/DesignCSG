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

float ipow(float f, int n){
	float r = 1.0;
	for(int i=0;i<n;i++){
		r*=f;
	}
	return r;
}

float3 cubicBezierCurve(float3 A, float3 B, float3 C, float3 D, float t){

	return scaledVector3f(ipow(1.0-t,3),A) + scaledVector3f(3*ipow(1.0-t,2)*t,B) + scaledVector3f(3*(1.0-t)*ipow(t,2),C) + scaledVector3f(ipow(t,3),D);

}

float cubicBezierSDF(float3 v, float3 A, float3 B, float3 C, float3 D, float thickness, int axesTag, int N){


	float d = MAX_DISTANCE;

	for(int i=0;i < N;i++){
		float t = (float)i/(float)N;
		float3 p = cubicBezierCurve(A,B,C,D,t);

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

	int offs = i*(9+2);
	d = T_min(d,quadraticBezierSDF(toVector3f(v),
		Vector3f(getAD(AD_CURVEDATA,offs+0),getAD(AD_CURVEDATA,offs+1),getAD(AD_CURVEDATA,offs+2)),
		Vector3f(getAD(AD_CURVEDATA,offs+3),getAD(AD_CURVEDATA,offs+4),getAD(AD_CURVEDATA,offs+5)),
		Vector3f(getAD(AD_CURVEDATA,offs+6),getAD(AD_CURVEDATA,offs+7),getAD(AD_CURVEDATA,offs+8)),
		getAD(AD_CURVEDATA,offs+9),(int)getAD(AD_CURVEDATA,offs+10),50
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

def midpoint(A,B):
	return 0.5*(A+B)


#render ttf here

def getFontData(chr):
	pen = TTGlyphPen(glyphSet)
	g = glyphSet[cmap[ord(chr)]]
	g.draw(pen)
	g=pen.glyph()
	return g.getCoordinates(glyphSet._glyphs)
	

letter = "A"
fontData = getFontData("A")
pts = fontData[0]
endPts = fontData[1]
flags = fontData[2]
print(pts)
print(endPts)
print(flags)

def scaleTo(pts, minX, maxX, minY, maxY):
	xvals = []
	yvals = []
	for pt in pts:
		xvals.append(pt[0])
		yvals.append(pt[1])
	print(xvals,yvals)
	_minX = np.min(xvals)
	_maxX = np.max(xvals)
	_minY = np.min(yvals)
	_maxY = np.max(yvals)
	print(_minX,_maxX,_minY,_maxY)
	rescaleX = lambda x: minX + (maxX-minX) * x / (_maxX-_minX)
	rescaleY = lambda y: minY + (maxY-minY)* y/ (_maxY-_minY)
	for i in range(len(xvals)):
		xvals[i] = rescaleX(xvals[i])
		yvals[i]=rescaleY(yvals[i])
	return list(zip(xvals,yvals))

print(scaleTo(pts,-1,1,-1,1))
pts = scaleTo(pts,-1,1,-1,1)


contours = []
contourFlags = []
pointer = 0
while pointer< len(pts) and len(endPts) > 0:
	end = endPts.pop()
	contours.append(pts[pointer:(end+1)])
	contourFlags.append(flags[pointer:(end+1)])
	pointer = end + 1

for contour in contours:
	if len(contour) < 3:
		A=vec3(contour[0][0],contour[0][1],0)
		C=vec3(contour[1][0],contour[1][1],0)
		B=midpoint(A,C)

		addCurve(Curve(A,B,C))

	else:
		for offs in range(len(contour)-2):
			A=vec3(contour[offs+0][0],contour[offs+0][1],0)
			B=vec3(contour[offs+1][0],contour[offs+1][1],0)
			C=vec3(contour[offs+2][0],contour[offs+2][1],0)
			addCurve(Curve(A,B,C))

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


#experiment with making a custom pen to intercept strokes
class InterceptorPen(TTGlyphPen):
	def closePath(self):
		print("Path Closed.")
		super().closePath()
	def endPath(self):
		print("Path ended but not closed.")
		super().endPath()
	def moveTo(self,point):
		print("Moved to point: "+repr(point))
		super().moveTo(point)
	def lineTo(self,point):
		print("Drew line to point: "+repr(point))
		super().lineTo(point)
	def curveTo(self,*points):
		print("Drew cubic curve to: " +repr(points))
		super().curveTo(*points)
	def qCurveTo(self,*points):
		print("Drew quadratic curve to: " +repr(points))
		super().qCurveTo(*points)
	
pen = InterceptorPen(glyphSet)
g = glyphSet[cmap[ord("e")]]
g.draw(pen)


