from DesignCSG import *
from designlibrary import *
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.pointInsidePen import PointInsidePen

# ######
#Courtesy of everestial007 on StackOverflow
#https://stackoverflow.com/a/42815781/5166365
from fontTools.ttLib import TTFont
font = TTFont('Designs/CourierPrime-Bold.ttf')
# ######

cmap = font.getBestCmap()
glyphSet = font.getGlyphSet()


AXES_XYZ  = -1
AXES_XY = 0
AXES_YZ = 1
AXES_ZX = 2

def vec3(x,y,z):
	return np.array([x,y,z])

def point(a,b):
	return (a,b)

def midpoint(A,B):
	return 0.5*(A+B)

class Curve:

	def __init__(self,A,B,C,thickness = 0.075,axesTag=AXES_XY):
		self.A = A
		self.B = B
		self.C = C

		self.thickness = thickness
		self.axesTag =axesTag

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
	_minX = np.min(xvals)
	_maxX = np.max(xvals)
	_minY = np.min(yvals)
	_maxY = np.max(yvals)
	rescaleX = lambda x: minX + (maxX-minX) * (x-_minX) / (_maxX-_minX)
	rescaleY = lambda y: minY + (maxY-minY)* (y-_minY) / (_maxY-_minY)
	return rescaleX, rescaleY

def getInverseScalers(letter):
	pts = getFontData(letter)[0]
	_minX = -1
	_maxX = 1
	_minY = -1
	_maxY = 1
	xvals = []
	yvals = []
	for pt in pts:
		xvals.append(pt[0])
		yvals.append(pt[1])
	minX = np.min(xvals)
	maxX = np.max(xvals)
	minY = np.min(yvals)
	maxY = np.max(yvals)
	rescaleX = lambda x: minX + (maxX-minX) * (x-_minX) / (_maxX-_minX)
	rescaleY = lambda y: minY + (maxY-minY)* (y-_minY) / (_maxY-_minY)
	return rescaleX, rescaleY

def packShort(bits):
	place = 0
	value = 0
	for bit in reversed(bits):
		value+=bit*(2**place)
		place+=1
	return value

def addADBits(name,bits):
	floatData = []
	for bitNumber in range(0,len(bits),16):
		bts = bits[bitNumber:(bitNumber+16)]
		floatData.append(packShort(bts))
	addArbitraryData(name,floatData)

def testPoint(letter,point):
	rescaleX,rescaleY = getInverseScalers(letter)
	testPoint = (rescaleX(point[0]),rescaleY(point[1]))
	pen=PointInsidePen(glyphSet,testPoint)
	g = glyphSet[cmap[ord(letter)]]
	g.draw(pen)
	return pen.getResult()

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
		self.pathStart = self.currentPoint

	def closePath(self):

		A = self.currentPoint
		C = self.pathStart
		B = tuple(midpoint(np.array(A),np.array(C)))
		self.quadraticSegments.append([A,B,C])
		super().closePath()
	def endPath(self):

		super().endPath()
	def moveTo(self,pt):

		self.currentPoint = self.rescalePoint(pt)
		self.pathStart = self.currentPoint
		super().moveTo(pt)
	def lineTo(self,pt):

		A = self.currentPoint
		C = self.rescalePoint(pt)
		B = tuple(midpoint(np.array(A),np.array(C)))

		self.quadraticSegments.append([A,B,C])
		self.currentPoint = self.rescalePoint(pt)
		super().lineTo(pt)

	def qCurveTo(self,*pts):
		if pts[-1] is None:
			raise Exception("The glyph drawn by this pen contains the rare case for a qCurveTo segment has only an off-curve last point.")

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

		L = len(full_pts)
			
		start = 0
		end = 2
		while end  < L:
			self.quadraticSegments.append([full_pts[start],full_pts[start+1],full_pts[start+2]])
			start +=2
			end +=2
			

		self.currentPoint = self.rescalePoint(pts[-1])
		super().qCurveTo(*pts)

LETTER_RESOLUTION = 64

