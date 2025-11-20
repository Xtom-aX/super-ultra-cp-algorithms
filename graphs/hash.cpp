// Tree Isomorphism I
#include <bits/stdc++.h>
 
using namespace std;
#define int long long
 
const int MOD = 1000000007;
const int POW = 911;
 
pair<int, int> hash_(int v, vector<vector<int>> &graph, vector<bool> &vis)
{
    vector<pair<int, int>> podhashe;
    vis[v] = true;
 
    for (int edge : graph[v])
    {
        if (!vis[edge])
            podhashe.push_back(hash_(edge, graph, vis));
    }
 
    sort(podhashe.begin(), podhashe.end());
 
    int res = 34562;
    int rozmiar = graph[v].size() - 1;
    int suma = 0;
    int xor_ = 0;
    for (pair<int, int> has : podhashe)
    {
        res = (res * POW + has.first) % MOD;
        rozmiar += has.second;
        xor_ ^= has.first;
        suma += has.first;
    }
 
    res = (res * POW + graph[v].size()) % MOD;
    res = (res * POW + rozmiar) % MOD;
    res = (res * POW + xor_) % MOD;
    res = (res * POW + suma) % MOD;
    return make_pair(res, rozmiar);
}