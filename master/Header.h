#ifndef _drawPane_
#define _drawPane_

#include "wx/wx.h"
#include "wx/glcanvas.h"

class BasicDrawPane : public wxPanel
{

public:
	BasicDrawPane(wxFrame* parent);

	void render(wxPaintEvent& evt);

	// events
	void mouseMoved(wxMouseEvent& event);
	void mouseDown(wxMouseEvent& event);
	void mouseWheelMoved(wxMouseEvent& event);
	void mouseReleased(wxMouseEvent& event);
	void rightClick(wxMouseEvent& event);
	void mouseLeftWindow(wxMouseEvent& event);
	void keyPressed(wxKeyEvent& event);
	void keyReleased(wxKeyEvent& event);

	DECLARE_EVENT_TABLE()
};

#endif 