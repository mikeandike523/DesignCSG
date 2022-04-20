
#pragma once


#include "stdio.h"
#include <vector>
#include <optional>
#include <map>

#define DEBUG_MAX_CHARS 2048
#define DebugPrint(...) {char out[DEBUG_MAX_CHARS];sprintf(out,__VA_ARGS__);OutputDebugStringA(out);}

#define T_min(a,b) ((a<b) ? a : b)
#define T_max(a,b) ((a>b) ? a : b)

typedef struct Vector3f { float x; float y; float z; 

template<typename T_vector> 
T_vector toVectorType() {

	return T_vector(x,y,z);
}

} Vector3f;
typedef struct Matrix3f {

	float m00; float m01; float m02;
	float m10; float m11; float m12;
	float m20; float m21; float m22;


} Matrix3f;

typedef Vector3f v3f_t;

Vector3f mul_Matrix3f_Vector3f(Matrix3f mat, Vector3f vec);

Matrix3f eulerX(float rads);

Matrix3f eulerY(float rads);

Matrix3f eulerZ(float rads);

Matrix3f mul_Matrix3f_Matrix3f(Matrix3f R1, Matrix3f R2);

Vector3f v3f(float x, float y, float z);

void print_v3f(Vector3f v);

Matrix3f inverseEuler(Vector3f heading);
Matrix3f  identity();
Matrix3f rotateAroundVector(Vector3f axis, float rads);

Matrix3f eulerFromXTo(Vector3f heading);

float magnitude(Vector3f v);
void v3f_print(Vector3f v);
Vector3f v3f_add(Vector3f a, Vector3f b);
Vector3f v3f_sub(Vector3f a, Vector3f b);
Vector3f v3f_max(Vector3f a, Vector3f b);
Vector3f v3f_min(Vector3f a, Vector3f b);
Vector3f v3f_abs(Vector3f a);
Vector3f v3f_scale(Vector3f a, float s);

void v3f_dumpTo(FILE* fl, Vector3f v);

Vector3f v3f_null();

Vector3f normalize(v3f_t v, float EPS);

float dot(Vector3f a, Vector3f b);

struct box_t {

	v3f_t center;
	v3f_t diameters;
	int level;

	box_t* north = nullptr;
	box_t* east = nullptr;
	box_t* south = nullptr;
	box_t* west = nullptr;
	box_t* above = nullptr;
	box_t* below = nullptr;



	box_t* c0 = nullptr;
	box_t* c1 = nullptr;
	box_t* c2 = nullptr;
	box_t* c3 = nullptr;
	box_t* c4 = nullptr;
	box_t* c5 = nullptr;
	box_t* c6 = nullptr;
	box_t* c7 = nullptr;
	box_t* c8 = nullptr;

	box_t* prnt;

	int cnumber = 0;


	int lookup = 0;

	int split = 0;

	std::vector<v3f_t> octant_points(float fractionAlongEdge) {
		std::vector<v3f_t> v =
		{
			v3f_add(center,v3f_scale(v3f(-diameters.x / 2,-diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
			v3f_add(center,v3f_scale(v3f(diameters.x / 2,-diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
			v3f_add(center,v3f_scale(v3f(diameters.x / 2,-diameters.y / 2,-diameters.z / 2),fractionAlongEdge)),
			v3f_add(center,v3f_scale(v3f(-diameters.x / 2,-diameters.y / 2,-diameters.z / 2),fractionAlongEdge)),
			v3f_add(center,v3f_scale(v3f(-diameters.x / 2,diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
			v3f_add(center,v3f_scale(v3f(diameters.x / 2,diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
			v3f_add(center,v3f_scale(v3f(diameters.x / 2,diameters.y / 2,-diameters.z / 2),fractionAlongEdge)),
			v3f_add(center,v3f_scale(v3f(-diameters.x / 2,diameters.y / 2,-diameters.z / 2),fractionAlongEdge))
		};
		return v;
	}

	//template<typename Functor>
	//std::vector<v3f_t> unique_octant_points(float fractionAlongEdge,std::map<int,v3f_t>& uniquePoints,Functor hash) {
	//	std::vector<v3f_t> v =
	//	{
	//		v3f_add(center,v3f_scale(v3f(-diameters.x / 2,-diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
	//		v3f_add(center,v3f_scale(v3f(diameters.x / 2,-diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
	//		v3f_add(center,v3f_scale(v3f(diameters.x / 2,-diameters.y / 2,-diameters.z / 2),fractionAlongEdge)),
	//		v3f_add(center,v3f_scale(v3f(-diameters.x / 2,-diameters.y / 2,-diameters.z / 2),fractionAlongEdge)),
	//		v3f_add(center,v3f_scale(v3f(-diameters.x / 2,diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
	//		v3f_add(center,v3f_scale(v3f(diameters.x / 2,diameters.y / 2,diameters.z / 2),fractionAlongEdge)),
	//		v3f_add(center,v3f_scale(v3f(diameters.x / 2,diameters.y / 2,-diameters.z / 2),fractionAlongEdge)),
	//		v3f_add(center,v3f_scale(v3f(-diameters.x / 2,diameters.y / 2,-diameters.z / 2),fractionAlongEdge))
	//	};
	//	for (v3f_t _v : v) {
	//		int hsh = hash(_v);
	//		//if (uniquePoints.find(hsh)!=uniquePoints.end()) {
	//		uniquePoints.insert(std::make_pair(hsh,_v));
	//		//}
	//	}
	//	return v;
	//}

};

box_t box(v3f_t center, v3f_t diameters);
box_t box(v3f_t center, v3f_t diameters, int level);

v3f_t v3f(float f);

void print_box(box_t b);


typedef struct Triangle3f {
	v3f_t A, B, C;
	Triangle3f(v3f_t _A, v3f_t _B, v3f_t _C) : A(_A), B(_B), C(_C) {};
} Triangle3f;


struct Vector3i {
	int x, y, z;
	Vector3i(int _x, int _y, int _z) :x(_x), y(_y), z(_z) {}
};

inline int boxIsEmpty(box_t* node)
{
	std::vector<box_t*> stack = { node };
	while (stack.size() > 0) {
		box_t* item = stack.back();
		stack.pop_back();
		if (item->lookup != 0) return 0;
		if (item->split) {
			stack.push_back(item->c0);
			stack.push_back(item->c1);
			stack.push_back(item->c2);
			stack.push_back(item->c3);
			stack.push_back(item->c4);
			stack.push_back(item->c5);
			stack.push_back(item->c6);
			stack.push_back(item->c7);
		}
	}

	return 1;
}

inline std::vector<std::pair<int, int>> getLookups(box_t* node) {
	std::vector<std::pair<int, int>> lookups;
	std::vector<box_t*> stack = { node };
	while (stack.size() > 0) {
		box_t* item = stack.back();
		stack.pop_back();
		lookups.push_back(std::make_pair(item->cnumber, item->lookup));
		if (item->split) {
			stack.push_back(item->c0);
			stack.push_back(item->c1);
			stack.push_back(item->c2);
			stack.push_back(item->c3);
			stack.push_back(item->c4);
			stack.push_back(item->c5);
			stack.push_back(item->c6);
			stack.push_back(item->c7);
		}
	}
	return lookups;
}


struct HashTriangle {

	uint64_t A = 0;
	uint64_t B = 0;
	uint64_t C = 0;
	HashTriangle(uint64_t _A, uint64_t _B, uint64_t _C) : A(_A), B(_B), C(_C) {}


};


