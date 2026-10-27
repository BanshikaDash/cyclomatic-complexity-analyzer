#include <iostream>
#include <vector>
#include <stdexcept>

// if (fake) while (comment) && ||
int simple() { return 1; }

int grade(int score) {
    if (score >= 90 && score <= 100) {
        return 4;
    } else if (score >= 80 || score == 79) {
        return 3;
    } else if (score >= 70) {
        return 2;
    }
    const char* text = "if (x) while (y) && ||";
    return score > 0 ? 1 : 0;
}

int loops(std::vector<int>& v, int n) {
    int total = 0;
    for (int i = 0; i < n; ++i) {
        if (i % 2 == 0) continue;
        if (i > 50) break;
        total += i;
    }
    for (auto x : v) { total += x; }
    int k = 0;
    while (k < 10 && total > 0) { k++; total--; }
    do { k--; } while (k > 0);
    return total;
}

int sw(int cmd) {
    switch (cmd) {
        case 1:
        case 2:
            cmd++;
            break;
        case 3:
            cmd--;
        case 4:
            cmd *= 2;
            break;
        default:
            cmd = 0;
    }
    return cmd;
}

void safe(int x) {
    try {
        if (x < 0) throw std::invalid_argument("neg");
        std::cout << x;
    } catch (const std::invalid_argument& e) {
        std::cout << "bad";
    } catch (...) {
        std::cout << "other";
    }
}

class Box {
public:
    Box(int v) : value(v) { if (v < 0) value = 0; }
    int get() const { return value; }
    bool ok() const { return value > 0 && value < 100 || value == 500; }
private:
    int value;
};

namespace util {
template <typename T>
T clamp(T v, T lo, T hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}
}

int Box_free(int a, int b) {
    for (;;) {
        if (a > b) return a;
        a++;
    }
}

int main() {
    auto f = [](int x) { if (x) return 1; return 0; };
    std::cout << grade(85) << f(2);
    if (!(grade(1) > 2 && sw(2) < 3)) { return 1; }
    return 0;
}
