#ifndef MESH_HPP
#define MESH_HPP

#ifndef logRoutine
#define logRoutine printf
#endif

#include <functional>
#include <vector>
#include <deque>
#include <map>
#include <mutex>

#include "geometry.hpp"
#include "octree.hpp"
#include "Evaluator.h"




namespace cms {

	class Mesh {

	public:
		int getGeneration() { return generation; }
		int getRemainingItems() { return remainingItems; };
		Mesh(Box3f _boundingBox, std::function<float(float, float, float)> _sampler,
			std::function<cms::Vector3f(float, float, float)> _unitNormalSampler,
			std::map<int, std::vector<IndexTriangle>> _trsMap,
			int _minimumOctreeLevel,
			int _maximumOctreeLevel,
			int _gridLevel,
			float _complexSurfaceThreshold,
			std::map<int, int>& _histogram,
			int _meshSubdivisionLevel,
			int _maxPoolSize


		);
		std::map<int, int> defaultHistogram;
		std::map<int, int>& histogram = defaultHistogram;
		std::vector<Triangle3f> getSurface();
		int remainingItems = 0;
		int generation = 0;
		cms::Box3f boundingBox = cms::Box3f::zero();
		int minimumOctreeLevel = 5;
		int maximumOctreeLevel = 7;
		int gridLevel = 8;
		float complexSurfaceThreshold = PI / 12.0f; //todo -- obtain value and equation for complex surface threshold
		std::function<float(float, float, float)> sampler;
		std::function<cms::Vector3f(float, float, float)> unitNormalSampler;
		std::map<int, std::vector<IndexTriangle>> trsMap;
		int complete = 1;
		int meshSubdivisionLevel = 4;
		int maxPoolSize = 12;



	};

	inline Mesh::Mesh(Box3f _boundingBox, std::function<float(float, float, float)> _sampler,
		std::function<cms::Vector3f(float, float, float)> _unitNormalSampler,
		std::map<int, std::vector<IndexTriangle>> _trsMap,
		int _minimumOctreeLevel,
		int _maximumOctreeLevel,
		int _gridLevel,
		float _complexSurfaceThreshold,
		std::map<int, int>& _histogram,
		int _meshSubdivisionLevel,
		int _maxPoolSize


	) {
		boundingBox = _boundingBox;
		sampler = _sampler;
		unitNormalSampler = _unitNormalSampler;
		trsMap = _trsMap;
		minimumOctreeLevel = _minimumOctreeLevel;
		maximumOctreeLevel = _maximumOctreeLevel;
		gridLevel = _gridLevel;
		complexSurfaceThreshold = _complexSurfaceThreshold;
		histogram = _histogram;
		meshSubdivisionLevel = _meshSubdivisionLevel;
		maxPoolSize = _maxPoolSize;
	}

	

