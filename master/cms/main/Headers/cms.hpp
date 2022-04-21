#ifndef CMS_HPP
#define CMS_HPP


#include <cmath>
#include <vector>
#include <thread>
#include <map>

#include "mesh.hpp"
#include "geometry.hpp"
#include "readLookupTable.hpp"
#include "utils.hpp"

#ifndef logRoutine
#define logRoutine printf
#endif

#ifdef CMS_IMPLEMENT_MAIN

float sdfSphere(float x, float y, float z, float cx, float cy, float cz, float r) {
	float dx = x - cx;
	float dy = y - cy;
	float dz = z - cz;
	return sqrt(dx * dx + dy * dy + dz * dz) - r;
}

float sdfBox(float x, float y, float z, float cx, float cy, float cz, float r) {
	auto max3 = [](float a, float b, float c) {
		float mx = a;
		if (b > mx) {
			mx = b;
		}
		if (c > mx) {
			mx = c;
		}
		return mx;
	};

	return max3(fabs(x - cx) - r, fabs(y - cy) - r, fabs(z - cz) - r);

}

float mainSDF(float x, float y, float z) {

	auto min2 = [](float a, float b) {
		return a < b ? a : b;
	};

	auto max2 = [](float a, float b) {
		return a > b ? a : b;
	};

	float d1 = sdfBox(x, y, z, 0.0, 0.0, 0.0, 0.75);
	float d2 = sdfSphere(x, y, z, 0.0, 0.0, 0.0, 1.0);
	float d3 = min2(d1, d2);

	for (int i = -1; i <= 1; i++)
		for (int j = -1; j <= 1; j++)
			for (int k = -1; k <= 1; k++)
			{
				if (abs(i) + abs(j) + abs(k) == 1) {

					d3 = max2(d3, -sdfSphere(x, y, z, (float)i, (float)j, (float)k, 0.75 * 0.5));
				}

			}

	return d3;

}


cms::Vector3f mainSDFUnitNormal(float x, float y, float z) {
	constexpr float normalEpsilon = 0.001;
	float westSD = mainSDF(x - normalEpsilon, y, z);
	float eastSD = mainSDF(x + normalEpsilon, y, z);
	float belowSD = mainSDF(x, y - normalEpsilon, z);
	float aboveSD = mainSDF(x, y + normalEpsilon, z);
	float southSD = mainSDF(x, y, z - normalEpsilon);
	float northSD = mainSDF(x, y, z + normalEpsilon);
	return cms::Vector3f(eastSD - westSD, aboveSD - belowSD, northSD - southSD).scaled(1.0 / (2.0 * normalEpsilon)).normalized(1e-6f);

}



int main() {

	std::map<int, std::vector<cms::IndexTriangle>> trsMap = cms::getIndexTrianglesFromTable("..\\lookupTable\\lookupTable.txt");
	logRoutine("trsMap:\n");
	for (int i = 0; i < 256; i++) {
		logRoutine("Lookup = %d: ", i);
		std::vector<cms::IndexTriangle> trs = trsMap[i];
		for (cms::IndexTriangle tr : trs) {
			logRoutine("IT(%d %d %d) ", tr.x, tr.y, tr.z);
		}
		logRoutine("\n");
	}

	cms::Mesh mesh(cms::Box3f(cms::Vector3f::zero(), cms::Vector3f(1.0, 1.0, 1.0)), mainSDF, mainSDFUnitNormal, trsMap, 5, 7, PI / 12.0);
	std::vector<cms::Triangle3f> trs = mesh.getSurface();
	cms::writeTrianglesToSTL("Output\\cms.stl", trs);



}


#endif //CMS_IMPLEMENT_MAIN



#endif //CMS_HPP