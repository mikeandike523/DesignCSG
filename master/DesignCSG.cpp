int edone = 1;
int hasModel = 0;

#include "wx/wx.h"
#include <wx/stc/stc.h>
#include <wx/rawbmp.h>
#include <wx/notebook.h>
#include <wx/listbox.h>
#include <Windows.h>
#include "DrawPane.h"
#include "Utils.h"
#include "Evaluator.h"
#include "Grid.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <queue>
#include "ISV.hpp"
#include <chrono>
#define CMS_DEBUG
#define logRoutine DebugPrint
#include "mesh.hpp"
#include "readLookupTable.hpp"
#include "utils.hpp"
#include "GetThreadCount.h"
#include <mutex>
#include <filesystem>

Evaluator* global_evaluator = nullptr;
std::string logString;
std::mutex logStringMutex;
std::string designPath = "Designs\\Untitled.py";
void setDesignPath(std::string dp) {
	designPath = dp;
	Utils::writeFile("designPath.txt", dp);
}

std::string newFileTemplate = 
"from DesignCSG import *\n"
"from designLibrary import *\n"
"\n"
"\n"

"#Your code here...\n"

"\n"
"\n"
"commit()\n"
;


enum class Mode {
	W,
	A
};

void log(wxTextCtrl* ctrl, std::string message, Mode mode);
void clearLogs(wxTextCtrl* ctrl);


enum
{
	ID_Run = 1,
	ID_Save = 2,
	ID_Export = 3,
	ID_New = 4,
	ID_Open = 5,
	ID_Delete = 6,
	ID_SaveAs = 7
};

class MyApp : public wxApp
{
public:
	virtual bool OnInit();

};

class MyFrame : public wxFrame
{

public:

	MyFrame(const wxString& title, const wxPoint& pos, const wxSize& size);
	BasicDrawPane* sbmp;
	wxTextCtrl* debugConsole;
	wxStyledTextCtrl* text;
	wxStyledTextCtrl* dlText;
	wxStyledTextCtrl* dCSGText;
	wxNotebook* tabs;
	int editCounter = -1;

private:

	void OnExit(wxCommandEvent& event);
	void OnAbout(wxCommandEvent& event);;
	void OnRun(wxCommandEvent& event);
	void OnSave(wxCommandEvent& event);
	void OnExport(wxCommandEvent& event);
	void OnIdle(wxIdleEvent& event);
	void OnNew(wxCommandEvent& event);
	void OnOpen(wxCommandEvent& event);
	void OnDelete(wxCommandEvent& event);
	void OnSaveAs(wxCommandEvent& event);
	void OnExportInner();

	wxDECLARE_EVENT_TABLE();

};

void loadRoutine(MyFrame* ths);

wxBEGIN_EVENT_TABLE(MyFrame, wxFrame)
EVT_MENU(wxID_EXIT, MyFrame::OnExit)
EVT_MENU(ID_Run, MyFrame::OnRun)
EVT_MENU(ID_Save, MyFrame::OnSave)
EVT_MENU(ID_Export, MyFrame::OnExport)
EVT_MENU(ID_New,MyFrame::OnNew)
EVT_MENU(ID_Open,MyFrame::OnOpen)
EVT_MENU(ID_Delete,MyFrame::OnDelete)
EVT_MENU(ID_SaveAs, MyFrame::OnSaveAs)

EVT_IDLE(MyFrame::OnIdle)
wxEND_EVENT_TABLE()
wxIMPLEMENT_APP(MyApp);


std::string stripPY(std::string s) {

	if (s.find(".py") != std::string::npos) {
		s = s.substr(0, s.size() - 3);
	}
	return s;
}

class OFD : wxDialog {

public:

