import dataclasses
from dataclasses import dataclass
import enum
from os import stat
import numpy as np
import os
from typing import List
import struct

INITIAL_SCALE = 5.0
ARBITRARY_DATA_POINTS=131072

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

class ArgumentType(enum.Enum):
    IMMEDIATE = enum.auto()
    ALLOCATION = enum.auto()

@dataclasses.dataclass
class Argument:
        """A dataclass to describe a static memory location, register, or immediate
        
        In the case of ArgumentType IMMEDIATE, the address represents any arbitrary value
        """
        type: ArgumentType
        address: int

        @staticmethod
        def null():
            return Argument(type=ArgumentType.IMMEDIATE,address=-1)

        @staticmethod
        def immediate(v):
            return Argument(type=ArgumentType.IMMEDIATE,address=v)

class Command:
    """A class to store a single scene build instruction
    
    This is one of the few classes that will use positional arguments in init
    """

    def __init__(self,command_code : str, left_argument: Argument, right_argument: Argument, destination: Argument):
        self.command_code = command_code
        self.left_argument = left_argument
        self.right_argument = right_argument
        self.destination = destination

    def __repr__(self):
        return "{} {} {} {}".format(self.command_code, self.left_argument.address,self.right_argument.address,self.destination.address)

    def __str__(self):
        return "{} {} {} {}".format(COMMAND_VALUES[self.command_code], self.left_argument.address,self.right_argument.address,self.destination.address)



class Incrementor:
    """A class to hold one incrementing value"""

    def __init__(self):
        self._count = 0
    
    def count(self):
        return self._count
    
    def preincremented(self):
        self._count +=1
        return self._count

    def postincremented(self):
        self._count +=1
        return self._count-1

class Allocator:
    """A class to simulate memory management in OpenCL"""

    def __init__(self):
        self.next_free_address = Incrementor()
        self.allocations = {}

    def allocate(self, **kwargs):

        argument = Argument(type = ArgumentType.ALLOCATION, address=self.next_free_address.postincremented())
    
        name="ALLOC_{}".format(argument.address)

        if "name" in kwargs:
            name=kwargs["name"]
            
        self.allocations[name] = argument
        
        setattr(self,name,argument)

        return argument
        


class Brush:
    """A class to hold the code for an SDF"""

    def __init__(self, **kwargs):
        self.body = kwargs["body"]
        self.bank_index = kwargs["bank_index"]

    def __str__(self):
        return """
        float sd{}( double3 v){{

            {}

        }}
        """.format(self.bank_index,self.body)


class Material:
    """A class to hold the code for a material"""

    def __init__(self, **kwargs):
        self.body = kwargs["body"]
        self.bank_index = kwargs["bank_index"]

    def __str__(self):
        return """
        double3 shader{} (double3 gv, double3 lv, double3 n){{

            {}

        }}
        """.format(self.bank_index,self.body)


class Component:
    """A class for GameObjects and Prefabs
    Any object can be treated as a prefab, and GameObjects are objects added to the compiler root
    Homogenous transformations are used
    We will ignore scaling for now, but later, the inverse relationship between scaled coordinates
    in raymarching and scaled coordinates in the compilation stage will need to be solved.
    """

    def __init__(self, **kwargs):

        self.brush = kwargs["brush"]
        self.material = kwargs["material"]

        self.intrinsic_transform = np.identity(4)
        if "transform" in kwargs:
            self.intrinsic_transform = kwargs["transform"]

        self.subtractive = False
        if "subtractive" in kwargs:
            self.subtractive = kwargs["subtractive"]

        self.inherited_transform = np.identity(4)
        self.propogated_transform = np.identity(4)

        self.children = []
        self.parent = None


    def add_child(self, child):
        self.children.append(child)
        self.children[-1].parent = self

    def fabricate(self,**kwargs):
        sub=self.subtractive
        if "subtractive" in kwargs:
            sub=kwargs["subtractive"]
        instance=Component(brush=self.brush,material=self.material,transform=matmul(kwargs["transform"],self.intrinsic_transform),subtractive=sub)

        for child in self.children:
            instance.add_child(child=child.fabricate(transform=np.identity(4)))
        return instance

    def propogate_transforms(self):
        #traverse linked list in reverse order
        self.propogated_transform = self.intrinsic_transform
        current = self
        while current.parent is not None:
            current=current.parent
            self.propogated_transform = matmul(current.intrinsic_transform,self.propogated_transform)

    def apply_transform(self,tf):
        self.intrinsic_transform=matmul(tf,self.intrinsic_transform)


    def position(self):
        return Transform.from_homogenous(matmul(self.propogated_transform,Transform.to_homogenous(np.array([0.0,0.0,0.0]))))
    

    def right(self):
        propogated_X=Transform.from_homogenous(self.propogated_transform.T[0,0:3].squeeze())
        norm_propogated_X=Transform.normalized(propogated_X)
        intrinsic_X=Transform.from_homogenous(self.intrinsic_transform.T[0,0:3].squeeze())
        d=np.linalg.norm(intrinsic_X)


        return propogated_X

    def up(self):
        propogated_Y=Transform.from_homogenous(self.propogated_transform.T[1,0:3].squeeze())
        norm_propogated_Y=Transform.normalized(propogated_Y)
        intrinsic_Y=Transform.from_homogenous(self.intrinsic_transform.T[1,0:3].squeeze())
        d=np.linalg.norm(intrinsic_Y)

  
        return propogated_Y

    def forward(self):
        propogated_Z=Transform.from_homogenous(self.propogated_transform.T[2,0:3].squeeze())
        norm_propogated_Z=Transform.normalized(propogated_Z)
        intrinsic_Z=Transform.from_homogenous(self.intrinsic_transform.T[2,0:3].squeeze())
        d=np.linalg.norm(intrinsic_Z)

   
        return propogated_Z

    def get_unrolled_components(self):
        components = []
        components.append(self)
        for child in self.children:
            components.extend(child.get_unrolled_components())
        return components

    def get_commands(self,allocator: Allocator,joinMode="MIN"):
        """Function to compile build-instructions recursively
        
        Parent's own shape is always additive to its children
        If the parent is SUBTRACTIVE, this applies to it calculation with its own parent

        A parent will handle its own direct children, so "leaf nodes" can be ignored
        """


        commands = []

        if len(self.children) > 0:

            #add parent shape
            commands.append(Command("IMPORT",Argument.immediate(self.brush.bank_index),Argument.immediate(self.unrolled_index),self.variable))

            for child in self.children:
                if len(child.children) == 0:
                    commands.append(Command("IMPORT",Argument.immediate(child.brush.bank_index),Argument.immediate(child.unrolled_index),allocator.R0))
                    if child.subtractive:
                        commands.append(Command("NEGATE",allocator.R0,Argument.null(),allocator.R0)) 
                        commands.append(Command("MAX",self.variable,allocator.R0,self.variable))
                    else:
                        commands.append(Command(joinMode,self.variable,allocator.R0,self.variable))
                else:
                    commands.extend(child.get_commands(allocator))
                    if child.subtractive:
                        commands.append(Command("NEGATE",child.variable,Argument.null(),allocator.R0)) 
                        commands.append(Command("MAX",self.variable,allocator.R0,self.variable))
                    else:
                        commands.append(Command(joinMode,self.variable,child.variable,self.variable))
                        

        return commands

