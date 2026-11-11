// From the repository root:
// g++ -std=c++14 -O3 -Wall -Wextra -Werror tests/native/stock_preview.cpp -o /tmp/stock-preview-tests
// /tmp/stock-preview-tests
// Add -fsanitize=address,undefined -fno-omit-frame-pointer for sanitizer checks.
#include "../../liblathe/base/stockstate.h"
#include <iostream>
#include <random>

using namespace stock_preview;

void check(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
Polygon rectangle(double x0, double z0, double x1, double z1) {
    return {{x0, z0}, {x1, z0}, {x1, z1}, {x0, z1}};
}
void close(double a, double b) { check(std::abs(a - b) < 1e-8, "Unexpected stock area"); }
bool inside(const Polygon& p, Point q) {
    for (size_t i = 0; i < p.size(); ++i)
        if (cross(p[(i + 1) % p.size()] - p[i], q - p[i]) < 0) return false;
    return true;
}
void validBoundary(const StockState& state) {
    const auto edges = state.boundary();
    long double signedArea = 0;
    for (const auto& edge : edges) {
        signedArea += cross(edge.start, edge.end) / 2;
        // The material is on the left of every exported edge.
        Point d = edge.end - edge.start;
        const double length = std::sqrt(dot(d, d));
        Point mid = (edge.start + edge.end) * 0.5;
        Point normal{-d.z / length * 1e-6, d.x / length * 1e-6};
        check(state.contains(mid + normal), "Export lost material-facing edge");
        check(!state.contains(mid - normal), "Export contains an internal edge");
    }
    close(static_cast<double>(signedArea), state.materialArea());
}

int main() {
    try {
        StockState initial(rectangle(0, 0, 10, 10));
        StockState pocket = initial;
        pocket.sweep(rectangle(0, 0, 2, 2), {3, 3}, {3, 3});
        close(initial.materialArea(), 100);
        close(pocket.materialArea(), 96);
        check(!pocket.contains({4, 4}) && pocket.contains({2, 4}), "Pocket classification");
        validBoundary(pocket);
        pocket.sweep(rectangle(0, 0, 2, 2), {3, 3}, {3, 3});
        close(pocket.materialArea(), 96);
        validBoundary(pocket);

        StockState split = initial;
        split.sweep(rectangle(0, 0, 1, 1), {4, -1}, {4, 11});
        close(split.materialArea(), 90);
        check(split.contains({3, 5}) && split.contains({6, 5})
              && !split.contains({4.5, 5}), "Disconnected material classification");
        validBoundary(split);
        split.sweep(rectangle(0, 0, 1, 1), {5, -1}, {5, 11});
        close(split.materialArea(), 80);
        validBoundary(split);

        StockState tangent = initial;
        tangent.sweep(rectangle(0, 0, 2, 2), {10, 0}, {10, 10});
        close(tangent.materialArea(), 100);
        validBoundary(tangent);
        StockState narrow = initial;
        narrow.sweep(rectangle(0, 0, 4.999999, 12), {0, -1}, {0, -1});
        narrow.sweep(rectangle(0, 0, 5, 12), {5, -1}, {5, -1});
        close(narrow.materialArea(), 0.00001);
        check(narrow.contains({4.9999995, 5}), "Narrow remnant lost");
        validBoundary(narrow);

        StockState empty = initial;
        empty.sweep(rectangle(-1, -1, 11, 11), {0, 0}, {0, 0});
        close(empty.materialArea(), 0);
        check(empty.boundary().empty(), "Empty stock has boundary");
        bool rejected = false;
        try { StockState bad({{0, 0}, {4, 0}, {1, 1}, {0, 4}}); }
        catch (const std::invalid_argument&) { rejected = true; }
        check(rejected, "Concave input silently enlarged");
        rejected = false;
        try { initial.sweep({{0, 0}, {4, 0}, {1, 1}, {0, 4}}, {0, 0}, {0, 0}); }
        catch (const std::invalid_argument&) { rejected = true; }
        check(rejected, "Concave insert silently enlarged");
        StockState translated(rectangle(-20, 100, -10, 110));
        translated.sweep(rectangle(0, 0, 2, 2), {-17, 103}, {-17, 103});
        close(translated.materialArea(), 96);
        validBoundary(translated);
        StockState reversed = initial;
        StockState forward = initial;
        forward.sweep(rectangle(0, 0, 1, 1), {2, 2}, {7, 6});
        reversed.sweep(rectangle(0, 0, 1, 1), {7, 6}, {2, 2});
        close(forward.materialArea(), reversed.materialArea());
        validBoundary(forward);
        validBoundary(reversed);
        StockState tiny = initial;
        tiny.sweep(rectangle(0, 0, 1, 1), {10 - 1e-14, 3}, {10 - 1e-14, 3});
        close(tiny.materialArea(), 100);
        check(tiny.retainedUncertain() > 0, "Unresolved removal not reported");

        // Independent occupancy oracle: initial rectangle minus all sweep polygons.
        std::mt19937 random(42);
        std::uniform_real_distribution<double> pos(-2, 12);
        StockState randomStock = initial;
        std::vector<Polygon> sweeps;
        const Polygon tool = convex({{0, 0}, {1.2, 0.1}, {0.7, 0.9}});
        for (int i = 0; i < 80; ++i) {
            Point a{pos(random), pos(random)}, b{pos(random), pos(random)};
            Polygon vertices;
            for (Point p : tool) { vertices.push_back(p + a); vertices.push_back(p + b); }
            sweeps.push_back(hull(vertices));
            const double before = randomStock.materialArea();
            randomStock.sweep(tool, a, b);
            check(randomStock.materialArea() <= before + 1e-9, "Removal grew material");
        }
        for (int i = 0; i < 20000; ++i) {
            Point q{pos(random), pos(random)};
            bool expected = q.x >= 0 && q.x <= 10 && q.z >= 0 && q.z <= 10;
            for (const auto& sweep : sweeps) expected = expected && !inside(sweep, q);
            check(randomStock.contains(q) == expected, "Random occupancy mismatch");
        }
        validBoundary(randomStock);
        std::cout << "PASS: snapshots, pockets, repeated cuts, disconnected stock, shared edges,\n"
                     "tangencies, narrow remnants, empty stock and 20000 occupancy queries\n";
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
