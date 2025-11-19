#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Wyznacza odległości najkrótszych ścieżek między wszystkimi parami wierzchołków
 * 
 * @param dist Macierz odległości między wierzchołkami. Na wejściu: waga krawędzi, INF jeśli brak krawędzi. Na wyjściu: najkrótsze odległości.
 */
void floydWarshall(vector<vector<int>> &dist) {
    int n = dist.size();

    for (int k = 0; k < n; ++k) {
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                // === Miejsce na przetwarzanie pary (i, j) przez wierzchołek k ===

                if (dist[i][k] < INT_MAX && dist[k][j] < INT_MAX) {
                    dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j]);
                }
            }
        }
    }
}