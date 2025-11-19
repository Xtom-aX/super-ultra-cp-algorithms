#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Drzewo przedziałowe przedział-przedział liczące maksimum na przedziale
 * Użycie:
 * Segtree segtree(tab);
 * segtree.update()
 * 
 * @param tab Tablica z wartościami początkowymi
 * @param n_   Liczba elementów
 * 
 * Query/Update:
 * @param `qLeft/qRight/uLeft/uRight` Indeks w tablicy [0; n-1]
 */
struct Segtree {
    int n;
    vector<long long> tree, lazy;

    Segtree(vector<long long> &tab) {
        n = tab.size();

        tree.assign(4*n, 0);
        lazy.assign(4*n, 0);

        build(1, 0, n-1, tab);
    }

    Segtree(int n_) {
        n = n_;
        tree.assign(4*n, 0);
        lazy.assign(4*n, 0);
    }

    void build(int v, int vLeft, int vRight, vector<long long> &tab) {
        if (vLeft == vRight) {
            tree[v] = tab[vLeft];
            return;
        }
        int mid = (vLeft + vRight) / 2;
        build(v*2, vLeft, mid, tab);
        build(v*2+1, mid+1, vRight, tab);
        tree[v] = max(tree[v*2], tree[v*2+1]);
    }

    void push(int v) {
        if (lazy[v] == 0) return;

        tree[v*2]   += lazy[v];
        tree[v*2+1] += lazy[v];

        lazy[v*2]   += lazy[v];
        lazy[v*2+1] += lazy[v];

        lazy[v] = 0;
    }

    void update_(int v, int vLeft, int vRight, int uLeft, int uRight, int val) {
        if (vRight < uLeft || vLeft > uRight)
            return;

        if (vLeft >= uLeft && vRight <= uRight) {
            tree[v] += val;
            lazy[v] += val;
            return;
        }
        push(v);
        int mid = (vLeft + vRight) / 2;
        update_(v*2, vLeft, mid, uLeft, uRight, val);
        update_(v*2+1, mid+1, vRight, uLeft, uRight, val);
        tree[v] = max(tree[v*2], tree[v*2+1]);
    }

    void update(int uLeft, int uRight, int value) {
        update_(1, 0, n-1, uLeft, uRight, value);
    }

    long long query_(int v, int vLeft, int vRight, int qLeft, int qRight) {
        if (vRight < qLeft || vLeft > qRight)
            return numeric_limits<long long>::min();

        if (vLeft >= qLeft && vRight <= qRight) {
            return tree[v];
        }
        push(v);
        int mid = (vLeft + vRight) / 2;
        return max(
            query_(v*2, vLeft, mid, qLeft, qRight),
            query_(v*2+1, mid+1, vRight, qLeft, qRight)
        );
    }

    long long query(int qLeft, int qRight) {
        return query_(1, 0, n-1, qLeft, qRight);
    }
};