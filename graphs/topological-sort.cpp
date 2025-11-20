#include <bits/stdc++.h>
using namespace std;

using Graph = vector<vector<int>>;

void dfs(const Graph &graph, int v, vector<int> &topoOrder, vector<uint8_t> &visited) {
    visited[v] = true;
    for (int u : graph[v]) {
        if (!visited[u])
            dfs(graph, u, topoOrder, visited);
    }
    topoOrder.push_back(v);
}

/**
 * @brief Zwraca porządek topologiczny w DAG'u
 * ! MUSI BYĆ DAG - NIE MOŻE BYĆ CYKLI !
 * 
 * @param graph Graf przedstawiony jako lista sąsiedztwa
 * @return Porządek topologiczny w podanym grafie
 */
vector<int> topologicalSort(const Graph &graph) {
    vector<int> topoOrder;
    vector<uint8_t> visited(graph.size(), false);

    for (int i = 0; i < graph.size(); i++) {
        if (!visited[i])
            dfs(graph, i, topoOrder, visited);
    }
    reverse(topoOrder.begin(), topoOrder.end());
    return topoOrder;
}