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
addArbitraryData = compiler.addArbitraryData
def commit(component = None):
    if component is not None:
        compiler.root.brush=component.brush
        compiler.root.material=component.material
        compiler.root.transform=component.intrinsic_transform
        compiler.commit()
    else:
        compiler.commit()
    
define_auxillary_function=compiler.define_auxillary_function
add_preprocessor_define = compiler.add_preprocessor_define
Transform = scenecompiler.Transform
PI=np.pi

def draw(brush, tf):
    compiler.root.add_child(scenecompiler.Component(brush=brush, material=compiler.default_material(),transform=tf))

def erase(brush, tf):
    compiler.root.add_child(scenecompiler.Component(brush=brush, material=compiler.default_material(),transform=tf,subtractive=True))

drawBrush=draw
eraseBrush=erase

def Component(brush,transform=Transform.identity()):
    return scenecompiler.Component(brush=brush,material=compiler.default_material(),transform=transform)

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


def drawComponent(component,transform=Transform.identity()):
    compiler.root.add_child(component.fabricate(transform=transform))
def eraseComponent(component,transform=Transform.identity()):
    compiler.root.add_child(component.fabricate(transform=transform,subtractive=True))
def drawUnion(*components,transform=Transform.identity()):
    root = scenecompiler.Component(brush=compiler.null_brush(),material=compiler.default_material(),transform=transform)
    for component in components:
        root.add_child(component)
    compiler.root.add_child(root)
def eraseUnion(*components,transform=Transform.identity()):
    root = scenecompiler.Component(brush=compiler.null_brush(),material=compiler.default_material(),transform=transform,subtractive=True)
    for component in components:
        root.add_child(component)
    compiler.root.add_child(root)
def drawIntersection(*components,transform=Transform.identity()):
    root = scenecompiler.IntersectionComponent(brush=compiler.null_brush(),material=compiler.default_material(),transform=transform)
    for component in components:
        root.add_child(component)
    compiler.root.add_child(root)
def eraseIntersection(*components,transform=Transform.identity()):
    root = scenecompiler.IntersectionComponent(brush=compiler.null_brush(),material=compiler.default_material(),transform=transform,subtractive=True)
    for component in components:
        root.add_child(component)
    compiler.root.add_child(root)

def setExportConfig(boundingBoxHalfDiameter,
minimumOctreeLevel,
maximumOctreeLevel,
gridLevel,
complexSurfaceThreshold,
gradientDescentSteps=10,
cacheSubdivision=16,
queriesBeforeGC=64,
queriesBeforeFree=1024,
meshSubdivisionLevel=4,
maxPoolSize = 0
):

    meshSubdivisionLevel = 0
    maxPoolSize = 0

    with open("exportConfig.txt","w") as fl:

        outstr = ""
        
        outstr+=(str(5.0*boundingBoxHalfDiameter)+"\n")
        outstr+=(str(minimumOctreeLevel)+"\n")
        outstr+=(str(maximumOctreeLevel)+"\n")
        outstr+=(str(gridLevel)+"\n")
        outstr+=(str(complexSurfaceThreshold)+"\n")
        outstr+=(str(gradientDescentSteps)+"\n")
        outstr+=(str(cacheSubdivision)+"\n")
        outstr+=(str(queriesBeforeGC)+"\n")
        outstr+=(str(queriesBeforeFree)+"\n")


        outstr.strip("\n")
        fl.write(outstr)