	inline std::vector<Triangle3f> Mesh::getSurface() {

		complete = 0;

		histogram.clear();
		histogram[0] = 0;

		std::vector<Triangle3f> mesh;
	

		generation = 0;





		std::deque<Node> stack = {Node(boundingBox,0)};
		int sp = 0;

			while (sp < stack.size()) {
				//remainingItems = stack.size() - sp;
				Node* nd = &stack[sp++];

				remainingItems = stack.size() - sp;


				if (nd->level > this->generation) {
					this->generation = nd->level;
					this->histogram[this->generation] = 0;

				}

				

				float d = this->sampler(nd->bounds.center.x, nd->bounds.center.y, nd->bounds.center.z);

				constexpr float sqrt3scaling = 1.5f;
				if (fabs(d) > nd->bounds.halfDiameter.magnitude() * sqrt3scaling) continue;





				std::vector<Vector3f> cornerLocations = nd->bounds.getCorners(1.0);
				std::vector<Vector3f> edgeLocations;
				int corners[8] = { 0 };
				int lookup = 0;
				for (int i = 0; i < 8; i++) {
					corners[i] = this->sampler(cornerLocations[i].x, cornerLocations[i].y, cornerLocations[i].z) < 0.0f ? 1 : 0;
					lookup |= (corners[i] << i);
				}

				std::vector<std::pair<int, int>> edgeIndices;

				for (int i = 0; i < 4; i++) {
					Vector3f A = cornerLocations[i];
					Vector3f B = cornerLocations[(i + 1) % 4];
					float sa = this->sampler(A.x, A.y, A.z);
					float sb = this->sampler(B.x, B.y, B.z);
					/*     if (corners[i] != corners[(i + 1) % 4]) {
							 edgeLocations.push_back(Vector3f::weightedSum(A, B, sa, sb, 1e-12));
						 }
						 else*/
					edgeLocations.push_back(Vector3f::midpoint(A, B));
					edgeIndices.push_back(std::make_pair(i, (i + 1) % 4));
				}

				for (int i = 0; i < 4; i++) {
					Vector3f A = cornerLocations[i + 4];
					Vector3f B = cornerLocations[(i + 1) % 4 + 4];
					float sa = this->sampler(A.x, A.y, A.z);
					float sb = this->sampler(B.x, B.y, B.z);
					/*   if (corners[i+4] != corners[(i + 1) % 4+4]) {
						   edgeLocations.push_back(Vector3f::weightedSum(A, B, sa, sb, 1e-12));
					   }
					   else*/
					edgeLocations.push_back(Vector3f::midpoint(A, B));
					edgeIndices.push_back(std::make_pair(i + 4, (i + 1) % 4 + 4));
				}

				for (int i = 0; i < 4; i++) {
					Vector3f A = cornerLocations[i];
					Vector3f B = cornerLocations[i + 4];
					float sa = this->sampler(A.x, A.y, A.z);
					float sb = this->sampler(B.x, B.y, B.z);
					/* if (corners[i] != corners[i+4]) {
						 edgeLocations.push_back(Vector3f::weightedSum(A, B, sa, sb, 1e-12));
					 }
					 else*/
					edgeLocations.push_back(Vector3f::midpoint(A, B));
					edgeIndices.push_back(std::make_pair(i, i + 4));
				}


				bool shouldSubdivide = false;

				if (nd->level < this->minimumOctreeLevel) {
					shouldSubdivide = true;

				}
				else {


					// Edge Ambiguity
					int pointsAlongEdge = 1 << (this->gridLevel - nd->level);
					for (std::pair<int, int> edge : edgeIndices) {
						Vector3f start = cornerLocations[edge.first];
						Vector3f end = cornerLocations[edge.second];
						Vector3f delta = end.diff(start);

						for (int i = 1; i < pointsAlongEdge; i++) {
							float fractionAlongEdge = (float)i / (float)pointsAlongEdge;
							Vector3f testPoint = start.sum(delta.scaled(fractionAlongEdge));
							int currentValue = this->sampler(testPoint.x, testPoint.y, testPoint.z) < 0.0f ? 1 : 0;
							if (currentValue == 1) {
								shouldSubdivide = true;
								goto condition1EarlyExit;
							}

						}
					}



					//Complex Edges
					//In this implementation, large angles are detected in 3D instead of 2D. This differs from the original paper
					for (std::pair<int, int> edge : edgeIndices) {
						Vector3f start = cornerLocations[edge.first];
						Vector3f end = cornerLocations[edge.second];

						float angle = Vector3f::angleBetweenVectors(this->unitNormalSampler(start.x, start.y, start.z),
							this->unitNormalSampler(end.x, end.y, end.z),
							1e-6f);

						// logRoutine("angle %f\n",angle);
						if (angle > this->complexSurfaceThreshold) {
							shouldSubdivide = true;
							goto condition2EarlyExit;
						}

					}

				}

			condition1EarlyExit:
			condition2EarlyExit:

				if (nd->level == this->maximumOctreeLevel) {
					shouldSubdivide = false;
				}

				if (shouldSubdivide) {

					nd->subdivideIntoQueue(stack);

				}
				else {



					std::vector<IndexTriangle> components = this->trsMap[lookup];

					/*  #ifdef CMS_DEBUG
					  if(components.size()>0)
					  logRoutine("%d %d %f %f %f\n",nd->level,lookup,nd->bounds.center.x,nd->bounds.center.y,nd->bounds.center.z);
					  #endif*/

					for (IndexTriangle it : components) {
						// logRoutine("%d %d %d\n",it.x,it.y,it.z);
						Vector3f A = edgeLocations[it.x];
						Vector3f B = edgeLocations[it.y];
						Vector3f C = edgeLocations[it.z];

					
							mesh.push_back(Triangle3f(A, B, C));
							this->histogram[this->generation]++;

						
					}

				}

			}







		
		remainingItems = 0;
		




		complete = 1;

		return mesh;


	}

