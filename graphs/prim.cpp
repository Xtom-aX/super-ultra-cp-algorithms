// tworzy (spojne drzewo ktore zawiera wszystkie wierzcholki dowolnego grafu) o minimalnej sumie wag
// zwraca jedynie sume wag

#include <vector>
#include <queue>

using namespace std;

// first -> edge
// second -> waga
long long prim(vector<vector<pair<int, int>>> &graph, int start) {
    long long total = 0;
    vector<bool> vis(graph.size(), false);
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, start});
    while (!pq.empty()) {
        pair<int, int> cur = pq.top();
        pq.pop();
        if (vis[cur.second]) continue;
        vis[cur.second] = true;
        total += cur.first;
        for (pair<int, int> edge: graph[cur.second]) {
            if (vis[edge.first]) continue;
            pq.push({edge.second, edge.first});
        }
    }
    return total;
}