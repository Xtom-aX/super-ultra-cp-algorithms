#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Liczy sposoby na uzyskanie sumy `S`
 * @param a Wartości tablicy
 * 
 * @return Na ile sposobów można uzyskać sumę `S` z elementów `a`
 */
long long countSubsetSum(const vector<int>& a, int S) {
    vector<long long> dp(S + 1, 0);
    dp[0] = 1;

    for (int x : a) {
        for (int s = S; s >= x; s--) {
            dp[s] += dp[s - x];
        }
    }
    return dp[S];
}