	template<typename T_key, typename T_value, typename T_classcomp>
	class DefaultMap {

	public:
		DefaultMap(T_value _defaultValue) {
			defaultValue = _defaultValue;
		}
		void insert(T_key key, T_value value) {
			data[key] = value;
		}
		T_value retrieve(T_key key) {
			if (data.find(key) != data.end())
			{
				return data[key];
			}
			return defaultValue;
		}
	private:
		std::map<T_key, T_value, T_classcomp> data;
		T_value defaultValue;
	};

	inline std::function<cms::Vector3i(cms::Vector3f)> Indexer(cms::Box3f bounds, int gridLevel) {
		std::function<cms::Vector3i(cms::Vector3f)> indexer = [&bounds, &gridLevel](cms::Vector3f v) {
			cms::Vector3f fraction = v.diff(bounds.center).sum(bounds.halfDiameter).termQuotient(bounds.halfDiameter);
			float gridPointsf = (float)((1 << gridLevel) + 1);
			fraction = fraction.scaled(gridPointsf);
			return cms::Vector3i(fraction.x, fraction.y, fraction.z);
		};
		return indexer;
	}

	inline std::function<cms::Vector3f(cms::Vector3i)> Deindexer(cms::Box3f bounds, int gridLevel) {
		std::function<cms::Vector3f(cms::Vector3i)> deindexer = [&bounds, &gridLevel](cms::Vector3i v) {
			float gridPointsf = (float)((1 << gridLevel) + 1);
			cms::Vector3f fraction = cms::Vector3f(v.x / gridPointsf, v.y / gridPointsf, v.z / gridPointsf);
			return bounds.center.diff(bounds.halfDiameter).sum(bounds.halfDiameter.scaled(2.0).termProduct(fraction));
		};
		return deindexer;
	}

