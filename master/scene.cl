
        
        #define AD_RANDOM_VALUES 0


        

         


#define MATERIAL_MATCH (SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL)
#define FABS(a) (a>=0.0?a:-a)
#define VFABS(v) ((float3)(FABS(v.x),FABS(v.y),FABS(v.z)))
#define Vector3f(x,y,z) ((float3)(x,y,z))
#define RGT rgt_g
#define UPP upp_g
#define FWD fwd_g

//https://stackoverflow.com/a/4275343/5166365
float rand(float2 co){
	float i = 0;
    return fract(sin(dot(co, (float2)(12.9898, 78.233))) * 43758.5453,&i);
}

float fastBox(float3 v, float3 center, float3 halfDiameter){
	float3 _v = (float3)(FABS(v.x-center.x),FABS(v.y-center.y),FABS(v.z-center.z));
	float3 q = _v-halfDiameter;
	return T_max(q.x,T_max(q.y,q.z));
}

float grassblade(float3 v, float3 baseCenter, float3 normal){
	v=v-baseCenter;

	float h = dot(v,normal);
	float3 p = (float3)(h*normal.x,h*normal.y,h*normal.z);

	float3 radialAxis = v-p;
	float rho2 = radialAxis.x*radialAxis.x+radialAxis.y*radialAxis.y+radialAxis.z*radialAxis.z;
	return T_max(rho2-0.000625,T_max(-h,h-0.4));

}


float wave(float x0, float z0,float x, float z, float amplitude){
	float t0 = x- x0;
	float t1 = z - z0;
	float r2 = t0*t0+t1*t1;
	return amplitude*exp(-r2);
}

float getHeight(float3 v){
	int N = 5;
	float h = 0.0;
	int ct = 0;
	for(int i=-N;i<=N;i++){
		for(int j=-N;j<=N;j++){
			float x0 = i*2.5/N;
			float z0 = j*2.5/N;
			float r = getAD(AD_RANDOM_VALUES,ct++);
			h+=wave(x0,z0,v.x,v.z,0.25*r);
		}
	}
	return h;
}

float ground_fn(float3 v){
	return v.y - (-2.4+getHeight(v));
}

NORMAL_FUNCTION(groundNormal,ground_fn)

float sceneSDF(float3 v){
	float d = MAX_DISTANCE;

	int G = 17;
	float D = 5.0/(G-1);
	float trash = 0;
	float xf0 = round(v.x/D)*D;
	float zf0 = round(v.z/D)*D;

	float h = getHeight(v);
	float d1 = v.y - (-2.4+h);

	float d2 = MAX_DISTANCE;
	int S = 1;
	for(int i=-S;i<=S;i++){
			for(int j=-S;j<=S;j++){
				float xf = xf0+D*i;
				float zf = zf0 + D*j;
				float3 grassCenter = Vector3f(xf,-2.4+getHeight(Vector3f(xf,0.0f,zf)),zf);
				float dg = grassblade(v,grassCenter,groundNormal(grassCenter));
				d2 = T_min(d2,dg);

		}

	}


	d=T_min(d,d1);
	d=T_min(d,d2);


	return T_max(d,fastBox(v,Vector3f(0.0,0.0,0.0),Vector3f(2.5,2.5,2.5)));
}

float3 sceneMaterial(float3 gv, float3 lv, float3 n)
{

	return VFABS(n);


}



        