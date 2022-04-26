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



