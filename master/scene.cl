
        
        #define AD_NUMCURVES 0
#define AD_CURVEDATA 1


        

         


#define AXES_XYZ -1
#define AXES_XY 0
#define AXES_YZ 1
#define AXES_ZX 2

#define Vector3f(x,y,z) ((float3)(x,y,z))
#define toVector3f(v) (Vector3f(v.x,v.y,v.z))
float3 scaledVector3f(float s,float3 v) {
	return Vector3f(s*v.x,s*v.y,s*v.z);
}
float box(float3 v){
	
	return T_max(fabs(v.x)-0.5,T_max(fabs(v.y)-0.5,fabs(v.z)-0.5));

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

float3 cubicBezierCurve(float3 A, float3 B, float3 C, float3 D, float t){

	return scaledVector3f(ipow(1.0-t,3),A) + scaledVector3f(3*ipow(1.0-t,2)*t,B) + scaledVector3f(3*(1.0-t)*ipow(t,2),C) + scaledVector3f(ipow(t,3),D);

}

float cubicBezierSDF(float3 v, float3 A, float3 B, float3 C, float3 D, float thickness, int axesTag, int N){


	float d = MAX_DISTANCE;

	for(int i=0;i < N;i++){
		float t = (float)i/(float)N;
		float3 p = cubicBezierCurve(A,B,C,D,t);

		switch(axesTag){
			case AXES_XY:
				p.z=0;
				v.z = 0;
			break;
			case AXES_YZ:
				p.x = 0;
				v.x = 0;	
			break;
			case AXES_ZX:
				p.y=0;
				v.y=0;
			break;
			default:
				//Do nothing.
			break;
		}


		float dist = length(p-toVector3f(v));
		if(dist<d){
			d = dist;
		}

	}

	return d-thickness;

}

float quadraticBezierSDF(float3 v,float3 A, float3 B, float3 C, float thickness,int axesTag,int N){

	float d = MAX_DISTANCE;

	for(int i=0;i < N;i++){
		float t = (float)i/(float)N;
		float3 p = quadraticBezierCurve(A,B,C,t);

		switch(axesTag){
			case AXES_XY:
				p.z=0;
				v.z = 0;
			break;
			case AXES_YZ:
				p.x = 0;
				v.x = 0;	
			break;
			case AXES_ZX:
				p.y=0;
				v.y=0;
			break;
			default:
				//Do nothing.
			break;
		}


		float dist = length(p-toVector3f(v));
		if(dist<d){
			d = dist;
		}

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
        

        float sd4( double3 v){

            


int numCurves = (int)getAD(AD_NUMCURVES,0);
float d = MAX_DISTANCE;

for(int i=0;i<numCurves;i++){

	int offs = i*(9+2);
	d = T_min(d,quadraticBezierSDF(toVector3f(v),
		Vector3f(getAD(AD_CURVEDATA,offs+0),getAD(AD_CURVEDATA,offs+1),getAD(AD_CURVEDATA,offs+2)),
		Vector3f(getAD(AD_CURVEDATA,offs+3),getAD(AD_CURVEDATA,offs+4),getAD(AD_CURVEDATA,offs+5)),
		Vector3f(getAD(AD_CURVEDATA,offs+6),getAD(AD_CURVEDATA,offs+7),getAD(AD_CURVEDATA,offs+8)),
		getAD(AD_CURVEDATA,offs+9),(int)getAD(AD_CURVEDATA,offs+10),50
	));

}

return d;




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


case 4: return sd4(v); break;


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
        
        
        