#include "DrawPane.h"

#include <wx/wx.h>
#include <wx/rawbmp.h>
#include <cmath>
#include <cstdio>
#include <CL/cl.h>

#include "Utils.h"
#include "CVector.h"

#define CLIP8(x) ((x>255) ? 255 : ((x < 0 )? 0: x))

void BasicDrawPane::setArbitraryData(float * data, size_t items) {
	memcpy(arbitrary_data,data, sizeof(float) * items);
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

void BasicDrawPane::idled(wxIdleEvent& event)
{
	//Awful hack --> Purpose is to allow draw before scene is initialized, but this is incredibly hacky
	//Not to mention there are unfreed malloc littered throughout the source code
	//That's what you get when copy-pasting old projects

	if (!is_init) {
		err = 0;
		FILE* test = fopen("k1build.cl", "r");
		if (!test) {
			event.RequestMore();
			return;
		}
		else {
			fclose(test);
		}

		device = Utils::create_device();

		context = clCreateContext(NULL, 1, &device, NULL, NULL, &err);

		queue = clCreateCommandQueueWithProperties(context, device, NULL, &err);




		shape_id_bank = (BYTE*)malloc(MAX_OBJECTS * sizeof(uint8_t));
		material_id_bank = (BYTE*)malloc(MAX_OBJECTS * sizeof(uint8_t));
		object_position_bank = (float*)malloc(MAX_OBJECTS * 3 * sizeof(float));
		object_right_bank = (float*)malloc(MAX_OBJECTS * 3 * sizeof(float));
		object_up_bank = (float*)malloc(MAX_OBJECTS * 3 * sizeof(float));
		object_forward_bank = (float*)malloc(MAX_OBJECTS * 3 * sizeof(float));
		pixel_data = (BYTE*)malloc(3 * 640 * 480);
		build_procedure_data = (int*)malloc(4 * sizeof(int) * MAX_BUILD_STEPS);
		arbitrary_data = (float*)calloc(ARBITRARY_DATA_POINTS, sizeof(float));

		pixdataout_buffer = clCreateBuffer(context, CL_MEM_READ_WRITE |
			CL_MEM_COPY_HOST_PTR, 3 * 640 * 480 * sizeof(uint8_t), pixel_data, &err);

		camposin_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float), campos, &err);

		rightin_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float), right, &err);

		upin_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float), up, &err);

		forwardin_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float), up, &err);

		shape_id_bank_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 1 * sizeof(uint8_t) * MAX_OBJECTS, shape_id_bank, &err);

		material_id_bank_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 1 * sizeof(uint8_t) * MAX_OBJECTS, material_id_bank, &err);

		object_position_bank_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float) * MAX_OBJECTS, object_position_bank, &err);

		DebugPrint("%p\n", object_up_bank);

		object_up_bank_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float) * MAX_OBJECTS, object_up_bank, &err);

		object_right_bank_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float) * MAX_OBJECTS, object_right_bank, &err);


		DebugPrint("err %d\n", err);

		object_forward_bank_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 3 * sizeof(float) * MAX_OBJECTS, object_forward_bank, &err);

		num_objects_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 1 * sizeof(int) * 1, &num_objects, &err);

		screen_stack_memory_buffer = clCreateBuffer(context, CL_MEM_READ_WRITE, 640 * 480 * sizeof(float) * STACK_MEMORY_PER_PIXEL, NULL, &err);

		build_procedure_data_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, 4 * sizeof(int) * MAX_BUILD_STEPS, build_procedure_data, &err);

		num_build_steps_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY |
			CL_MEM_COPY_HOST_PTR, sizeof(int), &num_build_steps, &err);

		arbitrary_data_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, sizeof(float) * ARBITRARY_DATA_POINTS, arbitrary_data, &err);


		is_init = 1;
	}
	else if (is_init && pvalid) {


		right[0] = v_right.x; right[1] = v_right.y; right[2] = v_right.z;
		up[0] = v_up.x; up[1] = v_up.y; up[2] = v_up.z;
		forward[0] = v_forward.x; forward[1] = v_forward.y; forward[2] = v_forward.z;

		//todo, only copy teh right buffers each frame, these are design choices

		clEnqueueWriteBuffer(queue,
			camposin_buffer,
			CL_TRUE,
			0,
			3 * sizeof(float),
			campos,
			0,
			NULL,
			NULL);

		clEnqueueWriteBuffer(queue,
			rightin_buffer,
			CL_TRUE,
			0,
			3 * sizeof(float),
			right,
			0,
			NULL,
			NULL);

		clEnqueueWriteBuffer(queue,
			upin_buffer,
			CL_TRUE,
			0,
			3 * sizeof(float),
			up,
			0,
			NULL,
			NULL);


		clEnqueueWriteBuffer(queue,
			forwardin_buffer,
			CL_TRUE,
			0,
			3 * sizeof(float),
			forward,
			0,
			NULL,
			NULL);



		err = clEnqueueNDRangeKernel(queue, kernel, 2, NULL, global_size,
			local_size, 0, NULL, NULL);


		err = clEnqueueReadBuffer(queue, pixdataout_buffer, CL_TRUE, 0,
			3 * 640 * 480, pixel_data, 0, NULL, NULL);





		int time_ms = Utils::time_ms();

		wxSize size = this->GetSize();
		int w = size.x;
		int h = size.y;
		wxBitmap bmp = wxBitmap(w, h, 32);

		wxAlphaPixelData data(bmp, wxPoint(0, 0),
			wxSize(w, h));

		if (!data)
		{
			wxLogError("Failed to gain raw access to bitmap data");
			return;
		}

		wxAlphaPixelData::Iterator p(data);

		for (int y = 0; y < h; ++y)
		{
			wxAlphaPixelData::Iterator rowStart = p;

			for (int x = 0; x < w; ++x)
			{

				if (x < 640 && y < 480) {
					int tid = y * 640 + x;
					p.Red() = CLIP8(pixel_data[tid * 3 + 0]);
					p.Green() = CLIP8(pixel_data[tid * 3 + 1]);
					p.Blue() = CLIP8(pixel_data[tid * 3 + 2]);
					p.Alpha() = 255;

				}
				else {

					float uvx = Utils::wrap((float)(x - w * (float)(time_ms % 2000) / 2000.0) / (float)w);
					float uvy = (float)(y) / (float)h;

					p.Red() = Utils::clip((int)(255.0 * uvx));
					p.Green() = Utils::clip((int)(255.0 * uvy));
					p.Blue() = 0;
					p.Alpha() = 255;
				}


				++p;
			}

			p = rowStart;
			p.OffsetY(data, 1);
		}

		wxClientDC dc(this);
		dc.DrawBitmap(bmp, wxPoint(0, 0));
		event.RequestMore();
	}
}

