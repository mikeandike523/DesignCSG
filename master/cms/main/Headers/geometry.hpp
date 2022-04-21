#ifndef GEOMETRY_HPP
#define GEOMETRY_HPP

#ifndef logRoutine
#define logRoutine printf
#endif

#include <vector>
#include <deque>

#define PI 3.14159265358979323846

namespace cms {

	struct Vector3f {
		float x, y, z;
		Vector3f(float _x, float _y, float _z) {
			x = _x;
			y = _y;
			z = _z;
		}
		static Vector3f zero() {
			return Vector3f(0.0, 0.0, 0.0);
		}

		static Vector3f sum(Vector3f a, Vector3f b) {
			return Vector3f(a.x + b.x, a.y + b.y, a.z + b.z);
		}

		Vector3f sum(Vector3f b) {
			return Vector3f::sum(*this, b);
		}

		Vector3f scaled(float s) {
			return Vector3f(s * x, s * y, s * z);
		}

		static Vector3f scaled(float s, Vector3f v) {
			return v.scaled(s);
		}


		static Vector3f diff(Vector3f a, Vector3f b) {
			return Vector3f(a.x - b.x, a.y - b.y, a.z - b.z);
		}

		Vector3f diff(Vector3f b) {
			return Vector3f::diff(*this, b);
		}

		static float dot(Vector3f a, Vector3f b) {
			return a.x * b.x + a.y * b.y + a.z * b.z;
		}

		float dot(Vector3f b) {
			return Vector3f::dot(*this, b);
		}

		static Vector3f termProduct(Vector3f a, Vector3f b) {
			return Vector3f(a.x * b.x, a.y * b.y, a.z * b.z);
		}

		Vector3f termProduct(Vector3f b) {
			return Vector3f::termProduct(*this, b);
		}

		static Vector3f termQuotient(Vector3f a, Vector3f b) {
			return Vector3f(a.x / b.x, a.y / b.y, a.z / b.z);
		}

		Vector3f termQuotient(Vector3f b) {
			return Vector3f::termProduct(*this, b);
		}

		float magnitude() {
			return sqrtf((*this).dot(*this));
		}

		Vector3f normalized(float cutoff) {

			float M = magnitude();

			if (M < cutoff) {
				return Vector3f::zero();
			}

			return scaled(1.0f / M);

		}

		static Vector3f midpoint(Vector3f a, Vector3f b) {
			return Vector3f::sum(a.scaled(0.5), b.scaled(0.5));
		}

		static Vector3f weightedSum(Vector3f a, Vector3f b, float sa, float sb, float cutoff) {
			if (sa < sb) {
				float temp = sb;
				sb = sa;
				sa = temp;

				Vector3f tempv = b;
				a = b;
				b = tempv;
			}

			float d = sa - sb;
			if (d < cutoff) {
				return Vector3f::midpoint(a, b);
			}

			Vector3f delta = a.diff(b);

			return b.sum(delta.scaled(fabs(sb) / d));


		}

		static float angleBetweenVectors(Vector3f a, Vector3f b, float tolerance) {
			if (a.magnitude() * b.magnitude() < tolerance) {
				return 0.0f;
			}

			return acosf(Vector3f::dot(a, b) / (a.magnitude() * b.magnitude()));
		}


	};

	struct Vector3i {
		int x, y, z;
		Vector3i(int _x, int _y, int _z) {
			x = _x;
			y = _y;
			z = _z;
		}
		static Vector3i zero() {
			return Vector3i(0.0, 0.0, 0.0);
		}

		static Vector3i sum(Vector3i a, Vector3i b) {
			return Vector3i(a.x + b.x, a.y + b.y, a.z + b.z);
		}

		Vector3i sum(Vector3i b) {
			return Vector3i::sum(*this, b);
		}

		Vector3i scaled(float s) {
			return Vector3i(s * x, s * y, s * z);
		}

		static Vector3i scaled(float s, Vector3i v) {
			return v.scaled(s);
		}


