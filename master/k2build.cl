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

#define getAD(name,offset) (arbitrary_data[name+offset])


#define standard_arg_list shape_id_bank,object_position_bank,object_right_bank,object_up_bank,object_forward_bank,num_objects,build_procedure_data,num_build_steps

 
#define print_double3(f3) printf("%f,%f,%f\n",f3.x,f3.y,f3.z);

#define T_min(a,b) (a<b?a:b)
#define T_max(a,b) (a>b?a:b)


float sdf_bank(double3 v, unsigned char shape_id);
double3 shader_bank(double3 gv, double3 lv, double3 n, unsigned char material_id);


__global double3 rgt_g;
__global double3 upp_g;
__global double3 fwd_g;
__global float * arbitrary_data;



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
    __global const int * num_build_steps_arr,
    __global float * _arbitrary_data

){

   arbitrary_data = _arbitrary_data;

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


        
        #define AD_RANDOM_VALUES 0


        

         


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

double grassblade(double3 v, double3 baseCenter, double3 normal){
	v=v-baseCenter;

	float h = dot(v,normal);
	double3 p = (double3)(h*normal.x,h*normal.y,h*normal.z);

	double3 radialAxis = v-p;
	float rho2 = radialAxis.x*radialAxis.x+radialAxis.y*radialAxis.y+radialAxis.z*radialAxis.z;
	return T_max(rho2-0.000625,T_max(-h,h-0.4));

}


double wave(double x0, double z0,double x, double z, double amplitude){
	float t0 = x- x0;
	float t1 = z - z0;
	float r2 = t0*t0+t1*t1;
	return amplitude*exp(-r2);
}

double getHeight(double3 v){
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

double ground_fn(double3 v){
	return v.y - (-2.4+getHeight(v));
}

NORMAL_FUNCTION(groundNormal,ground_fn)

double sceneSDF(double3 v){
	float d = MAX_DISTANCE;

	int G = 17;
	float D = 5.0/(G-1);
	float trash = 0;
	float xf0 = round(v.x/D)*D;
	float zf0 = round(v.z/D)*D;

	double h = getHeight(v);
	float d1 = v.y - (-2.4+h);

	float d2 = MAX_DISTANCE;
	int S = 1;
	for(int i=-S;i<=S;i++){
			for(int j=-S;j<=S;j++){
				float xf = xf0+D*i;
				float zf = zf0 + D*j;
				double3 grassCenter = Vector3d(xf,-2.4+getHeight(Vector3d(xf,0.0f,zf)),zf);
				float dg = grassblade(v,grassCenter,groundNormal(grassCenter));
				d2 = T_min(d2,dg);

		}

	}


	d=T_min(d,d1);
	d=T_min(d,d2);


	return T_max(d,fastBox(v,Vector3d(0.0,0.0,0.0),Vector3d(2.5,2.5,2.5)));
}

double3 sceneMaterial(double3 gv, double3 lv, double3 n)
{

	return VFABS(n);


}



        