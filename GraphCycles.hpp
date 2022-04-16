#ifndef _GRAPH_CYCLES_HPP
#define _GRAPH_CYCLES_HPP

#include <vector>
#include <algorithm>

using AdjacencyList = std::vector<std::vector<int>>;
using CycleList = std::vector<std::vector<int>>;
using PredicateList = std::vector<bool>;
using CycleStackItemWithHistory = std::pair<int, std::vector<int>>;
using CycleStackWithHistory = std::vector<CycleStackItemWithHistory>;
using History = std::vector<int>;

#define isInVector(vec,item) (std::find(vec.begin(), vec.end(), item) != vec.end())

class DirectedGraph {

public:

	DirectedGraph() {
		adjacencyList = AdjacencyList();
	}

	void insertEdge(int a, int b)
	{
		if (a >= adjacencyList.size()) {
			adjacencyList.resize(a + 1, std::vector<int>());
		}

		if (b >= adjacencyList.size()) {
			adjacencyList.resize(b + 1, std::vector<int>());
		}

		if (!isInVector(adjacencyList[a], b)) {
			adjacencyList[a].push_back(b);
		}

	}

	void insertDualEdge(int a, int b)
	{
		insertEdge(a, b);
		insertEdge(b, a);

	}

	int getNodeCount() {
		return adjacencyList.size();
	}

	AdjacencyList getAdjacencyList() {
		return adjacencyList;
	}

	void shuffleEdgeOrder() {
		for (int i = 0; i < getNodeCount(); i++) {
			std::random_shuffle(adjacencyList[i].begin(), adjacencyList[i].end());
		}
	}

private:
	AdjacencyList adjacencyList;

};

inline CycleList detectCycles(AdjacencyList adjacencyList) {

	auto isMemberOfCycle = [](std::vector<int>& cycle, int node) {
		for (int nd : cycle) {
			if (node == nd) {
				return true;
			}
		}
		return false;
	};

	CycleList cycles;

	int nodeCount = adjacencyList.size();

	//PredicateList isMemberOfCycle;
	//isMemberOfCycle.resize(nodeCount, false);


	for (int nodeIndex = 0; nodeIndex < nodeCount; nodeIndex++) {

		if (adjacencyList.at(nodeIndex).size() == 4)continue;

		//if (isMemberOfCycle.at(nodeIndex)) continue;
		if (adjacencyList[nodeIndex].size() < 1) continue;

		CycleStackWithHistory stack;

		PredicateList markedNodes;
		markedNodes.resize(nodeCount, false);
		//for (int j = 0; j < nodeCount; j++) {
		//	//if (isMemberOfCycle[j]) { markedNodes[j] = true; }
		//}


		stack.push_back(std::make_pair(nodeIndex, History()));

		int initialGuess = adjacencyList.at(nodeIndex).at(0);

		bool returnFlag = false;





		while (stack.size() > 0 && !returnFlag) {



			CycleStackItemWithHistory item = stack.back();
			stack.pop_back();
			//	DebugPrint("Marking Visited Node %d\n",item.first);
			markedNodes[item.first] = true;

			std::vector<int> neighbors = adjacencyList.at(item.first);
			//DebugPrint("Line 85\n", item.first);

			for (int neighbor : neighbors) {
				if (neighbor == nodeIndex && item.first != initialGuess) {
					std::vector<int> cycle = item.second;
					cycle.push_back(item.first);

					int cycleDoesNotContainInnerCycles = 1;

					for (int nd : cycle) {
						if (adjacencyList[nd].size() > 2) {
							for (int nd2 : cycle) {
								if (nd2 != nd) {
									int populatedCount = 0;
									if (isMemberOfCycle(adjacencyList[nd], nd2)) {
										populatedCount++;
									}
									if (populatedCount == 2) {
										cycleDoesNotContainInnerCycles = 0;
										goto addCycle;
									}
								}
							}
						}
					}
				addCycle:
					if (cycleDoesNotContainInnerCycles)
						cycles.push_back(cycle);

					//for (int node : cycle) {

					//	

					//////	DebugPrint("Marking Cycle Member\n");
					////	if (adjacencyList.at(node).size() < 4)
					////		isMemberOfCycle[node] = true;
					////	else
					////		DebugPrint("Found Junction\n");

					//}

					returnFlag = true;
				}
				else {
					if (!markedNodes[neighbor]) {
						std::vector<int> history = item.second;
						history.push_back(item.first);
						stack.push_back(std::make_pair(neighbor, history));
						break;
					}

				}
			}



		}

	}

	int maxLength = 0;
	for (auto cycle : cycles) {
		if (cycle.size() > maxLength) {
			maxLength = cycle.size();
		}
	}

	for (int i = 0; i < cycles.size(); i++) {
		while (cycles[i].size() < maxLength) {
			cycles[i].push_back(-1);
		}
		std::sort(cycles[i].begin(), cycles[i].end());
	}

	auto vectorEquals = [](std::vector<int> v1, std::vector<int> v2) {
		if (v1.size() != v2.size()) return false;
		for (int i = 0; i < v1.size(); i++) {
			if (v1[i] != v2[i]) {
				return false;
			}
		}
		return true;
	};

	auto vectorIsMemberOfVectorOfVectors = [&vectorEquals](std::vector<std::vector<int>>& vv, std::vector<int>& v) {
		for (auto& compare : vv) {
			if (vectorEquals(compare, v)) {
				return true;
			}
		}

		return false;
	};

	std::vector<std::vector<int>> uniqueCycles;
	for (auto cycle : cycles) {
		if (!vectorIsMemberOfVectorOfVectors(uniqueCycles, cycle)) {
			uniqueCycles.push_back(cycle);
		}
	}

	return uniqueCycles;
}

void printCycles(CycleList cycles) {
	for (std::vector<int> cycle : cycles) {
		for (int in = 0; in < cycle.size(); in++) {
			printf("%d", cycle[in]);
			if (in < cycle.size() - 1) {
				printf(" ");
			}
		}
		printf("\n");
	}
}


void printCycles2(CycleList cycles) {
	for (std::vector<int> cycle : cycles) {
		for (int in = 0; in < cycle.size(); in++) {
			DebugPrint("%d", cycle[in]);
			if (in < cycle.size() - 1) {
				DebugPrint(" ");
			}
		}
		DebugPrint("\n");
	}
}
void printAdjacencyList(AdjacencyList adjacencyList) {
	for (int node = 0; node < adjacencyList.size(); node++) {
		printf("%d --> ", node);
		for (int nbr : adjacencyList[node]) {

			printf("%d", nbr);
			if (node < adjacencyList.size() - 1) {
				printf(" ");
			}

		}
		printf("\n");
	}
}

void printAdjacencyList2(AdjacencyList adjacencyList) {
	for (int node = 0; node < adjacencyList.size(); node++) {
		DebugPrint("%d --> ", node);
		for (int nbr : adjacencyList[node]) {

			DebugPrint("%d ", nbr);



		}
		DebugPrint("\n");
	}
}






#endif //_GRAPH_CYCLES_HPP