LoadSceneResult BasicDrawPane::loadScene()
{


	if (!is_init)
		return LoadSceneResult::GENERIC_FAILURE;


	if (is_init) {

		//Need this code to update brushes

		 //For some reason it doesnt work

		 //Also don't forget the system("copy...") line

		// program = Utils::build_program(context, device, "k1build.cl");

		// kernel = clCreateKernel(program, "k1", &err);

	}

	//for some reason, the build log does not show up anymore on error
	//This needs to be investigated, and there is also a possibility of a memory leak in build_program (do logs or other variables need to be released?)
	//Reading the build logs directly in this copde works, but its hacky

	std::string buildLog;
	int p_prev_valid = pvalid;
	pvalid = 0;
	if (p_prev_valid)
		clReleaseProgram(program);
	program = Utils::build_program(context, device, "k1build.cl", &err, buildLog, STACK_MEMORY_PER_PIXEL);

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

		buildLog = "Failed to compile brushes:\n" + buildLog;
		console->AppendText(buildLog);


		return LoadSceneResult::SUCCESS;
	}

	if (err == CL_SUCCESS) {
		if (p_prev_valid)
			clReleaseKernel(kernel);
		kernel = clCreateKernel(program, "k1", &err);
	}

	err |= clSetKernelArg(kernel, 0, sizeof(cl_mem), &pixdataout_buffer);
	err |= clSetKernelArg(kernel, 1, sizeof(cl_mem), &camposin_buffer);
	err |= clSetKernelArg(kernel, 2, sizeof(cl_mem), &rightin_buffer);
	err |= clSetKernelArg(kernel, 3, sizeof(cl_mem), &upin_buffer);
	err |= clSetKernelArg(kernel, 4, sizeof(cl_mem), &forwardin_buffer);;
	err |= clSetKernelArg(kernel, 5, sizeof(cl_mem), &arbitrary_data_buffer);

	if (err == CL_SUCCESS)
		pvalid = 1;


	static int rotatedOnce = 0;
	//static int rotatedOnce = 1; //dont rotate


	if (!rotatedOnce) {
		rotatedOnce = 1;
		float da = -PI / 4.0f;
		float db = PI / 4.0f;
		Matrix3f rMatrix = rotateAroundVector(v_up, da);
		rMatrix = mul_Matrix3f_Matrix3f(eulerX(db), rMatrix);
		v_right = mul_Matrix3f_Vector3f(rMatrix, v_right);
		v_up = mul_Matrix3f_Vector3f(rMatrix, v_up);
		v_forward = mul_Matrix3f_Vector3f(rMatrix, v_forward);
	}

	clEnqueueWriteBuffer(queue,
		shape_id_bank_buffer,
		CL_TRUE,
		0,
		1 * sizeof(uint8_t) * MAX_OBJECTS,
		shape_id_bank,
		0,
		NULL,
		NULL);

	clEnqueueWriteBuffer(queue,
		material_id_bank_buffer,
		CL_TRUE,
		0,
		1 * sizeof(uint8_t) * MAX_OBJECTS,
		material_id_bank,
		0,
		NULL,
		NULL);



	clEnqueueWriteBuffer(queue,
		object_position_bank_buffer,
		CL_TRUE,
		0,
		3 * sizeof(float) * MAX_OBJECTS,
		object_position_bank,
		0,
		NULL,
		NULL);

	clEnqueueWriteBuffer(queue,
		object_right_bank_buffer,
		CL_TRUE,
		0,
		3 * sizeof(float) * MAX_OBJECTS,
		object_right_bank,
		0,
		NULL,
		NULL);

	clEnqueueWriteBuffer(queue,
		object_up_bank_buffer,
		CL_TRUE,
		0,
		3 * sizeof(float) * MAX_OBJECTS,
		object_up_bank,
		0,
		NULL,
		NULL);

	clEnqueueWriteBuffer(queue,
		object_forward_bank_buffer,
		CL_TRUE,
		0,
		3 * sizeof(float) * MAX_OBJECTS,
		object_forward_bank,
		0,
		NULL,
		NULL);

	clEnqueueWriteBuffer(queue,
		num_objects_buffer,
		CL_TRUE,
		0,
		1 * sizeof(int) * 1,
		&num_objects,
		0,
		NULL,
		NULL);

	clEnqueueWriteBuffer(queue,
		build_procedure_data_buffer,
		CL_TRUE,
		0,
		4 * sizeof(int) * MAX_BUILD_STEPS,
		build_procedure_data,
		0,
		NULL,
		NULL);

	clEnqueueWriteBuffer(queue,
		num_build_steps_buffer,
		CL_TRUE,
		0,
		1 * sizeof(int),
		&num_build_steps,
		0,
		NULL,
		NULL);

	return LoadSceneResult::SUCCESS;

}