		static Vector3i diff(Vector3i a, Vector3i b) {
			return Vector3i(a.x - b.x, a.y - b.y, a.z - b.z);
		}

		Vector3i diff(Vector3i b) {
			return Vector3i::diff(*this, b);
		}

		static float dot(Vector3i a, Vector3i b) {
			return a.x * b.x + a.y * b.y + a.z * b.z;
		}

		float dot(Vector3i b) {
			return Vector3i::dot(*this, b);
		}

		static Vector3i termProduct(Vector3i a, Vector3i b) {
			return Vector3i(a.x * b.x, a.y * b.y, a.z * b.z);
		}

		Vector3i termProduct(Vector3i b) {
			return Vector3i::termProduct(*this, b);
		}


		static bool less(const Vector3i& a, const Vector3i& b) {

			if (a.x < b.x) {
				return true;
			}
			if (a.x > b.x) {
				return false;
			}

			if (a.y < b.y) {
				return true;
			}
			if (a.y > b.y) {
				return false;
			}


			if (a.z < b.z) {
				return true;
			}
			if (a.z > b.z) {
				return false;
			}

			return false;

		}

	};

	struct Triangle3f {

		Vector3f A = Vector3f::zero();
		Vector3f B = Vector3f::zero();
		Vector3f C = Vector3f::zero();

		Triangle3f(Vector3f _A, Vector3f _B, Vector3f _C) {
			A = _A;
			B = _B;
			C = _C;
		}

	};

	using IndexTriangle = Vector3i;

	std::vector<IndexTriangle> getIndexTriangleStrip(std::vector<int> loop) {
		std::vector<IndexTriangle> trs;
		std::deque<int> loopDeque = std::deque<int>{};
		for (int e : loop) {
			loopDeque.push_back(e);
		}
		if (loop.size() % 2 == 1) {
			trs.push_back(IndexTriangle(loopDeque[0], loopDeque[1], loopDeque.back()));
			loopDeque.pop_front();
		}
		for (int A = 0; A < loopDeque.size() / 2 - 1; A++) {
			int B = A + 1;
			int D = loopDeque.size() - 1 - A;
			int C = D - 1;
			trs.push_back(IndexTriangle(loopDeque[A], loopDeque[B], loopDeque[C]));
			trs.push_back(IndexTriangle(loopDeque[C], loopDeque[D], loopDeque[A]));
		}

		return trs;

	}

	struct Box3f {

		Vector3f center = Vector3f::zero();
		Vector3f halfDiameter = Vector3f::zero();

		Box3f(Vector3f _center, Vector3f _halfDiameter) {
			center = _center;
			halfDiameter = _halfDiameter;
		}

		static Box3f zero() {
			return Box3f(Vector3f::zero(), Vector3f::zero());
		}

		std::vector<Vector3f> getCorners(float s = 1.0f) {

			return std::vector<Vector3f>{

				center.sum(halfDiameter.termProduct(Vector3f(-1.0f, -1.0f, 1.0f)).scaled(s)),
					center.sum(halfDiameter.termProduct(Vector3f(1.0f, -1.0f, 1.0f)).scaled(s)),
					center.sum(halfDiameter.termProduct(Vector3f(1.0f, -1.0f, -1.0f)).scaled(s)),
					center.sum(halfDiameter.termProduct(Vector3f(-1.0f, -1.0f, -1.0f)).scaled(s)),

					center.sum(halfDiameter.termProduct(Vector3f(-1.0f, 1.0f, 1.0f)).scaled(s)),
					center.sum(halfDiameter.termProduct(Vector3f(1.0f, 1.0f, 1.0f)).scaled(s)),
					center.sum(halfDiameter.termProduct(Vector3f(1.0f, 1.0f, -1.0f)).scaled(s)),
					center.sum(halfDiameter.termProduct(Vector3f(-1.0f, 1.0f, -1.0f)).scaled(s))

			};
		}

	};


}

#endif //GEOMETRY_HPP