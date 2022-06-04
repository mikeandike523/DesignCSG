from matplotlib import image
import scenecompiler
import numpy as np
import struct
from math import *
import itertools
from PIL import Image
import cv2

#attributions
#None yet.

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

def vec2(x,y):
    return np.array([x,y])

def vec2Tovec3(v):
    return vec3(v[0],v[1],0.0)

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

def zero_float(): return 0.0
def zero_vec3(): return vec3(0.0,0.0,0.0)
def null_float(): return -1.0

class Texture:
    def __init__(self,path,scaling = 1.0):

        #solution to cv2.resize() error ("error: (-215:Assertion failed) func != 0 in function 'resize'") courtesy of https://stackoverflow.com/a/55429040/5166365 

        image = Image.open(path)
        self.data = np.asarray(image).astype(float)/255
        self.data = self.data[:,:,0:3]
        self.W = self.data.shape[1]
        self.H = self.data.shape[0]
        assert(self.data.shape[2]==3)
        ww = int(scaling*self.W)
        hh = int(scaling*self.H)
        # --- cv2.resize() usage Courtesy of https://www.tutorialkart.com/opencv/python/opencv-python-resize-image/
        self.data = cv2.resize(self.data,dsize=(ww,hh))
        self.W = ww
        self.H = hh
        # ---
        self.data = (np.ravel(self.data)*255).astype(int)

textures = []
def addTexture(texture):
    global textures
    textures.append(texture)
    return len(textures) - 1

class Triangle3f:

    A=zero_vec3()
    B=zero_vec3()
    C=zero_vec3()
    N=zero_vec3()
    Color=zero_vec3()
    Specular=zero_float()
    Emmissive=zero_float()
    TextureId=null_float()
    UV0A=zero_vec3()
    UV0B=zero_vec3()
    UV0C=zero_vec3()

    def __init__(self,A,B,C):
        self.A=A
        self.B=B
        self.C=C
        self.N=normalize(cross(C-A,B-A))
        self.TextureId = -1 #it seems that to make default values, the variables must be set in __init__ in order to initialize isntance members instead of class members
                            #therefore, null_float() will make no difference from zero_float()
        
    def hasNan(self):
        return vectorHasNaN(self.A) or vectorHasNaN(self.B) or vectorHasNaN(self.C) or vectorHasNaN(self.N)

    def transformed(self,transform):
        AH = scenecompiler.Transform.to_homogenous(self.A)
        BH = scenecompiler.Transform.to_homogenous(self.B)
        CH = scenecompiler.Transform.to_homogenous(self.C)
        A = scenecompiler.Transform.from_homogenous(scenecompiler.matmul(transform,AH))
        B = scenecompiler.Transform.from_homogenous(scenecompiler.matmul(transform,BH))
        C = scenecompiler.Transform.from_homogenous(scenecompiler.matmul(transform,CH))
        tr = Triangle3f(A,B,C)
        tr.Color = self.Color
        tr.Specular = self.Specular
        tr.Emmissive = self.Emmissive
        tr.TextureId = self.TextureId
        tr.UV0A = self.UV0A.copy()
        tr.UV0B = self.UV0B.copy()
        tr.UV0C = self.UV0C.copy()
        return tr

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

class Vertex:
    def __init__(self,UV,N,P):
        self.P = np.array(P,dtype=float)
        self.N = N
        self.UV = UV
    def scaled(self,s):
        return Vertex(self.UV,self.N,s*self.P)

