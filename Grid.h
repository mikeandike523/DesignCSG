#pragma once

#include <vector>
#include <CVector.h>
#include "Utils.h"

template <typename T>
class Grid
{
public:

	Grid(std::vector<T> * _data, int _w, int _h, int _d) :data(_data), w(_w), h(_h), d(_d) {}
	T at(int ix, int iy, int iz) {
		return data->at(iz+iy*d+ix*h*d);
	}
	
private:
	std::vector<T> * data;
	int w, h, d;
};

std::vector<v3f_t> linspace(box_t bx, int w, int h, int d) {
	std::vector<v3f_t> out;
	out.reserve(w * h * d);
	for (int ix = 0; ix < w; ix++)
		for (int iy = 0; iy < h; iy++)
			for (int iz = 0; iz < d; iz++)
				{
				out.push_back(v3f(
					bx.center.x - bx.diameters.x / 2 + (float)ix / w * bx.diameters.x,
					bx.center.y - bx.diameters.y / 2 + (float)iy / w * bx.diameters.y,
					bx.center.z - bx.diameters.z / 2 + (float)iz / w * bx.diameters.z

				));
				}
	return out;
}