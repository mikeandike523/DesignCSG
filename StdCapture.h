//coutesy of https://stackoverflow.com/a/68348821

#ifdef _MSC_VER
#include <io.h>
#define popen _popen 
#define pclose _pclose
#define stat _stat 
#define dup _dup
#define dup2 _dup2
#define fileno _fileno
#define close _close
#define pipe _pipe
#define read _read
#define eof _eof
#else
#include <unistd.h>
#endif
#include <fcntl.h>
#include <stdio.h>
#include <mutex>
#include <chrono>
#include <thread>

#define STD_OUT_FD (_fileno(stdout)) 


#define STD_ERR_FD (_fileno(stderr)) 


class StdCapture
{
public:

	StdCapture();

	void BeginCapture();
	bool IsCapturing();
	bool EndCapture();
	std::string GetCapture();

private:
	enum PIPES { READ, WRITE };

	int secure_dup(int src);
	void secure_pipe(int* pipes);
	void secure_dup2(int src, int dest);
	void secure_close(int& fd);

	int m_pipe[2];
	int m_oldStdOut;
	int m_oldStdErr;
	bool m_capturing;
	std::mutex m_mutex;
	std::string m_captured;
};