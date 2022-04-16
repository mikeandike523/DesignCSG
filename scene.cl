

        

#define union(a,b) T_min(a,b)
#define intersection(a,b) T_max(a,b)
#define subtraction(a,b) T_max(a,-b)
#define Vector3f(x,y,z) ((float3)((float)x,(float)y,(float)z))
#define signOfInt(i) (i>0?1:(i<0?-1:(0)))




#define lineWidth 0.05



         


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







        
        float sd0( float3 v){

            return MAX_DISTANCE;

        }
        

        float sd1( float3 v){

            return length(v)-0.5;

        }
        

        float sd2( float3 v){

            

    v=fabs(v);
    float x = length((float2)(v.x,v.z));
    float y = v.y;
    return max(x-0.5,y-0.5);



        }
        

        float sd3( float3 v){

            
    v=fabs(v);
    return max(v.x-0.5,max(v.y-0.5,v.z-0.5));


        }
        

        float sd4( float3 v){

            return length(v)-0.5;

        }
        

        float sd5( float3 v){

            

    v=fabs(v);
    float x = length((float2)(v.x,v.z));
    float y = v.y;
    return max(x-0.5,y-0.5);



        }
        

        float sd6( float3 v){

            
    v=fabs(v);
    return max(v.x-0.5,max(v.y-0.5,v.z-0.5));


        }
        

        float sd7( float3 v){

             

	float scene_sdf = hilbertUnitCell(v);
	return T_max(scene_sdf, box(v,(float3)(0.0,0.0,0.0),(float3)(0.5,0.5,0.5)));



        }
        

        
        float3 shader0 (float3 gv, float3 lv, float3 n){

            return fabs(n);

        }
        

        float3 shader1 (float3 gv, float3 lv, float3 n){

            
        
        float3 n_g = n.x*rgt_g+n.y*upp_g+n.z*fwd_g;

        float L = dot(n_g,(float3)(0.0,0.0,-1.0)); return (float3)(L,L,L);



        

        }
        


        float sdf_bank(float3 v, unsigned char shape_id){

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

        float3 shader_bank(float3 gv, float3 lv, float3 n, unsigned char material_id){


            switch(material_id){

                
case 0: return shader0(gv,lv,n); break;


case 1: return shader1(gv,lv,n); break;


            }

            return (float3)(1.0, 1.0, 1.0);
        }
        
        
        