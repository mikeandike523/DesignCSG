#define APPLICATION_STATE_TIME_MILLISECONDS 0
#define nowMillis() (getAS(APPLICATION_STATE_TIME_MILLISECONDS,0))

#define EPSILON_DENOMINATOR_MISS 0.000001
#define EPSILON_INTERSECTION_TOLERANCE 0.001
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

#define Vector3f(x,y,z) ((float3)(x,y,z))

#define f2f3(f) Vector3f(f,f,f)

float angleZeroToTwoPi(float x, float y){

    float a = atan2(y,x);
    if(a<0.0){
        a = 2.0*M_PI+a;
    }
    return a;

}

float3 termProduct(float3 a,float3 b){

    return Vector3f(a.x*b.x,a.y*b.y,a.z*b.z);

}

float3 fragment(float3 gv, int it, int * rand_counter_p, int * bounces_p);
Triangle3f_t vertex(Triangle3f_t tr, int it);

float rand(int * counter){
	float r = getAD(AD_RANDOM_TABLE,*counter);
	(*counter) = ((*counter)+1)%RANDOM_TABLE_SIZE;
	return r;
}

float randCoord(int * counter){
	return -1.0+rand(counter)*2.0;
}

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

    return of3((float3)(0.0,0.0,0.0),-1);

}

float3 toGlobal(float3 lcl){

	return lcl.x*rgt_g+lcl.y*upp_g+lcl.z*fwd_g;

}
float3 toLocal(float3 glbl){

	return Vector3f(dot(glbl,rgt_g),dot(glbl,upp_g),dot(glbl,fwd_g));

}


float3 adjust(float3 v){

    return v.x*rgt_g+v.y*upp_g+v.z*fwd_g;

}


int getNumTriangles(int bankName){

    return (int)getAD(bankName,0);  

}

float scalarProject(float3 subject, float3 base){

    float3 n = base/length(base);
    return dot(subject,n);

}

int signum(float f){

    if(f==0.0) return 0;
    if(f>0.0) return 1;
    return -1;

}

of3_t raycastTriangle(float3 o, float3 r,float3 A, float3 B, float3 C, float3 N ){

    float3 offset=A-o;
    float3 AB = B-A;
    float3 BC = C-B;
    float3 CA = A-C;

    float rDotN = dot(r,N);

    if(fabs(rDotN)<EPSILON_DENOMINATOR_MISS){
        return miss();
    }

    float t = dot(offset,N)/dot(r,N);

    if(t<-EPSILON_INTERSECTION_TOLERANCE){
        return miss();
    }

    float3 intersectionPoint =o+t*r;
    float3 P1 = intersectionPoint - A;
    float3 P2 = intersectionPoint - B;
    float3 P3 = intersectionPoint - C;

    int insideAB = 0;
    int insideBC = 0;
    int insideCA = 0;

    float3 orthogonalC = (C-A)-vectorProjection(C-A,AB);
    float3 orthogonalA = (A-B)-vectorProjection(A-B,BC);
    float3 orthogonalB = (B-C)-vectorProjection(B-C,CA);

    insideAB = dot(P1,orthogonalC) >= 0.0 ? 1 : 0;
    insideBC = dot(P2,orthogonalA) >= 0.0 ? 1 : 0;
    insideCA = dot(P3,orthogonalB) >= 0.0 ? 1 : 0;

    if(insideAB+insideBC+insideCA!=3){
        return miss();
    }

    of3_t of= of3(intersectionPoint,0);
    return of;
    
}

of3_t raycast(float3 o, float3 r, int numBankName, int bankName){

    int numTriangles = getNumTriangles(numBankName);

    float dist = 0.0;
    float3 hitPoint = (float3)(0.0,0.0,0.0);
    int itHit = -1;
    of3_t ret;

    for(int it=0;it<numTriangles;it++){

        Triangle3f_t tr = getTriangle3f(bankName,it);

        tr.A=toGlobal(tr.A);
        tr.B=toGlobal(tr.B);
        tr.C=toGlobal(tr.C);
        tr.N=toGlobal(tr.N);

        tr=vertex(tr,it);

        of3_t cast= raycastTriangle(o,r,tr.A,tr.B,tr.C,tr.N);
        if(cast.hit!=-1){
            float d = length(cast.hitPoint-o); //global hitpoint
            if(itHit==-1||d<dist){
                dist=d;
                itHit = it;
                hitPoint=cast.hitPoint; //global hitpoint
            }
        }

    }

    if(itHit!=-1){

        ret.hitPoint = hitPoint;
        ret.hit= itHit;
        return ret;

    }

    return miss();

}

float3 skybox(float3 ray);

__kernel void  k1(

    __global unsigned char * outpixels,
    __global float * campos,
    __global float * right,
    __global float * up, 
    __global float * forward,
    __global float * _arbitrary_data,
    __global float * _application_state

){

    arbitrary_data = _arbitrary_data;
    application_state = _application_state;
    
    int ix = get_global_id(0);
    int iy = get_global_id(1);

    int tid = iy*640+ix;

    int rand_counter = ((int)getAD(AD_SHUFFLE_TABLE,(tid+(int)getAD(AD_SHUFFLE_TABLE,(int)_application_state[1]))%RANDOM_TABLE_SIZE))%RANDOM_TABLE_SIZE;                    

    float3 o = (float3)(campos[0],campos[1],campos[2]);
    camera_g = o;

    float2 uv = (float2)((float)(ix-640/2),-(float)(iy-480/2))/(float2)(640.0/2.0,640.0/2.0);

    float3 rgt = (float3)(right[0],right[1],right[2]);
    float3 upp = (float3)(up[0],up[1],up[2]);
    float3 fwd = (float3)(forward[0],forward[1],forward[2]);

    rgt_g = rgt;
    upp_g = upp;
    fwd_g = fwd;

    float3 r = (float3)(uv.x,uv.y,IFOV);

    float3 color = (float3)(1.0,1.0,1.0);
    float3 totalColor = (float3)(0.0,0.0,0.0);



    float blurRadius = BLUR_PIXELS*1.0/480.0;
    float3 br = r;

    int samplesTaken = 0;

    int hasHit = 0;


    for(int bc=0;bc<BLUR_COUNT;bc++){

        r= br + termProduct(Vector3f(randCoord(&rand_counter),randCoord(&rand_counter),0.0),Vector3f(blurRadius,blurRadius,0.0));

        int hits = 0;
        int bounces = 0; //represents one less than the true number of bounces

        //for(int i=0;i<SAMPLES;i++){

            of3_t intersection = raycast(
                o,r,AD_NUM_TRIANGLES,AD_TRIANGLE_DATA
            );

            samplesTaken++;

            if(intersection.hit!=-1){
                hasHit = 1;
                int bounces = 0;

                totalColor += fragment(intersection.hitPoint,intersection.hit,&rand_counter,&bounces);
                hits++;

                if(bounces==0) break;
            }else{
                break;
            }

        
       // }
    }



    color = termProduct(f2f3((1.0/samplesTaken)),totalColor);

    if(!hasHit){

    //    color = skybox(r);
        color=f2f3(_application_state[1]/SAMPLES);
    }

    color=pow(color,COLOR_POW);
    
    outpixels[tid*3+0] = RCOMP(color);
    outpixels[tid*3+1] = GCOMP(color);
    outpixels[tid*3+2] = BCOMP(color);
    
}