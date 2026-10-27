#include <iostream>
using namespace std;

int classify(int number) {
    if (number < 0) {
        return -1;
    } else if (number == 0) {
        return 0;
    }

    if (number > 10 && number < 100) {
        return 1;
    }

    return 2;
}

int main() {
    cout << classify(25) << endl;
    return 0;
}
