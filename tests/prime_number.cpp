#include <iostream>
using namespace std;
int main() {
    int n;
    cin >> n;
    bool prime = n >= 2;
    for (int i = 2; i * i <= n && prime; i++) {
        if (n % i == 0)
            prime = false;
    }
    if (prime)
        cout << "Prime";
    else
        cout << "Not Prime";
    return 0;
}
