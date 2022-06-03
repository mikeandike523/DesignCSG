import dataclasses
from dataclasses import dataclass
import enum
from os import stat
import numpy as np
import os
from typing import List
import struct

INITIAL_SCALE = 1.0
DEFAULT_RANDOM_TABLE_SIZE=4096

with open("deviceInfo.txt","r") as fl:
    ARBITRARY_DATA_POINTS=int(int(fl.read())/4)

compiler =  None

#a variadic wrapper for numpy matmul
def matmul(*args):
    if len(args) == 1:
        raise TypeError("Insufficient Arguments")
    if len(args) == 2:
        return np.matmul(args[0],args[1])
    return matmul(*args[:-2],np.matmul(args[-2],args[-1]))
 

#must match C/OpenCL implementation
COMMAND_VALUES = {
    "IMPORT":0,  
    "EXPORT":1, 
    "MIN":2,
    "MAX":3,
    "NEGATE":4,
    "IDENTITY":5
}

class Utils:

    @staticmethod
    def fwrite(fname, content):
        with open(fname,"w") as fl:
            fl.write(content)

    @staticmethod
    def fread(fname):
        with open(fname,"r") as fl:
            return fl.read()

class Transform:
    """A wrapper class for common homogenous transformations"""


    #matrices are row major in Numpy

    @staticmethod
    def homogenize(v):
        return np.array([v[0],v[1],v[2],0],dtype=float)

    @staticmethod
    def axes(v1,v2,v3):
        return np.array([
          Transform.homogenize(v1),Transform.homogenize(v2),Transform.homogenize(v3),[0,0,0,1] 
        ],dtype=float).T

    @staticmethod
    def translation(offset):
        return np.array([
        
            [1,0,0,offset[0]],
            [0,1,0,offset[1]],
            [0,0,1,offset[2]],
            [0,0,0,1]
        
        ],dtype=float)

    @staticmethod
    def to_homogenous(v):
        return np.concatenate((v,[1.0]))

    @staticmethod
    def from_homogenous(v):
        return v[0:3]

    @staticmethod
    def reciprocal_vector(v):
        d = np.linalg.norm(v)
        return v/(d**2)

    @staticmethod
    def eulerY(yaw):
        return np.array([
        
            [np.cos(-yaw),0,np.sin(-yaw),0],
            [0,1,0,0],
            [np.cos(-yaw+np.pi/2),0,np.sin(-yaw+np.pi/2),0],
            [0,0,0,1]
        
        ],dtype=float).T

    @staticmethod
    def eulerX(pitch):
        return np.array([
        
            [1,0,0,0],
            [0,np.sin(pitch+np.pi/2),np.cos(pitch+np.pi/2),0],
            [0,np.sin(pitch),np.cos(pitch),0],
            [0,0,0,1]
        
        ],dtype=float).T

    @staticmethod
    def eulerZ(roll):
        return np.array([
        
            [np.cos(roll),np.sin(roll),0,0],
            [np.cos(roll+np.pi/2.0),np.sin(roll+np.pi/2.0),0,0],
            [0,0,1,0],
            [0,0,0,1]
        
        ],dtype=float).T

    @staticmethod
    def scaling(scale):
        return np.array([
        
            [scale[0],0,0,0],
            [0,scale[1],0,0],
            [0,0,scale[2],0],
            [0,0,0,1]
        
        ],dtype=float).T

    #ignore roll for now
    @staticmethod
    def rotation(yaw,pitch,roll):
        return matmul(Transform.eulerY(yaw),Transform.eulerX(pitch),Transform.eulerZ(roll))
    

    @staticmethod
    def initial(position,yaw,pitch,roll,scale):
        return matmul(Transform.translation(position),Transform.rotation(yaw,pitch,roll),Transform.scaling(scale))
        
    @staticmethod
    def normalized(v):
        return v/np.linalg.norm(v)

    @staticmethod
    def identity():
        return Transform.axes([1,0,0],[0,1,0],[0,0,1])

