#include <bits/stdc++.h>
using namespace std;

typedef unsigned long long ull;

const ull MOD = 1e9+7;

ull qpow(ull base, ull exp) {
    if (base == 0)
        return 1;

    if (exp % 2 == 1)
        return (qpow(base, exp-1) * base) % MOD;

    ull p = qpow(base, exp / 2);
    return (p * p) % MOD;
}