#include <bits/stdc++.h>
using namespace std;
#define MID ((vLeft + vRight) / 2)

/**
 * @brief Drzewo przedziałowe przedział-przedział liczące sumę na przedziale z operacją mnożenia
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

// ===== [ MODULO DO ZMIANY WG. TREŚCI ZADANIA! ] =====
const long long MOD = 123456789;

struct Segtree {
    int n;
    vector<long long> tree, lazy;

    Segtree(vector<long long> &tab) {
        n = tab.size();

        tree.assign(4*n, 0);
        lazy.assign(4*n, 1);

        build(1, 0, n-1, tab);
    }

    void build(int v, int vLeft, int vRight, vector<long long> &tab) {
        if (vLeft == vRight) {
            tree[v] = tab[vLeft];
            return;
        }
        int mid = MID;
        build(v*2, vLeft, mid, tab);
        build(v*2+1, mid+1, vRight, tab);
        tree[v] = ((tree[v*2] % MOD + tree[v*2+1] % MOD) + MOD) % MOD;
    }

    void push(int v, int vLeft, int vRight) {
        if (lazy[v] == 1) return;
        tree[v*2] = (tree[v*2] * lazy[v]) % MOD;
        tree[v*2+1] = (tree[v*2+1] * lazy[v]) % MOD;
        lazy[v*2] = (lazy[v*2] * lazy[v]) % MOD;
        lazy[v*2+1] = (lazy[v*2+1] * lazy[v]) % MOD;
        lazy[v] = 1;
    }

    void update_(int v, int vLeft, int vRight, int updateLeft, int updateRight, long long val) {
        if (vLeft > updateRight || vRight < updateLeft)
            return;
        
        if (vLeft >= updateLeft && vRight <= updateRight) {
            tree[v] = ((tree[v] % MOD) * (val % MOD)) % MOD;
            lazy[v] = (lazy[v] % MOD * val % MOD) % MOD;
            return;
        }
        int mid = MID;
        push(v, vLeft, vRight);

        update_(v*2, vLeft, mid, updateLeft, updateRight, val);
        update_(v*2+1, mid+1, vRight, updateLeft, updateRight, val);
        tree[v] = (tree[v*2] + tree[v*2+1]) % MOD;
    }

    void update(int uLeft, int uRight, int value) {
        update_(1, 0, n-1, uLeft, uRight, value);
    }


    long long query_(int v, int vLeft, int vRight, int queryLeft, int queryRight) {
        if (vLeft > queryRight || vRight < queryLeft)
            return 0;
        
        if (vLeft >= queryLeft && vRight <= queryRight)
            return tree[v];
        int mid = MID;
        push(v, vLeft, vRight);

        return (query_(v*2, vLeft, mid, queryLeft, queryRight) + query_(v*2+1, mid+1, vRight, queryLeft, queryRight) + MOD) % MOD;
    }   

    long long query(int qLeft, int qRight) {
        return query_(1, 0, n-1, qLeft, qRight);
    }
};