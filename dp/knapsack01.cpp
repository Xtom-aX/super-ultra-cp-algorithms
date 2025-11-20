#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Rozwiązanie problemu typu knapsack 0/1
 * 
 * @param w Wagi przedmiotów
 * @param v Wartości przedmiotów
 * @param W Pojemność plecaka 
 * 
 * @return Maksymalna wartosc przedmiotów, które można wziąć
 */
int knapsack01(const vector<int>& w, const vector<int>& v, int W) {
    int n = w.size();
    vector<int> dp(W + 1, 0);

    for (int i = 0; i < n; i++) {
        // idziemy od W w dół, aby nie używać jednego przedmiotu wiele razy
        for (int weight = W; weight >= w[i]; weight--) {
            dp[weight] = max(dp[weight], dp[weight - w[i]] + v[i]);
        }
    }
    return dp[W];
}