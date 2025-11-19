#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Drzewo przedziałowe przedział-przedział liczące sumę na przedziale
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
    vector<long long> tree, lazy;
    int n;
    
    Segtree(vector<long long> &tab) {
        n = tab.size();

        tree.assign(4*n, 0);
        lazy.assign(4*n, 0);

        build(1, 0, n-1, tab);
    }

    void push(int v, int vLeft, int vRight) {
        if (lazy[v] == 0) return;
        int mid = (vLeft + vRight) / 2;
        tree[v*2]   += lazy[v] * (mid-vLeft+1);
        tree[v*2+1] += lazy[v] * (vRight-mid);
        lazy[v*2]   += lazy[v];
        lazy[v*2+1] += lazy[v];
        lazy[v] = 0;
    }

    void build(int v, int left, int right, vector<long long> &tab) {
        if (left == right) {
            tree[v] = tab[left];
            return;
        }
        int mid = (left + right) / 2;
        build(v*2, left, mid, tab);
        build(v*2+1, mid+1, right, tab);
        tree[v] = tree[v*2] + tree[v*2+1];
    }

    void update_(int v, int vLeft, int vRight, int uLeft, int uRight, int val) {
        if (uRight < vLeft || vRight < uLeft)
            return;

        if (vLeft >= uLeft && vRight <= uRight) {
            tree[v] += val * (vRight - vLeft + 1);
            lazy[v] += val;
            return;
        }
        int mid = (vLeft + vRight) / 2;
        push(v, vLeft, vRight);
        update_(v*2, vLeft, mid, uLeft, uRight, val);
        update_(v*2+1, mid+1, vRight, uLeft, uRight, val);
        tree[v] = tree[v*2] + tree[v*2+1];
    }

    void update(int uLeft, int uRight, int value) {
        update_(1, 0, n-1, uLeft, uRight, value);
    }

    int query_(int v, int vLeft, int vRight, int qLeft, int qRight) {
        if (qRight < vLeft || vRight < qLeft)
            return 0;

        if (vLeft >= qLeft && vRight <= qRight) {
            return tree[v];
        }
        int mid = (vLeft + vRight) / 2;
        push(v, vLeft, vRight);
        return query_(v*2, vLeft, mid, qLeft, qRight) + query_(v*2+1, mid+1, vRight, qLeft, qRight);
    }

    long long query(int qLeft, int qRight) {
        return query_(1, 0, n-1, qLeft, qRight);
    }
};