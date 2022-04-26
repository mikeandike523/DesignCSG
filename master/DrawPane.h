#ifndef _drawPane_
#define _drawPane_

#include <wx/wx.h>
#include <CL/cl.h>

#include "CVector.h"


#define BYTE uint8_t
#define PI 3.1415926
#define speed 0.5f
#define yawspeed PI/30.0
#define MAX_OBJECTS 512
#define MAX_BUILD_STEPS 256
#define IZOOM 2.5
#define STACK_MEMORY_PER_PIXEL 64



enum class LoadSceneResult{

	SUCCESS,
	PROGRAM_BUILD_FAILURE,
	GENERIC_FAILURE

};

class BasicDrawPane : public wxPanel
{

public:
	int ARBITRARY_DATA_POINTS = 65536 / 4;
	int initialized();
	BasicDrawPane(wxFrame* parent, wxSize s, wxTextCtrl* _console);
	void mouseMoved(wxMouseEvent& event);
	void mouseDown(wxMouseEvent& event);
	void mouseWheelMoved(wxMouseEvent& event);
	void mouseReleased(wxMouseEvent& event);
	void rightClick(wxMouseEvent& event);
	void mouseLeftWindow(wxMouseEvent& event);
	void keyPressed(wxKeyEvent& event);
	void keyReleased(wxKeyEvent& event);
	void idled(wxIdleEvent& event);
	LoadSceneResult loadScene();
	void setArbitraryData(float* data, size_t items);




	cl_device_id device;
	cl_context context;
	cl_program program;
	cl_kernel kernel;
	cl_command_queue queue;
	cl_int err;
	int is_init;
	uint8_t* shape_id_bank;
	uint8_t* material_id_bank;
	float* object_position_bank;
	float* object_right_bank;
	float* object_up_bank;
	float* object_forward_bank;
	uint8_t* pixel_data;
	int* build_procedure_data;
	float* arbitrary_data;
	int num_objects = 0;
	int num_build_steps = 0;
	float campos[3] = { 0.0,0.0,-IZOOM };
	float right[3] = { 1.0,0.0,0.0 };
	float forward[3] = { 0.0,0.0,1.0 };
	float up[3] = { 0.0,1.0,0.0 };
	Vector3f v_right = v3f(1.0, 0.0, 0.0);
	Vector3f v_up = v3f(0.0, 1.0, 0.0);
	Vector3f v_forward = v3f(0.0, 0.0, 1.0);
	cl_mem pixdataout_buffer;
	cl_mem camposin_buffer;
	cl_mem rightin_buffer;
	cl_mem upin_buffer;
	cl_mem forwardin_buffer;


	cl_mem arbitrary_data_buffer;

	cl_mem application_state_buffer;
	float* application_state;

	const size_t global_size[2] = { 640,480 };
	const size_t local_size[2] = { 8,8 };

	int pMX = 0, pMY = 0;
	int cMX = 0, cMY = 0;
	int dragging = 0;

	wxTextCtrl* console;
	int pvalid = 0;

	DECLARE_EVENT_TABLE()


};

#endif 