class ArbitraryDataChunk:

    def __init__(self,name,start,data):
        self.name=name
        self.start=start
        self.data=data

def getOpenCLClassFieldsInOrder(clss):
    ## --- https://stackoverflow.com/a/1939279/5166365
    members = [member for member in dir(clss) if (not callable(getattr(clss,member)) and not member.startswith("__"))]
    ## ---
    return members

def createOpenCLClass(clss,constructedMembers = None):
    className = clss.__name__

    ## --- https://stackoverflow.com/a/1939279/5166365
    members = [member for member in dir(clss) if (not callable(getattr(clss,member)) and not member.startswith("__"))]
    ## ---

    tName = lambda obj,member: "float3" if (isinstance(getattr(obj,member),list) or np.array(getattr(obj,member),dtype=float).shape==(3,)) else "float"

    structCode = """
typedef struct tag_{}_t {{
{}
}} {}_t;
    """.format(className,"\n".join(["{} {};".format(tName(clss,member),member) for member in members]),className)


    constructorList = [member for member in members]

    if constructedMembers != None:
        constructorList = list(filter(lambda m: m in constructedMembers,constructorList))

    constructorCode = """
{}_t {}({}){{
{}_t obj;
{}
return obj;
}}
    """.format(
    className,className,
    ",".join(["{} {}".format(tName(clss,member),member) for member in constructorList]),
    className,
    "\n".join(["obj.{}={};".format(member,member) for member in constructorList])
    )

    totalFloats = sum([(3 if tName(clss,member)=="float3" else 1) for member in constructorList])
    adCounter = 0
    ADCalls = {}
    for member in constructorList:
        ADCalls[member] = ""
        if tName(clss,member) == "float":
            ADCalls[member]+="getAD(bankName,index*{}+{})".format(totalFloats,adCounter)
            adCounter+=1
        else:
            ADCalls[member]+="(float3)(getAD(bankName,index*{}+{}),getAD(bankName,index*{}+{}),getAD(bankName,index*{}+{}))".format(totalFloats,adCounter,totalFloats,adCounter+1,totalFloats,adCounter+2)
            adCounter+=3

    getterCode="""
{}_t get{}(int bankName,int index){{

    return {}({});

}}
    """.format(className,className,className,",".join([ADCalls[member] for member in constructorList]))


    return structCode + "\n" + constructorCode + "\n" + getterCode

    
