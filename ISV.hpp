#pragma once
#include <tuple>
#include <mutex>
namespace ISV {
	using I643 = std::tuple<int64_t, int64_t, int64_t>;
#define I643get(a,b) std::get<b>(a) 
	template <typename T, typename F>
	class ISV3D64 {
	public:
		ISV3D64(int W, int H, int D, int64_t WW, int64_t HH, int64_t DD, box_t* BB, F& DataSource, int MaxCounts, int GcFrequency)
			:w(W), h(H), d(D), ww(WW), hh(HH), dd(DD), bb(BB), dataSource(DataSource), maxCounts(MaxCounts), gcFrequency(GcFrequency) {}



		T getValue(v3f_t point) {


			if(gcFrequency!=-1)
			std::lock_guard<std::mutex> lock(accessMutex);

			I643 coords = getCoords(point);
			I643 hsh = hash(coords);
			if (sections.find(hsh) == sections.end()) {

				if(gcFrequency==-1)
				std::lock_guard<std::mutex> lock(accessMutex);

				std::vector<v3f_t> grid;
				for (int iz = I643get(hsh, 2) * dd; iz < (I643get(hsh, 2) + 1) * dd; iz++)
					for (int iy = I643get(hsh, 1) * hh; iy < (I643get(hsh, 1) + 1) * hh; iy++)
						for (int ix = I643get(hsh, 0) * ww; ix < (I643get(hsh, 0) + 1) * ww; ix++) {
							grid.push_back(getPoint(ix, iy, iz));
						}

				sections[hsh] = dataSource(grid);
				if(gcFrequency!=-1)
				counts[hsh] = maxCounts;

			}
			else {
				if (gcFrequency != -1)
				counts[hsh] = maxCounts;

			}



			T s = sections[hsh][getIndex(coords)];


			if (gcFrequency != -1) {
				gcCount++;
				if (gcCount >= gcFrequency) {

					collectGarbage();
					gcCount = 0;
				}
			}
			

			return s;

		}

		ISV3D64<T, F> fork() {
			return ISV3D64(w,h,d,ww,hh,dd,bb,dataSource,maxCounts,gcFrequency);
		
		}

		ISV3D64<T, F> (const ISV3D64& toFork) : w(toFork.w), h(toFork.h), d(toFork.d), 
			ww(toFork.ww), hh(toFork.hh), dd(toFork.dd),
			bb(toFork.bb),dataSource(toFork.dataSource),maxCounts(toFork.maxCounts),gcFrequency(toFork.gcFrequency)
		
		{}

		std::mutex accessMutex;
		int dimensions;
		std::map<std::tuple<int64_t, int64_t, int64_t>, std::vector<T>> sections;
		std::map<std::tuple<int64_t, int64_t, int64_t>, int> counts;
		int64_t ww, hh, dd, w, h, d;
		box_t* bb;
		F& dataSource;
		int maxCounts;
		int gcFrequency;
		int gcCount = 0;
		std::tuple<int64_t, int64_t, int64_t> hash(int64_t ix, int64_t iy, int64_t iz) {
			return std::make_tuple(ix / ww, iy / hh, iz / dd);
		}
		std::tuple<int64_t, int64_t, int64_t> hash(I643 coords) {
			return hash(I643get(coords, 0), I643get(coords, 1), I643get(coords, 2));
		}
		std::tuple<int64_t, int64_t, int64_t> getCoords(v3f_t point) {
			int64_t ix = (int64_t)(w * (point.x - bb->center.x + bb->diameters.x / 2.0f) / (bb->diameters.x));
			int64_t iy = (int64_t)(h * (point.y - bb->center.y + bb->diameters.y / 2.0f) / (bb->diameters.y));
			int64_t iz = (int64_t)(d * (point.z - bb->center.z + bb->diameters.z / 2.0f) / (bb->diameters.z));
			return std::make_tuple(ix, iy, iz);
		}
		int64_t getIndex(I643 coords) {
			int64_t ixx = std::get<0>(coords) % ww;
			int64_t iyy = std::get<1>(coords) % hh;
			int64_t izz = std::get<2>(coords) % dd;
			return ixx + iyy * dd + izz * hh * dd;
		}
		v3f_t getPoint(int ix, int iy, int iz) {
			return v3f_add(v3f_sub(bb->center, v3f_scale(bb->diameters, 0.5)), v3f(
				bb->diameters.x * (float)ix / (float)w,
				bb->diameters.y * (float)iy / (float)h,
				bb->diameters.z * (float)iz / (float)d
			));
		}
		void collectGarbage() {
			std::vector<I643> key;
			for (std::map<I643, int>::iterator it = counts.begin(); it != counts.end(); ++it) {
				key.push_back(it->first);
			}

			for (I643 hsh : key) {
				counts[hsh] -= gcFrequency;
				if (counts[hsh] <= 0) {
					sections.erase(hsh);
					counts.erase(hsh);
				}
			}

		}

		T getValue(float x, float y, float z) {
		
		
			return getValue(v3f(x, y, z));
		}

		T operator()(float x, float y, float z) {
			return getValue(x,y,z);
		}



	};
}