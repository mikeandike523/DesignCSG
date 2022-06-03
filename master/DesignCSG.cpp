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
#include "Grid.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <queue>
#include <chrono>
#define CMS_DEBUG
#define logRoutine DebugPrint
#include <mutex>
#include <filesystem>

std::string logString;
std::mutex logStringMutex;
std::string designPath = "Designs\\Untitled.py";
void setDesignPath(std::string dp) {
	designPath = dp;
	Utils::writeFile("designPath.txt", dp);
}

std::string newFileTemplate = 
"from DesignCSG import *\n"
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
	void OnIdle(wxIdleEvent& event);
	void OnNew(wxCommandEvent& event);
	void OnOpen(wxCommandEvent& event);
	void OnDelete(wxCommandEvent& event);
	void OnSaveAs(wxCommandEvent& event);

	wxDECLARE_EVENT_TABLE();

};

void loadRoutine(MyFrame* ths);

wxBEGIN_EVENT_TABLE(MyFrame, wxFrame)
EVT_MENU(wxID_EXIT, MyFrame::OnExit)
EVT_MENU(ID_Run, MyFrame::OnRun)
EVT_MENU(ID_Save, MyFrame::OnSave)
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

enum OFD_Ids {

	ID_ok_button = 10

};

class OFD : wxDialog {

public:

	int selected = 0;

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

		

		wxButton* okButton = new wxButton(this,ID_ok_button, "Open");

		//okButton->Bind(wxEVT_BUTTON, &okButtonPressed, this);
	//	okButton->Bind(wxEVT_BUTTON, wxEventHandler(okButtonPressed),-1,-1,nullptr);


		vbox->Add(okButton, wxSizerFlags().CenterHorizontal());

		SetSizer(vbox);

		Centre();

		int retCode = ShowModal();

		DebugPrint("Modal exit code: %d\n", retCode);

		if (selected==0) {
			DebugPrint("Modal was exited or there was an error.\n");
		}
		else {

			DebugPrint("Ok button pressed.\n");

			if (lb->GetSelection() == wxNOT_FOUND) {
				setDesignPath("Designs\\Untitled.py");
				if (!std::filesystem::is_regular_file("Designs\\Untitled.py")) {
					Utils::writeFile("Designs\\Untitled.py", newFileTemplate);
				}
			}
			else
			setDesignPath("Designs\\" + filenames[lb->GetSelection()]);
		
		}



	
		Destroy();
	
	}

	void okButtonPressed(wxCommandEvent& event) {
		selected = 1;
		EndModal(0);
	}

	DECLARE_EVENT_TABLE();

	
};

BEGIN_EVENT_TABLE(OFD,wxDialog)

EVT_BUTTON(ID_ok_button,OFD::okButtonPressed)

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

void IdleRoutine(MyFrame * ctx) {

	if (ctx->sbmp->is_init) {
		char message[512];
		snprintf(message, 512, "Max Bytes %d; Max Floats %d\n", ctx->sbmp->ARBITRARY_DATA_POINTS * 4, ctx->sbmp->ARBITRARY_DATA_POINTS);
		static int loggedOnce = 0;
		if (!loggedOnce) {
			log(ctx->debugConsole, message, Mode::A);
			loggedOnce = 1;
		}
	}

	std::lock_guard<std::mutex> guard(logStringMutex);

	if (std::string(ctx->debugConsole->GetValue().c_str()) != logString) {

		ctx->debugConsole->SetValue(wxString(logString));
		
	}

}

void MyFrame::OnIdle(wxIdleEvent& event) {

	IdleRoutine(this);

	event.RequestMore();

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

	//freopen("consolelog.txt", "w", stdout);
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



	//wxStyledTextCtrl * designLibraryText = new wxStyledTextCtrl(tabs, wxNewId(), wxDefaultPosition, wxDefaultSize);

	//dlText = designLibraryText;

	//setupStyledTextControl(designLibraryText, Utils::readFile("designlibrary.py"));

	//wxStyledTextCtrl* designCSGText = new wxStyledTextCtrl(tabs, wxNewId(), wxDefaultPosition, wxDefaultSize);

	//dlText = designCSGText;

	//dCSGText = designCSGText;

	//setupStyledTextControl(designCSGText, Utils::readFile("DesignCSG.py"));


	tabs->AddPage(text, wxString(std::filesystem::path(designPath).filename()), false, -1);

	//tabs->AddPage(designLibraryText, "designlibrary.py", false, -1);

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
	this->sbmp = new BasicDrawPane((wxFrame*)pnl, wxSize(640, 480), debugConsole);
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
	Utils::writeFile("designPath.txt", designPath);
}

void loadRoutine(MyFrame* ths) {

	if (!std::filesystem::is_regular_file(designPath)) {
		Utils::writeFile(designPath.c_str(),newFileTemplate);
	}
	setEditorTitle(ths->tabs);
	ths->text->SetValue(wxString(Utils::readFile(designPath.c_str()).c_str()));
}



void updateArbitraryData(MyFrame * ctx) {

	float * arbitrary_data_temp = (float *) calloc(ctx->sbmp->ARBITRARY_DATA_POINTS,sizeof(float));
	if (std::filesystem::is_regular_file("arbitrary_data.hex")) {

		FILE* dataFile = fopen("arbitrary_data.hex", "rb");
		size_t itemCount = 0;
		uint8_t dataPoint[4];
		while (fread(&dataPoint, 4, 1, dataFile)) {
			/*if (cms::is_big_endian()) {
				cms::reverseFourBytes(dataPoint);
			}*/
			float dataPointf = 0.0;
			memcpy(&dataPointf, dataPoint, 4);
			if (itemCount < ctx->sbmp->ARBITRARY_DATA_POINTS)
				arbitrary_data_temp[itemCount++] = dataPointf;
			else
				break;
		}
		fclose(dataFile);
		ctx->sbmp->setArbitraryData(arbitrary_data_temp, itemCount);

	}
	free(arbitrary_data_temp);

}

void MyFrame::OnRun(wxCommandEvent& event) {




	log(debugConsole, "Updating.", Mode::W);

	saveRoutine(this);

	Utils::writeFile("compiled.py", Utils::readFile(designPath.c_str()));

	clearLogs(debugConsole);

	Utils::runProcess("", "C:\\Windows\\System32\\cmd.exe /K \".\\Python310\\python.exe compiled.py > .\\log.txt 2>&1 && exit || exit\"");

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

	updateArbitraryData(this);

	sbmp->loadParameters();

	IdleRoutine(this);

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