def loadTrianglesFromOBJ(filepath,scale=1.0,textureScale = 1.0):

    import pywavefront
    import sys
    import os

    print("Loading model \"{}\"...".format(os.path.basename(filepath)))

    '''
    # --- Courtesy of https://www.pluralsight.com/guides/importing-image-data-into-numpy-arrays
    from PIL import Image
    image = Image.open(image_file)
    array = np.asarray(image)
    array = array.astype(int)
    #print(array)
    # --- 

    # --- test the ordering of the numpy array
    print(array.shape)
    image2 = Image.new("RGB",(array.shape[0],array.shape[1]))
    for row in range(array.shape[0]):
        for col in range(array.shape[1]):
            y=row
            x=col
            image2.putpixel((x,y),tuple(array[row,col,:]))
    image2.save(os.path.join(os.path.dirname(filepath),"testimage.png"))
    # ---
    '''

    scene = pywavefront.Wavefront(filepath,collect_faces = True)

    trs = []

    maxX = float("-inf")
    minX = float("+inf")
    maxY = float("-inf")
    minY = float("+inf")
    maxZ = float("-inf")
    minZ = float("+inf")
    
    vertices = []

    for name, material in scene.materials.items():

        image_file = os.path.join(os.path.dirname(filepath),material.texture.file_name)
        texId = addTexture(Texture(image_file,scaling = textureScale))
        num_points = len(material.vertices)//material.vertex_size
        


        for i in range(num_points):

            vdata = material.vertices[(i*int(material.vertex_size)):((i+1)*int(material.vertex_size))]

            #Do not swap y and z
            v = Vertex(vec2(vdata[0],vdata[1]),vec3(vdata[2],vdata[3],vdata[4]),vec3(vdata[5],vdata[6],vdata[7]))
            
            #Swap y and z
            #v=Vertex(vec2(vdata[0],vdata[1]),vec3(vdata[2],vdata[4],vdata[3]),vec3(vdata[5],vdata[7],vdata[6])).scaled(scale)

            v.texId = texId;

            vertices.append(v)

            if v.P[0] > maxX:
                maxX = v.P[0]
            if v.P[0] < minX:
                minX = v.P[0]
            if v.P[1] > maxY:
                maxY = v.P[1]
            if v.P[1] < minY:
                minY = v.P[1]
            if v.P[2] > maxZ:
                maxZ = v.P[2]
            if v.P[2] < minZ:
                minZ = v.P[2]
    



    d1 = maxX - minX
    d2 = maxY - minY
    d3 = maxZ - minZ

    minD = np.min([d1,d2,d3])

    aspect = vec3(1.0,1.0,1.0)

    aspect = vec3(d1/minD,d2/minD,d3/minD)

    rescaleX = lambda x: -1+2*(x-minX)/(maxX-minX)
    rescaleY = lambda y: -1+2*(y-minY)/(maxY-minY)
    rescaleZ = lambda z: -1+2*(z-minZ)/(maxZ-minZ)

    rescalePoint = lambda v: vec3(aspect[0]*rescaleX(v[0]),aspect[1]*rescaleY(v[1]),aspect[2]*rescaleZ(v[2]))

    for i in range(len(vertices)):
        vertices[i].P = rescalePoint(vertices[i].P)

    numtrs = len(vertices) // 3
    for i in range(numtrs):
        vA = vertices[i*3+0]
        vB = vertices[i*3+1]
        vC = vertices[i*3+2]
        tr=Triangle3f(vA.P,vB.P,vC.P)
        tr.TextureId = vA.texId
        tr.UV0A = vec2Tovec3(vA.UV)
        tr.UV0B = vec2Tovec3(vB.UV)
        tr.UV0C = vec2Tovec3(vC.UV)
        if not tr.hasNan():
            trs.append(tr)

    return trs,aspect

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

    print("Adding skybox...")

    img = Image.open(path)
    img =np.asarray(img)
    img = img.astype(float)/255
    W = img.shape[1]
    H = img.shape[0]
    WW = int(W/downscale)
    HH = int(H/downscale)
    import cv2
    img = cv2.resize(img,dsize=(WW,HH))
    img = (img*255).astype(int)
    addArbitraryData("SKYBOX_W",[WW])
    addArbitraryData("SKYBOX_H",[HH])
    texture = []
    for row in range(img.shape[0]):
        for col in range(img.shape[1]):
            for channel in range(img.shape[2]):
                texture.append(float(img[row,col,channel]))
    addArbitraryData("SKYBOX_DATA",texture)

setShaders(""" 

float3 skybox(float3 ray){

    ray=toLocal(normalize(ray));
    int skyW = (int)(getAD(AD_SKYBOX_W,0));
    int skyH = (int)(getAD(AD_SKYBOX_H,0));
    float angleXZ = (atan2(ray.z,ray.x)+2.0*M_PI)/(2.0*M_PI);
    float r = length((float2)(ray.x,ray.z));
    float angleRY = (atan2(ray.y,r)+M_PI/2.0)/(M_PI);
    int pixelX = (int)(skyW*angleXZ) % skyW;
    int pixelY = (int)(skyH*(1.0-angleRY)) % skyH;
    if(pixelX < 0 || pixelX >= skyW || pixelY < 0 || pixelY >= skyH) return f2f3(0.0);
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

   // return Barycentric(gv,toGlobal(tr.A),toGlobal(tr.B),toGlobal(tr.C));

	const int maxBounces = MAX_BOUNCES;
	const float bias = BIAS;


	int bounces = 0;
	float3 bounced = (float3)(1.0,1.0,1.0);
	float3 hitPoint = gv;
	float3 oldPoint = camera_g;
	int hitLightSource = 0;


	while(bounces<maxBounces){

        int texId = (int)tr.TextureId;
        if(texId!=-1){
            float3 uvw = Barycentric(hitPoint,toGlobal(tr.A),toGlobal(tr.B),toGlobal(tr.C));
            float _u = uvw.x*tr.UV0A.x+uvw.y*tr.UV0B.x+uvw.z*tr.UV0C.x;
            float _v = uvw.x*tr.UV0A.y+uvw.y*tr.UV0B.y+uvw.z*tr.UV0C.y;
            return Vector3f(_u,_v,0.0);
            tr.Color = sampleTexture(tr.TextureId,_u,_v);
        }

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
            float3 skyboxColor = skybox(reflected);
            return tr.Specular*skyboxColor + ((float)1.0-tr.Specular)*termProduct(tr.Color,skyboxColor);
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

    print("Loading textures to arbitrary_data.hex...")

    #load texture data here
    allTextureData = []
    textureStarts = []
    textureWidths = []
    textureHeights = []
    pointer = 0
    for texture in textures:
        textureWidths.append(texture.W)
        textureHeights.append(texture.H)
        textureStarts.append(pointer)
        allTextureData.extend(list(texture.data/255))
        pointer+=texture.W*texture.H

    addArbitraryData("TEX_START",textureStarts)
    addArbitraryData("TEX_DATA",allTextureData)
    addArbitraryData("TEX_W",textureWidths)
    addArbitraryData("TEX_H",textureHeights)

    print("Loading triangles to arbitrary_data.hex...")

    addArbitraryData("NUM_TRIANGLES",[len(triangles)])
    triangleData=[]

    fields = scenecompiler.getOpenCLClassFieldsInOrder(Triangle3f)

    for triangle in triangles:
        for field in fields:
            if isinstance(getattr(triangle,field),float) or np.array([getattr(triangle,field)]).shape == (1,):
                triangleData.append(float(getattr(triangle,field)))
            else:
                triangleData.extend(list(getattr(triangle,field)))

    addArbitraryData("TRIANGLE_DATA",triangleData)

    compiler.shaders=shaders_g

    compiler.commit()