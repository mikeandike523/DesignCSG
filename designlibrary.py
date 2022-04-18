#To make a capsule, we can unscale different dimensions by a value known before building the final object
#This system of unscaling may eventually be baked into the scenecompiler, but will first test it manually before incorporating it

import scenecompiler
import numpy as np


compiler = scenecompiler.SceneCompiler()
sphere_brush = compiler.define_brush(body="return length(v)-0.5;")
cylinder_brush = compiler.define_brush(body="""

    v=fabs(v);
    float x = length((float2)(v.x,v.z));
    float y = v.y;
    return max(x-0.5,y-0.5);

""")

box_brush = compiler.define_brush(body="""
    v=fabs(v);
    return max(v.x-0.5,max(v.y-0.5,v.z-0.5));
""")

define_brush = compiler.define_brush
define_material = compiler.define_material
define_auxillary_function=compiler.define_auxillary_function
add_preprocessor_define = compiler.add_preprocessor_define
Transform = scenecompiler.Transform
Component = scenecompiler.Component
PI=np.pi

def draw(brush, tf):
    compiler.root.add_child(Component(brush=brush, material=compiler.default_material(),transform=tf))

def erase(brush, tf):
    compiler.root.add_child(Component(brush=brush, material=compiler.default_material(),transform=tf,subtractive=True))


def draw_capsule(A,B,T=1):
    M=(A+B)/2
    D=B-A
    d=np.linalg.norm(D)
    cyl = scenecompiler.Component(brush=cylinder_brush,material=compiler.default_material(),transform=scenecompiler.Transform.initial(

        position=np.array([0.0,0.0,0.0]),
        yaw=0,
        pitch=0,
        roll=0,
        scale=np.array([T,d,T])

    ))
    cyl.add_child(scenecompiler.Component(brush=sphere_brush,material=compiler.default_material(),transform=scenecompiler.Transform.initial(


        position=np.array([0.0,0.5,0.0]),
        yaw=0,
        pitch=0,
        roll=0,
        scale=np.array([1,T/d,1])


    )))

    cyl.add_child(scenecompiler.Component(brush=sphere_brush,material=compiler.default_material(),transform=scenecompiler.Transform.initial(


        position=np.array([0.0,-0.5,0.0]),
        yaw=0,
        pitch=0,
        roll=0,
        scale=np.array([1,T/d,1])


    )))



    nD = scenecompiler.Transform.normalized(D)
    a=np.arctan2(nD[2],nD[0])
    b=np.arcsin(nD[1])

    _pitch=b-np.pi/2
    _yaw=np.pi/2-a
    

    compiler.root.add_child(cyl.fabricate(transform=scenecompiler.Transform.initial(


        position=M,
        yaw=_yaw,
        pitch=_pitch,
        roll=0,
        scale=np.array([1.0,1.0,1.0])


    )))

def cut_capsule(A,B,T=1):
    M=(A+B)/2
    D=B-A
    d=np.linalg.norm(D)
    cyl = scenecompiler.Component(brush=cylinder_brush,material=compiler.default_material(),transform=scenecompiler.Transform.initial(

        position=np.array([0.0,0.0,0.0]),
        yaw=0,
        pitch=0,
        roll=0,
        scale=np.array([T,d,T])

    ))
    cyl.add_child(scenecompiler.Component(brush=sphere_brush,material=compiler.default_material(),transform=scenecompiler.Transform.initial(


        position=np.array([0.0,0.5,0.0]),
        yaw=0,
        pitch=0,
        roll=0,
        scale=np.array([1,T/d,1])


    )))

    cyl.add_child(scenecompiler.Component(brush=sphere_brush,material=compiler.default_material(),transform=scenecompiler.Transform.initial(


        position=np.array([0.0,-0.5,0.0]),
        yaw=0,
        pitch=0,
        roll=0,
        scale=np.array([1,T/d,1])


    )))



    nD = scenecompiler.Transform.normalized(D)
    a=np.arctan2(nD[2],nD[0])
    b=np.arcsin(nD[1])

    _pitch=b-np.pi/2
    _yaw=np.pi/2-a
    

    compiler.root.add_child(cyl.fabricate(transform=scenecompiler.Transform.initial(


        position=M,
        yaw=_yaw,
        pitch=_pitch,
        roll=0,
        scale=np.array([1.0,1.0,1.0])


    ),subtractive=True))


def draw_box(origin,diameter):
    compiler.root.add_child(scenecompiler.Component(
        brush = box_brush,
        material=compiler.default_material(),
        transform=scenecompiler.Transform.initial(

            position=origin,
            yaw=0,
            pitch=0,
            roll=0,
            scale=diameter*np.ones((3,),dtype=float)

        )
    ))


def setExportConfig(boundingBoxHalfDiameter,minimumOctreeLevel,maximumOctreeLevel,gridLevel,complexSurfaceThreshold,gradientDescentSteps=10,cacheSubdivision=16):

    with open("exportConfig.txt","w") as fl:

        outstr = ""
        
        outstr+=(str(5.0*boundingBoxHalfDiameter)+"\n")
        outstr+=(str(minimumOctreeLevel)+"\n")
        outstr+=(str(maximumOctreeLevel)+"\n")
        outstr+=(str(gridLevel)+"\n")
        outstr+=(str(complexSurfaceThreshold)+"\n")
        outstr+=(str(gradientDescentSteps)+"\n")
        outstr+=(str(cacheSubdivision)+"\n")

        outstr.strip("\n")
        fl.write(outstr)


def commit():
    compiler.commit()