	inline std::vector<cms::Triangle3f> retopologize(std::vector<cms::Triangle3f>& trs, cms::Box3f bounds, int minimumOctreeLevel, int gridLevel) {
		std::vector<cms::Triangle3f> retopoTrs;
		auto indexer = Indexer(bounds, gridLevel);
		auto deindexer = Deindexer(bounds, gridLevel);
		auto min3 = [](float a, float b, float c) {
			float m = a;
			if (b < m) {
				m = b;
			}
			if (c < m) {
				m = c;
			}
			return m;
		};


		float gridPointsf = (float)((1 << gridLevel) + 1);

		float joinDistance = 0.25 * min3(2.0 * bounds.halfDiameter.x / gridPointsf, 2.0 * bounds.halfDiameter.y / gridPointsf, 2.0 * bounds.halfDiameter.z / gridPointsf);


		auto Vector3fIsInVector = [&joinDistance](std::vector<Vector3f>& ngon, Vector3f v) {
			for (Vector3f testPoint : ngon) {
				if (v.diff(testPoint).magnitude() <= joinDistance) {
					return true;
				}
			}

			return false;
		};


		std::vector<std::vector<cms::Triangle3f>> trsBank;

		struct classcomp {
			bool operator() (const Vector3i& lhs, const Vector3i& rhs) const
			{
				return Vector3i::less(lhs, rhs);
			}
		};


		DefaultMap<cms::Vector3i, int, classcomp> occupied(0);


		for (cms::Triangle3f tr : trs) {
			trsBank.push_back(std::vector<cms::Triangle3f>{tr});
			occupied.insert(indexer(tr.A), 1);
			occupied.insert(indexer(tr.B), 1);
			occupied.insert(indexer(tr.C), 1);
		}

		int pointsAlongEdge = 1 << (gridLevel - minimumOctreeLevel);


		int binIndex = 0;
		for (std::vector<cms::Triangle3f> bin : trsBank) {
			std::vector<cms::Triangle3f> newBin;
			for (Triangle3f tr : bin) {
				std::vector<cms::Vector3f> ngon;

				for (std::pair<cms::Vector3f, cms::Vector3f> edge : { std::make_pair(tr.A,tr.B),std::make_pair(tr.B,tr.C),std::make_pair(tr.C,tr.A) }) {
					Vector3f start = edge.first;
					Vector3f end = edge.second;
					Vector3f delta = end.diff(start);
					for (int i = 0; i < pointsAlongEdge; i++) {
						Vector3f testPoint = start.sum(delta.scaled((float)i / pointsAlongEdge));
						if (occupied.retrieve(indexer(testPoint))) {
							ngon.push_back(testPoint);
						}
					}

				}

				std::vector<int> indices;
				for (int i = 0; i < ngon.size(); i++) {
					indices.push_back(i);
				}

				std::vector<cms::IndexTriangle> tStrip = getIndexTriangleStrip(indices);
				for (IndexTriangle indexTriangle : tStrip) {
					newBin.push_back(cms::Triangle3f(ngon[indexTriangle.x], ngon[indexTriangle.y], ngon[indexTriangle.z]));
				}

			}
			trsBank[binIndex] = newBin;
			binIndex++;
		}

		for (std::vector<cms::Triangle3f> bin : trsBank) {
			for (cms::Triangle3f tr : bin) {
				retopoTrs.push_back(tr);
			}
		}


		return retopoTrs;
	}

	inline void performGradientDescent(
		int numSteps,
		std::vector<Triangle3f>& trs,
		Evaluator* evaluator,
		int* gradientDescentStepsCompleted
	) {

		(*gradientDescentStepsCompleted) = 0;

		for (int step = 0; step < numSteps; step++) {
			logRoutine("Performing gradient descent step %d of %d\n", step + 1, numSteps);

			//char buffer[512];
			//snprintf(buffer, 512, "\rGradient descent step  %d of %d        ", step + 1, numSteps);
			//logAppend(std::string(buffer));

			int start = 0;
			int end = 0;
			int numTrs = trs.size();

			while (start < numTrs) {
				int amt = T_min(MAX_EVAL_POINTS, numTrs - end);
				end = start + amt;

				std::vector<v3f_t> evalPoints;

				for (int i = 0; i < end - start; i++) {
					int I = start + i;
					evalPoints.push_back(v3f(trs[I].A.x, trs[I].A.y, trs[I].A.z));
					evalPoints.push_back(v3f(trs[I].B.x, trs[I].B.y, trs[I].B.z));
					evalPoints.push_back(v3f(trs[I].C.x, trs[I].C.y, trs[I].C.z));
				}

				std::vector<float> sdfs = evaluator->eval_sdf_at_points(evalPoints);
				std::vector<v3f_t> normals = evaluator->eval_normal_at_points(evalPoints);


				for (int i = 0; i < (end - start) * 3; i++) {
					evalPoints[i] = v3f_add(evalPoints[i], v3f_scale(normals[i], -sdfs[i]));
				}

				for (int i = 0; i < end - start; i++) {
					int I = i + start;
					Vector3f A = Vector3f(evalPoints[i * 3 + 0].x, evalPoints[i * 3 + 0].y, evalPoints[i * 3 + 0].z);
					Vector3f B = Vector3f(evalPoints[i * 3 + 1].x, evalPoints[i * 3 + 1].y, evalPoints[i * 3 + 1].z);
					Vector3f C = Vector3f(evalPoints[i * 3 + 2].x, evalPoints[i * 3 + 2].y, evalPoints[i * 3 + 2].z);
					trs[I] = cms::Triangle3f(A, B, C);
				}




				start = end;
			}


			(*gradientDescentStepsCompleted) = step+1;


		}


	}

}


#endif //MESH_HPP