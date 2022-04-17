#ifndef UTILS_HPP
#define UTILS_HPP

#include <vector>
#include <cstdint>
#include <cstring>

#ifndef logRoutine
#define logRoutine printf
#endif

#include "geometry.hpp"

#include "happly.h"

namespace cms {


	//courtesy of https://stackoverflow.com/a/1001373
	inline bool is_big_endian(void)
	{
		union {
			uint32_t i;
			char c[4];
		} bint = { 0x01020304 };

		return bint.c[0] == 1;
	}

	inline void reverseFourBytes(uint8_t* buffer) {
		uint8_t temp[4] = { buffer[0],buffer[1],buffer[2],buffer[3] };
		for (int i = 0; i < 4; i++) {
			buffer[3 - i] = temp[i];
		}
	}

	inline void writeFloatToBuffer(float f, uint8_t* buffer) {
		memcpy(buffer, &f, 4);
	}

	inline void writeTrianglesToSTL(const char* filename, std::vector<Triangle3f> trs, int* trianglesWritten) {

		(*trianglesWritten) = 0;

		FILE* outputFile = fopen(filename, "wb");
		uint8_t header[80] = { 0 };
		uint8_t buffer[4] = { 0 };
		fwrite(header, 1, 80, outputFile);
		uint32_t numTrs = trs.size();
		logRoutine("size: %d\n", trs.size());
		memcpy(buffer, &numTrs, 4);
		if (is_big_endian()) {
			reverseFourBytes(buffer);
		}
		fwrite(buffer, 1, 4, outputFile);

		for (Triangle3f tr : trs) {





			for (float f : {
				0.0f,
					0.0f,
					0.0f,
					tr.A.x,
					tr.A.z,
					tr.A.y,
					tr.B.x,
					tr.B.z,
					tr.B.y,
					tr.C.x,
					tr.C.z,
					tr.C.y

			}) {

				// #ifdef CMS_DEBUG
			   //  logRoutine("%f ",f);
			   //  #endif

				writeFloatToBuffer(f, buffer);
				if (is_big_endian()) {
					reverseFourBytes(buffer);
				}
				fwrite(buffer, 1, 4, outputFile);

			}

			//  #ifdef CMS_DEBUG
			 // logRoutine("\n");
			//  #endif

			uint16_t zero = 0;

			fwrite(&zero, 1, 2, outputFile);

			(*trianglesWritten)++;
		}
		fclose(outputFile);

	}


	inline void writeTrianglesToPLY(const char* filename, std::vector<Triangle3f> trs, int * numTrianglesWritten) {

		*numTrianglesWritten = 0;

		// Suppose these hold your data
		std::vector<std::array<double, 3>> meshVertexPositions;
		std::vector<std::vector<size_t>> meshFaceIndices;


		for (int i = 0; i < trs.size(); i++) {

			Triangle3f tr = trs[i];


			meshVertexPositions[i * 3 + 0] = {tr.A.x,tr.A.z,tr.A.y};

			meshVertexPositions[i * 3 + 1] = { tr.B.x,tr.B.z,tr.B.y };


			meshVertexPositions[i * 3 + 2] = { tr.C.x,tr.C.z,tr.C.y };

			std::vector<size_t> trFace;
			for (int i = 0; i < 3; i++) {
			
				trFace.push_back(i * 3 + 0);
				trFace.push_back(i * 3 + 1);
				trFace.push_back(i * 3 + 2);
			}

			meshFaceIndices.push_back(trFace);


		}


		// Create an empty object
		happly::PLYData plyOut;

		// Add mesh data (elements are created automatically)
		plyOut.addVertexPositions(meshVertexPositions);
		plyOut.addFaceIndices(meshFaceIndices);


		// Write the object to file
		plyOut.write(filename, happly::DataFormat::Binary);

		*numTrianglesWritten = trs.size();


	}

}


#endif //UTILS_HPP