class _IntersectionComponent(Component):
    def get_commands(self,allocator: Allocator):
        return super().get_commands(allocator,"MAX")
    def __init__(self,compiler,**kwargs):
        del kwargs["brush"]
        super().__init__(brush=compiler.void_brush(),**kwargs)
    

class ArbitraryDataChunk:


    def __init__(self,name,start,data):
        self.name=name
        self.start=start
        self.data=data
    



class _SceneCompiler:

    def define_auxillary_function(self,function):
        self.auxillary_functions.append(function)

    def add_preprocessor_define(self,define):
        self.preprocessor_defines.append(define)

    """Scene Compiler Class -- Singleton Pattern"""
    def __init__(self, **kwargs):
        self.adCounter = 0
        self.ad=[]
        self.brush_counter = Incrementor()
        self.material_counter = Incrementor()
        self.brushes = []
        self.materials = []
        self.empty_brush=self.define_brush(body="return MAX_DISTANCE;")
        self.space_brush = self.define_brush(body = "return 0.0;")
        self.abs_normals=self.define_material(body = "return fabs(n);")
        self.basic_lighting = self.define_material(body = """
        
        double3 n_g = n.x*rgt_g+n.y*upp_g+n.z*fwd_g;

        float L = dot(n_g,(double3)(0.0,0.0,-1.0)); return (double3)(L,L,L);



        """)
        self.root = Component(brush=self.null_brush(),material=self.default_material(),transform=Transform.scaling(np.array([INITIAL_SCALE,INITIAL_SCALE,INITIAL_SCALE])))
        self.allocator = Allocator()
        self.auxillary_functions=[
            """ """



        ]
        self.preprocessor_defines=[


        ]

    def define_brush(self,**kwargs):
        self.brushes.append(Brush(body=kwargs["body"], bank_index = self.brush_counter.postincremented()))
        return self.brushes[-1]

    def define_material(self,**kwargs):
        self.materials.append(Material(body=kwargs["body"], bank_index = self.material_counter.postincremented()))
        return self.materials[-1]

    def null_brush(self):
        return self.empty_brush

    def void_brush(self):
        return self.space_brush

    def default_material(self):
        return self.basic_lighting

    def commit(self):


        ad_definitions = ""
        for chunk in self.ad:
            name=chunk.name
            start=chunk.start
            ad_definitions+=("#define AD_{} {}\n".format(name,start))

        #compile scene.cl


        header_cl="""
        
{}

{}

{}

        """.format(
            ad_definitions,
            "\n".join(self.preprocessor_defines),
            "\n".join(self.auxillary_functions),
            )
        

        Utils.fwrite("k1build.cl",header_cl+Utils.fread("k1.cl"))

        dataBuffer = [np.array(0.0,dtype="<f4") for I in range(ARBITRARY_DATA_POINTS)]

        for chunk in self.ad:
            name = chunk.name
            start = chunk.start
            data = chunk.data
            for i,dataPoint in enumerate(data):
                dataBuffer[start+i] = np.array(dataPoint,dtype="<f4")

        with open("arbitrary_data.hex","wb") as fl:
            for item in dataBuffer:
                fl.write(item.tobytes())

        print("Instance tree compiled successfully.")

    def addArbitraryData(self,name,data):
        start = self.adCounter
        self.adCounter+=len(data)
        self.ad.append(ArbitraryDataChunk(name,start,data))
        
        
compiler = _SceneCompiler()
def SceneCompiler():
    return compiler
def IntersectionComponent(**kwargs):
    return _IntersectionComponent(compiler,**kwargs)
