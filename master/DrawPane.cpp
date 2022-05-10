#include "DrawPane.h"

#include <wx/wx.h>
#include <wx/rawbmp.h>
#include <cmath>
#include <cstdio>
#include <CL/cl.h>
#include <chrono>
#include <thread>

#include "Utils.h"
#include "CVector.h"

#define CLIP8(x) ((x>255) ? 255 : ((x < 0 )? 0: x))

#define APPLICATION_STATE_POINTS 2048
#define APPLICATION_STATE_TIME_MILLISECONDS 0

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

#define MAX_STORAGE 128 * 1024 * 1024 //128MB

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



		static uint64_t max_floats = 1;
	
		
		
		static int buffer_task_complete = 0;
		static int buffer_task_running = 0;
		auto task = []( uint64_t* max_floats_p, int* task_complete_p, int * running_p, cl_context * context) {
			(*running_p) = 1;
			int testing_max_floats = 1;
			int* testing_max_floats_p = &testing_max_floats;
			while (*testing_max_floats_p) {
				(* max_floats_p) *= 2;
				if ((*max_floats_p) >  MAX_STORAGE/ 4) (*testing_max_floats_p) = 0; 
				DebugPrint("Attempting to create float buffer with %d elements... ", *max_floats_p);
				float* testArray = (float*)calloc((*max_floats_p), sizeof(float));
				cl_int max_floats_err = CL_SUCCESS;
				cl_mem testBuffer = clCreateBuffer(*context, CL_MEM_READ_ONLY |
					CL_MEM_COPY_HOST_PTR, (*max_floats_p) * sizeof(float), testArray, &max_floats_err);
				if (max_floats_err == CL_SUCCESS) {
					DebugPrint("Success.\n");
					clReleaseMemObject(testBuffer);
				}
				else {
					DebugPrint("Failed.\n");
					(*testing_max_floats_p) = 0;
				}
				free(testArray);

			}
			(*task_complete_p) = 1;
		};



		if (!buffer_task_running&&!buffer_task_complete) {
			std::thread t(task,&max_floats,&buffer_task_complete,&buffer_task_running,&context);
			t.detach();
			return;
		}
		if (!buffer_task_complete) {
			return;
		}
	

		max_floats /= 2; //since last clCreateBuffer was not successful

		if (max_floats > MAX_STORAGE / 4) {
			max_floats = MAX_STORAGE / 4;
			DebugPrint("Capped buffer.\n");
		}

	
		DebugPrint("Buffer max floats: %d\n", max_floats);
	
		FILE* deviceInfoFile = fopen("deviceInfo.txt", "w");
		fprintf(deviceInfoFile, "%d", max_floats);
		fclose(deviceInfoFile);


		ARBITRARY_DATA_POINTS = std::stoi(Utils::readFile("deviceInfo.txt")) / 4;

		pixel_data = (BYTE*)malloc(3 * 640 * 480);
		arbitrary_data = (float*)calloc(ARBITRARY_DATA_POINTS, sizeof(float));
		application_state = (float*)calloc(APPLICATION_STATE_POINTS, sizeof(float));

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

		arbitrary_data_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, sizeof(float) * ARBITRARY_DATA_POINTS, arbitrary_data, &err);


		application_state_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, sizeof(float) * APPLICATION_STATE_POINTS, application_state, &err);


		is_init = 1;
	}
	else if (is_init && pvalid) {


		right[0] = v_right.x; right[1] = v_right.y; right[2] = v_right.z;
		up[0] = v_up.x; up[1] = v_up.y; up[2] = v_up.z;
		forward[0] = v_forward.x; forward[1] = v_forward.y; forward[2] = v_forward.z;

		//https://stackoverflow.com/a/56107709/5166365
		uint64_t millis = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();

		
		constexpr uint64_t twelve_seconds = 1000 * 12;
		application_state[APPLICATION_STATE_TIME_MILLISECONDS] = (float)(millis%twelve_seconds);

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




		clEnqueueWriteBuffer(queue,
			application_state_buffer,
			CL_TRUE,
			0,
			ARBITRARY_DATA_POINTS * sizeof(float),
			application_state,
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
	err |= clSetKernelArg(kernel, 6, sizeof(cl_mem), &application_state_buffer);

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


