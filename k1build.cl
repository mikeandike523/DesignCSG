#define MAX_STEPS 128
#define MAX_DISTANCE 64.0
#define SDF_EPSILON 0.001
#define NORMAL_EPSILON 0.005
#define TOLERANCE_FACTOR_MARCHSTEP 0.5
#define TOLERANCE_FACTOR_MATERIAL 2.0
#define RCOMP(c) (clip((int)(255.0*c.x)))
#define GCOMP(c) (clip((int)(255.0*c.y)))
#define BCOMP(c) (clip((int)(255.0*c.z)))
#define IFOV 1.0f
#define INITIAL_SCALE 5.0

#define IMPORT 0 
#define EXPORT 1 
#define MIN 2
#define MAX 3
#define NEGATE 4
#define IDENTITY 5

#define wargs shape_id_bank,object_position_bank,object_right_bank,object_up_bank,object_forward_bank,num_objects
#define bsargs screen_stack_memory,build_procedure_data,num_build_steps,tid
 
#define print_float3(f3) printf("%f,%f,%f\n",f3.x,f3.y,f3.z);

#define T_min(a,b) (a<b?a:b)
#define T_max(a,b) (a>b?a:b)


float sdf_bank(float3 v, unsigned char shape_id);
float3 shader_bank(float3 gv, float3 lv, float3 n, unsigned char material_id);

__global float3 rgt_g;
__global float3 upp_g;
__global float3 fwd_g;


float axes_cylinderSDF(float r, float h, float halfLength, float radius){
    return T_max((fabs(h)-halfLength),r-radius);
}


void matmul(float * A, float * B, float * AB){

    for(int i=0;i<3;i++){ //row
        for(int j=0;j<3;j++){ //col
            float total = 0.0;
            for(int k=0;k<3;k++){
                total+=A[i*3+j+k]*B[(i+k)*3+j];
            }
            AB[i*3+j] = total;
        }   
    
    }

}

float innerProduct(float * v1, float * v2){
   return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2];
}

void outerProduct(float * v1, float * v2, float * v1v2){
     for(int i=0;i<3;i++){ //row
        for(int j=0;j<3;j++){ //col

        v1v2[i*3+j] = v1[i]*v2[j];
   

        }   
    
    }
}

void mscale(float s, float * A){
     for(int i=0;i<3;i++){ //row
        for(int j=0;j<3;j++){ //col

        A[i*3+j]*=s;
   

        }   
    
    }
}

void msub(float * A, float * B){
    for(int i=0;i<3;i++){ //row
        for(int j=0;j<3;j++){ //col

        A[i*3+j]-=B[i*3+j];
   

        }   
    }
    
}


void eye(float * I){
    for(int i=0;i<3;i++){ //row
        for(int j=0;j<3;j++){ //col

        if(i==j){
            I[i*3+j] = 1.0;
        }else{
            I[i*3+j] = 0.0;
        }
   

        }   
    
    }
}


void rodrigues(float * v1, float * v2, float * v1v2){


    outerProduct(v1,v2,v1v2);

    mscale(2.0/innerProduct(v1,v2),v1v2);

    float I[9];

    eye(I);

    msub(v1v2,I);

}


