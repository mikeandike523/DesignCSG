//Coutesy of https://docs.microsoft.com/en-us/windows/win32/toolhelp/traversing-the-thread-list

#include <windows.h>
#include "tlhelp32.h"
#include <tchar.h>
#include <cstdio>

#ifndef logRoutine
#define logRoutine printf
#endif

namespace GetThreadCount {

	//  Forward declarations:
	inline void printError(CHAR* msg);


	inline BOOL GetNumProcessThreads(DWORD dwOwnerPID, int* numThreads)
	{
		*numThreads = 0;

		HANDLE hThreadSnap = INVALID_HANDLE_VALUE;
		THREADENTRY32 te32;

		// Take a snapshot of all running threads  
		hThreadSnap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
		if (hThreadSnap == INVALID_HANDLE_VALUE)
			return(FALSE);

		// Fill in the size of the structure before using it. 
		te32.dwSize = sizeof(THREADENTRY32);

		// Retrieve information about the first thread,
		// and exit if unsuccessful
		if (!Thread32First(hThreadSnap, &te32))
		{
			printError((CHAR*)"Thread32First");  // Show cause of failure
			CloseHandle(hThreadSnap);     // Must clean up the snapshot object!
			return(FALSE);
		}

		// Now walk the thread list of the system,
		// and display information about each thread
		// associated with the specified process
		do
		{
			if (te32.th32OwnerProcessID == dwOwnerPID)
			{
				(*numThreads)++;
			}
		} while (Thread32Next(hThreadSnap, &te32));

		logRoutine("\n");

		//  Don't forget to clean up the snapshot object.
		CloseHandle(hThreadSnap);
		return(TRUE);
	}

	inline void printError(CHAR* msg)
	{
		DWORD eNum;
		TCHAR sysMsg[256];
		TCHAR* p;

		eNum = GetLastError();
		FormatMessage(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
			NULL, eNum,
			MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
			sysMsg, 256, NULL);

		// Trim the end of the line and terminate it with a null
		p = sysMsg;
		while ((*p > 31) || (*p == 9))
			++p;
		do { *p-- = 0; } while ((p >= sysMsg) &&
			((*p == '.') || (*p < 33)));

		// Display the message
		logRoutine(("\n  WARNING: %s failed with error %d (%s)"), msg, eNum, sysMsg);

	}

}