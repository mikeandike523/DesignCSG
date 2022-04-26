#define EPSILON_DENOMINATOR_MISS 0.000001
#define clip(c) (c>255?255:(c<0?0:c))
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


__global float * arbitrary_data;
__global float3 rgt_g;
__global float3 upp_g;
__global float3 fwd_g;

//optional float3
typedef struct tag_of3_t{
    float3 hitPoint;
    int hit;
} of3_t;

of3_t of3(float3 hitPoint,int hit){
    of3_t intersection;
    intersection.hitPoint=hitPoint;
    intersection.hit = hit;
    return intersection;
}

of3_t miss(){
    return of3((float3)(0.0,0.0,0.0),0);
}

float3 getTriangleA(int it){
    return (float3)(
    getAD(AD_TRIANGLE_DATA,it*12+0*3+0),
    getAD(AD_TRIANGLE_DATA,it*12+0*3+1),
    getAD(AD_TRIANGLE_DATA,it*12+0*3+2)
    );
}
float3 getTriangleB(int it){
    return (float3)(
    getAD(AD_TRIANGLE_DATA,it*12+1*3+0),
    getAD(AD_TRIANGLE_DATA,it*12+1*3+1),
    getAD(AD_TRIANGLE_DATA,it*12+1*3+2)
    );
}
float3 getTriangleC(int it){
    return (float3)(
    getAD(AD_TRIANGLE_DATA,it*12+2*3+0),
    getAD(AD_TRIANGLE_DATA,it*12+2*3+1),
    getAD(AD_TRIANGLE_DATA,it*12+2*3+2)
    );
}
float3 getTriangleN(int it){
    return (float3)(
    getAD(AD_TRIANGLE_DATA,it*12+3*3+0),
    getAD(AD_TRIANGLE_DATA,it*12+3*3+1),
    getAD(AD_TRIANGLE_DATA,it*12+3*3+2)
    );
}

int getNumTriangles(){
    return (int)getAD(AD_NUM_TRIANGLES,0);    
}

of3_t raycastTriangle(float3 o, float3 r,float3 A, float3 B, float3 C, float3 N ){
    return miss();
}

of3_t raycast(float3 o, float3 r){

    int numTriangles = getNumTriangles();


    float dist = 0.0;
    float3 hitPoint = (float3)(0.0,0.0,0.0);
    int itHit = -1;

    
    for(int it=0;it<numTriangles;it++){
        float3 A = getTriangleA(it);
        float3 B = getTriangleB(it);
        float3 C = getTriangleC(it);
        float3 N = getTriangleN(it);
        of3_t cast= raycastTriangle(o,r,A,B,C,N);
        if(cast.hit!=-1){
            float d = length(cast.hitPoint-o);
            if(itHit==-1||d<dist){
                d=dist;
                itHit = it;
                hitPoint=cast.hitPoint;
            }
        }
    }

    if(itHit!=-1){
        return of3(hitPoint,itHit);
    }

    return miss();


}


                           

__kernel void  k1(

    __global unsigned char * outpixels,
    __global float * campos,
    __global float * right,
    __global float * up, 
    __global float * forward,
    __global float * _arbitrary_data
){

    arbitrary_data = _arbitrary_data;


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



    float3 color = (float3)(1.0,1.0,1.0);

    of3_t intersection = raycast(
        o,r
    );

    if(intersection.hit!=-1){
        float3 n = getTriangleN(intersection.hit);
        color = fabs(n);
    }




  
    outpixels[tid*3+0] = RCOMP(color);
    outpixels[tid*3+1] = GCOMP(color);
    outpixels[tid*3+2] = BCOMP(color);
    
 
}