define_auxillary_function("""

__global int LETTER_AD_OFFS = -1;

#define AXES_XYZ -1
#define AXES_XY 0
#define AXES_YZ 1
#define AXES_ZX 2

#define LETTER_RESOLUTION <{LETTER_RESOLUTION}>

#define Vector3f(x,y,z) ((float3)(x,y,z))
#define toVector3f(v) (Vector3f(v.x,v.y,v.z))

#define SUBSEGMENTS 64

float arg(float x, float y){
	float angle = atan2(y,x);
	if(angle<0.0){
		return 2.0*M_PI+angle;
	}
	return angle;
}

int getADBit(int name, int offs){
	int foffs = offs/16;
	int soffs = offs % 16;
	float fval = getAD(name, foffs);
	int shortval = (int)fval;
	return (shortval  >> (15-soffs) ) & 0x1;
}


float3 scaledVector3f(float s,float3 v) {
	return Vector3f(s*v.x,s*v.y,s*v.z);
}
float box(float3 v){
	
	return T_max(fabs(v.x)-0.5,T_max(fabs(v.y)-0.5,fabs(v.z)-0.5));

}

float box3(float3 v, float3 c, float3 r){
	
	return T_max(fabs(v.x-c.x)-r.x,T_max(fabs(v.y-c.y)-r.y,fabs(v.z-c.z)-r.z));

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

float quadraticBezierSDF(float3 v,float3 A, float3 B, float3 C, float thickness,int axesTag,int N){

	float d = MAX_DISTANCE;

	for(int i=0;i < N;i++){

		float t = (float)i/(float)N;
		float3 p = quadraticBezierCurve(A,B,C,t);
		//assume axesTag = AXES_XY
		p.z=0;
		v.z = 0;

		float dist = length(p-toVector3f(v));

		if(dist<d){
				d = dist;
		}

	}

	int queryCol = (int)(LETTER_RESOLUTION*(v.x+1.0)/2.0);
	int queryRow = LETTER_RESOLUTION-(int)(LETTER_RESOLUTION*(v.y+1.0)/2.0);
	int bitPosition = queryRow*(LETTER_RESOLUTION+1) + queryCol;
	
	int val = 0 ;
	if(queryCol>=0&&queryCol<=LETTER_RESOLUTION&&queryRow>=0&&queryRow<=LETTER_RESOLUTION)
	{
		val=getADBit(LETTER_AD_OFFS,bitPosition);
	}
	if(val){
		return -d;
	}


	
	
	return d-thickness;

}



""".replace("<{LETTER_RESOLUTION}>",str(LETTER_RESOLUTION))

)

def getLetterComponent(letter,transform=Transform.identity()):

	letter_brush = define_brush(body="""

	LETTER_AD_OFFS = AD_LETTER_OFFS_<{LETTER}>;

	v=(float3)(2.0*v.x,2.0*v.y,2.0*v.z);

	int numCurves = (int)getAD(AD_NUMCURVES_<{LETTER}>,0);
	float d = MAX_DISTANCE;


	for(int i=0;i<numCurves;i++){

		int offs = i*(9+2);
		d = T_min(d,quadraticBezierSDF(toVector3f(v),
			Vector3f(getAD(AD_CURVEDATA_<{LETTER}>,offs+0),getAD(AD_CURVEDATA_<{LETTER}>,offs+1),getAD(AD_CURVEDATA_<{LETTER}>,offs+2)),
			Vector3f(getAD(AD_CURVEDATA_<{LETTER}>,offs+3),getAD(AD_CURVEDATA_<{LETTER}>,offs+4),getAD(AD_CURVEDATA_<{LETTER}>,offs+5)),
			Vector3f(getAD(AD_CURVEDATA_<{LETTER}>,offs+6),getAD(AD_CURVEDATA_<{LETTER}>,offs+7),getAD(AD_CURVEDATA_<{LETTER}>,offs+8)),
			getAD(AD_CURVEDATA_<{LETTER}>,offs+9),(int)getAD(AD_CURVEDATA_<{LETTER}>,offs+10),SUBSEGMENTS
		));


	}

	return T_max(T_max(d,box3(toVector3f(v),Vector3f(0.0,0.0,0.0),Vector3f(1.25,1.25,1.25))),fabs(v.z-1.25)-0.125);

	""".replace("<{LETTER}>",letter))

	curves = []

	def addCurve(curve):
		curves.append(curve)

	pen = InterceptorPen(glyphSet,*getScalers(letter))
	g = glyphSet[cmap[ord(letter)]]
	g.draw(pen)

	for segment in pen.getQuadraticSegments():
		addCurve(Curve(vec3(segment[0][0],segment[0][1],0.0),vec3(segment[1][0],segment[1][1],0.0),vec3(segment[2][0],segment[2][1],0.0)))



	letterbits = []
	for row in range (LETTER_RESOLUTION + 1):
		for col in range(LETTER_RESOLUTION + 1):
			y = 1 - 2 * row/LETTER_RESOLUTION
			x =  -1 + 2* col/LETTER_RESOLUTION
			inside = 1 if testPoint(letter,(x,y)) else 0
			if row == 0 or row == LETTER_RESOLUTION or col == 0 or col == LETTER_RESOLUTION: inside = 0
			letterbits.append(inside)
			print(inside,end="")
		print("\n",end="")

	addADBits("LETTER_OFFS_"+letter,letterbits)


	addArbitraryData("NUMCURVES_"+letter,[float(len(curves))])
	curvedata = []
	for curve in curves:
		curvedata.extend(list(curve.A))
		curvedata.extend(list(curve.B))
		curvedata.extend(list(curve.C))
		curvedata.append(curve.thickness)
		curvedata.append(curve.axesTag)
	addArbitraryData("CURVEDATA_"+letter,curvedata)
	return Component(brush=letter_brush,transform=transform)


EKS = vec3(1,0,0)
WHY = vec3(0,1,0)
ZEE = vec3(0,0,1)
 
leftLetter = getLetterComponent("C",transform = Transform.axes(EKS,WHY,-ZEE))
rightLetter = getLetterComponent("S", transform = Transform.axes(ZEE,WHY,EKS))
topLetter= getLetterComponent("G",transform = Transform.axes(ZEE,-EKS,WHY))

drawUnion(leftLetter,rightLetter,topLetter)

commit()