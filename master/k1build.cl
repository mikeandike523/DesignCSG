#define MAX_STEPS 4096
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
 
#define print_float3(f3) printf("%f,%f,%f\n",f3.x,f3.y,f3.z);

#define T_min(a,b) (a<b?a:b)
#define T_max(a,b) (a>b?a:b)

#define getAD(name,offset) (arbitrary_data[name+offset])


float sdf_bank(float3 v, unsigned char shape_id);
float3 shader_bank(float3 gv, float3 lv, float3 n, unsigned char material_id);
float sceneSDF(float3 v);
float3 sceneMaterial(float3 gv, float3 lv, float3 n);

__global float3 rgt_g;
__global float3 upp_g;
__global float3 fwd_g;
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


  


    return sceneSDF(v);
    

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


    

    float3 v2 = (float3)(v.x/5.0,v.y/5.0,v.z/5.0);
    
        //x axis
    {
            
        float r = sqrt(v2.y*v2.y+v2.z*v2.z);
        float h = v2.x-0.5;
        float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
        if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
            return (float3)(1.0, 0.0, 0.0);
        }
        
    }

        //y axis
    {
            
        float r = sqrt(v2.x*v2.x+v2.z*v2.z);
        float h = v2.y-0.5;
        float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
        if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
            return (float3)(0.0, 1.0, 0.0);
        }
        
    }


        //z axis
    {
            
        float r = sqrt(v2.x*v2.x+v2.y*v2.y);
        float h = v2.z-0.5;
	float axes_s=axes_cylinderSDF(r, h, 0.5, 0.025);
            
        if(axes_s<SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL){
            
            return (float3)(0.0, 0.0, 1.0);
        }
        
        
    }
    

    float3 lv = v;
    float3 gv = v.x*rgt_g + v.y*upp_g+v.z*fwd_g;

    return sceneMaterial(gv,lv,n);

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

#define NORMAL_FUNCTION(name,functor) float3 name(float3 v){ \
    float3 dx = (float3)(NORMAL_EPSILON,0.0,0.0); \
    float3 dy = (float3)(0.0,NORMAL_EPSILON,0.0); \
    float3 dz = (float3)(0.0,0.0,NORMAL_EPSILON); \
 \
    float Dx = functor(v+dx)-functor(v-dx); \
    float Dy = functor(v+dy)-functor(v-dy); \
    float Dz = functor(v+dz)-functor(v-dz); \
 \
    float  twoE = 2.0*NORMAL_EPSILON; \
 \
    return normalize((float3)(1.0/twoE*Dx,1.0/twoE*Dy,1.0/twoE*Dz)); \
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


    float3 o = (float3)(campos[0],campos[1],campos[2]);

    //o=(float3)(o.x/5.0,o.y/5.0,o.z/5.0); 

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
        
        #define AD_RANDOM_VALUES 0


        

         
#define Vector3f(x,y,z) ((float3)(x,y,z))

typedef struct tag_mat3_t{
    float3 v0;
    float3 v1;
    float3 v2;
} mat3_t;

mat3_t mat3(float3 v0, float3 v1, float3 v2){
    mat3_t mat;
    mat.v0=v0;
    mat.v1=v1;
    mat.v2=v2;
    return mat;
}


float3 fastcross(float3 a, float3 b){
    float3 c = Vector3f(0.0,0.0,0.0);
    c.x = a.y*b.z-a.z*b.y;
    c.y = -(a.x*b.z-a.z*b.x);
    c.z = a.x*b.y-a.y*b.x;
    return c;

}






#define MATERIAL_MATCH (SDF_EPSILON*TOLERANCE_FACTOR_MATERIAL)
#define FABS(a) (a>=0.0?a:-a)
#define VFABS(v) ((float3)(FABS(v.x),FABS(v.y),FABS(v.z)))
#define Vector3f(x,y,z) ((float3)(x,y,z))
#define RGT rgt_g
#define UPP upp_g
#define FWD fwd_g

//https://stackoverflow.com/a/4275343/5166365
float rand(float2 co){
	float i = 0;
    return fract(sin(dot(co, (float2)(12.9898, 78.233))) * 43758.5453,&i);
}

float fastBox(float3 v, float3 center, float3 halfDiameter){
	float3 _v = (float3)(FABS(v.x-center.x),FABS(v.y-center.y),FABS(v.z-center.z));
	float3 q = _v-halfDiameter;
	return T_max(q.x,T_max(q.y,q.z));
}

float grassblade(float3 v, float3 baseCenter, float3 normal,float3 gradient){
	float3 upV =normal;
	float3  rightV = gradient;
	float3 fwdV = -fastcross(normal,gradient);



	v=v-baseCenter;

	float t0 = dot(v,rightV);
	float t1 = dot(v,upV);
	float t2 = dot(v,fwdV);

	float L = 0.4;

	return fastBox(Vector3f(t0,t1,t2),Vector3f(0.0,L/2.0,0.0),Vector3f(0.025,L/2.0,0.0025));

}


float wave(float x0, float z0,float x, float z, float amplitude){
	float t0 = x- x0;
	float t1 = z - z0;
	float r2 = t0*t0+t1*t1;
	return amplitude*exp(-r2);
}

float getHeight(float3 v){
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

float ground_fn(float3 v){
	return v.y - (-2.4+getHeight(v));
}

NORMAL_FUNCTION(groundNormal,ground_fn)

float3 groundGradient(float3 v,float epsilon){
	float hx1 = ground_fn(Vector3f(v.x-epsilon,v.y,v.z));
	float hx2 = ground_fn(Vector3f(v.x+epsilon,v.y,v.z));
	float hz1 = ground_fn(Vector3f(v.x,v.y,v.z-epsilon));
	float hz2 = ground_fn(Vector3f(v.x,v.y,v.z-epsilon));
	return normalize(Vector3f((hx2-hx1)/(2.0*epsilon),0.0,(hz2-hz1)/(2.0*epsilon)));
}

float sceneSDF(float3 v){
	float d = MAX_DISTANCE;

	int G = 17;
	float D = 5.0/(G-1);
	float trash = 0;
	float xf0 = round(v.x/D)*D;
	float zf0 = round(v.z/D)*D;

	float h = getHeight(v);
	float d1 = v.y - (-2.4+h);

	float d2 = MAX_DISTANCE;
	int S = 1;
	for(int i=-S;i<=S;i++){
			for(int j=-S;j<=S;j++){
				float xf = xf0+D*i;
				float zf = zf0 + D*j;
				float3 grassCenter = Vector3f(xf,-2.4+getHeight(Vector3f(xf,0.0f,zf)),zf);
				float dg = grassblade(v,grassCenter,groundNormal(grassCenter),groundGradient(grassCenter,NORMAL_EPSILON));
				d2 = T_min(d2,dg);

		}

	}


	d=T_min(d,d1);
	d=T_min(d,d2);


	return T_max(d,fastBox(v,Vector3f(0.0,0.0,0.0),Vector3f(2.5,2.5,2.5)));
}

float3 sceneMaterial(float3 gv, float3 lv, float3 n)
{

	return VFABS(n);


}



        