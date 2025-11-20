// daje najnizszego wspolnego przodka dla dwoch nodow w drzewie

#include <vector>
#include <math.h>

using namespace std;

vector<vector<int>> jmp;
vector<int> depths;

int LOG;
void get_parents(vector<vector<int>> &graph, vector<int> &parent, int v, int prev, int depth) {
    parent[v] = prev;
    depths[v] = depth;
    for (int edge: graph[v]) {
        if (edge == prev) continue;
        get_parents(graph, parent, edge, v, depth + 1);
    }
}   

void create(vector<vector<int>> &graph) {
    vector<int> parent(graph.size());
    depths.resize(graph.size());
    int max_dep = 0;
    get_parents(graph, parent, 1, -1, 0);
    LOG = (int)log2(graph.size()) + 1;
    jmp = vector<vector<int>> (graph.size(), vector<int>(LOG));
    for (int v = 0; v < graph.size(); v++)
        jmp[v][0] = parent[v];
    for (int k = 1; k < LOG; k++) {
        for (int v = 0; v < graph.size(); v++) {
            int mid = jmp[v][k - 1];
            if (mid != -1)
                jmp[v][k] = jmp[mid][k - 1];
        }
    }   


}

int jump(int v, int k) {
    for (int i = 0; i < LOG; i++) {
        if (k & (1 << i)) {
            v = jmp[v][i];
            if (v == -1) return -1;
        }
    }
    return v;
}



int lca(int a, int b) {
    if (depths[b] > depths[a])
        swap(a, b);
    
    a = jump(a, depths[b] - depths[a]);
    if (a == b) return a;

    for (int i = LOG - 1; i >= 0; i++) {
        if (jmp[a][i] != jmp[b][i]) {
            a = jmp[a][i];
            b = jmp[b][i];
        }
    }

    return jmp[a][0];
}
