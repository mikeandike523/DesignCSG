import scenecompiler
import numpy as np
import struct
from math import *
import itertools

compiler = scenecompiler.SceneCompiler()

addArbitraryData = compiler.addArbitraryData

def setSamples(samples):
    compiler.set_samples(samples)
    with open("maxSamples.txt","w") as fl:
        fl.write(str(int(samples)))
    
define_auxillary_function=compiler.define_auxillary_function
add_preprocessor_define = compiler.add_preprocessor_define
Transform = scenecompiler.Transform
PI=np.pi

def includeCL(filename):
    with open(filename,"r") as fl:
        define_auxillary_function(fl.read())

from stl import mesh
def readSTLData(filepath):
    stlMesh = mesh.Mesh.from_file(filepath)
    numtrs = len(stlMesh.v1)
    normalPlaceholder = np.zeros((len(stlMesh.v1),3),dtype=float)
    data = []
    for A,B,C,N in zip(stlMesh.v0,stlMesh.v1,stlMesh.v2,normalPlaceholder):
        for coord in range(3):
            data.append(N[coord])
        for coord in range(3):
            data.append(A[coord])
        for coord in range(3):
            data.append(B[coord])
        for coord in range(3):
            data.append(C[coord])
    return numtrs,data

def setRandomTableSize(sz):
    compiler.set_random_table_size(sz)

def setColorPow(colorPow):
    compiler.set_color_pow(colorPow)
    with open("colorPow.txt","w") as fl:
        fl.write(str(float(colorPow)))

includeCL("LinAlg.cl")

def vec3(x,y,z):
    return np.array([x,y,z],dtype=float)

def normalize(v):
    return v/sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2])

def cross(A,B):
    C = vec3(0.0,0.0,0.0)
    C[0] = A[1]*B[2]-A[2]*B[1]
    C[1]=-(A[0]*B[2]-A[2]*B[0])
    C[2]=(A[0]*B[1]-A[1]*B[0])
    return C 

def vectorHasNaN(v):
    if isnan(v[0]): return True
    if isnan(v[1]): return True
    if isnan(v[2]): return True
    return False

def null_float(): return 0.0
def null_vec3(): return vec3(0.0,0.0,0.0)

class Triangle3f:

    A=null_vec3()
    B=null_vec3()
    C=null_vec3()
    N=null_vec3()
    Color=null_vec3()
    Specular=null_float()
    Emmissive=null_float()

    def __init__(self,A,B,C):
        self.A=A
        self.B=B
        self.C=C
        self.N=normalize(cross(C-A,B-A))
        
    def hasNan(self):
        return vectorHasNaN(self.A) or vectorHasNaN(self.B) or vectorHasNaN(self.C) or vectorHasNaN(self.N)

def addClass(clss):
    compiler.add_class(clss)

addClass(Triangle3f)

triangles = []

def addTriangle(tr):
    triangles.append(tr)

shaders_g = ""
def setShaders(shaders):
    global shaders_g
    shaders_g = shaders

def setBlurCount(BLUR_COUNT):
    compiler.set_blur_count(BLUR_COUNT)

def setBlurPixels(BLUR_PIXELS):
    compiler.set_blur_pixels(BLUR_PIXELS)

def setMaxBounces(MAX_BOUNCES):
    compiler.set_max_bounces(MAX_BOUNCES)

def setBias(BIAS):
    compiler.set_bias(BIAS)

def setViewportSamples(samples):
    compiler.set_viewport_samples(samples)
    with open("viewportSamples","w") as fl:
        fl.write(str(int(samples)))

def toCoordinates(v,xdir,ydir,zdir):
	return v[0]*xdir+v[1]*ydir+v[2]*zdir

def swapYZ(v):
	temp=v[1]
	v[1]=v[2]
	v[2]=temp
	return v

def loadTrianglesFromSTL(filepath):

    trs=[]

    numtrs,data = readSTLData(filepath)

    Apoints = []
    Bpoints = []
    Cpoints = []

    for it in range(numtrs):
        A=vec3(data[it*12+3+0],data[it*12+3+1],data[it*12+3+2])
        B=vec3(data[it*12+6+0],data[it*12+6+1],data[it*12+6+2])
        C=vec3(data[it*12+9+0],data[it*12+9+1],data[it*12+9+2])
        A=swapYZ(A)
        B=swapYZ(B)
        C=swapYZ(C)
        Apoints.append(A)
        Bpoints.append(B)
        Cpoints.append(C)

    minX = float("+inf")
    maxX = float("-inf")
    minY =float("+inf")
    maxY=float("-inf")
    minZ=float("+inf")
    maxZ=float("-inf")

    for point in itertools.chain(Apoints,Bpoints,Cpoints):
        minX = min(minX,point[0])
        maxX = max(maxX,point[0])
        minY = min(minY,point[1])
        maxY = max(maxY,point[1])
        minZ = min(minZ,point[2])
        maxZ = max(maxZ,point[2])

    aspect = np.array([maxX-minX,maxY-minY,maxZ-minZ],dtype=float)
    minaspect = np.min(aspect)
    aspect/=minaspect

    S=1.0

    rescaleX = lambda x: (-1.0*S + 2.0*S * (x-minX)/(maxX-minX))*aspect[0]
    rescaleY= lambda y: (-1.0 *S+ 2.0 *S* (y-minY)/(maxY-minY))*aspect[1]
    rescaleZ = lambda z: (-1.0 *S+ 2.0 *S* (z-minZ)/(maxZ-minZ))*aspect[2]

    rescaleVector  = lambda v: vec3(rescaleX(v[0]),rescaleY(v[1]),rescaleZ(v[2]))

    for A,B,C in zip(Apoints,Bpoints,Cpoints):
        tr=Triangle3f(rescaleVector(A),rescaleVector(B),rescaleVector(C))
        if tr.hasNan(): continue
        trs.append(tr)

    return trs, aspect

