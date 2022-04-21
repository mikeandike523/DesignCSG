#pragma once

#include <string>
#include <vector>

namespace Compiler {


	class tFSM { //tokenizer FSM
	public:
		tFSM();

		std::vector<std::string> feed(char in);
		
	private:
		//need to adjust to handle comments later
		std::string state;

		int belongsTo(char c, std::string cls);

	};


}
