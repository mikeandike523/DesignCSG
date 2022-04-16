from DesignCSG import *
import numpy as np
from designlibrary import *


add_preprocessor_define(define="""

#define union(a,b) T_min(a,b)
#define intersection(a,b) T_max(a,b)
#define subtraction(a,b) T_max(a,-b)
#define Vector3f(x,y,z) ((float3)((float)x,(float)y,(float)z))
#define signOfInt(i) (i>0?1:(i<0?-1:(0)))

""")

add_preprocessor_define(define="""

#define lineWidth 0.05

""")


define_auxillary_function(function="""

	float max3(float a, float b, float c){

		return T_max(a,T_max(b,c));
	}


	float maxComponent(float3 v){

		return T_max(v.x,T_max(v.y,v.z));
	}

	float box(float3 point, float3 center, float3 halfDiameter ){

		point=fabs(point-center);

		return maxComponent(point-halfDiameter);
		
	}

	float getComponent(float3 v, int component){

		if(component==0) return v.x;
		if(component==1) return v.y;
		if(component==2) return v.z;

		return HUGE_VALF;
	
	}

	float3 termProduct(float3 a, float3 b){

		return Vector3f(a.x*b.x,a.y*b.y,a.z*b.z);
	}

	float3 swizzle(float3 v, int a, int b, int c){
		return Vector3f(getComponent(v,a),getComponent(v,b),getComponent(v,c));
	}



	//Messed up the orientation at first
	float _hilbertUnitCell(float3 v){

		float d1 = box(v,Vector3f(-0.5,-0.5,0.0),Vector3f(lineWidth,lineWidth,0.5));
		float d2 = box(v,Vector3f(0.5,-0.5,0.0),Vector3f(lineWidth,lineWidth,0.5));
		float d3 = box(v,Vector3f(0.0,-0.5,-0.5),Vector3f(0.5,lineWidth,lineWidth));

		float d4 = box(v,Vector3f(-0.5,0.5,0.0),Vector3f(lineWidth,lineWidth,0.5));
		float d5 = box(v,Vector3f(0.5,0.5,0.0),Vector3f(lineWidth,lineWidth,0.5));
		float d6 = box(v,Vector3f(0.0,0.5,-0.5),Vector3f(0.5,lineWidth,lineWidth));

		float d7 = box(v,Vector3f(0.5,0.0,0.5),Vector3f(lineWidth,0.5,lineWidth));

		return union(

			union(

			union(d1,union(d2,d3)),

			union(d4,union(d5,d6))

			),

			d7

		);
	
	}

	//Messed up the orientation at first
	float hilbertUnitCell(float3 v){

		v=termProduct(swizzle(v,1,0,2),Vector3f(1,-1,1));
		v=termProduct(swizzle(v,2,1,0),Vector3f(1,1,-1));
		return _hilbertUnitCell(v);

	}





""")


def vec3(x,y,z):
	return np.array([x,y,z])

scene_brush=define_brush(body=""" 

	float scene_sdf = hilbertUnitCell(v);
	return T_max(scene_sdf, box(v,(float3)(0.0,0.0,0.0),(float3)(0.5,0.5,0.5)));

""")

draw(scene_brush,Transform.initial(
	position=vec3(0.0,0.0,0.0),
	yaw=0,
	pitch=0,
	roll=0,
	scale=vec3(1.0,1.0,1.0)
))



setExportConfig(

	boundingBoxHalfDiameter=10.0,
	minimumOctreeLevel=4,
	maximumOctreeLevel=6,
	gridLevel = 7,
	complexSurfaceThreshold=np.pi/2.0*0.3,
	gradientDescentSteps = 30,
	cacheSubdivision = 16
)

commit()