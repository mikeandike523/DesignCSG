#include "Evaluator.h"

#include <wx/wx.h>
#include <mutex>

//need to find a way to define STACK_MEMORY_PER_PIXEL globally
#define STACK_MEMORY_PER_PIXEL 64


std::mutex evaluatorMutex;



Evaluator::Evaluator(cl_device_id _device, cl_context _context, cl_command_queue _queue, wxTextCtrl* _console)
{
	device = _device;
	context = _context;
	queue = _queue;
	console = _console;

	eval_bank = (float*)malloc(3 * sizeof(float) * MAX_EVAL_POINTS);
	eval_points_bank = (float*)malloc(sizeof(float) * MAX_EVAL_POINTS * 3);
	eval_types_bank = (int*)malloc(sizeof(int) * 1);
	arbitrary_data = (float*)calloc(ARBITRARY_DATA_POINTS, sizeof(float));

	arbitrary_data_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, sizeof(float) * ARBITRARY_DATA_POINTS, &arbitrary_data, &err);




	eval_buffer = clCreateBuffer(context, CL_MEM_WRITE_ONLY |
		CL_MEM_COPY_HOST_PTR, 3 * sizeof(float) * MAX_EVAL_POINTS, eval_bank, &err);

	eval_points_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
		CL_MEM_COPY_HOST_PTR, sizeof(float) * MAX_EVAL_POINTS * 3, eval_points_bank, &err);

	eval_types_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
		CL_MEM_COPY_HOST_PTR, sizeof(int) * 1, eval_types_bank, &err);

}




std::pair<int,std::string> Evaluator::build(cl_mem shape_id_bank_buffer, cl_mem object_position_bank_buffer,

	cl_mem object_right_bank_buffer,
	cl_mem object_up_bank_buffer,
	cl_mem object_forward_bank_buffer,
	cl_mem num_objects_arr_buffer,
	cl_mem build_procedure_data_buffer,
	cl_mem num_build_steps_arr_buffer)
{
	if (build_success)
	{
		clReleaseProgram(program);
		clReleaseKernel(kernel);
	}

	std::string buildLog;

	program = Utils::build_program(context, device, "k2build.cl", &err, buildLog, STACK_MEMORY_PER_PIXEL);

	if (err != CL_SUCCESS) {

		char* program_log;
		size_t log_size;

		clGetProgramBuildInfo(program, device, CL_PROGRAM_BUILD_LOG,
			0, NULL, &log_size);

		program_log = (char*)malloc(log_size + 1);

		program_log[log_size] = '\0';

		clGetProgramBuildInfo(program, device, CL_PROGRAM_BUILD_LOG,

			log_size + 1, program_log, NULL);

		buildLog += std::string(program_log);

		free(program_log);


		console->Clear();
		console->AppendText("Error when building evaluation program:\n");
		console->AppendText(buildLog.c_str());
		return std::make_pair( - 1,std::string(buildLog.c_str()));
	}

	kernel = clCreateKernel(program, "k2", &err);



	err |= clSetKernelArg(kernel, 0, sizeof(cl_mem), &eval_points_buffer);
	err |= clSetKernelArg(kernel, 1, sizeof(cl_mem), &eval_buffer);
	err |= clSetKernelArg(kernel, 2, sizeof(cl_mem), &eval_types_buffer);
	err |= clSetKernelArg(kernel, 3, sizeof(cl_mem), &shape_id_bank_buffer);
	err |= clSetKernelArg(kernel, 4, sizeof(cl_mem), &object_position_bank_buffer);
	err |= clSetKernelArg(kernel, 5, sizeof(cl_mem), &object_right_bank_buffer);
	err |= clSetKernelArg(kernel, 6, sizeof(cl_mem), &object_up_bank_buffer);
	err |= clSetKernelArg(kernel, 7, sizeof(cl_mem), &object_forward_bank_buffer);
	err |= clSetKernelArg(kernel, 8, sizeof(cl_mem), &num_objects_arr_buffer);
	err |= clSetKernelArg(kernel, 9, sizeof(cl_mem), &build_procedure_data_buffer);
	err |= clSetKernelArg(kernel, 10, sizeof(cl_mem), &num_build_steps_arr_buffer);
	err |= clSetKernelArg(kernel, 11, sizeof(cl_mem), &arbitrary_data_buffer);



	return std::make_pair(0, std::string("Success!"));

}