def getCircleTriangles(center,radius,xdir,ydir,zdir,segments=32):
    R=radius
    segments =32
    trs=[]
    for I in range(segments):
        t1 = 2.0*np.pi*I/segments
        t2 = 2.0*np.pi*(I+1)/segments
        A = center
        B = center + toCoordinates(R*vec3(cos(t1),0.0,sin(t1)),xdir,ydir,zdir)
        C = center + toCoordinates(R*vec3(cos(t2),0.0,sin(t2)),xdir,ydir,zdir)
        trs.append(Triangle3f(A,B,C))
    return trs

import imageio
def addSkybox(path,downscale = 1):
    img = imageio.imread(path)
    if downscale > 1:
        img=np.resize(img,[int(img.shape[0]/downscale),int(img.shape[1]/downscale),img.shape[2]])
    addArbitraryData("SKYBOX_W",[img.shape[0]/downscale])
    addArbitraryData("SKYBOX_H",[img.shape[1]/downscale])
    texture = []
    for row in range(img.shape[1]):
        for col in range(img.shape[0]):
            for channel in range(img.shape[2]):
                texture.append(float(img[col,row,channel]))
    addArbitraryData("SKYBOX_DATA",texture)
    print(img.shape,np.amin(img),np.amax(img))



setShaders(""" 

float3 skybox(float3 ray){

    ray=toLocal(normalize(ray));
    int skyW = (int)(getAD(AD_SKYBOX_W,0));
    int skyH = (int)(getAD(AD_SKYBOX_H,0));
    float angleXZ = (atan2(ray.z,ray.x)+2.0*M_PI)/(2.0*M_PI);
    float r = length((float2)(ray.x,ray.z));
    float angleRY = (atan2(ray.y,r)+M_PI/2.0)/(M_PI);
    int pixelX = (int)(skyW*(1.0-angleRY)) % skyW;
    int pixelY = (int)(skyH*angleXZ) % skyH;
    int tid = pixelY*skyW + pixelX;
    float R =getAD(AD_SKYBOX_DATA,tid*3+0)/255.0;
    float G =getAD(AD_SKYBOX_DATA,tid*3+1)/255.0;
    float B =getAD(AD_SKYBOX_DATA,tid*3+2)/255.0;
    return Vector3f(R,G,B);

}

float3 reflection(float3 ray, float3 normal){

	float normalComponent = dot(normal,ray);
	float3 normalComponentVector = normalComponent*normal;
	float3 orthagonalVector = ray-normalComponentVector;
	float3 reflected = orthagonalVector-normalComponentVector;
	return reflected;
}

float3 fragment(float3 gv, int it, int * rand_counter_p, int * bounces_p){

	Triangle3f_t tr = getTriangle3f(AD_TRIANGLE_DATA,it);

	const int maxBounces = MAX_BOUNCES;
	const float bias = BIAS;


	int bounces = 0;
	float3 bounced = (float3)(1.0,1.0,1.0);
	float3 hitPoint = gv;
	float3 oldPoint = camera_g;
	int hitLightSource = 0;


	while(bounces<maxBounces){

		if(tr.Emmissive==1.0) return termProduct(bounced,tr.Color);
		else{
			
			bounced = termProduct(bounced,scaledVector3f(1.0-tr.Specular,tr.Color)+scaledVector3f(tr.Specular,Vector3f(1.0,1.0,1.0)));
		}
		
		float3 n = toGlobal(tr.N);
		float3 AB = toGlobal(tr.B-tr.A);
		
		float3 xdir=normalize(AB);
		float3 ydir=n;
		float3 zdir = normalize(-cross(xdir,ydir));

		float3 incident = normalize(hitPoint-oldPoint);
		if(dot(incident,ydir)>0.0) ydir = -ydir;

		float t1 = rand(rand_counter_p)*M_PI*2.0;
		float t2= rand(rand_counter_p)*M_PI/2.0;
		float3 diffuseReflection = scaledVector3f(cos(t2)*cos(t1),xdir) + scaledVector3f(cos(t2)*sin(t1),zdir) + scaledVector3f(sin(t2),ydir);
		float3 specularReflection = reflection(incident,ydir);
		float3 reflected = normalize(scaledVector3f(tr.Specular,specularReflection)+scaledVector3f(1.0-tr.Specular,diffuseReflection));

		of3_t intersection=raycast(hitPoint+bias*n,reflected,AD_NUM_TRIANGLES,AD_TRIANGLE_DATA);
		if(intersection.hit==-1) {
			bounces++;
			*bounces_p=bounces;
			return skybox(reflected);
		}
		else{
			
			oldPoint=hitPoint;
			hitPoint = intersection.hitPoint;
			tr=getTriangle3f(AD_TRIANGLE_DATA,intersection.hit);
			bounces++;
			*bounces_p=bounces;
		}
	
	}


	return (float3)(0.0,0.0,0.0);
}

Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}

""")

def commit():

    addArbitraryData("NUM_TRIANGLES",[len(triangles)])
    triangleData=[]
    for triangle in triangles:
        triangleData.extend(list(triangle.A))
        triangleData.extend(list(triangle.B))
        triangleData.extend(list(triangle.C))
        triangleData.extend(list(triangle.Color))
        triangleData.append(triangle.Emmissive)
        triangleData.extend(list(triangle.N))
        triangleData.append(triangle.Specular)


    addArbitraryData("TRIANGLE_DATA",triangleData)

    compiler.shaders=shaders_g
    compiler.commit()