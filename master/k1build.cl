
#define RANDOM_TABLE_SIZE 4096
#define SAMPLES 32

#define AD_NUM_TRIANGLES 0
#define AD_TRIANGLE_DATA 1
#define AD_NUM_LIGHT_TRIANGLES 42733
#define AD_LIGHT_TRIANGLE_DATA 42734
#define AD_RANDOM_TABLE 43118
#define AD_SHUFFLE_TABLE 47214




 
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

#define getAD(name,offset) (arbitrary_data[name+offset])
#define getAS(name,offset) (arbitrary_data[name+offset])

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

typedef struct tag_Triangle3f {
    float3 A;
    float3 B;
    float3 C;
    float3 N;

} Triangle3f_t;

Triangle3f_t Triangle3f(float3 A, float3 B, float3 C){
    Triangle3f_t tr;
    tr.A = A;
    tr.B = B;
    tr.C = C;
    tr.N = cross(C-A,B-A);
    return tr;
}

Triangle3f_t Triangle3fWithNormal(float3 A, float3 B, float3 C,float3 N){
    Triangle3f_t tr;
    tr.A = A;
    tr.B = B;
    tr.C = C;
    tr.N = N;
    return tr;
}

float3 fragment(float3 gv, int it, int * rand_counter_p);
Triangle3f_t vertex(Triangle3f_t tr, int it);


__global float * arbitrary_data;
__global float * application_state;
__global float3 rgt_g;
__global float3 upp_g;
__global float3 fwd_g;
__global float3 camera_g;

float rand(int * counter){
	float r = getAD(AD_RANDOM_TABLE,*counter);
	(*counter) = ((*counter)+1)%RANDOM_TABLE_SIZE;
	return r;
}
float randCoord(int * counter){
	return -1.0+rand(counter)*2.0;
}

