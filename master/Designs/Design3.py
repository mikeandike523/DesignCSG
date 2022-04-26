from DesignCSG import *
from designlibrary import *


define_auxillary_function("""

#define MATERIAL_MATCH (SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL)
#define FABS(a) (a>=0.0?a:-a)
#define VFABS(v) ((double3)(FABS(v.x),FABS(v.y),FABS(v.z)))
#define Vector3d(x,y,z) ((double3)(x,y,z))
#define RGT rgt_g
#define UPP upp_g
#define FWD fwd_g

//https://stackoverflow.com/a/4275343/5166365
float rand(float2 co){
	double i = 0;
    return fract(sin(dot(co, (float2)(12.9898, 78.233))) * 43758.5453,&i);
}

double fastBox(double3 v, double3 center, double3 halfDiameter){
	double3 _v = (double3)(FABS(v.x-center.x),FABS(v.y-center.y),FABS(v.z-center.z));
	double3 q = _v-halfDiameter;
	return T_max(q.x,T_max(q.y,q.z));
}


double wave(double x0, double z0,double x, double z, double amplitude, double angle){
	float t0 = dot((float2)(x-x0,z-z0),(float2)(cos(angle),sin(angle)));
	float t1 = dot((float2)(x-x0,z-z0),(float2)(cos(angle+M_PI/2.0),sin(angle+M_PI/2.0)));
	float r = sqrt(t0*t0+t1*t1);
	return amplitude*exp(-r*r);
}

double sceneSDF(double3 v){

	float h = 0.0;
	for(int i=-5;i<=5;i++){
		for(int j=-5;j<=5;j++){
			float x0 = i/2.0;
			float z0 = j/2.0;
			h+=wave(x0,z0,v.x,v.z,0.25*rand((float2)(x0,z0)),0.0);
		}
	}

	float d1 = v.y - (-2.4+h);
	


	return d1;
}

double3 sceneMaterial(double3 gv, double3 lv, double3 n)
{

	return VFABS(n);
}

""")

sceneBrush = define_brush(body="""
	return T_max(sceneSDF(v),fastBox(v,Vector3d(0.0,0.0,0.0),Vector3d(2.5,2.5,2.5)));
""")

sceneMaterial= define_material(body="""
	return sceneMaterial(gv,lv,n);
""")




drawComponent(scenecompiler.Component(brush=sceneBrush,material=sceneMaterial,transform=Transform.identity()))



commit()
