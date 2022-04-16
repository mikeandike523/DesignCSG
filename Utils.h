#pragma once


#include "CVector.h"

#include <string>
#include <cstdio>



#include <CL/cl.h>



#include <vector>


namespace Utils
{
#define T_max(a,b) (a>b ? a : b) 
#define T_min(a,b) (a<b ? a : b) 

	cl_device_id create_device();
	cl_program build_program(cl_context ctx, cl_device_id dev, const char* filename, int* err, std::string& buildLog, int STACK_MEM_PER_PIXEL);


	int clip(int a);
	long time_ms();
	float wrap(float v);
	std::string readFile(const char* fn);
	void writeFile(const char* fn, std::string content);
	void runProcess(std::string prgm, std::string cmd);
	void write_stl(const char* fn, std::vector<Triangle3f> tris);


#define DEBUG_MAX_CHARS 2048
#define DebugPrint(...) {char out[DEBUG_MAX_CHARS];sprintf(out,__VA_ARGS__);OutputDebugStringA(out);}



}

