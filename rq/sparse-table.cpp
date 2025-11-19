#include <vector>
#include <algorithm>


using namespace std;

struct st {
    // ZMIEN TO. to powinno byc log2(MAXN)
    int K = 25;
    int n;
    vector<vector<int>> sparse;
    vector<int> lg;
    

    st(vector<int> v) {
        sparse = vector<vector<int>>(K + 1, vector<int>(v.size(), 0));
        lg = vector<int>(v.size() + 1, 0);
        lg[1] = 0;
        for (int i = 2; i <= v.size(); i++)
            lg[i] = lg[i/2] + 1;
        std::copy(v.begin(), v.end(), sparse[0].begin());
        for (int i = 1; i <= K; i++)
            for (int j = 0; j + (1 << i) <= v.size(); j++)
                sparse[i][j] = min(sparse[i - 1][j],  sparse[i - 1][j + (1 << (i - 1))]);
    }

    int qery(int l, int r) {
        int i = lg[r - l + 1];
        return min(sparse[i][l], sparse[i][r - (1 << i) + 1]);
    }
};