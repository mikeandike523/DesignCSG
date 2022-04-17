from DesignCSG import *
import numpy as np
from designlibrary import *


add_preprocessor_define(define="""

#define union(a,b) T_min(a,b)
#define intersection(a,b) T_max(a,b)
#define subtraction(a,b) T_max(a,-b)
#define Vector3f(x,y,z) ((float3)((float)(x),(float)(y),(float)(z)))
#define signOfInt(i) (i>0?1:(i<0?-1:(0)))

#define DIRECTION_X 0
#define DIRECTION_Y 1
#define DIRECTION_Z 2

""")

add_preprocessor_define(define="""

#define lineWidth 0.1

""")


#front = +z
#top = +y
#right side = +x


define_auxillary_function(function="""


//front->+x
//top->+z
//right side -> +y


//front -> -z
//top -> -y
//right side -> -x or +x

	__constant float quadrantMatrices[27*9] = {


//x=-1
0,1,0, 0,0,1, 1,0,0, //check
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,-1,0, 0,0,-1, //check
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
0,0,1, 1,0,0, 0,1,0, // z = -1, front-> +y, top->+x or -x, right-> +z  //check
1,0,0, 0,1,0, 0,0,1,
0,0,1, 1,0,0, 0,1,0, // z = 1 //check


//x=0
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,


//x=1
0,1,0, 0,0,1, -1,0,0, //check
1,0,0, 0,1,0, 0,0,1,
-1,0,0, 0,-1,0, 0,0,-1, //check
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
0,0,-1, -1,0,0, 0,1,0,  // z = -1 //check
1,0,0, 0,1,0, 0,0,1,
0,0,-1, -1,0,0, 0,1,0,  //z = 1 //check

	};

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

		float d1 = box(v,Vector3f(-0.5,-0.5,0.0),Vector3f(lineWidth,lineWidth,0.5+lineWidth));
		float d2 = box(v,Vector3f(0.5,-0.5,0.0),Vector3f(lineWidth,lineWidth,0.5+lineWidth));
		float d3 = box(v,Vector3f(0.0,-0.5,-0.5),Vector3f(0.5+lineWidth,lineWidth,lineWidth));

		float d4 = box(v,Vector3f(-0.5,0.5,0.0),Vector3f(lineWidth,lineWidth,0.5+lineWidth));
		float d5 = box(v,Vector3f(0.5,0.5,0.0),Vector3f(lineWidth,lineWidth,0.5+lineWidth));
		float d6 = box(v,Vector3f(0.0,0.5,-0.5),Vector3f(0.5+lineWidth,lineWidth,lineWidth));

		float d7 = box(v,Vector3f(0.5,0.0,0.5),Vector3f(lineWidth,0.5+lineWidth,lineWidth));

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


	float putHilbert(float3 v,int x, int y, int z)
	{
		float3 c = Vector3f(x/3.0,y/3.0,z/3.0);
		v=Vector3f(v.x-c.x,v.y-c.y,v.z-c.z);
		v=Vector3f(3.0*v.x,3.0*v.y,3.0*v.z);

		int xp1 = x+1;
		int yp1= y+1;
		int zp1 = z+1;
		int matrixOffset = (xp1*9+yp1*3+zp1)*9;

		float m00=quadrantMatrices[matrixOffset+0];
		float m01=quadrantMatrices[matrixOffset+1];
		float m02=quadrantMatrices[matrixOffset+2];

		float m10=quadrantMatrices[matrixOffset+3];
		float m11=quadrantMatrices[matrixOffset+4];
		float m12=quadrantMatrices[matrixOffset+5];

		float m20=quadrantMatrices[matrixOffset+6];
		float m21=quadrantMatrices[matrixOffset+7];
		float m22=quadrantMatrices[matrixOffset+8];

		float3 mc0 = Vector3f(m00,m01,m02);
		float3 mc1 = Vector3f(m10,m11,m12);
		float3 mc2 = Vector3f(m20,m21,m22); 

		float A = dot(v,mc0);
		float B = dot(v,mc1);
		float C = dot(v,mc2);

		return hilbertUnitCell(Vector3f(A,B,C));

	}

	float putShaft(float3 v, float3 center, float halfWidth, float halfLength, int direction){
		float d = MAX_DISTANCE;
		switch(direction){
			case DIRECTION_X:

				d=box(v,center,Vector3f(halfLength+halfWidth,halfWidth,halfWidth));
			break;
			case DIRECTION_Y: 

				d=box(v,center,Vector3f(halfWidth,halfLength+halfWidth,halfWidth));
			break;
			case DIRECTION_Z:

				d=box(v,center,Vector3f(halfWidth,halfWidth,halfLength+halfWidth));
			break;

		}
		return d;
	}

	float putConnector(float3 v, int largeI, int largeJ, int largeK, int i, int j, int k, int direction){

		float3 center = Vector3f(

(largeI*1.0+i/2.0)*1/3.0,
(largeJ*1.0+j/2.0)*1/3.0,
(largeK*1.0+k/2.0)*1/3.0

		);

		return putShaft(v,center,lineWidth/3.0,1.0/6.0,direction);

	}

	float putConnectors(float3 v){

		float d = MAX_DISTANCE;
		d=union(d,putConnector(v,0,-1,1,0,1,1,DIRECTION_X));

		d=union(d,putConnector(v,1,0,-1,1,0,-1,DIRECTION_Y));
		d=union(d,putConnector(v,-1,0,-1,-1,0,-1,DIRECTION_Y));
		
		d=union(d,putConnector(v,1,0,1,1,0,1,DIRECTION_Y));
		d=union(d,putConnector(v,-1,0,1,-1,0,1,DIRECTION_Y));
		
		d=union(d,putConnector(v,1,1,0,1,-1,0,DIRECTION_Z));
		d=union(d,putConnector(v,-1,1,0,-1,-1,0,DIRECTION_Z));

		return d;

	}


	float hilbert_sdf(float3 v){


		//return hilbertUnitCell(v);
		
		float m = MAX_DISTANCE;
		for(int i=-1;i<=1;i++)
		for(int j=-1;j<=1;j++)
		for(int k=-1;k<=1;k++)
		{
			if(abs(i)+abs(j)+abs(k)!=3) continue;
			float d = putHilbert(v,i,j,k);
			if ( d < m)
			{
				m=d;
			}
		}
	
		return T_min(m,putConnectors(v));
	}

""")


