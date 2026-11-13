#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace stock_preview {

struct Point {
    double x, z;
};
using Polygon = std::vector<Point>;
struct Edge {
    Point start, end;
};

inline Point operator+(Point a, Point b) { return {a.x + b.x, a.z + b.z}; }
inline Point operator-(Point a, Point b) { return {a.x - b.x, a.z - b.z}; }
inline Point operator*(Point a, double s) { return {a.x * s, a.z * s}; }
inline double dot(Point a, Point b) { return a.x * b.x + a.z * b.z; }
inline long double cross(Point a, Point b) {
    return static_cast<long double>(a.x) * b.z - static_cast<long double>(a.z) * b.x;
}
inline long double area(const Polygon& polygon) {
    long double result = 0;
    for (size_t i = 1; i + 1 < polygon.size(); ++i)
        result += cross(polygon[i] - polygon[0], polygon[i + 1] - polygon[0]);
    return result / 2;
}

inline Polygon hull(Polygon points) {
    for (Point p : points)
        if (!std::isfinite(p.x) || !std::isfinite(p.z))
            throw std::invalid_argument("Coordinates must be finite");
    std::sort(points.begin(), points.end(), [](Point a, Point b) {
        return a.x < b.x || (a.x == b.x && a.z < b.z);
    });
    points.erase(std::unique(points.begin(), points.end(), [](Point a, Point b) {
        return a.x == b.x && a.z == b.z;
    }), points.end());
    if (points.size() < 3)
        throw std::invalid_argument("A polygon needs three non-collinear vertices");
    Polygon result(2 * points.size());
    size_t n = 0;
    for (Point p : points) {
        while (n >= 2 && cross(result[n - 1] - result[n - 2], p - result[n - 1]) <= 0)
            --n;
        result[n++] = p;
    }
    const size_t lower = n;
    for (auto i = points.rbegin() + 1; i != points.rend(); ++i) {
        while (n > lower && cross(result[n - 1] - result[n - 2], *i - result[n - 1]) <= 0)
            --n;
        result[n++] = *i;
    }
    result.resize(n - 1);
    if (result.size() < 3 || area(result) <= 0)
        throw std::invalid_argument("Polygon has no area");
    return result;
}

inline Polygon convex(Polygon polygon) {
    if (polygon.size() > 1 && polygon.front().x == polygon.back().x
            && polygon.front().z == polygon.back().z)
        polygon.pop_back();
    Polygon boundary = hull(polygon);
    // Validate the supplied boundary rather than silently filling a concavity.
    const long double supplied = std::abs(area(polygon));
    const long double expected = area(boundary);
    if (std::abs(supplied - expected) > 1e-12L * expected)
        throw std::invalid_argument("Prototype requires a simple convex polygon");
    return boundary;
}

struct Bounds {
    double xmin, xmax, zmin, zmax;
    explicit Bounds(const Polygon& polygon)
        : xmin(polygon[0].x), xmax(xmin), zmin(polygon[0].z), zmax(zmin) {
        for (Point p : polygon) {
            xmin = std::min(xmin, p.x); xmax = std::max(xmax, p.x);
            zmin = std::min(zmin, p.z); zmax = std::max(zmax, p.z);
        }
    }
    bool overlaps(const Bounds& b) const {
        return xmin < b.xmax && xmax > b.xmin && zmin < b.zmax && zmax > b.zmin;
    }
};

inline Polygon clip(const Polygon& polygon, Point a, Point b, bool inside) {
    Polygon result;
    if (polygon.empty())
        return result;
    Point previous = polygon.back();
    long double before = cross(b - a, previous - a);
    for (Point current : polygon) {
        const long double after = cross(b - a, current - a);
        const bool keepBefore = inside ? before >= 0 : before <= 0;
        const bool keepAfter = inside ? after >= 0 : after <= 0;
        if (keepBefore != keepAfter) {
            const double t = static_cast<double>(before / (before - after));
            Point intersection = previous + (current - previous) * t;
            // Preserve exact axis-aligned boundaries despite interpolation rounding.
            if (a.x == b.x)
                intersection.x = a.x;
            if (a.z == b.z)
                intersection.z = a.z;
            result.push_back(intersection);
        }
        if (keepAfter)
            result.push_back(current);
        previous = current;
        before = after;
    }
    result.erase(std::unique(result.begin(), result.end(), [](Point p, Point q) {
        return p.x == q.x && p.z == q.z;
    }), result.end());
    if (result.size() > 1 && result.front().x == result.back().x
            && result.front().z == result.back().z)
        result.pop_back();
    if (result.size() < 3 || area(result) == 0)
        result.clear();
    return result;
}

inline bool resolved(const Polygon& polygon) {
    double magnitude = 1, perimeter = 0;
    for (size_t i = 0; i < polygon.size(); ++i) {
        Point p = polygon[i], d = polygon[(i + 1) % polygon.size()] - p;
        magnitude = std::max({magnitude, std::abs(p.x), std::abs(p.z)});
        perimeter += std::sqrt(dot(d, d));
    }
    return area(polygon) > 64 * std::numeric_limits<double>::epsilon() * magnitude * perimeter;
}

