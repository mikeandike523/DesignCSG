#define MAX_STEPS 512
#define MAX_DISTANCE 64.0
#define SDF_EPSILON 0.005
#define NORMAL_EPSILON 0.005
#define AXES_RADIUS 0.015
#define TOLERANCE_FACTOR_MARCHSTEP 0.85
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
 
#define print_double3(f3) printf("%f,%f,%f\n",f3.x,f3.y,f3.z);

#define T_min(a,b) (a<b?a:b)
#define T_max(a,b) (a>b?a:b)

#define getAD(name,offset) (arbitrary_data[name+offset])


float sdf_bank(double3 v, unsigned char shape_id);
double3 shader_bank(double3 gv, double3 lv, double3 n, unsigned char material_id);
double sceneSDF(double3 v);
double3 sceneMaterial(double3 gv, double3 lv, double3 n);

__global double3 rgt_g;
__global double3 upp_g;
__global double3 fwd_g;
__global float * arbitrary_data;


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

    double3 v, 
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


  


    return sceneSDF(v);
    

}

double3 shade(

    double3 v, 
    double3 n,
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


    

    double3 v2 = (double3)(v.x/5.0,v.y/5.0,v.z/5.0);
    
        //x axis
    {
            
        float r = sqrt(v2.y*v2.y+v2.z*v2.z);
        float h = v2.x-0.5;
        float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
        if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
            return (double3)(1.0, 0.0, 0.0);
        }
        
    }

        //y axis
    {
            
        float r = sqrt(v2.x*v2.x+v2.z*v2.z);
        float h = v2.y-0.5;
        float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
        if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
            return (double3)(0.0, 1.0, 0.0);
        }
        
    }


        //z axis
    {
            
        float r = sqrt(v2.x*v2.x+v2.y*v2.y);
        float h = v2.z-0.5;
	float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
            
        if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
            return (double3)(0.0, 0.0, 1.0);
        }
        
        
    }
    

    double3 lv = v;
    double3 gv = v.x*rgt_g + v.y*upp_g+v.z*fwd_g;

    return sceneMaterial(gv,lv,n);

}

double3 get_normal(double3 v,

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

    double3 dx = (double3)(NORMAL_EPSILON,0.0,0.0);
    double3 dy = (double3)(0.0,NORMAL_EPSILON,0.0);
    double3 dz = (double3)(0.0,0.0,NORMAL_EPSILON);

    float Dx = primary_sdf(v+dx, wargs, bsargs)-primary_sdf(v-dx, wargs, bsargs);
    float Dy = primary_sdf(v+dy, wargs, bsargs)-primary_sdf(v-dy, wargs, bsargs);
    float Dz = primary_sdf(v+dz, wargs, bsargs)-primary_sdf(v-dz, wargs, bsargs);

    float  twoE = 2.0*NORMAL_EPSILON;

    return normalize((double3)(1.0/twoE*Dx,1.0/twoE*Dy,1.0/twoE*Dz));

}

#define NORMAL_FUNCTION(name,functor) double3 name(double3 v){ \
    double3 dx = (double3)(NORMAL_EPSILON,0.0,0.0); \
    double3 dy = (double3)(0.0,NORMAL_EPSILON,0.0); \
    double3 dz = (double3)(0.0,0.0,NORMAL_EPSILON); \
 \
    float Dx = functor(v+dx)-functor(v-dx); \
    float Dy = functor(v+dy)-functor(v-dy); \
    float Dz = functor(v+dz)-functor(v-dz); \
 \
    float  twoE = 2.0*NORMAL_EPSILON; \
 \
    return normalize((double3)(1.0/twoE*Dx,1.0/twoE*Dy,1.0/twoE*Dz)); \
} 


float march(double3 o, double3 r,

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
    double3 rgt,
    double3 upp,
    double3 fwd


){    


    

    float d = 0.0;
    double3 v = (double3)(dot(o,rgt),dot(o,upp),dot(o,fwd));


    r= (double3)(dot(r,rgt),dot(r,upp),dot(r,fwd));



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
    __global int * num_build_steps_arr,
    __global float * _arbitrary_data
){

    arbitrary_data = _arbitrary_data;

     int num_objects = num_objects_arr[0];
     int num_build_steps = num_build_steps_arr[0];
    //printf("%d\n",num_build_steps);

    int ix = get_global_id(0);
    int iy = get_global_id(1);

    int tid = iy*640+ix;


    double3 o = (double3)(campos[0],campos[1],campos[2]);

    //o=(double3)(o.x/5.0,o.y/5.0,o.z/5.0); 

    float2 uv = (float2)((float)(ix-640/2),-(float)(iy-480/2))/(float2)(640.0/2.0,640.0/2.0);

    double3 rgt = (double3)(right[0],right[1],right[2]);
    double3 upp = (double3)(up[0],up[1],up[2]);
    double3 fwd = (double3)(forward[0],forward[1],forward[2]);

    rgt_g = rgt;
    upp_g = upp;
    fwd_g = fwd;



    double3 r = (double3)(uv.x,uv.y,IFOV);

    //double3 color = (double3)(uv.x,uv.y,1.0);

    double3 color = (double3)(1.0,1.0,1.0);

    
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
        
        double3 p = (double3)(dot(o,rgt),dot(o,upp),dot(o,fwd))+d*(double3)(dot(r,rgt),dot(r,upp),dot(r,fwd));
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
	float rho = length(radialAxis);
	return T_max(rho-0.05,T_max(-h,h-0.4));

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

	int G = 31;
	float D = 5.0/(G-1);
	float xf = (float)((int)(v.x/D))*D;
	float zf = (float)((int)(v.z/D))*D;

	double h = getHeight(v);
	float d1 = v.y - (-2.4+h);

	double3 grassCenter = Vector3d(xf,-2.4+h,zf);
	float d2 = grassblade(v,grassCenter,groundNormal(grassCenter));

	d=T_min(d,d1);
	d=T_min(d,d2);


	return T_max(d,fastBox(v,Vector3d(0.0,0.0,0.0),Vector3d(2.5,2.5,2.5)));
}

double3 sceneMaterial(double3 gv, double3 lv, double3 n)
{

	return VFABS(n);


}



        