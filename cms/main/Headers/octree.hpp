#ifndef OCTREE_HPP
#define OCTREE_HPP

#ifndef logRoutine
#define logRoutine printf
#endif

#include <deque>

#include "geometry.hpp"


namespace cms {

	struct Node {
		int level = 0;
		cms::Box3f bounds = Box3f::zero();

		Node* children[8] = { nullptr };
		Node(Box3f _bounds, int _level) {
			bounds = _bounds;
			level = _level;
		}
		void subdivideIntoQueue(std::deque<Node>& Q) {
			std::vector<Vector3f> corners = bounds.getCorners(0.5);
			for (int i = 0; i < 8; i++) {
				Vector3f c = corners[i];
				Node n = Node(Box3f(c, bounds.halfDiameter.scaled(0.5)), level + 1);
				Q.push_back(n);
				children[i] = &Q[Q.size() - 1];
			}
		}

	};





}


#endif //OCTREE_HPP
