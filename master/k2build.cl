#define MAX_STEPS 512
#define MAX_DISTANCE 64.0
#define SDF_EPSILON 0.005
#define NORMAL_EPSILON 0.005
#define TOLERANCE_FACTOR_MARCHSTEP 0.85
#define TOLERANCE_FACTOR_MATERIAL 2.0
#define RCOMP(c) (clip((int)(255.0*c.x)))
#define GCOMP(c) (clip((int)(255.0*c.y)))
#define BCOMP(c) (clip((int)(255.0*c.z)))
#define IFOV 1.0f

#define IMPORT 0 
#define EXPORT 1 
#define MIN 2
#define MAX 3
#define NEGATE 4
#define IDENTITY 5

#define EVAL_TYPE_SDF 0
#define EVAL_TYPE_NORMAL 1


#define standard_arg_list shape_id_bank,object_position_bank,object_right_bank,object_up_bank,object_forward_bank,num_objects,build_procedure_data,num_build_steps

 
#define print_double3(f3) printf("%f,%f,%f\n",f3.x,f3.y,f3.z);

#define T_min(a,b) (a<b?a:b)
#define T_max(a,b) (a>b?a:b)


float sdf_bank(double3 v, unsigned char shape_id);
double3 shader_bank(double3 gv, double3 lv, double3 n, unsigned char material_id);


__global double3 rgt_g;
__global double3 upp_g;
__global double3 fwd_g;



float primary_sdf(

    double3 v, 
    __global unsigned char * shape_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,


    __global int * build_procedure_data,
     int num_build_steps
 

){


    /*                    
    float min_s = MAX_DISTANCE;

    for(int i=0;i< num_objects;i++){

        unsigned char shape_id = shape_id_bank[i];

        double3 shape_right = (double3)(object_right_bank[i*3+0],object_right_bank[i*3+1],object_right_bank[i*3+2]);
        double3 shape_up = (double3)(object_up_bank[i*3+0],object_up_bank[i*3+1],object_up_bank[i*3+2]);
        double3 shape_forward = (double3)(object_forward_bank[i*3+0],object_forward_bank[i*3+1],object_forward_bank[i*3+2]);
        double3 o = (double3)(object_position_bank[i*3+0],object_position_bank[i*3+1],object_position_bank[i*3+2]);

        double3 ABC = (double3)(dot(v-o,shape_right),dot(v-o,shape_up),dot(v-o,shape_forward));

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
                        double3 shape_right = (double3)(object_right_bank[i*3+0],object_right_bank[i*3+1],object_right_bank[i*3+2]);
                        double3 shape_up = (double3)(object_up_bank[i*3+0],object_up_bank[i*3+1],object_up_bank[i*3+2]);
                        double3 shape_forward = (double3)(object_forward_bank[i*3+0],object_forward_bank[i*3+1],object_forward_bank[i*3+2]);
                        double3 o = (double3)(object_position_bank[i*3+0],object_position_bank[i*3+1],object_position_bank[i*3+2]);
                        double3 ABC = (double3)(dot(v-o,shape_right),dot(v-o,shape_up),dot(v-o,shape_forward));
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


    return export_value;
    

}




double3 get_normal(double3 v,

    __global unsigned char * shape_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,

        
  
    __global int * build_procedure_data,
     int num_build_steps



){

    double3 dx = (double3)(NORMAL_EPSILON,0.0,0.0);
    double3 dy = (double3)(0.0,NORMAL_EPSILON,0.0);
    double3 dz = (double3)(0.0,0.0,NORMAL_EPSILON);

    float Dx = primary_sdf(v+dx, standard_arg_list)-primary_sdf(v-dx, standard_arg_list);
    float Dy = primary_sdf(v+dy, standard_arg_list)-primary_sdf(v-dy, standard_arg_list);
    float Dz = primary_sdf(v+dz, standard_arg_list)-primary_sdf(v-dz, standard_arg_list);

    float  twoE = 2.0*NORMAL_EPSILON;

    return normalize((double3)(1.0/twoE*Dx,1.0/twoE*Dy,1.0/twoE*Dz));

}

float march(double3 o, double3 r,

    __global unsigned char * shape_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,

        

    __global int * build_procedure_data,
     int num_build_steps,

    double3 rgt,
    double3 upp,
    double3 fwd


){     

    float d = 0.0;
    double3 v = (double3)(dot(o,rgt),dot(o,upp),dot(o,fwd));
    r= (double3)(dot(r,rgt),dot(r,upp),dot(r,fwd));
    for(int i=0;i<MAX_STEPS;i++){

        float s = primary_sdf(v,standard_arg_list)*TOLERANCE_FACTOR_MARCHSTEP; 

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


__kernel void  k2(

    __global float * eval_points,
    __global float * eval_out,
    __global const int * eval_types,
    __global const unsigned char * shape_id_bank,
    __global const float * object_position_bank,
    __global const float * object_right_bank,
    __global const float * object_up_bank,
    __global const float * object_forward_bank,
    __global const int * num_objects_arr,
    __global const int * build_procedure_data,
    __global const int * num_build_steps_arr

){


    rgt_g = (double3)(0.0,0.0,0.0);
    upp_g = (double3)(0.0,0.0,0.0);
    fwd_g = (double3)(0.0,0.0,0.0);


    const int num_objects = num_objects_arr[0];
    const int num_build_steps = num_build_steps_arr[0];
    const int point_id = get_global_id(0);
    const int eval_type = eval_types[0];
    const double3 eval_point = (double3)(eval_points[point_id*3+0],eval_points[point_id*3+1],eval_points[point_id*3+2]);


        if(eval_type==EVAL_TYPE_SDF){
            
            eval_out[point_id] = primary_sdf(eval_point,standard_arg_list);
        
        }else{

            double3 n = get_normal(eval_point,standard_arg_list);
            eval_out[point_id*3+0] = n.x;
            eval_out[point_id*3+1] = n.y;
            eval_out[point_id*3+2] = n.z;

        }

    

}


        
        #define AD_LETTERBITS 0
#define AD_NUMCURVES 4129
#define AD_CURVEDATA 4130


        

         


#define AXES_XYZ -1
#define AXES_XY 0
#define AXES_YZ 1
#define AXES_ZX 2

#define LETTER_RESOLUTION 256

#define Vector3f(x,y,z) ((float3)(x,y,z))
#define toVector3f(v) (Vector3f(v.x,v.y,v.z))

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

	if(axesTag!=AXES_XY)
		return d-thickness;

	int queryCol = (int)(LETTER_RESOLUTION*(v.x+1.0)/2.0);
	int queryRow = LETTER_RESOLUTION-(int)(LETTER_RESOLUTION*(v.y+1.0)/2.0);
	int bitPosition = queryRow*(LETTER_RESOLUTION+1) + queryCol;
	int val = getADBit(AD_LETTERBITS,bitPosition);
	if(val)
	d*=-1.0;

	
	return d;

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
		getAD(AD_CURVEDATA,offs+9),(int)getAD(AD_CURVEDATA,offs+10),256
	));


}

return T_max(d,box3(toVector3f(v),Vector3f(0.0,0.0,0.0),Vector3f(1.0,1.0,1.0)));



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
        
        
        