float primary_sdf(

    float3 v, 
    __global unsigned char * shape_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,

    __global  float * uscreen_stack_memory,
    __global int * build_procedure_data,
     int num_build_steps,
    int tid

){


    /*                    
    float min_s = MAX_DISTANCE;

    for(int i=0;i< num_objects;i++){

        unsigned char shape_id = shape_id_bank[i];

        float3 shape_right = (float3)(object_right_bank[i*3+0],object_right_bank[i*3+1],object_right_bank[i*3+2]);
        float3 shape_up = (float3)(object_up_bank[i*3+0],object_up_bank[i*3+1],object_up_bank[i*3+2]);
        float3 shape_forward = (float3)(object_forward_bank[i*3+0],object_forward_bank[i*3+1],object_forward_bank[i*3+2]);
        float3 o = (float3)(object_position_bank[i*3+0],object_position_bank[i*3+1],object_position_bank[i*3+2]);

        float3 ABC = (float3)(dot(v-o,shape_right),dot(v-o,shape_up),dot(v-o,shape_forward));

        float s  = sdf_bank(ABC,shape_id);


        if(s<min_s){
            min_s = s;
        }

    }




    return min_s;
    */

    __private float screen_stack_memory[STACK_MEMORY_PER_PIXEL];
    
    float export_value = MAX_DISTANCE;
    //int stack_offset = tid * STACK_MEMORY_PER_PIXEL;
    int stack_offset = 0;
    for(int command_number = 0; command_number < num_build_steps; command_number++){

        int command_opcode = build_procedure_data[command_number*4+0];
        int command_left_argument = build_procedure_data[command_number*4+1];
        int command_right_argument = build_procedure_data[command_number*4+2];
        int command_destination = build_procedure_data[command_number*4+3];
        int i = command_right_argument;

        switch(command_opcode){

            case IMPORT:
                    {
                        float3 shape_right = (float3)(object_right_bank[i*3+0],object_right_bank[i*3+1],object_right_bank[i*3+2]);
                        float3 shape_up = (float3)(object_up_bank[i*3+0],object_up_bank[i*3+1],object_up_bank[i*3+2]);
                        float3 shape_forward = (float3)(object_forward_bank[i*3+0],object_forward_bank[i*3+1],object_forward_bank[i*3+2]);
                        float3 o = (float3)(object_position_bank[i*3+0],object_position_bank[i*3+1],object_position_bank[i*3+2]);
                        float3 ABC = (float3)(dot(v-o,shape_right),dot(v-o,shape_up),dot(v-o,shape_forward));
                        screen_stack_memory[stack_offset+command_destination]=sdf_bank(ABC,command_left_argument);
                    }
            break;

            case EXPORT:
                export_value = screen_stack_memory[stack_offset+command_left_argument];
            break;

            case MIN:
                screen_stack_memory[stack_offset+command_destination] = T_min(screen_stack_memory[stack_offset+command_left_argument],screen_stack_memory[stack_offset+command_right_argument]);
            break;

            case MAX:
                screen_stack_memory[stack_offset+command_destination] = T_max(screen_stack_memory[stack_offset+command_left_argument],screen_stack_memory[stack_offset+command_right_argument]);
            break;

            case NEGATE:
                screen_stack_memory[stack_offset+command_destination] = -screen_stack_memory[stack_offset+command_left_argument];
            break;

            case IDENTITY:
                screen_stack_memory[stack_offset+command_destination] = screen_stack_memory[stack_offset+command_left_argument];
            break;

        }

    }


        //x axis
        {
            
            float r = sqrt(v.y*v.y+v.z*v.z);
            float h = v.x-0.5;
            export_value=T_min(export_value,axes_cylinderSDF(r, h, 0.5, 0.025));
        
        
        }

         //y axis
        {
            
            float r = sqrt(v.x*v.x+v.z*v.z);
            float h = v.y-0.5;
            export_value=T_min(export_value,axes_cylinderSDF(r, h, 0.5, 0.025));
        
        
        }


          //z axis
        {
            
            float r = sqrt(v.x*v.x+v.y*v.y);
            float h = v.z-0.5;
            export_value=T_min(export_value,axes_cylinderSDF(r, h, 0.5, 0.025));
        
        
        }




    return export_value;
    

}

float3 shade(

    float3 v, 
    float3 n,
    __global unsigned char * shape_id_bank,
    __global unsigned char * material_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,

        
    __global float * screen_stack_memory,
    __global int * build_procedure_data,
     int num_build_steps,
    int tid

){

  //  v=(float3)(v.x/INITIAL_SCALE,v.y/INITIAL_SCALE,v.z/INITIAL_SCALE);

    float min_s = MAX_DISTANCE;
    int material_match =  -1;
    float3 ABC_out = (float3)(0.0,0.0,0.0);

    for(int i=0;i< num_objects;i++){

        unsigned char shape_id = shape_id_bank[i];

        float3 o = (float3)(object_position_bank[i*3+0],object_position_bank[i*3+1],object_position_bank[i*3+2]);
        float3 shape_right = (float3)(object_right_bank[i*3+0],object_right_bank[i*3+1],object_right_bank[i*3+2]);
        float3 shape_up = (float3)(object_up_bank[i*3+0],object_up_bank[i*3+1],object_up_bank[i*3+2]);
        float3 shape_forward = (float3)(object_forward_bank[i*3+0],object_forward_bank[i*3+1],object_forward_bank[i*3+2]);

        float3 ABC = (float3)(dot(v-o,shape_right),dot(v-o,shape_up),dot(v-o,shape_forward));

        float s  = sdf_bank(ABC,shape_id);

        if(s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            material_match = i;
            ABC_out = ABC;
        }

    }

    if(material_match!=-1)
        return shader_bank(v,ABC_out,n, material_id_bank[material_match]);
    else{
    
           //x axis
        {
            
            float r = sqrt(v.y*v.y+v.z*v.z);
            float h = v.x-0.5;
            float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
            if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
                return (float3)(1.0, 0.0, 0.0);
            }
        
        }

         //y axis
        {
            
            float r = sqrt(v.x*v.x+v.z*v.z);
            float h = v.y-0.5;
            float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
            if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
                return (float3)(0.0, 1.0, 0.0);
            }
        
        }


          //z axis
        {
            
            float r = sqrt(v.x*v.x+v.y*v.y);
            float h = v.z-0.5;
		float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
            
            if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
                return (float3)(0.0, 0.0, 1.0);
            }
        
        
        }
    
    }
    
    return (float3)(239.0/255.0, 66.0/255.0, 245/255.0);

}