//no need to copy scene data, assume already in GPU memory
//TODO: Ensure export cannot happen before a valid scene is loaded

std::vector<float> Evaluator::eval_sdf_at_points(std::vector<v3f_t>& points)
{

	std::lock_guard<std::mutex> lock(evaluatorMutex);

	std::vector<float> evaluations;
	evaluations.reserve(points.size());



	int cursor = 0;



	eval_types_bank[0] = EVAL_TYPE_SDF;

	while (cursor < points.size()) {
		int amt = T_min(MAX_EVAL_POINTS, points.size() - cursor);



		for (int i = cursor; i < cursor + amt; i++) {
			int I = i - cursor;
			eval_points_bank[I * 3 + 0] = points.at(i).x;
			eval_points_bank[I * 3 + 1] = points.at(i).y;
			eval_points_bank[I * 3 + 2] = points.at(i).z;
		}

		clEnqueueWriteBuffer(queue, eval_types_buffer, CL_TRUE, 0, sizeof(int) * 1, eval_types_bank, 0, NULL, NULL);

		clEnqueueWriteBuffer(queue, eval_points_buffer, CL_TRUE, 0, sizeof(float) * 3 * amt, eval_points_bank, 0, NULL, NULL);

		const size_t g_size[] = { amt };
		const size_t l_size[] = { 1 };

		clEnqueueNDRangeKernel(queue, kernel, 1, 0, g_size, l_size, 0, NULL, NULL);

		clEnqueueReadBuffer(queue, eval_buffer, CL_TRUE, 0, 1 * sizeof(float) * amt, eval_bank, 0, NULL, NULL);


		for (int i = 0; i < amt; i++) {
			evaluations.push_back(eval_bank[i]);
		}

		cursor += amt;
	}

	return evaluations;
}

std::vector<v3f_t> Evaluator::eval_normal_at_points(std::vector<v3f_t>& points)
{

	std::lock_guard<std::mutex> lock(evaluatorMutex);


	std::vector<v3f_t> evaluations;
	evaluations.reserve(points.size());
	eval_types_bank[0] = EVAL_TYPE_NORMAL;

	int cursor = 0;

	while (cursor < points.size()) {

		int amt = T_min(MAX_EVAL_POINTS, points.size() - cursor);


		for (int i = cursor; i < cursor + amt; i++) {
			int I = i - cursor;
			eval_points_bank[I * 3 + 0] = points.at(i).x;
			eval_points_bank[I * 3 + 1] = points.at(i).y;
			eval_points_bank[I * 3 + 2] = points.at(i).z;
		}

		clEnqueueWriteBuffer(queue, eval_types_buffer, CL_TRUE, 0, sizeof(int) * 1, eval_types_bank, 0, NULL, NULL);

		clEnqueueWriteBuffer(queue, eval_points_buffer, CL_TRUE, 0, sizeof(float) * 3 * amt, eval_points_bank, 0, NULL, NULL);

		const size_t g_size[] = { amt };
		const size_t l_size[] = { 1 };

		clEnqueueNDRangeKernel(queue, kernel, 1, 0, g_size, l_size, 0, NULL, NULL);

		clEnqueueReadBuffer(queue, eval_buffer, CL_TRUE, 0, 3 * sizeof(float) * amt, eval_bank, 0, NULL, NULL);


		for (int i = 0; i < amt; i++) {
			evaluations.push_back(v3f(eval_bank[i * 3 + 0], eval_bank[i * 3 + 1], eval_bank[i * 3 + 2]));
		}

		cursor += amt;
	}

	return evaluations;
}

void Evaluator::setArbitraryData(float* data, size_t items) {
	memcpy(arbitrary_data, data, sizeof(float) * items);
	clEnqueueWriteBuffer(queue,
		arbitrary_data_buffer,
		CL_TRUE,
		0,
		ARBITRARY_DATA_POINTS * sizeof(float),
		arbitrary_data,
		0,
		NULL,
		NULL);

}