class StockState {
    struct Cell {
        Polygon polygon;
        Bounds bounds;
        explicit Cell(Polygon p) : polygon(std::move(p)), bounds(polygon) {}
    };
    std::vector<Cell> cells;
    size_t uncertainRetentions = 0;

public:
    explicit StockState(Polygon stock) { cells.emplace_back(convex(std::move(stock))); }

private:
    void remove(const Polygon& cutter) {
        const Bounds bounds(cutter);
        std::vector<Cell> next;
        for (const Cell& cell : cells) {
            if (!cell.bounds.overlaps(bounds)) {
                next.push_back(cell);
                continue;
            }
            Polygon intersection = cell.polygon;
            for (size_t i = 0; i < cutter.size() && !intersection.empty(); ++i)
                intersection = clip(intersection, cutter[i], cutter[(i + 1) % cutter.size()], true);
            if (intersection.empty()) {
                next.push_back(cell);
                continue;
            }
            if (!resolved(intersection)) {
                ++uncertainRetentions;
                next.push_back(cell);
                continue;
            }
            Polygon remaining = cell.polygon;
            const size_t checkpoint = next.size();
            bool uncertain = false;
            // Peel off outside pieces; only the final intersection is discarded.
            for (size_t i = 0; i < cutter.size() && !remaining.empty(); ++i) {
                Point a = cutter[i], b = cutter[(i + 1) % cutter.size()];
                Polygon outside = clip(remaining, a, b, false);
                if (!outside.empty() && !resolved(outside)) {
                    uncertain = true;
                    break;
                }
                if (!outside.empty())
                    next.emplace_back(std::move(outside));
                remaining = clip(remaining, a, b, true);
            }
            if (uncertain) {
                ++uncertainRetentions;
                next.erase(next.begin() + checkpoint, next.end());
                next.push_back(cell);
            }
        }
        cells = std::move(next);
    }

public:
    void sweep(const Polygon& tool, Point start, Point end) {
        if (!std::isfinite(start.x) || !std::isfinite(start.z)
                || !std::isfinite(end.x) || !std::isfinite(end.z))
            throw std::invalid_argument("Move coordinates must be finite");
        const Polygon insert = convex(tool);
        Polygon points;
        for (Point p : insert) {
            points.push_back(p + start);
            points.push_back(p + end);
        }
        remove(hull(std::move(points)));
    }

    size_t cellCount() const { return cells.size(); }
    std::vector<Polygon> polygons() const {
        std::vector<Polygon> result;
        result.reserve(cells.size());
        for (const Cell& cell : cells)
            result.push_back(cell.polygon);
        return result;
    }
    size_t retainedUncertain() const { return uncertainRetentions; }
    double materialArea() const {
        long double result = 0;
        for (const Cell& cell : cells)
            result += area(cell.polygon);
        return static_cast<double>(result);
    }
    bool contains(Point p) const {
        if (!std::isfinite(p.x) || !std::isfinite(p.z))
            throw std::invalid_argument("Query coordinates must be finite");
        for (const Cell& cell : cells) {
            bool inside = true;
            for (size_t i = 0; i < cell.polygon.size(); ++i)
                if (cross(cell.polygon[(i + 1) % cell.polygon.size()] - cell.polygon[i],
                          p - cell.polygon[i]) < 0) {
                    inside = false;
                    break;
                }
            if (inside)
                return true;
        }
        return false;
    }

    std::vector<Edge> boundary(double tolerance = 1e-12) const {
        if (!std::isfinite(tolerance) || tolerance < 0)
            throw std::invalid_argument("Boundary tolerance must be finite and non-negative");
        std::vector<Edge> edges, result;
        for (const Cell& cell : cells) {
            if (area(cell.polygon) <= 0)
                throw std::runtime_error("Degenerate stock cell");
            for (size_t i = 0; i < cell.polygon.size(); ++i)
                edges.push_back({cell.polygon[i], cell.polygon[(i + 1) % cell.polygon.size()]});
        }
        using Interval = std::pair<double, double>;
        std::vector<std::vector<Interval>> retained(edges.size(), {{0, 1}});
        const auto erase = [](std::vector<Interval>& intervals, double low, double high) {
            std::vector<Interval> next;
            for (auto part : intervals) {
                if (high <= part.first || low >= part.second) {
                    next.push_back(part);
                    continue;
                }
                if (part.first < low) next.emplace_back(part.first, low);
                if (part.second > high) next.emplace_back(high, part.second);
            }
            intervals = std::move(next);
        };
        // Cancel each shared span on both edges together; never cancel it twice.
        for (size_t i = 0; i < edges.size(); ++i) {
            Point d = edges[i].end - edges[i].start;
            const double length2 = dot(d, d), length = std::sqrt(length2);
            if (length2 == 0) continue;
            for (size_t j = i + 1; j < edges.size() && !retained[i].empty(); ++j) {
                if (retained[j].empty()) continue;
                Point v = edges[j].end - edges[j].start;
                if (dot(d, v) >= 0)
                    continue;
                if (std::abs(cross(d, edges[j].start - edges[i].start)) > tolerance * length
                        || std::abs(cross(d, edges[j].end - edges[i].start)) > tolerance * length)
                    continue;
                const auto first = retained[i], second = retained[j];
                for (auto a : first) for (auto b : second) {
                    const double low = std::max(a.first, dot(edges[j].start + v * b.second - edges[i].start, d) / length2);
                    const double high = std::min(a.second, dot(edges[j].start + v * b.first - edges[i].start, d) / length2);
                    if (low >= high) continue;
                    erase(retained[i], low, high);
                    const double otherLow = dot(edges[i].start + d * high - edges[j].start, v) / dot(v, v);
                    const double otherHigh = dot(edges[i].start + d * low - edges[j].start, v) / dot(v, v);
                    erase(retained[j], std::max(b.first, otherLow), std::min(b.second, otherHigh));
                }
            }
        }
        for (size_t i = 0; i < edges.size(); ++i) {
            Point d = edges[i].end - edges[i].start;
            const double length = std::sqrt(dot(d, d));
            for (auto part : retained[i])
                if ((part.second - part.first) * length > tolerance)
                    result.push_back({edges[i].start + d * part.first, edges[i].start + d * part.second});
        }
        return result;
    }
};

} // namespace stock_preview
