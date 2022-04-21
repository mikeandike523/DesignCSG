#pragma once
#include <CVector.h>
#include <Evaluator.h>

typedef struct v3i_t {
	int ix, iy, iz;
	v3i_t(int IX, int IY, int IZ) {
		ix = IX; iy = IY; iz = IZ;
	}
} v3i_t;

inline v3i_t v3i(int IX, int IY, int IZ) {
	return v3i_t(IX, IY, IZ);
}


class GridSampler {
public:
	GridSampler() {}
	GridSampler(box_t* BB, int RES, Evaluator* EVR);
	void process();
	const float sample(v3f_t position);

private:
	v3i_t getCoords(v3f_t coords);
	v3f_t getPoint(v3i_t coords);
	v3i_t limit(v3i_t coords);
	int getIndex(v3i_t coords);
	box_t* bb = nullptr;
	int res;
	Evaluator* evr = nullptr;
	std::vector<v3f_t> gridPoints;
	std::vector<float> sdfs;
	float resf;

};

inline GridSampler::GridSampler(box_t* BB, int RES, Evaluator* EVR) {
	bb = BB;
	res = RES;
	evr = EVR;
	resf = (float)res;
}

#define SIMPLECLIP(x,low,high) (x<low?low:(x>high?high:x))

inline v3i_t GridSampler::limit(v3i_t coords) {
	return v3i(SIMPLECLIP(coords.ix, 0, res - 1), SIMPLECLIP(coords.iy, 0, res - 1), SIMPLECLIP(coords.iz, 0, res - 1));
}

inline v3i_t GridSampler::getCoords(v3f_t point) {
	int ix = (int)(resf * (point.x - bb->center.x + bb->diameters.x / 2.0f) / bb->diameters.x);
	int iy = (int)(resf * (point.y - bb->center.y + bb->diameters.y / 2.0f) / bb->diameters.y);
	int iz = (int)(resf * (point.z - bb->center.z + bb->diameters.z / 2.0f) / bb->diameters.z);
	return v3i(ix, iy, iz);
}

inline v3f_t GridSampler::getPoint(v3i_t coords) {
	return v3f(bb->center.x - bb->diameters.x / 2.0f + (float)coords.ix / resf * bb->diameters.x,
		bb->center.y - bb->diameters.y / 2.0f + (float)coords.iy / resf * bb->diameters.y,
		bb->center.z - bb->diameters.z / 2.0f + (float)coords.iz / resf * bb->diameters.z);
}

inline int GridSampler::getIndex(v3i_t coords) {
	return coords.ix + coords.iy * res + coords.iz * res * res;
}

inline void GridSampler::process() {
	for (int iz = 0; iz < res; iz++)
		for (int iy = 0; iy < res; iy++)
			for (int ix = 0; ix < res; ix++) {
				gridPoints.push_back(getPoint(v3i(ix, iy, iz)));

			}
	sdfs = evr->eval_sdf_at_points(gridPoints);
}

inline const float GridSampler::sample(v3f_t point) {
	return sdfs.at(getIndex(limit(getCoords(point))));
}