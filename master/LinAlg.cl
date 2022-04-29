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

float3 scaledVector3f(float s, float3 v){

    return Vector3f(s*v.x,s*v.y,s*v.z);

}

float3 vectorProjection(float3 target, float3 base){

    float f = dot(target,base)/dot(base,base);
    return scaledVector3f(f,base);

}



