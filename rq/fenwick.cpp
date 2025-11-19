#include <bits/stdc++.h>

using namespace std;

struct fenwick {
    vector<int> bits;
    int n;

    fenwick(int num) {
        n = num;
        bits.assign(n, 0);
    }

    int sum(int x) {
        int res = 0;
        while (x >= 0) {
            res += bits[x];
            x = x & -x;
        }
        return res;
    }

    void update(int x, int val) {
        while (x < n) {
            bits[x] += val;
            x = x & -x;
        }
    }

    int sum(int l, int r) {
        return sum(r) - sum(l - 1);
    }
};