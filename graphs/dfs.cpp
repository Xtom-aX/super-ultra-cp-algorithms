#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Przeszukiwanie grafu w głąb (DFS)
 * 
 * @param graf Graf reprezentowany jako lista sąsiedztwa
 * @param v Aktualnie odwiedzany wierzchołek
 * @param odwiedzone Wektor z informacją czy wierzchołek został odwiedzony
 */
void DFS(const vector<vector<int>> &graf, int v, vector<bool> &odwiedzone) {
    odwiedzone[v] = true;

    // == Miejsce na przetwarzanie wierzchołka ==
    //cout << "V = " << v << endl;

    for (const int &sasiad : graf[v])
        if (!odwiedzone[sasiad])
            DFS(graf, sasiad, odwiedzone);
}