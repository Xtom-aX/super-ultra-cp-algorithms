#include <bits/stdc++.h>
using namespace std;

struct Edge {
    int a, b, w;
};

/**
 * @brief Znajduje odległości najkrótszych ścieżek
 * w grafie ważonym z ujemnymi wagami.
 * Sprawdza również czy występuje ujemny cykl.
 * 
 * @param n Liczba wierzchołków w grafie
 * @param graph Graf przedstawiony jaki lista krawędzi
 * @param start Wierzchołek startowy
 * 
 * @return Odległości do wszystkich wierzchołków
 * Dla nieodwiedzonych wierzchołków zwraca `numeric_limits<long long>::max()`
 */
vector<long long> bellmanFord(int n, const vector<Edge> &graph, int start, bool &negativeCycleExists) {
    vector<long long> dist(n, numeric_limits<long long>::max());
    dist[start] = 0;

    bool any = true;
    negativeCycleExists = false;
    for (int i = 0; i < n && any; i++) {
        any = false;
        for (const Edge &edge : graph) {
            if (dist[edge.a] == numeric_limits<long long>::max()) continue;

            if (dist[edge.a] + edge.w < dist[edge.b]) {                
                dist[edge.b] = dist[edge.a] + edge.w;
                any = true;
                if (i == n-1)
                    negativeCycleExists = true;
            }
        }   
    } 

    return dist;
}

vector<long long> bellmanFord(int n, const vector<Edge> &graph, int start) {
    bool x;
    return bellmanFord(n, graph, start, x);
}