#include <bits/stdc++.h>
using namespace std;

set<long long> znajdDzielniki(long long n) {
    set<long long> dzielniki = {1, n};

    for (int d = 2; d * d <= n; d++) {
        if (n % d == 0) {
            dzielniki.insert(d);
            dzielniki.insert(n / d);
        }
    }
    return dzielniki;
}