class _SceneCompiler:

    def define_auxillary_function(self,function):
        self.auxillary_functions.append(function)

    def add_preprocessor_define(self,define):
        self.preprocessor_defines.append(define)
    
    def set_samples(self,samples):
        self.samples = samples

    def set_color_pow(self,color_pow):
        self.color_pow = color_pow

    def set_max_bounces(self,MAX_BOUNCES):
        self.MAX_BOUNCES = MAX_BOUNCES
    
    def set_bias(self,BIAS):
        self.BIAS = BIAS

    def set_blur_pixels(self,BLUR_PIXELS):
        self.BLUR_PIXELS=BLUR_PIXELS

    def set_blur_count(self,BLUR_COUNT):
        self.BLUR_COUNT = BLUR_COUNT

    def set_viewport_samples(self,VIEWPORT_SAMPLES):
        self.VIEWPORT_SAMPLES=VIEWPORT_SAMPLES
    
    """Scene Compiler Class -- Singleton Pattern"""
    def __init__(self, **kwargs):
        self.color_pow=1.0
        self.RANDOM_TABLE_SIZE=DEFAULT_RANDOM_TABLE_SIZE
        self.adCounter = 0
        self.ad=[]
        self.samples = 1
        self.auxillary_functions=[]
        self.preprocessor_defines=[]
        self.classes = []
        self.MAX_BOUNCES = 3
        self.BIAS = 0.005
        self.BLUR_PIXELS = 2
        self.BLUR_COUNT = 4
        self.VIEWPORT_SAMPLES = 1

    def add_class(self,clss):
        self.classes.append(clss)

    def set_random_table_size(self,sz):
        self.RANDOM_TABLE_SIZE=sz

    def commit(self):

        print("Loading random number table to arbitrary_data.hex")

        randomTexture = []
        for _ in range(self.RANDOM_TABLE_SIZE):
            randomTexture.append(np.random.uniform())
        self.addArbitraryData("RANDOM_TABLE",randomTexture)
        shuffleTable = list(range(len(randomTexture)))
        np.random.shuffle(shuffleTable)
        self.addArbitraryData("SHUFFLE_TABLE",shuffleTable)

        print("Assembling k1build.cl...")

        ad_definitions = ""
        for chunk in self.ad:
            name=chunk.name
            start=chunk.start
            ad_definitions+=("#define AD_{} {}\n".format(name,start))

                 
        header_cl="""

#define RANDOM_TABLE_SIZE {}
#define SAMPLES {}
#define COLOR_POW {}
#define MAX_BOUNCES {}
#define BIAS {}
#define BLUR_COUNT {}
#define BLUR_PIXELS {}
#define VIEWPORT_SAMPLES {}


#define getAD(name,offset) (arbitrary_data[name+offset])
#define getAS(name,offset) (arbitrary_data[name+offset])

__global float * arbitrary_data;
__global float * application_state;
__global float3 rgt_g;
__global float3 upp_g;
__global float3 fwd_g;
__global float3 camera_g;

{}

{}

{}

{}

        """.format(
            int(self.RANDOM_TABLE_SIZE),int(self.samples),float(self.color_pow),int(self.MAX_BOUNCES),float(self.BIAS),int(self.BLUR_COUNT),int(self.BLUR_PIXELS),int(self.VIEWPORT_SAMPLES),
            ad_definitions,
            "\n".join(self.preprocessor_defines),
            "\n".join(self.auxillary_functions),
            "\n".join([createOpenCLClass(clss) for clss in self.classes])
            )

        Utils.fwrite("k1build.cl",header_cl+"\n"+Utils.fread("k1.cl")+"\n"+self.shaders)

        print("Flushing arbitrary data to file...")

        '''
        dataBuffer = [np.array(0.0,dtype="<f4") for I in range(ARBITRARY_DATA_POINTS)]

        for chunk in self.ad:
            name = chunk.name
            start = chunk.start
            data = chunk.data
            for i,dataPoint in enumerate(data):
                dataBuffer[start+i] = np.array(dataPoint,dtype="<f4")

        with open("data_buffer_size.txt","w") as fl:
            fl.write(str(sum([len(ad.data) for ad in self.ad])))

        with open("arbitrary_data.hex","wb") as fl:
            for item in dataBuffer:
                fl.write(struct.pack("<f",item))
        '''

        with open("data_buffer_size.txt","w") as fl:
            fl.write("{}".format(int(sum([len(chunk.data) for chunk in self.ad]))))

        with open("arbitrary_data.hex","wb") as fl:
            for chunk in self.ad:
                for point in chunk.data:
                    fl.write(struct.pack('<f',point))

        print("Scene compiled successfully.")

    def addArbitraryData(self,name,data):
        start = self.adCounter
        self.adCounter+=len(data)
        if self.adCounter >= ARBITRARY_DATA_POINTS:
            raise Exception(f"Arbitrary data limit exceed. Maximum is {ARBITRARY_DATA_POINTS} data points = {ARBITRARY_DATA_POINTS*4} bytes.");
        self.ad.append(ArbitraryDataChunk(name,start,data))
        
compiler = _SceneCompiler()

def SceneCompiler():
    return compiler

def IntersectionComponent(**kwargs):
    return _IntersectionComponent(compiler,**kwargs)