	OFD() : wxDialog(nullptr,wxID_ANY,"Open an Existing Design") {

		std::vector<std::string> filenames;

		for (const auto& e : std::filesystem::directory_iterator("Designs")) {
			filenames.push_back(std::string(e.path().filename().u8string()));
		}

		wxListBox * lb = new wxListBox(this, wxID_ANY,wxDefaultPosition,wxDefaultSize,wxArrayString(),wxLB_SINGLE);

		wxBoxSizer * vbox = new wxBoxSizer(wxVERTICAL);
		
		vbox->Add(lb, wxSizerFlags().Expand());



		for (std::string& s : filenames) {
			lb->Append(std::vector<wxString>{wxString(s)});
		}

		wxButton* okButton = new wxButton(this,wxID_OK,"Open");

		//okButton->Bind(wxEVT_BUTTON, &okButtonPressed, this);
	//	okButton->Bind(wxEVT_BUTTON, wxEventHandler(okButtonPressed),-1,-1,nullptr);


		vbox->Add(okButton, wxSizerFlags().CenterHorizontal());

		SetSizer(vbox);

		Centre();

		int retCode = ShowModal();

		DebugPrint("Modal exit code: %d", retCode);

		if (retCode != 0) {
			DebugPrint("Modal was exited or there was an error.\n");
		}
		else {

			if (lb->GetSelection() == wxNOT_FOUND) {
				setDesignPath("Designs\\Untitled.py");
				if (!std::filesystem::is_regular_file("Designs\\Untitled.py")) {
					Utils::writeFile("Designs\\Untitled.py", newFileTemplate);
				}
			}
			else
			setDesignPath("Designs\\" + filenames[lb->GetSelection()]);
		
		}

	//	delete vbox;
	//	delete lb;
	//	delete okButton;

		//Connect(ID_Ok, wxEVT_BUTTON, wxEventHandler(okButtonPressed));


	
	}

	void okButtonPressed(wxCommandEvent& event) {
		EndModal(0);
	}

	DECLARE_EVENT_TABLE();

	
};

BEGIN_EVENT_TABLE(OFD,wxDialog)

EVT_BUTTON(wxID_OK,OFD::okButtonPressed)

END_EVENT_TABLE()



void setEditorTitle(wxNotebook * nb) {

	std::string basename = std::string(std::filesystem::path(designPath).filename().u8string());
	nb->SetPageText(0, basename);


}

std::string getDesignBasename() {

	return std::string(std::filesystem::path(designPath).filename().u8string());
}



void MyFrame::OnSaveAs(wxCommandEvent& event) {
	wxTextEntryDialog dlg(this, "Enter a new name for the new design.", "", "");
	if (dlg.ShowModal() == wxID_OK)
	{
		
		std::string value = stripPY(std::string(dlg.GetValue().c_str())) + ".py";
		Utils::writeFile(("Designs\\" + value).c_str(), std::string(text->GetValue().c_str()));
		std::filesystem::remove(std::filesystem::path(designPath));

		designPath = "Designs\\" + value;
		loadRoutine(this);
	}
}

void MyFrame::OnOpen(wxCommandEvent& event) {
	std::string originalPath = designPath;
	OFD ofd;
	if(designPath!=originalPath)
	loadRoutine(this);
}

void MyFrame::OnDelete(wxCommandEvent& event) {


	wxMessageDialog mdlg = wxMessageDialog(
	this,
		wxString(std::string(std::string("Really delete ") + getDesignBasename() + std::string("?")).c_str()),
		"",
		wxYES_NO 
	
	);

	if (mdlg.ShowModal() == wxID_YES) {
		std::filesystem::remove(designPath);
		setDesignPath("Designs\\Untitled.py");
		loadRoutine(this);
	}

}

void MyFrame::OnNew(wxCommandEvent& event) {
	wxTextEntryDialog dlg(this,"Enter a name for the new design.","","");
	if (dlg.ShowModal() == wxID_OK)
	{
		// We can be certain that this string contains letters only.
		std::string value = stripPY(std::string(dlg.GetValue().c_str()))+".py";
		Utils::writeFile(("Designs\\" + value).c_str(), newFileTemplate);
		designPath = "Designs\\" + value;
		loadRoutine(this);
	}


}

void MyFrame::OnIdle(wxIdleEvent& event) {

	std::lock_guard<std::mutex> guard(logStringMutex);


	if (std::string(debugConsole->GetValue().c_str()) != logString) {
		debugConsole->SetValue(wxString(logString));
		event.RequestMore();
	}

}

