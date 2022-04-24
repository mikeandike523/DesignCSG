
        
#define AD_LETTER_OFFS_C 0
#define AD_NUMCURVES_C 265
#define AD_CURVEDATA_C 266
#define AD_LETTER_OFFS_S 618
#define AD_NUMCURVES_S 883
#define AD_CURVEDATA_S 884
#define AD_LETTER_OFFS_G 1456
#define AD_NUMCURVES_G 1721
#define AD_CURVEDATA_G 1722


        

         


__global int LETTER_AD_OFFS = -1;

#define AXES_XYZ -1
#define AXES_XY 0
#define AXES_YZ 1
#define AXES_ZX 2

#define LETTER_RESOLUTION 64

#define Vector3f(x,y,z) ((float3)(x,y,z))
#define toVector3f(v) (Vector3f(v.x,v.y,v.z))

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
	
	int val = 0 ;
	if(queryCol>=0&&queryCol<=LETTER_RESOLUTION&&queryRow>=0&&queryRow<=LETTER_RESOLUTION)
	{
		val=getADBit(LETTER_AD_OFFS,bitPosition);
	}
	if(val){
		return -d;
	}


	
	
	return d-thickness;

}





        
        float sd0( double3 v){

            return MAX_DISTANCE;

        }
        

        float sd1( double3 v){

            return 0.0;

        }
        

        float sd2( double3 v){

            return length(v)-0.5;

        }
        

        float sd3( double3 v){

            

    v=fabs(v);
    float x = length((float2)(v.x,v.z));
    float y = v.y;
    return max(x-0.5,y-0.5);



        }
        

        float sd4( double3 v){

            
    v=fabs(v);
    return max(v.x-0.5,max(v.y-0.5,v.z-0.5));


        }
        

        float sd5( double3 v){

            

	LETTER_AD_OFFS = AD_LETTER_OFFS_C;

	v=(double3)(2.0*v.x,2.0*v.y,2.0*v.z);

	int numCurves = (int)getAD(AD_NUMCURVES_C,0);
	float d = MAX_DISTANCE;


	for(int i=0;i<numCurves;i++){

		int offs = i*(9+2);
		d = T_min(d,quadraticBezierSDF(toVector3f(v),
			Vector3f(getAD(AD_CURVEDATA_C,offs+0),getAD(AD_CURVEDATA_C,offs+1),getAD(AD_CURVEDATA_C,offs+2)),
			Vector3f(getAD(AD_CURVEDATA_C,offs+3),getAD(AD_CURVEDATA_C,offs+4),getAD(AD_CURVEDATA_C,offs+5)),
			Vector3f(getAD(AD_CURVEDATA_C,offs+6),getAD(AD_CURVEDATA_C,offs+7),getAD(AD_CURVEDATA_C,offs+8)),
			getAD(AD_CURVEDATA_C,offs+9),(int)getAD(AD_CURVEDATA_C,offs+10),SUBSEGMENTS
		));


	}

	return T_max(T_max(d,box3(toVector3f(v),Vector3f(0.0,0.0,0.0),Vector3f(1.25,1.25,1.25))),fabs(v.z-1.25)-0.125);

	

        }
        

        float sd6( double3 v){

            

	LETTER_AD_OFFS = AD_LETTER_OFFS_S;

	v=(double3)(2.0*v.x,2.0*v.y,2.0*v.z);

	int numCurves = (int)getAD(AD_NUMCURVES_S,0);
	float d = MAX_DISTANCE;


	for(int i=0;i<numCurves;i++){

		int offs = i*(9+2);
		d = T_min(d,quadraticBezierSDF(toVector3f(v),
			Vector3f(getAD(AD_CURVEDATA_S,offs+0),getAD(AD_CURVEDATA_S,offs+1),getAD(AD_CURVEDATA_S,offs+2)),
			Vector3f(getAD(AD_CURVEDATA_S,offs+3),getAD(AD_CURVEDATA_S,offs+4),getAD(AD_CURVEDATA_S,offs+5)),
			Vector3f(getAD(AD_CURVEDATA_S,offs+6),getAD(AD_CURVEDATA_S,offs+7),getAD(AD_CURVEDATA_S,offs+8)),
			getAD(AD_CURVEDATA_S,offs+9),(int)getAD(AD_CURVEDATA_S,offs+10),SUBSEGMENTS
		));


	}

	return T_max(T_max(d,box3(toVector3f(v),Vector3f(0.0,0.0,0.0),Vector3f(1.25,1.25,1.25))),fabs(v.z-1.25)-0.125);

	

        }
        

        float sd7( double3 v){

            

	LETTER_AD_OFFS = AD_LETTER_OFFS_G;

	v=(double3)(2.0*v.x,2.0*v.y,2.0*v.z);

	int numCurves = (int)getAD(AD_NUMCURVES_G,0);
	float d = MAX_DISTANCE;


	for(int i=0;i<numCurves;i++){

		int offs = i*(9+2);
		d = T_min(d,quadraticBezierSDF(toVector3f(v),
			Vector3f(getAD(AD_CURVEDATA_G,offs+0),getAD(AD_CURVEDATA_G,offs+1),getAD(AD_CURVEDATA_G,offs+2)),
			Vector3f(getAD(AD_CURVEDATA_G,offs+3),getAD(AD_CURVEDATA_G,offs+4),getAD(AD_CURVEDATA_G,offs+5)),
			Vector3f(getAD(AD_CURVEDATA_G,offs+6),getAD(AD_CURVEDATA_G,offs+7),getAD(AD_CURVEDATA_G,offs+8)),
			getAD(AD_CURVEDATA_G,offs+9),(int)getAD(AD_CURVEDATA_G,offs+10),SUBSEGMENTS
		));


	}

	return T_max(T_max(d,box3(toVector3f(v),Vector3f(0.0,0.0,0.0),Vector3f(1.25,1.25,1.25))),fabs(v.z-1.25)-0.125);

	

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


case 5: return sd5(v); break;


case 6: return sd6(v); break;


case 7: return sd7(v); break;


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
        
        
        