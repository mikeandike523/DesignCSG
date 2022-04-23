
        


        

         


__global int LETTER_AD_OFFS = -1;

#define AXES_XYZ -1
#define AXES_XY 0
#define AXES_YZ 1
#define AXES_ZX 2

#define LETTER_RESOLUTION 64

#define Vector3f(x,y,z) ((float3)(x,y,z))
#define toVector3f(v) (Vector3f(v.x,v.y,v.z))

#define ZERO_WINDING (M_PI/64.0f)
#define SUBSEGMENTS 64

float arg(float x, float y){
	float angle = atan2(y,x);
	if(angle<0.0){
		return 2.0*M_PI+angle;
	}
	return angle;
}

int getADBit(int name, int offs){
	int foffs = offs/16;
	int soffs = offs % 16;
	float fval = getAD(name, foffs);
	int shortval = (int)fval;
	return (shortval  >> (15-soffs) ) & 0x1;
}


float3 scaledVector3f(float s,float3 v) {
	return Vector3f(s*v.x,s*v.y,s*v.z);
}
float box(float3 v){
	
	return T_max(fabs(v.x)-0.5,T_max(fabs(v.y)-0.5,fabs(v.z)-0.5));

}

float box3(float3 v, float3 c, float3 r){
	
	return T_max(fabs(v.x-c.x)-r.x,T_max(fabs(v.y-c.y)-r.y,fabs(v.z-c.z)-r.z));

}



float3 quadraticBezierCurve(float3 A, float3 B, float3 C, float t){
		return scaledVector3f(1.0-t,scaledVector3f(1.0-t,A)+scaledVector3f(t,B)) + scaledVector3f(t,scaledVector3f(1.0-t,B)+scaledVector3f(t,C));


}

float ipow(float f, int n){
	float r = 1.0;
	for(int i=0;i<n;i++){
		r*=f;
	}
	return r;
}

float quadraticBezierSDF(float3 v,float3 A, float3 B, float3 C, float thickness,int axesTag,int N){

	float d = MAX_DISTANCE;

	for(int i=0;i < N;i++){

		float t = (float)i/(float)N;
		float3 p = quadraticBezierCurve(A,B,C,t);
		//assume axesTag = AXES_XY
		p.z=0;
		v.z = 0;

		float dist = length(p-toVector3f(v));

		if(dist<d){
				d = dist;
		}

	}

	int queryCol = (int)(LETTER_RESOLUTION*(v.x+1.0)/2.0);
	int queryRow = LETTER_RESOLUTION-(int)(LETTER_RESOLUTION*(v.y+1.0)/2.0);
	int bitPosition = queryRow*(LETTER_RESOLUTION+1) + queryCol;
	int val = getADBit(LETTER_AD_OFFS,bitPosition);
	if(val){
		return -d;
	}


	
	
	return d-thickness;

}





        
        float sd0( double3 v){

            return MAX_DISTANCE;

        }
        

        float sd1( double3 v){

            return length(v)-0.5;

        }
        

        float sd2( double3 v){

            

    v=fabs(v);
    float x = length((float2)(v.x,v.z));
    float y = v.y;
    return max(x-0.5,y-0.5);



        }
        

        float sd3( double3 v){

            
    v=fabs(v);
    return max(v.x-0.5,max(v.y-0.5,v.z-0.5));


        }
        

        
        double3 shader0 (double3 gv, double3 lv, double3 n){

            return fabs(n);

        }
        

        double3 shader1 (double3 gv, double3 lv, double3 n){

            
        
        double3 n_g = n.x*rgt_g+n.y*upp_g+n.z*fwd_g;

        float L = dot(n_g,(double3)(0.0,0.0,-1.0)); return (double3)(L,L,L);



        

        }
        


        float sdf_bank(double3 v, unsigned char shape_id){

            switch(shape_id){

                
case 0: return sd0(v); break;


case 1: return sd1(v); break;


case 2: return sd2(v); break;


case 3: return sd3(v); break;


            }

            return 0.0;

        }

        double3 shader_bank(double3 gv, double3 lv, double3 n, unsigned char material_id){


            switch(material_id){

                
case 0: return shader0(gv,lv,n); break;


case 1: return shader1(gv,lv,n); break;


            }

            return (double3)(1.0, 1.0, 1.0);
        }
        
        
        