bool MyApp::OnInit()
{

	if (std::filesystem::is_regular_file("designPath.txt")) {
		designPath = Utils::readFile("designPath.txt");
	
	}
	else {
		Utils::writeFile("designPath.txt","Designs\\Untitled.py");
		designPath = Utils::readFile("designPath.txt");
	
	}

	freopen("consolelog.txt", "w", stdout);
	MyFrame* frame = new MyFrame("DesignCSG", wxDefaultPosition, wxSize(640 + 350, 700));
	frame->Show(true);
	return true;

}
MyFrame::MyFrame(const wxString& title, const wxPoint& pos, const wxSize& size)
	: wxFrame(NULL, wxNewId(), title, pos, size)
{


	if (!std::filesystem::is_directory("Exports")) {
		system("mkdir Exports");
	}

	Maximize(true);
	wxMenu* menuFile = new wxMenu;

	menuFile->Append(ID_New, "&New",
		"Create a new design");
	menuFile->Append(ID_Open, "&Open",
		"Open an existing design");
	menuFile->Append(ID_Save, "&Save",
		"Save your design");
	menuFile->Append(ID_SaveAs, "&Save as","Save your design with a new name.");

	menuFile->Append(ID_Delete, "&Delete this design", "Delete this design");

	menuFile->Append(ID_Run, "&Run",
		"Run your design");

	menuFile->Append(ID_Export, "&Export",
		"Export your design");

	wxMenu* menuHelp = new wxMenu;
	menuHelp->Append(wxID_ABOUT);
	wxMenuBar* menuBar = new wxMenuBar;
	menuBar->Append(menuFile, "&File");
	menuBar->Append(menuHelp, "&Help");
	SetMenuBar(menuBar);
	CreateStatusBar();
	SetStatusText("DesignCSG -- Untitled.py");
	wxBoxSizer* hbox = new wxBoxSizer(wxHORIZONTAL);


	wxPanel* editorPanel = new wxPanel(this, wxID_ANY, wxDefaultPosition,wxDefaultSize);
	editorPanel->SetBackgroundColour(wxColor(0,0,255));
	wxBoxSizer* editorBoxSizer = new wxBoxSizer(wxVERTICAL);
	editorPanel->SetSizer(editorBoxSizer);

	tabs = new wxNotebook(editorPanel, wxID_ANY, wxDefaultPosition, wxDefaultSize, 0L, wxString::FromAscii("tabs"));

	auto setupStyledTextControl = [](wxStyledTextCtrl* ctrl, std::string initialText) {

		ctrl->StyleSetForeground(wxSTC_STYLE_LINENUMBER, wxColour(75, 75, 75));
		ctrl->StyleSetBackground(wxSTC_STYLE_LINENUMBER, wxColour(220, 220, 220));
		ctrl->SetWrapMode(wxSTC_WRAP_WORD);
		ctrl->SetText(initialText);
		ctrl->StyleClearAll();
		ctrl->SetLexer(wxSTC_LEX_PYTHON);
		ctrl->StyleSetForeground(wxSTC_H_DOUBLESTRING, wxColour(255, 0, 0));
		ctrl->StyleSetForeground(wxSTC_H_SINGLESTRING, wxColour(255, 0, 0));
		ctrl->StyleSetForeground(wxSTC_H_ENTITY, wxColour(255, 0, 0));
		ctrl->StyleSetForeground(wxSTC_H_TAG, wxColour(0, 150, 0));
		ctrl->StyleSetForeground(wxSTC_H_TAGUNKNOWN, wxColour(0, 150, 0));
		ctrl->StyleSetForeground(wxSTC_H_ATTRIBUTE, wxColour(0, 0, 150));
		ctrl->StyleSetForeground(wxSTC_H_ATTRIBUTEUNKNOWN, wxColour(0, 0, 150));
		ctrl->StyleSetForeground(wxSTC_H_COMMENT, wxColour(150, 150, 150));
		ctrl->SetMarginCount(2);
		ctrl->SetMarginType(1, wxSTC_MARGIN_NUMBER);
	};

	text = new wxStyledTextCtrl(tabs, wxNewId(), wxDefaultPosition, wxDefaultSize);

	setupStyledTextControl(text, Utils::readFile("Designs\\Untitled.py"));



	wxStyledTextCtrl * designLibraryText = new wxStyledTextCtrl(tabs, wxNewId(), wxDefaultPosition, wxDefaultSize);

	dlText = designLibraryText;

	setupStyledTextControl(designLibraryText, Utils::readFile("designlibrary.py"));

	//wxStyledTextCtrl* designCSGText = new wxStyledTextCtrl(tabs, wxNewId(), wxDefaultPosition, wxDefaultSize);

	//dlText = designCSGText;

	//dCSGText = designCSGText;

	//setupStyledTextControl(designCSGText, Utils::readFile("DesignCSG.py"));


	tabs->AddPage(text, wxString(std::filesystem::path(designPath).filename()), false, -1);

	tabs->AddPage(designLibraryText, "designlibrary.py", false, -1);

//	tabs->AddPage(designCSGText, "DesignCSG.py", false, -1);


	editorBoxSizer->Add(tabs, wxSizerFlags(1).Expand());

	wxPanel* pnl = new wxPanel(this, wxID_ANY, wxDefaultPosition, wxDefaultSize);
	wxBoxSizer* panel_box = new wxBoxSizer(wxVERTICAL);
	wxBoxSizer* panel_box_2 = new wxBoxSizer(wxVERTICAL);
	pnl->SetSizer(panel_box_2);
	pnl->SetBackgroundColour(wxColor(255, 255, 255));

	hbox->Add(editorPanel, wxSizerFlags(1).Expand());


	hbox->Add(panel_box, wxSizerFlags(1).Expand());
	this->debugConsole = new wxTextCtrl((wxWindow*)pnl, wxID_ANY, wxEmptyString, wxDefaultPosition, wxSize(640, 200), wxTE_MULTILINE);
	this->sbmp = new BasicDrawPane((wxFrame*)pnl, wxSize(640, 480), debugConsole, &global_evaluator);
	panel_box->Add(pnl, wxSizerFlags(1).Expand());
	panel_box_2->Add(this->sbmp, wxSizerFlags(1).CenterHorizontal());
	debugConsole->SetEditable(false);
	debugConsole->SetBackgroundColour(wxColor(0, 0, 255));
	debugConsole->SetForegroundColour(wxColor(255, 255, 255));
	wxBoxSizer* panel_box_3 = new wxBoxSizer(wxHORIZONTAL);
	panel_box_2->Add(panel_box_3, wxSizerFlags(1).Expand());
	panel_box_3->Add(debugConsole, wxSizerFlags(1).Expand());
	SetSizer(hbox);
	Utils::writeFile("ver.txt", "0");

	loadRoutine(this);

}

