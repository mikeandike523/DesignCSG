

        

#define union(a,b) T_min(a,b)
#define intersection(a,b) T_max(a,b)
#define subtraction(a,b) T_max(a,-b)
#define Vector3f(x,y,z) ((double3)((double)(x),(double)(y),(double)(z)))
#define signOfInt(i) (i>0?1:(i<0?-1:(0)))
#define upperClampVector3f(v) (Vector3f(T_max(v.x,0.0),T_max(v.y,0.0),T_max(v.z,0.0)))

#define DIRECTION_X 0
#define DIRECTION_Y 1
#define DIRECTION_Z 2




#define lineWidth 0.1



         



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


	float maxComponent(double3 v){

		return T_max(v.x,T_max(v.y,v.z));
	}

	float box(double3 point, double3 center, double3 halfDiameter ){

	
	
		point=fabs(point-center);
		double3 q = point-halfDiameter;


		//courtesy of Inigo Quiles
		//https://iquilezles.org/articles/distfunctions/
		//return length(upperClampVector3f(q))+T_min(0.0,maxComponent(q));

		return maxComponent(q);


		
	}

	float getComponent(double3 v, int component){

		if(component==0) return v.x;
		if(component==1) return v.y;
		if(component==2) return v.z;

		return HUGE_VALF;
	
	}

	double3 termProduct(double3 a, double3 b){

		return Vector3f(a.x*b.x,a.y*b.y,a.z*b.z);
	}

	double3 swizzle(double3 v, int a, int b, int c){
		return Vector3f(getComponent(v,a),getComponent(v,b),getComponent(v,c));
	}



	//Messed up the orientation at first
	float _hilbertUnitCell(double3 v){

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
	float hilbertUnitCell(double3 v){

		v=termProduct(swizzle(v,1,0,2),Vector3f(1,-1,1));
		v=termProduct(swizzle(v,2,1,0),Vector3f(1,1,-1));
		return _hilbertUnitCell(v);

	}


	float putHilbert(double3 v,int x, int y, int z)
	{
		double3 c = Vector3f(x/3.0,y/3.0,z/3.0);
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

		double3 mc0 = Vector3f(m00,m01,m02);
		double3 mc1 = Vector3f(m10,m11,m12);
		double3 mc2 = Vector3f(m20,m21,m22); 

		float A = dot(v,mc0);
		float B = dot(v,mc1);
		float C = dot(v,mc2);

		return hilbertUnitCell(Vector3f(A,B,C));

	}

	float putShaft(double3 v, float halfWidth, float halfLength, int direction){
		float d = MAX_DISTANCE;
		double3 center = Vector3f(0.0,0.0,0.0);
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

	float putConnector(double3 v, int largeI, int largeJ, int largeK, int i, int j, int k, int direction){

		double3 center = Vector3f(

(largeI*1.0+i/2.0)*1/3.0,
(largeJ*1.0+j/2.0)*1/3.0,
(largeK*1.0+k/2.0)*1/3.0

		);

		return putShaft((v-center)*3.0,lineWidth,0.5,direction);

	}

	float putConnectors(double3 v){

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


	float hilbert_sdf(double3 v){


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

             

	return hilbert_sdf(v);



        }
        

        float sd5( double3 v){

            

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
        
        
        