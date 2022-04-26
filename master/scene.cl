
        


        

         


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

            
	return T_max(sceneSDF(v),fastBox(v,Vector3d(0.0,0.0,0.0),Vector3d(2.5,2.5,2.5)));


        }
        

        
        double3 shader0 (double3 gv, double3 lv, double3 n){

            return fabs(n);

        }
        

        double3 shader1 (double3 gv, double3 lv, double3 n){

            
        
        double3 n_g = n.x*rgt_g+n.y*upp_g+n.z*fwd_g;

        float L = dot(n_g,(double3)(0.0,0.0,-1.0)); return (double3)(L,L,L);



        

        }
        

        double3 shader2 (double3 gv, double3 lv, double3 n){

            
	return sceneMaterial(gv,lv,n);


        }
        


        float sdf_bank(double3 v, unsigned char shape_id){

            switch(shape_id){

                
case 0: return sd0(v); break;


case 1: return sd1(v); break;


case 2: return sd2(v); break;


case 3: return sd3(v); break;


case 4: return sd4(v); break;


case 5: return sd5(v); break;


            }

            return 0.0;

        }

        double3 shader_bank(double3 gv, double3 lv, double3 n, unsigned char material_id){


            switch(material_id){

                
case 0: return shader0(gv,lv,n); break;


case 1: return shader1(gv,lv,n); break;


case 2: return shader2(gv,lv,n); break;


            }

            return (double3)(1.0, 1.0, 1.0);
        }
        
        
        