void MyFrame::OnExit(wxCommandEvent& event)
{
	Close(true);
}

void MyFrame::OnAbout(wxCommandEvent& event)
{
	wxMessageBox("Design CAD Models With Code!",
		"About DesignCSG", wxOK | wxICON_INFORMATION);
}

void saveRoutine(MyFrame * ths) {
	Utils::writeFile(designPath.c_str(), std::string(ths->text->GetText()));
	Utils::writeFile("designlibrary.py", std::string(ths->dlText->GetText()));
	//Utils::writeFile("DesignCSG.py", std::string(ths->dCSGText->GetText()));
	Utils::writeFile("designPath.txt", designPath);
}

void loadRoutine(MyFrame* ths) {

	if (!std::filesystem::is_regular_file(designPath)) {
		Utils::writeFile(designPath.c_str(),newFileTemplate);
	}
	setEditorTitle(ths->tabs);
	ths->text->SetValue(wxString(Utils::readFile(designPath.c_str()).c_str()));
}

void MyFrame::OnRun(wxCommandEvent& event) {

	log(debugConsole, "Updating.", Mode::W);

	saveRoutine(this);

	Utils::writeFile("compiled.py", Utils::readFile(designPath.c_str()));

	clearLogs(debugConsole);

	Utils::runProcess("", "C:\\Windows\\System32\\cmd.exe /K \".\\Python310\\python.exe compiled.py > .\\log.txt 2>&1 && exit || exit\"");
	Utils::runProcess("", "C:\\Windows\\System32\\cmd.exe /K copy /b k1.cl + scene.cl k1build.cl && exit || exit");
	Utils::runProcess("", "C:\\Windows\\System32\\cmd.exe /K copy /b k2.cl + scene.cl k2build.cl && exit || exit");
	
	long then = Utils::time_ms();

	LoadSceneResult result;

	if (this->sbmp->initialized()) {
		result = this->sbmp->loadScene();
	}


	log(debugConsole, std::string(debugConsole->GetValue().c_str()),Mode::W);

	if (result == LoadSceneResult::SUCCESS) {
		log(debugConsole, "Brushes compiled successfully.\n", Mode::A);
	}

	log(debugConsole, Utils::readFile("log.txt"), Mode::A);
	hasModel = 1;

}