//optional float3
typedef struct tag_of3_t{
    float3 hitPoint;
    int hit;
    float p1;
    float p2;
    float p3;
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

float3 getTriangleA(int it,int bankName){
    return (float3)(
    getAD(bankName,it*12+0*3+0),
    getAD(bankName,it*12+0*3+1),
    getAD(bankName,it*12+0*3+2)
    );
}
float3 getTriangleB(int it,int bankName){
    return (float3)(
    getAD(bankName,it*12+1*3+0),
    getAD(bankName,it*12+1*3+1),
    getAD(bankName,it*12+1*3+2)
    );
}
float3 getTriangleC(int it, int bankName){
    return (float3)(
    getAD(bankName,it*12+2*3+0),
    getAD(bankName,it*12+2*3+1),
    getAD(bankName,it*12+2*3+2)
    );
}
float3 getTriangleN(int it, int bankName){
    return (float3)(
    getAD(bankName,it*12+3*3+0),
    getAD(bankName,it*12+3*3+1),
    getAD(bankName,it*12+3*3+2)
    );
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
    float L1 = length(AB);
    float L2 = length(BC);
    float L3 = length(CA);

    //(o+t*r).N = 0
    //o.N+t*r.N = 0
    //t=-o.N/r.N
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

 //   float p1 = scalarProject(P1,AB);
   // float p2 = scalarProject(P2,BC);
   // float p3 = scalarProject(P3,CA);





    //if(p1<0.0||p1>L1||p2<0.0||p2>L2||p3<0.0||p3>L3){
      //  return miss();
    //}


    //Courtesy of https://math.stackexchange.com/a/51328/523713
    float p1 = dot(cross(P1,AB),N);
    float p2= dot(cross(P2,BC),N);
    float p3 = dot(cross(P3,CA),N);
    int s = signum(p1)+signum(p2)+signum(p3);
    if(s!=-3&&s!=3){
        return miss();
    }




    of3_t of= of3(intersectionPoint,0);
    of.p1 = p1;
    of.p2 = p2;
    of.p3 = p3;
    return of;
}

of3_t raycast(float3 o, float3 r, int numBankName, int bankName){

    int numTriangles = getNumTriangles(numBankName);

    float dist = 0.0;
    float3 hitPoint = (float3)(0.0,0.0,0.0);
    int itHit = -1;
    of3_t ret;

    
    for(int it=0;it<numTriangles;it++){
        float3 A = toGlobal(getTriangleA(it,bankName));
        float3 B = toGlobal(getTriangleB(it,bankName));
        float3 C = toGlobal(getTriangleC(it,bankName));
        float3 N = toGlobal(getTriangleN(it,bankName));
        Triangle3f_t tr = Triangle3fWithNormal(A,B,C,N);
        tr=vertex(tr,it);
        A = tr.A;
        B = tr.B;
        C = tr.C;
        N = tr.N;


        of3_t cast= raycastTriangle(o,r,A,B,C,N);
        if(cast.hit!=-1){
            float d = length(cast.hitPoint-o); //global hitpoint
            if(itHit==-1||d<dist){
                dist=d;
                itHit = it;
                hitPoint=cast.hitPoint; //global hitpoint
                ret.p1 = cast.p1;
                ret.p2 = cast.p2;
                ret.p3 = cast.p3;
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

    int rand_counter = getAD(AD_SHUFFLE_TABLE,tid%RANDOM_TABLE_SIZE);                    





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


    int hits = 0;
    for(int i=0;i<SAMPLES;i++){

        of3_t intersection = raycast(
            o,r,AD_NUM_TRIANGLES,AD_TRIANGLE_DATA
        );

        if(intersection.hit!=-1){
            totalColor += fragment(intersection.hitPoint,intersection.hit,&rand_counter);
            hits++;
        }
    }

    color = termProduct(f2f3((1.0/SAMPLES)),totalColor);
    if(hits==0){
        color=Vector3f(uv.x,uv.y,1.0);
        of3_t intersection = raycast(o,r,AD_NUM_LIGHT_TRIANGLES,AD_LIGHT_TRIANGLE_DATA);
        if(intersection.hit!=-1){
          //  float3 ln = getTriangleN(intersection.hit,AD_LIGHT_TRIANGLE_DATA);
          //  color = fabs(ln);
            color=Vector3f(1.0,1.0,1.0);
        }
    }

    
  
    outpixels[tid*3+0] = RCOMP(color);
    outpixels[tid*3+1] = GCOMP(color);
    outpixels[tid*3+2] = BCOMP(color);
    
 
}
 
#define R 11.845834549999923
#define H 3.480871528856729

float3 reflection(float3 ray, float3 normal){
	float normalComponent = dot(normal,ray);
	float3 normalComponentVector = normalComponent*normal;
	float3 orthagonalVector = ray-normalComponentVector;
	float3 reflected = orthagonalVector-normalComponentVector;
	return reflected;
}
float3 fragment(float3 gv, int it, int * rand_counter_p){

	const float specular = 0.0;
	const float bias = 0.01;

	float L = 0.0;
	int numLightingTriangles = (int)getNumTriangles(AD_NUM_LIGHT_TRIANGLES);
	float3 ln = getTriangleN(it,AD_TRIANGLE_DATA);	
	float3 gn = toGlobal(ln);
	float3 lAB = normalize(getTriangleB(it,AD_TRIANGLE_DATA)-getTriangleA(it,AD_TRIANGLE_DATA));
	float3 gAB = toGlobal(lAB);
	float3 vx = gAB;
	float3 vy=normalize(gn);
	float3 vz =normalize(-cross(vx,vy));

	float3 incident = normalize(gv-camera_g);
	float3 reflected = reflection(incident,vy);
	float t0 = dot(reflected,vx);
	float t1 = dot(reflected,vy);
	float t2 = dot(reflected,vz);

	float anglexy = atan2(t1,t0);
	float d1 = randCoord(rand_counter_p)*M_PI*(1.0-specular);
	anglexy+=d1;
	t0=cos(anglexy);
	t1=sin(anglexy);
	t2 = t2;

	float anglezy = atan2(t1,t2);
	float d2 = randCoord(rand_counter_p)*M_PI*(1.0-specular);
	anglezy+=d2;
	t0=t0;
	t1=sin(anglezy);
	t2=cos(anglezy);

	reflected = t0*vx+t1*vy+t2*vz;


	of3_t intersection = raycast(gv,reflected,AD_NUM_LIGHT_TRIANGLES,AD_LIGHT_TRIANGLE_DATA);
	if(intersection.hit!=-1){
		gv = gv+bias*gn;
		intersection = raycast(gv,reflected,AD_NUM_TRIANGLES,AD_TRIANGLE_DATA);
		if(intersection.hit==-1)
		L += 1.0;
	}
	return f2f3(L);
	
}
Triangle3f_t vertex(Triangle3f_t tr, int it) {return tr;}
