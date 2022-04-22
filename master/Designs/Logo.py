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

def getScalers(letter):

	pts = getFontData(letter)[0]
	minX = -1
	maxX = 1
	minY = -1
	maxY = 1
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
	return rescaleX, rescaleY

def point(a,b):
	return (a,b)

class InterceptorPen(TTGlyphPen):

	def getQuadraticSegments(self):
		return self.quadraticSegments

	def __init__(self,glyphSet,rescaleX,rescaleY):
	
		self.rescaleX = rescaleX
		self.rescaleY = rescaleY
		self.rescalePoint = lambda p: (rescaleX(p[0]),rescaleY(p[1]))
		self.quadraticSegments = []
		self.currentPoint = self.rescalePoint(point(0,0))
		super().__init__(glyphSet)

	def closePath(self):
		print("Path Closed.")
		super().closePath()
	def endPath(self):
		print("Path ended but not closed.")
		super().endPath()
	def moveTo(self,pt):
		print("Moved to point: "+repr(pt))
		self.currentPoint = self.rescalePoint(pt)
		super().moveTo(pt)
	def lineTo(self,pt):
		print("Drew line to point: "+repr(pt))
		A = self.currentPoint
		C = self.rescalePoint(pt)
		B = tuple(midpoint(np.array(A),np.array(C)))
		print(A,B,C)
		self.quadraticSegments.append([A,B,C])
		self.currentPoint = self.rescalePoint(pt)
		super().lineTo(pt)

	#due to using trueType font, I can assume curveTo will not be called
	def curveTo(self,*pts):
		print("Drew cubic curve to: " +repr(pts))
		super().curveTo(*pts)

	def qCurveTo(self,*pts):
		if pts[-1] is None:
			raise Exception("The glyph drawn by this pen contains the rare case for a qCurveTo segment has only an off-curve last point.")
		print("Drew quadratic curve to: " +repr(pts))
		L = 1 + len(pts)
		if L < 3:
			raise Exception("The glyph has a quadratic segment with only two points.")
		full_pts = []
		full_pts.append(self.currentPoint)
		for I in range(len(pts)-2):
			A = self.rescalePoint(pts[I])
			B = self.rescalePoint(pts[I+1])
			full_pts.append(A)
			full_pts.append(tuple(midpoint(np.array(A),np.array(B))))
		full_pts.append(self.rescalePoint(pts[-2]))
		full_pts.append(self.rescalePoint(pts[-1]))
		print(L,len(full_pts))
		
			

		self.currentPoint = self.rescalePoint(pts[-1])
		super().qCurveTo(*pts)


letter = "f"
pen = InterceptorPen(glyphSet,*getScalers(letter))
g = glyphSet[cmap[ord(letter)]]
g.draw(pen)

for segment in pen.getQuadraticSegments():
	addCurve(Curve(vec3(segment[0][0],segment[0][1],0.0),vec3(segment[1][0],segment[1][1],0.0),vec3(segment[2][0],segment[2][1],0.0)))


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


