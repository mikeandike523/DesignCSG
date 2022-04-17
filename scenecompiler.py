import dataclasses
import enum
from os import stat
import numpy as np
import os

INITIAL_SCALE = 1.0

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

class Transform:
    """A wrapper class for common homogenous transformations"""


    #matrices are row major in Numpy

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

    def get_commands(self,allocator: Allocator):
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
                        commands.append(Command("MIN",self.variable,allocator.R0,self.variable))
                else:
                    commands.extend(child.get_commands(allocator))
                    if child.subtractive:
                        commands.append(Command("NEGATE",child.variable,Argument.null(),allocator.R0)) 
                        commands.append(Command("MAX",self.variable,allocator.R0,self.variable))
                    else:
                        commands.append(Command("MIN",self.variable,child.variable,self.variable))
                        

        return commands



    

    




class _SceneCompiler:

    def define_auxillary_function(self,function):
        self.auxillary_functions.append(function)

    def add_preprocessor_define(self,define):
        self.preprocessor_defines.append(define)

    """Scene Compiler Class -- Singleton Pattern"""
    def __init__(self, **kwargs):
        self.brush_counter = Incrementor()
        self.material_counter = Incrementor()
        self.brushes = []
        self.materials = []
        self.empty_brush=self.define_brush(body="return MAX_DISTANCE;")
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

    def default_material(self):
        return self.abs_normals

    def commit(self):

        #compile scene.cl
        scene_cl="""

        {}

        {}

        {}

        {}


        float sdf_bank(double3 v, unsigned char shape_id){{

            switch(shape_id){{

                {}

            }}

            return 0.0;

        }}

        double3 shader_bank(double3 gv, double3 lv, double3 n, unsigned char material_id){{


            switch(material_id){{

                {}

            }}

            return (double3)(1.0, 1.0, 1.0);
        }}
        
        
        """.format(
            "\n".join(self.preprocessor_defines),
            "\n".join(self.auxillary_functions),
            "\n".join([str(b) for b in self.brushes]),
            "\n".join([str(m) for m in self.materials]),
            "\n".join([ "\ncase {}: return sd{}(v); break;\n".format(brush.bank_index,brush.bank_index) for brush in self.brushes]),
            "\n".join([ "\ncase {}: return shader{}(gv,lv,n); break;\n".format(material.bank_index,material.bank_index) for material in self.materials])
        )
        
        Utils.fwrite("scene.cl",scene_cl)

        #unroll components
        unrolled_components = []
        unrolled_components.extend(self.root.get_unrolled_components())
        for index, component in enumerate(unrolled_components):
            component.unrolled_index = index
            component.propogate_transforms()
        
        scene_txt = ""
        for component in unrolled_components:
            brush_index = component.brush.bank_index
            material_index = component.material.bank_index
            position = component.position()
            _up=Transform.reciprocal_vector(component.up())
            _right = Transform.reciprocal_vector(component.right())
            _forward = Transform.reciprocal_vector(component.forward())
            scene_txt+=("{:d} {:d} "+"{:.6f} "*3 + "{:.6f} "*8 + "{:.6f}\n").format(brush_index,material_index,*list(position),*list(_right),*list(_up),*list(_forward))
            
        Utils.fwrite("scene.txt",scene_txt)

        #next step: restore build process

        #step 1: allocate a variable for each object with children
        for component in unrolled_components:
            if len(component.children) > 0:
                component.variable = self.allocator.allocate()

        #capture the root allocation for export
        export_variable = self.root.variable

        #allocate a register to handle more complex operations
        self.allocator.allocate(name="R0")

        #generate commands recursively
        commands = self.root.get_commands(self.allocator)

        commands.append(Command("EXPORT",export_variable,Argument.null(),Argument.null()))

        #print("\n".join([repr(cmd) for cmd in commands]))

        Utils.fwrite("buildprocedure.txt", "\n".join([str(cmd) for cmd in commands]))

        print("Instance tree compiled successfully.")
        
compiler = _SceneCompiler()
def SceneCompiler():
    return compiler