def vec3(x,y,z):
	return np.array([x,y,z])

hilbert_brush=define_brush(body=""" 

	return hilbert_sdf(v);

""")

base_brush=define_brush(body="""

	const float outerRadius = 0.5;
	const float innerRadius = 0.45;
	const float height = 0.05;

	float r = sqrt(v.x*v.x+v.z*v.z);
	float d = r-outerRadius;
	if(v.y>0){
		float newRadius = innerRadius+(outerRadius-innerRadius)*(1.0-v.y/height);
		d=r-newRadius;
	}

	return intersection(d,fabs(v.y)-height);
	

""")

draw(hilbert_brush,Transform.initial(
	position=vec3(0.0,0.0,0.0),
	yaw=np.pi/4,
	pitch=np.pi/4,
	roll=np.pi/4,
	scale=vec3(1.0,1.0,1.0)
))


dy=-0.0075

draw(base_brush,Transform.initial(
	position=vec3(0.0,-np.sqrt(3*0.25)-dy,0.0),
	yaw=0.0,
	pitch=0.0,
	roll=0.0,
	scale=vec3(1.0,1.0,1.0)
))




setExportConfig(

	boundingBoxHalfDiameter=10.0,
	minimumOctreeLevel=6,
	maximumOctreeLevel=9,
	gridLevel = 9,
	complexSurfaceThreshold=np.pi/2.0*0.3,
	gradientDescentSteps = 30,
	cacheSubdivision = 32
)

commit()