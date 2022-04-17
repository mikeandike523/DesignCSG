#define MAX_STEPS 4096
#define MAX_DISTANCE 4096.0
#define SDF_EPSILON 0.005
#define NORMAL_EPSILON 0.001
#define TOLERANCE_FACTOR_MARCHSTEP 0.5
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

 
#define print_float3(f3) printf("%f,%f,%f\n",f3.x,f3.y,f3.z);

#define T_min(a,b) (a<b?a:b)
#define T_max(a,b) (a>b?a:b)


float sdf_bank(float3 v, unsigned char shape_id);
float3 shader_bank(float3 gv, float3 lv, float3 n, unsigned char material_id);

__global float3 rgt_g;
__global float3 upp_g;
__global float3 fwd_g;


float primary_sdf(

    float3 v, 
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


    return export_value;
    

}




float3 get_normal(float3 v,

    __global unsigned char * shape_id_bank,
    __global float * object_position_bank,
    __global float * object_right_bank,
    __global float * object_up_bank,
    __global float * object_forward_bank,
    int num_objects,

        
  
    __global int * build_procedure_data,
     int num_build_steps



){

    float3 dx = (float3)(NORMAL_EPSILON,0.0,0.0);
    float3 dy = (float3)(0.0,NORMAL_EPSILON,0.0);
    float3 dz = (float3)(0.0,0.0,NORMAL_EPSILON);

    float Dx = primary_sdf(v+dx, standard_arg_list)-primary_sdf(v-dx, standard_arg_list);
    float Dy = primary_sdf(v+dy, standard_arg_list)-primary_sdf(v-dy, standard_arg_list);
    float Dz = primary_sdf(v+dz, standard_arg_list)-primary_sdf(v-dz, standard_arg_list);

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

        

    __global int * build_procedure_data,
     int num_build_steps,

    float3 rgt,
    float3 upp,
    float3 fwd


){     

    float d = 0.0;
    float3 v = (float3)(dot(o,rgt),dot(o,upp),dot(o,fwd));
    r= (float3)(dot(r,rgt),dot(r,upp),dot(r,fwd));
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


    rgt_g = (float3)(0.0,0.0,0.0);
    upp_g = (float3)(0.0,0.0,0.0);
    fwd_g = (float3)(0.0,0.0,0.0);


    const int num_objects = num_objects_arr[0];
    const int num_build_steps = num_build_steps_arr[0];
    const int point_id = get_global_id(0);
    const int eval_type = eval_types[0];
    const float3 eval_point = (float3)(eval_points[point_id*3+0],eval_points[point_id*3+1],eval_points[point_id*3+2]);


        if(eval_type==EVAL_TYPE_SDF){
            
            eval_out[point_id] = primary_sdf(eval_point,standard_arg_list);
        
        }else{

            float3 n = get_normal(eval_point,standard_arg_list);
            eval_out[point_id*3+0] = n.x;
            eval_out[point_id*3+1] = n.y;
            eval_out[point_id*3+2] = n.z;

        }

    

}