BEGIN_EVENT_TABLE(BasicDrawPane, wxPanel)
EVT_MOTION(BasicDrawPane::mouseMoved)
EVT_LEFT_DOWN(BasicDrawPane::mouseDown)
EVT_LEFT_UP(BasicDrawPane::mouseReleased)
EVT_RIGHT_DOWN(BasicDrawPane::rightClick)
EVT_LEAVE_WINDOW(BasicDrawPane::mouseLeftWindow)
EVT_KEY_DOWN(BasicDrawPane::keyPressed)
EVT_KEY_UP(BasicDrawPane::keyReleased)
EVT_MOUSEWHEEL(BasicDrawPane::mouseWheelMoved)
EVT_IDLE(BasicDrawPane::idled)
END_EVENT_TABLE()

void BasicDrawPane::mouseMoved(wxMouseEvent& event) {



	if (dragging) {
		wxGetMousePosition(&cMX, &cMY);
		float da = -(float)(pMX - cMX) / 15.0 * yawspeed;
		float db = -(float)(pMY - cMY) / 15.0 * yawspeed;
		Matrix3f rMatrix = rotateAroundVector(v_up, da);
		rMatrix = mul_Matrix3f_Matrix3f(eulerX(db), rMatrix);
		v_right = mul_Matrix3f_Vector3f(rMatrix, v_right);
		v_up = mul_Matrix3f_Vector3f(rMatrix, v_up);
		v_forward = mul_Matrix3f_Vector3f(rMatrix, v_forward);
		pMX = cMX;
		pMY = cMY;
	}

}
void BasicDrawPane::mouseDown(wxMouseEvent& event) {
	wxGetMousePosition(&pMX, &pMY); dragging = 1;
}
void BasicDrawPane::mouseWheelMoved(wxMouseEvent& event) {
	campos[2] += (float)event.GetWheelRotation() / event.GetWheelDelta();
}
void BasicDrawPane::mouseReleased(wxMouseEvent& event) { dragging = 0; }
void BasicDrawPane::rightClick(wxMouseEvent& event) {}
void BasicDrawPane::mouseLeftWindow(wxMouseEvent& event) {}
void BasicDrawPane::keyPressed(wxKeyEvent& event) {}
void BasicDrawPane::keyReleased(wxKeyEvent& event) {}

int BasicDrawPane::initialized()
{
	return is_init;
}

BasicDrawPane::BasicDrawPane(wxFrame* parent, wxSize s, wxTextCtrl* _console) :
	wxPanel(parent, wxID_ANY, wxDefaultPosition, s), console(_console)
{
	this->SetBackgroundColour(wxColor(*wxWHITE));
	is_init = 0;
}


