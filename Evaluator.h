#pragma once

#include <CL/cl.h>
#include <wx/wx.h>
#include <vector>

#include "Utils.h"
#include "CVector.h"


#define EVAL_TYPE_SDF 0
#define EVAL_TYPE_NORMAL 1

//will use later in order to allocate buffers in Evaluator class constructor
//global size is good enough , don't need to pass a num_eval_points argument
#define MAX_EVAL_POINTS (200*200*200)


class Evaluator
{
public:
	cl_int err = CL_SUCCESS;
	cl_device_id device;
	cl_context context;
	cl_program program = NULL;
	cl_kernel kernel = NULL;
	cl_command_queue queue;
	wxTextCtrl* console;
	int build_success = 0;

	Evaluator(cl_device_id _device, cl_context _context, cl_command_queue queue, wxTextCtrl* _console);

	std::pair<int,std::string> build(cl_mem shape_id_bank_buffer, cl_mem object_position_bank_buffer,

		cl_mem object_right_bank_buffer,
		cl_mem object_up_bank_buffer,
		cl_mem object_forward_bank_buffer,
		cl_mem num_objects_arr_buffer,
		cl_mem build_procedure_data_buffer,
		cl_mem num_build_steps_arr_buffer
	);
	float* eval_points_bank;
	int* eval_types_bank;
	float* eval_bank;
	cl_mem eval_points_buffer;
	cl_mem eval_types_buffer;
	cl_mem eval_buffer;

	std::vector<float> eval_sdf_at_points(std::vector<v3f_t>& points);
	std::vector<v3f_t> eval_normal_at_points(std::vector<v3f_t>& points);


};

