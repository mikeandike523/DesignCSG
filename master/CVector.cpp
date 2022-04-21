#include "CVector.h"
#include "math.h"
#define PI 3.1415926
#define PI_2 (PI/2.0f)
#include "stdio.h"
#include <windows.h>

Vector3f mul_Matrix3f_Vector3f(Matrix3f mat, Vector3f vec) {

	Vector3f R;
	R.x = mat.m00 * vec.x + mat.m10 * vec.y + mat.m20 * vec.z;
	R.y = mat.m01 * vec.x + mat.m11 * vec.y + mat.m21 * vec.z;
	R.z = mat.m02 * vec.x + mat.m12 * vec.y + mat.m22 * vec.z;

	return R;
}


Matrix3f eulerX(float rads) {

	Matrix3f R = {

		 1.0f,  0.0f,  0.0f,
		 0.0f,  sin(rads + PI_2),  cos(rads + PI_2),
		0.0f,  sin(rads),  cos(rads)

	};

	return R;
}

Matrix3f eulerY(float rads) {

	Matrix3f R = {
cos(rads),  0.0, sin(rads),
		0.0,  1.0, 0.0,
	   cos(rads + PI_2),  0.0,sin(rads + PI_2)
	};

	return R;
}


Matrix3f eulerZ(float rads) {

	Matrix3f R = {

		 cos(rads),  sin(rads),  0.0,
		 cos(rads + PI_2),  sin(rads + PI_2),  0.0,
		0.0,  0.0,  1.0
	};

	return R;
}

Matrix3f inverseEuler(Vector3f heading) {

	float a = atan2(heading.z, heading.x);
	Matrix3f R1 = eulerY(-a);
	Vector3f heading_1 = mul_Matrix3f_Vector3f(R1, heading);
	float b = atan2(heading_1.y, heading_1.x);
	Matrix3f R2 = eulerZ(-b);

	return mul_Matrix3f_Matrix3f(R2, R1);

}

Matrix3f eulerFromXTo(Vector3f heading) {

	float a = atan2(heading.z, heading.x);
	Vector3f headingXY = mul_Matrix3f_Vector3f(eulerY(-a), heading);
	float b = atan2(headingXY.y, headingXY.x);
	return mul_Matrix3f_Matrix3f(eulerY(a), eulerZ(b));

}




Matrix3f mul_Matrix3f_Matrix3f(Matrix3f R1, Matrix3f R2) {
	Matrix3f R = { R2.m00 * R1.m00 + R2.m01 * R1.m10 + R2.m02 * R1.m20,
 R2.m00 * R1.m01 + R2.m01 * R1.m11 + R2.m02 * R1.m21,
 R2.m00 * R1.m02 + R2.m01 * R1.m12 + R2.m02 * R1.m22,
 R2.m10 * R1.m00 + R2.m11 * R1.m10 + R2.m12 * R1.m20,
 R2.m10 * R1.m01 + R2.m11 * R1.m11 + R2.m12 * R1.m21,
 R2.m10 * R1.m02 + R2.m11 * R1.m12 + R2.m12 * R1.m22,
 R2.m20 * R1.m00 + R2.m21 * R1.m10 + R2.m22 * R1.m20,
 R2.m20 * R1.m01 + R2.m21 * R1.m11 + R2.m22 * R1.m21,
 R2.m20 * R1.m02 + R2.m21 * R1.m12 + R2.m22 * R1.m22 };

	return R;
}





Vector3f v3f(float _x, float _y, float _z) {
	Vector3f R = { _x, _y,  _z };
	return R;
}

void print_v3f(Vector3f v) {
	DebugPrint("%f %f %f\n", v.x, v.y, v.z);
}

Matrix3f  identity() {
	Matrix3f R = {
		 1.0,  0.0,  0.0,
		 0.0,  1.0,  0.0,
		 0.0,  0.0,  1.0,
	};
	return R;

}

Matrix3f rotateAroundVector(Vector3f axis, float rads) {
	Matrix3f R1 = inverseEuler(axis);
	Matrix3f aR1 = eulerFromXTo(axis);
	return mul_Matrix3f_Matrix3f(aR1, mul_Matrix3f_Matrix3f(eulerX(rads), R1));
}

float magnitude(Vector3f v) {
	float m2 = v.x * v.x + v.y * v.y + v.z * v.z;
	return sqrt(m2);
}

Vector3f v3f_add(Vector3f a, Vector3f b) {
	return v3f(a.x + b.x, a.y + b.y, a.z + b.z);
}
Vector3f v3f_sub(Vector3f a, Vector3f b) {
	return v3f(a.x - b.x, a.y - b.y, a.z - b.z);
}
Vector3f v3f_max(Vector3f a, Vector3f b) {
	return v3f(T_max(a.x, b.x), T_max(a.y, b.y), T_max(a.z, b.z));

}
Vector3f v3f_min(Vector3f a, Vector3f b) {
	return v3f(T_min(a.x, b.x), T_min(a.y, b.y), T_min(a.z, b.z));
}

Vector3f v3f_abs(Vector3f a) {
	return v3f(fabs(a.x), fabs(a.y), fabs(a.z));
}

Vector3f v3f_scale(Vector3f a, float s) {

	return v3f(s * a.x, s * a.y, s * a.z);
}

void v3f_dumpTo(FILE* fl, Vector3f v) {

	float data[3] = { 0 };
	data[0] = v.x;
	data[1] = v.y;
	data[2] = v.z;
	fwrite(data, sizeof(float), 3, fl);
}

void v3f_print(Vector3f v) {

	printf("%f %f %f\n", v.x, v.y, v.z);

}

Vector3f v3f_null() {
	return v3f(0.0, 0.0, 0.0);
}

Vector3f normalize(v3f_t v, float EPS) {

	float m = magnitude(v);
	//   printf("normalized ");
	  // v3f_print(v);
	  // printf("m %f\n",m);
	if (m < EPS) {
		// printf("nulled\n");
		return v3f_null();
	}
	return v3f_scale(v, 1.0 / m);
}


float dot(Vector3f a, Vector3f b) {
	return a.x * b.x + a.y * b.y + a.z * b.z;
}

box_t box(v3f_t center, v3f_t diameters) {

	box_t box = { center,diameters,0 };
	return box;
}

box_t box(v3f_t center, v3f_t diameters, int level) {

	box_t box = { center,diameters,level };
	return box;
}

v3f_t v3f(float f)
{
	return v3f(f, f, f);
}

void print_box(box_t b) {
	DebugPrint("box{\n");
	DebugPrint("center=[%.6f %.6f %.6f]\n", b.center.x, b.center.y, b.center.z);
	DebugPrint("diameters=[%.6f %.6f %.6f]\n", b.diameters.x, b.diameters.y, b.diameters.z);
	DebugPrint("}\n");
}
