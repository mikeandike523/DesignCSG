
#define _SILENCE_CXX17_CODECVT_HEADER_DEPRECATION_WARNING

#include "Utils.h"

#include <Windows.h>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <codecvt>
#include <locale>
#include <vector>
#include <CVector.h>
#include <filesystem>

#include <CL/cl.h>

#define scale_stl 100.0



namespace Utils {


	cl_device_id create_device()
	{

		cl_platform_id platform;
		cl_device_id dev;

		clGetPlatformIDs(1, &platform, NULL);

		int err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 1, &dev, NULL);

		if (err == CL_DEVICE_NOT_FOUND) {

			printf("Defaulting to CPU.\n");

			err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_CPU, 1, &dev, NULL);

		}

		/*
		int param_name = CL_DEVICE_MAX_CONSTANT_BUFFER_SIZE;
		int param_value_size = sizeof(cl_ulong);
		cl_ulong param_value = 0;
		size_t param_value_size_ret;

		clGetDeviceInfo(dev, param_name, param_value_size, &param_value, &param_value_size_ret);
		*/


		return dev;
	}

	cl_program build_program(cl_context ctx, cl_device_id dev, const char* filename, int* err, std::string& buildLog, int STACK_MEM_PER_PIXEL)
	{

		cl_program program;
		FILE* program_handle;
		char* program_buffer, * program_log;
		size_t program_size, log_size;


		program_handle = fopen(filename, "rb");

		fseek(program_handle, 0, SEEK_END);

		program_size = ftell(program_handle);

		rewind(program_handle);

		program_buffer = (char*)malloc(program_size + 1);

		program_buffer[program_size] = '\0';

		fread(program_buffer, sizeof(char), program_size, program_handle);

		fclose(program_handle);

		program = clCreateProgramWithSource(ctx, 1,
			(const char**)&program_buffer, &program_size, err);

		free(program_buffer);

		char options_string[512];
		sprintf(options_string, "-D STACK_MEMORY_PER_PIXEL=%d -w", STACK_MEM_PER_PIXEL);

		*err = clBuildProgram(program, 0, NULL, options_string, NULL, NULL);

		if (*err < 0) {

			clGetProgramBuildInfo(program, dev, CL_PROGRAM_BUILD_LOG,
				0, NULL, &log_size);

			program_log = (char*)malloc(log_size + 1);

			program_log[log_size] = '\0';

			clGetProgramBuildInfo(program, dev, CL_PROGRAM_BUILD_LOG,

				log_size + 1, program_log, NULL);

			buildLog += std::string(program_log);

			free(program_log);

		}

		return program;
	}


	int clip(int a) {
		return (a > 255 ? 255 : (a < 0 ? 0 : a));
	}

	void runProcess(std::string prgm, std::string cmd) {


		STARTUPINFO si;
		PROCESS_INFORMATION pi;

		ZeroMemory(&si, sizeof(si));
		si.cb = sizeof(si);
		ZeroMemory(&pi, sizeof(pi));
		std::wstring prgmw = std::wstring_convert<std::codecvt_utf8<wchar_t>>().from_bytes(prgm);
		std::wstring cmdw = std::wstring_convert<std::codecvt_utf8<wchar_t>>().from_bytes(cmd);

		// Start the child process. 
		if (!CreateProcess(NULL,   // No module name (use command line)
			(LPWSTR)cmdw.c_str(),        // Command line
			NULL,           // Process handle not inheritable
			NULL,           // Thread handle not inheritable
			FALSE,          // Set handle inheritance to FALSE
			0,              // No creation flags
			NULL,           // Use parent's environment block
			NULL,           // Use parent's starting directory 
			&si,            // Pointer to STARTUPINFO structure
			&pi)           // Pointer to PROCESS_INFORMATION structure
			)
		{
			printf("CreateProcess failed (%d).\n", GetLastError());
			return;
		}

		// Wait until child process exits.
		WaitForSingleObject(pi.hProcess, INFINITE);

		// Close process and thread handles. 
		CloseHandle(pi.hProcess);
		CloseHandle(pi.hThread);
	}


	long time_ms() {
		SYSTEMTIME time;
		GetSystemTime(&time);
		LONG _time_ms = (time.wSecond * 1000) + time.wMilliseconds;
		return _time_ms;
	}

	float wrap(float v)
	{
		return v - floor(v);
	}

	std::string readFile(const char* fn)
	{

		std::ifstream t(fn);
		std::stringstream buffer;
		buffer << t.rdbuf();
		return  buffer.str();
	}

	void writeFile(const char* fn, std::string content)
	{
		FILE* f = fopen(fn, "wb");
		fwrite(content.c_str(), 1, content.length(), f);
		fclose(f);
	}

	void write_stl(const char* fn, std::vector<Triangle3f> tris) {
		FILE* fl = fopen(fn, "wb");
		char header[80] = { 0 };
		fwrite(header, 1, 80, fl);
		int sz = tris.size();
		fwrite(&sz, sizeof(int), 1, fl);
		int abc = 0;
		for (int it = 0; it < sz; it++) {
			Triangle3f T = tris[it];
			//	DebugPrint("%f %f %f\n", T.A.x, T.A.y, T.A.z);
				//DebugPrint("%f %f %f\n", T.B.x, T.B.y, T.B.z);
			//	DebugPrint("%f %f %f\n", T.C.x, T.C.y, T.C.z);
			float N[3] = { 0.0,0.0,0.0 };
			float A[3] = { scale_stl * T.A.x,scale_stl * T.A.z,scale_stl * T.A.y };
			float B[3] = { scale_stl * T.B.x,scale_stl * T.B.z,scale_stl * T.B.y };
			float C[3] = { scale_stl * T.C.x,scale_stl * T.C.z,scale_stl * T.C.y };
			fwrite(N, sizeof(float) * 3, 1, fl);
			fwrite(A, sizeof(float) * 3, 1, fl);
			fwrite(B, sizeof(float) * 3, 1, fl);
			fwrite(C, sizeof(float) * 3, 1, fl);
			fwrite(&abc, sizeof(uint16_t), 1, fl);
		}


		fclose(fl);
	}

	std::string replaceExtension(std::string path, std::string originalExtension, std::string newExtension) {
		std::string result = "";
		
		if (path.find(originalExtension)!=std::string::npos) {
			result = path.substr(0,path.length()-originalExtension.length())+newExtension;
		
		}
		else {
			result = path + newExtension;
		}

		return result;

	}
	std::string getBaseName(std::string path) {
		return std::string((std::filesystem::path(path)).filename().u8string());
	}


}