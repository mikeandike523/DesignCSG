#ifndef READLOOKUPTABLE_HPP
#define READLOOKUPTABLE_HPP

#ifndef logRoutine
#define logRoutine printf
#endif

#include <vector>
#include <map>
#include <string>

#include "geometry.hpp"

namespace cms {

	//courtesy of https://www.techiedelight.com/split-string-cpp-using-delimiter/
	std::vector<std::string> tokenize(std::string const& str, const char delim)
	{

		std::vector<std::string> out;
		size_t start;
		size_t end = 0;

		while ((start = str.find_first_not_of(delim, end)) != std::string::npos)
		{
			end = str.find(delim, start);
			out.push_back(str.substr(start, end - start));
		}
		return out;
	}

	inline std::map<int, std::vector<IndexTriangle>> getIndexTrianglesFromTable(const char* filename) {

		std::map<int, std::vector<IndexTriangle>> trsMap;

		std::string lookupTableFileContents;

		FILE* lookupTableFile = fopen(filename, "r");
		char c;
		while (fread(&c, 1, 1, lookupTableFile)) {
			lookupTableFileContents += c;
		}
		fclose(lookupTableFile);

		// logRoutine("Lookup Table File Contents:\n%s\n",lookupTableFileContents.c_str());

		std::vector<std::string> lines = tokenize(lookupTableFileContents, '\n');

		// logRoutine("sz %d\n",lines.size());

		for (int i = 0; i < lines.size(); i++) {

			if (lines[i] == "\t") { trsMap[i] = std::vector<IndexTriangle>{}; continue; };

			std::vector<std::string> cyclesStrings = tokenize(lines[i], ';');
			std::vector<IndexTriangle> trs;
			for (std::string s : cyclesStrings) {
				std::vector<int> cycle;
				std::vector<std::string> indicesStrings = tokenize(s, ',');
				for (std::string s2 : indicesStrings) {
					cycle.push_back(std::stoi(s2));
				}
				std::vector<IndexTriangle> strip = getIndexTriangleStrip(cycle);
				for (IndexTriangle tr : strip) {
					trs.push_back(tr);
				}

			}

			trsMap[i] = trs;

		}

		return trsMap;

	}

}


#endif //READLOOKUPTABLE_HPP