void MyFrame::OnSave(wxCommandEvent& event)
{
	saveRoutine(this);
}

void log(wxTextCtrl* ctrl, std::string message, Mode mode) {

	std::lock_guard<std::mutex> guard(logStringMutex);
	std::string existing = logString;
	if (mode == Mode::W)
		existing = message;
	else
		existing += message;
	logString = existing;

}

void logDelete(wxTextCtrl* ctrl, int numChars) {

	std::lock_guard<std::mutex> guard(logStringMutex);
	std::string existing = logString;
	existing = existing.substr(0, existing.length() - numChars);
	logString = existing;

}

void clearLogs(wxTextCtrl* ctrl) {
	std::lock_guard<std::mutex> guard(logStringMutex);
	logString = "";
	ctrl->SetValue("");

}

enum class ExportProcessState {

	IDLE,
	ESTIMATING_BOUNDING_BOX,
	PERFORMING_CMS,
	RETOPOLOGIZING,
	PERFORMING_GRADIENT_DESCENT,
	WRITING_TRIANGLES_TO_STL,
	WRITING_TRIANGLES_TO_PLY,
	COMPLETE

};

cms::Mesh* mesh = nullptr;
std::map<int, int> histogram;
int minimumOctreeLevel = 5;
int maximumOctreeLevel = 7;
int gridLevel = 8;
float complexSurfaceThreshold = PI / 2.0f * 0.5;
float boundingBoxHalfDiameter = 15.0f;
int gradientDescentSteps = 50;
int numTrianglesWritten;
int maxTriangles;
int writingTriangles = 0;
int gradientDescentStepsCompleted = 0;
int cacheSubdivision = 16;
int queriesBeforeGC = 64;
int queriesBeforeFree = 1024;


ExportProcessState exportProcessState = ExportProcessState::IDLE;


std::pair<int, std::string> buildStatus;

