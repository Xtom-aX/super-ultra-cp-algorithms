#include <vector>

using namespace std;

vector<int> par;
vector<int> siz;

void init(int n) {
    par.assign(n + 1, 0);
    siz.assign(n + 1, 1);
    for (int i = 1; i<=n; i++)
        par[i] = i;
}

int find(int v) {
    if (par[v] == v)
        return v;
    return par[v] = find(par[v]);
}

void onion(int a, int b) {
    a = find(a);
    b = find(b);
    if (a == b)
        return;
    if (siz[b] > siz[a])
        swap(a, b);
    par[b] = a;
    siz[a] += siz[b];
}