#include <bits/stdc++.h>
using namespace std;

vector<long long> rozkladNaCzynniki(long long n) {
    vector<long long> czynniki;

    int d = 2;
    while (n > 1) {
        if (n % d == 0) {
            czynniki.push_back(d);
            n /= d;
        } else {
            d++;
        }
    }
    return czynniki;
}