void MyFrame::OnExportInner() {

	if (this->sbmp->initialized()) {

		//log(debugConsole, "Exporting...\n", Mode::W);
		DebugPrint("Exporting.\n");
		DebugPrint("Autodetect build volume.\n");

		

		 buildStatus = global_evaluator->build(
			this->sbmp->shape_id_bank_buffer,
			this->sbmp->object_position_bank_buffer,
			this->sbmp->object_right_bank_buffer,
			this->sbmp->object_up_bank_buffer,
			this->sbmp->object_forward_bank_buffer,
			this->sbmp->num_objects_buffer,
			this->sbmp->build_procedure_data_buffer,
			this->sbmp->num_build_steps_buffer
		);

		if (buildStatus.first == -1) {
			log(debugConsole,"Error building export kernel:\n"+buildStatus.second,Mode::W);
			return;
		}

		exportProcessState = ExportProcessState::ESTIMATING_BOUNDING_BOX;
		
#define BOUNDING_BOX_DIAMETER boundingBoxHalfDiameter
#define BOUNDING_BOX_RESOLUTION 256
#define BB_EPSILON ((float)BOUNDING_BOX_DIAMETER/BOUNDING_BOX_RESOLUTION*1.0)
#define ISOLEVEL 0.000
#define MCUBES_EPS 0.000010
		const float cube_diameter = (float)BOUNDING_BOX_DIAMETER / BOUNDING_BOX_RESOLUTION;
		std::vector<v3f_t> grid;
		for (int ix = -BOUNDING_BOX_RESOLUTION / 2; ix < BOUNDING_BOX_RESOLUTION / 2; ix++)
			for (int iy = -BOUNDING_BOX_RESOLUTION / 2; iy < BOUNDING_BOX_RESOLUTION / 2; iy++)
				for (int iz = -BOUNDING_BOX_RESOLUTION / 2; iz < BOUNDING_BOX_RESOLUTION / 2; iz++)
				{
					grid.push_back(v3f_add(v3f(-cube_diameter / 2), v3f_scale(v3f(ix, iy, iz), cube_diameter)));
				}
		std::vector<float> sdfvals = global_evaluator->eval_sdf_at_points(grid);
		std::vector<std::pair<v3f_t, float>> data;
		data.reserve(sdfvals.size());
		std::transform(grid.begin(), grid.end(), sdfvals.begin(), std::back_inserter(data),
			[](v3f_t a, float b) { return std::make_pair(a, b); });
		std::vector<std::pair<v3f_t, float>> interiorPoints;
		std::copy_if(data.begin(), data.end(), std::back_inserter(interiorPoints), [](std::pair<v3f_t, float> p) {return p.second < BB_EPSILON; });
		float minX = 0.0;
		float maxX = 0.0;
		float minY = 0.0;
		float maxY = 0.0;
		float minZ = 0.0;
		float maxZ = 0.0;
		for (int i = 0; i < interiorPoints.size(); i++) {
			v3f_t pt = interiorPoints.at(i).first;
			if (pt.x < minX) minX = pt.x;
			if (pt.x > maxX)maxX = pt.x;
			if (pt.y < minY) minY = pt.y;
			if (pt.y > maxY)maxY = pt.y;
			if (pt.z < minZ) minZ = pt.z;
			if (pt.z > maxZ) maxZ = pt.z;
		}
		v3f_t center = v3f((minX + maxX) * 0.5, (minY + maxY) * 0.5, (minZ + maxZ) * 0.5);
		v3f_t diameters = v3f(maxX - minX, maxY - minY, maxZ - minZ);
		box_t bx = box(center, diameters);
		float mbx = T_max(bx.diameters.x, T_max(bx.diameters.y, bx.diameters.z));
		bx.diameters = v3f(mbx);
		print_box(bx);
		sdfvals.resize(0);
		sdfvals.shrink_to_fit();
		grid.resize(0);
		grid.shrink_to_fit();
		DebugPrint("Setting up CMS export.\n");

		exportProcessState = ExportProcessState::PERFORMING_CMS;

		std::map<int, std::vector<cms::IndexTriangle>> trsMap = cms::getIndexTrianglesFromTable(".\\lookupTable.txt");
		cms::Box3f boundingBox(cms::Vector3f(bx.center.x, bx.center.y, bx.center.z), cms::Vector3f(bx.diameters.x / 2.0f, bx.diameters.y / 2.0f, bx.diameters.z / 2.0f));
		std::function<std::vector<float>(std::vector<v3f_t>&)> evr;
		std::function<std::vector<v3f_t>(std::vector<v3f_t>&)> evrN;
		evr = (std::function<std::vector<float>(std::vector<v3f_t>&)>)(
			[](std::vector<v3f_t>& pts) {
				return global_evaluator->eval_sdf_at_points(pts);
			}
		);
		evrN = (std::function<std::vector<v3f_t>(std::vector<v3f_t>&)>)(
			[](std::vector<v3f_t>& pts) {
				return global_evaluator->eval_normal_at_points(pts);
			}
		);
		int res = 1 << gridLevel;
		ISV::ISV3D64<float, std::function<std::vector<float>(std::vector<v3f_t>&)>> sampler(res, res, res, res / cacheSubdivision, res / cacheSubdivision, res / cacheSubdivision, bx, evr, queriesBeforeFree, queriesBeforeGC);
		ISV::ISV3D64<v3f_t, std::function<std::vector<v3f_t>(std::vector<v3f_t>&)>> samplerN(res, res, res, res / cacheSubdivision, res / cacheSubdivision, res / cacheSubdivision, bx, evrN, queriesBeforeFree, queriesBeforeGC);
		mesh = new cms::Mesh(boundingBox, sampler, 
		samplerN, trsMap, minimumOctreeLevel, maximumOctreeLevel, gridLevel, complexSurfaceThreshold, histogram);
		wxTextCtrl* dC = debugConsole;
		auto logAppend = [&dC](std::string message) {
			log(dC, message, Mode::A);
		};
		logRoutine("Extracting Surface...\n");
		std::vector<cms::Triangle3f> trs = mesh->getSurface();
		delete mesh;

		exportProcessState = ExportProcessState::RETOPOLOGIZING;


		logRoutine("Retopologizing...\n");
		int osize = trs.size();
		trs = cms::retopologize(trs, boundingBox, minimumOctreeLevel, gridLevel);
		DebugPrint("Retopology: Added %d triangles.\n", trs.size() - osize);

		exportProcessState = ExportProcessState::PERFORMING_GRADIENT_DESCENT;

		cms::performGradientDescent(gradientDescentSteps, trs,
			global_evaluator
			,
			&gradientDescentStepsCompleted
		);
		maxTriangles = trs.size();
		writingTriangles = 1;


		exportProcessState = ExportProcessState::WRITING_TRIANGLES_TO_STL;



		cms::writeTrianglesToSTL((std::string("Exports\\")+Utils::replaceExtension(Utils::getBaseName(designPath),".py",".stl")).c_str(), trs, &numTrianglesWritten);
		cms::writeTrianglesToPLY((std::string("Exports\\") + Utils::replaceExtension(Utils::getBaseName(designPath), ".py", ".ply")).c_str(), trs, &numTrianglesWritten);

		writingTriangles = 0;

		char buff1[4096];
		snprintf(buff1,4096, "Python310\\python.exe convert.py \"Exports\\\%s\" && start Exports\\", "Untitled.stl");

		system(buff1);


		system("start Exports");

		exportProcessState = ExportProcessState::COMPLETE;

		edone = 1;
	
	}
	else {
		log(debugConsole, "Cannot Export Yet.", Mode::W);
		edone = 1;
	}

}