float3 get_normal(float3 v,

    __global unsigned char * shape_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,

        
    __global float * screen_stack_memory,
    __global int * build_procedure_data,
     int num_build_steps,
    int tid


){

    float3 dx = (float3)(NORMAL_EPSILON,0.0,0.0);
    float3 dy = (float3)(0.0,NORMAL_EPSILON,0.0);
    float3 dz = (float3)(0.0,0.0,NORMAL_EPSILON);

    float Dx = primary_sdf(v+dx, wargs, bsargs)-primary_sdf(v-dx, wargs, bsargs);
    float Dy = primary_sdf(v+dy, wargs, bsargs)-primary_sdf(v-dy, wargs, bsargs);
    float Dz = primary_sdf(v+dz, wargs, bsargs)-primary_sdf(v-dz, wargs, bsargs);

    float  twoE = 2.0*NORMAL_EPSILON;

    return normalize((float3)(1.0/twoE*Dx,1.0/twoE*Dy,1.0/twoE*Dz));

}

float march(float3 o, float3 r,

    __global unsigned char * shape_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,

        
    __global float * screen_stack_memory,
    __global int * build_procedure_data,
     int num_build_steps,
    int tid,
    float3 rgt,
    float3 upp,
    float3 fwd


){     

    float d = 0.0;
    float3 v = (float3)(dot(o,rgt),dot(o,upp),dot(o,fwd));

  //  v=(float3)(v.x/INITIAL_SCALE,v.y/INITIAL_SCALE,v.z/INITIAL_SCALE);


    r= (float3)(dot(r,rgt),dot(r,upp),dot(r,fwd));
    for(int i=0;i<MAX_STEPS;i++){

        float s = primary_sdf(v,wargs, bsargs)*TOLERANCE_FACTOR_MARCHSTEP; 

        if(s<SDF_EPSILON){
            return d;
        } 

        v=v+s*r; 
        d=d+s;
        
        if(d>MAX_DISTANCE){
            return -1.0;
        }

    }

    return -1.0;                          
}
                    
unsigned char clip(int value){

    value = (value < 0) ? 0 : ((value>255) ? 255:value);

    return (unsigned char)(value);

}                           

__kernel void  k1(

    __global unsigned char * outpixels,
    __global float * campos,
    __global float * right,
    __global float * up, 
    __global float * forward,
    __global unsigned char * shape_id_bank,
    __global unsigned char * material_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    __global int * num_objects_arr,
    __global float * screen_stack_memory,
    __global int * build_procedure_data,
    __global int * num_build_steps_arr
){

     int num_objects = num_objects_arr[0];
     int num_build_steps = num_build_steps_arr[0];
    //printf("%d\n",num_build_steps);

    int ix = get_global_id(0);
    int iy = get_global_id(1);

    int tid = iy*640+ix;


    float3 o = (float3)(campos[0],campos[1],campos[2]);

    float2 uv = (float2)((float)(ix-640/2),-(float)(iy-480/2))/(float2)(640.0/2.0,640.0/2.0);

    float3 rgt = (float3)(right[0],right[1],right[2]);
    float3 upp = (float3)(up[0],up[1],up[2]);
    float3 fwd = (float3)(forward[0],forward[1],forward[2]);

    rgt_g = rgt;
    upp_g = upp;
    fwd_g = fwd;



    float3 r = (float3)(uv.x,uv.y,IFOV);

    //float3 color = (float3)(uv.x,uv.y,1.0);

    float3 color = (float3)(1.0,1.0,1.0);

    
    float d = march(

        o,r,

        shape_id_bank,
        object_position_bank,
        object_right_bank,
        object_up_bank,
        object_forward_bank,
        num_objects,
        bsargs,
        rgt,
        upp,
        fwd

    );

    if(d>0.0){
        
        float3 p = (float3)(dot(o,rgt),dot(o,upp),dot(o,fwd))+d*(float3)(dot(r,rgt),dot(r,upp),dot(r,fwd));
        color = shade(
            
        p,get_normal(p, wargs, bsargs),
        
        shape_id_bank,
        material_id_bank,
        object_position_bank,
        object_right_bank,
        object_up_bank,
        object_forward_bank,
        num_objects,

        bsargs
                    
        );

    }


  
    outpixels[tid*3+0] = RCOMP(color);
    outpixels[tid*3+1] = GCOMP(color);
    outpixels[tid*3+2] = BCOMP(color);
    
 
}

        

#define union(a,b) T_min(a,b)
#define intersection(a,b) T_max(a,b)
#define subtraction(a,b) T_max(a,-b)
#define Vector3f(x,y,z) ((float3)((float)(x),(float)(y),(float)(z)))
#define signOfInt(i) (i>0?1:(i<0?-1:(0)))




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
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,


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
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,
1,0,0, 0,1,0, 0,0,1,

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


	float scene_sdf(float3 v){


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
	
		return m;
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

             

	return scene_sdf(v);



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
        
        
        