//credit dgoguerra https://gist.github.com/dgoguerra/7194777
static const char* humanSize(uint64_t bytes)
{

	const char* suffix[] = { "B", "KB", "MB", "GB", "TB" };
	char length = sizeof(suffix) / sizeof(suffix[0]);
	int i = 0;
	double dblBytes = bytes;
	if (bytes > 1024) {
		for (i = 0; (bytes / 1024) > 0 && i < length - 1; i++, bytes /= 1024)
			dblBytes = bytes / 1024.0;
	}
	static char output[200];
	sprintf(output, "%.02lf %s", dblBytes, suffix[i]);
	return output;

}

std::string logText;

void MyFrame::OnExport(wxCommandEvent& event) {

	if (!hasModel) { log(debugConsole, "Cannot Export Yet.", Mode::W); return; }
	FILE* exportConfigFile = fopen("exportConfig.txt", "rb");
	std::string exportConfigFileContents;
	char c;
	while (fread(&c, 1, 1, exportConfigFile)) {
		exportConfigFileContents += c;
	}
	fclose(exportConfigFile);
	std::vector<std::string> configLines = cms::tokenize(exportConfigFileContents, '\n');
	for (std::string configLine : configLines) {
		std::string cl = std::string(configLine);
		DebugPrint("%s\n", cl.c_str());
	}
	boundingBoxHalfDiameter = std::stof(configLines[0]);
	minimumOctreeLevel = std::stoi(configLines[1]);
	maximumOctreeLevel = std::stoi(configLines[2]);
	gridLevel = std::stoi(configLines[3]);
	complexSurfaceThreshold = std::stof(configLines[4]);
	gradientDescentSteps = std::stoi(configLines[5]);
	cacheSubdivision = std::stoi(configLines[6]);
	queriesBeforeGC = std::stoi(configLines[7]);
	queriesBeforeFree = std::stoi(configLines[8]);

		

	auto task = [](MyFrame* frm) {
		logRoutine("Logging test...\n");
		frm->OnExportInner();
	};
	if (edone) {


		exportProcessState = ExportProcessState::IDLE;

		edone = 0;
		std::thread t(task, this);
		t.detach();
		wxMilliSleep(50);
		unsigned long long start = std::chrono::duration_cast<std::chrono::seconds>(
			std::chrono::system_clock::now().time_since_epoch()).count();
		auto task2 = [/*&start*/](wxTextCtrl* debugConsole, unsigned long long start) {
			while (!edone) {

				if (buildStatus.first == -1) {
				
					edone = 1;
					return;
				}

				auto timeAndMemoryString = [&start]() {
					MEMORYSTATUSEX statex;
					statex.dwLength = sizeof(statex);
					GlobalMemoryStatusEx(&statex);
					unsigned long total = statex.ullTotalVirtual;
					unsigned long avail = statex.ullAvailVirtual;
					unsigned long used = total - avail;
					unsigned long long end = std::chrono::duration_cast<std::chrono::seconds>(
						std::chrono::system_clock::now().time_since_epoch()).count();
					unsigned long long delta = end - start;
					long hours = delta / 3600;
					long minutes = (delta % 3600) / 60;
					long seconds = (delta % 60);
					std::string timeString = "";
					static char buff1[4096];
					if (hours) {
						snprintf(buff1,4096, "%u hours", hours);
						timeString += std::string(buff1);
					}
					if (minutes || (hours && seconds)) {
						snprintf(buff1,4096, " %u minutes", minutes);
						timeString += std::string(buff1);
					}
					if (seconds || minutes || (minutes && hours) || (!seconds && !minutes && !hours)) {
						snprintf(buff1,4096, " %u seconds", seconds);
						timeString += std::string(buff1);
					}
					std::string message = "Memory Usage: " + std::string(humanSize(used)) + "\nTime Elapsed: " + timeString + "\n";

					return message;

				};

				auto histogramString = []() {

					static char buff1[4096];
					std::string message="";
					static std::string hS;
					//std::string hS;
					if (mesh != nullptr) {
						snprintf(buff1,4096, "Total Remaining Items: %d\n", mesh->getRemainingItems());
						message += std::string(buff1);

						message += "Triangle counts:\t";

						if (!mesh->complete) {

							std::lock_guard<std::mutex> lock(mesh->meshMutex);
							hS = "";
							for (auto p : mesh->histogram) {
								snprintf(buff1,4096, "lvl%d->%d\t", p.first, p.second);
								hS += std::string(buff1);
							}
						}
						message += hS;
						message += '\n';
						
					}

					return message;

				};

				logText = "";

				logText += "Exporting...\n";

				logText += timeAndMemoryString();

				static char buff1[4096];

				switch (exportProcessState) {
				
				case ExportProcessState::IDLE: break;

				case ExportProcessState::ESTIMATING_BOUNDING_BOX: 
					
					logText += "Estimating bounding box...\n";
				
	
				break;

				case ExportProcessState::PERFORMING_CMS: 

					logText += "Estimating bounding box... Done.\n";
					logText += "Performing cms algorithm...\n";
					logText += histogramString();

				break;

				case ExportProcessState::RETOPOLOGIZING: 
					
					logText += "Estimating bounding box... Done.\n";
					logText += "Performing cms algorithm...\n";
					logText += histogramString();
					logText += "Done.\n";
					logText += "Retopologizing...\n";

				break;

				case ExportProcessState::PERFORMING_GRADIENT_DESCENT:
				
					logText += "Estimating bounding box... Done.\n";
					logText += "Performing cms algorithm...\n";
					logText += histogramString();
					logText += "Done.\n";
					logText += "Retopologizing... Done.\n";
					snprintf(buff1,4096, "Performing gradient descent... step %d of %d", gradientDescentStepsCompleted, gradientDescentSteps);
					logText += std::string(buff1);

				break;


				case ExportProcessState::WRITING_TRIANGLES_TO_STL:

					logText += "Estimating bounding box... Done.\n";
					logText += "Performing cms algorithm...\n";
					logText += histogramString();
					logText += "Done.\n";
					logText += "Retopologizing... Done.\n";
					snprintf(buff1,4096, "Performing gradient descent... Done.\n");
					logText += std::string(buff1);
					snprintf(buff1,4096,"Writing triangles to STL... %d of %d\n", numTrianglesWritten,maxTriangles);
					logText += std::string(buff1);
			

				break;


				case ExportProcessState::WRITING_TRIANGLES_TO_PLY:

					logText += "Estimating bounding box... Done.\n";
					logText += "Performing cms algorithm...\n";
					logText += histogramString();
					logText += "Done.\n";
					logText += "Retopologizing... Done.\n";
					snprintf(buff1, 4096, "Performing gradient descent... Done.\n");
					logText += std::string(buff1);
					snprintf(buff1, 4096, "Writing triangles to STL... Done.\n");
					logText += std::string(buff1);
					snprintf(buff1, 4096, "Writing triangles to PLY... %d of %d\n", numTrianglesWritten, maxTriangles);
					logText += std::string(buff1);


				break;

				case ExportProcessState::COMPLETE: break;

					

				}

				log(debugConsole,logText,Mode::W);

				wxMilliSleep(100);
			}

			log(debugConsole, "Done exporting.", Mode::A);
			

		};
		std::thread t2(task2, debugConsole, start);
		t2.detach();
	}
	else {
		log(debugConsole, "Export Already In Progress", Mode::W);
	}

}




