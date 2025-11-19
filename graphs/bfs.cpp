#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Przeszukiwanie grafu wszerz (BFS)
 * 
 * @param graf Graf reprezentowany jako lista sąsiedztwa
 * @param starty Wektor wierzchołków startowych
 * @param odwiedzone Wektor z informacją czy wierzchołek został odwiedzony
 */
void BFS(const vector<vector<int>> &graf, const vector<int> &starty, vector<bool> &odwiedzone) {
    queue<int> kolejka;

    for (int v : starty) {
        odwiedzone[v] = true;
        kolejka.push(v);
    }

    int v;
    while (!kolejka.empty()) {
        v = kolejka.front(); kolejka.pop();

        for (const int &sasiad : graf[v]) {
            if (odwiedzone[sasiad]) continue;

            // == Miejsce na przetwarzanie wierzchołka ==
            //cout << "V = " << v << endl;

            odwiedzone[sasiad] = true;
            kolejka.push(sasiad);
        }
    }   
}

/**
 * @brief Przeszukiwanie grafu wszerz (BFS)
 * 
 * @param graf Graf reprezentowany jako lista sąsiedztwa
 * @param start Wierzchołek startowy
 * @param odwiedzone Wektor z informacją czy wierzchołek został odwiedzony
 */
void BFS(const vector<vector<int>> &graf, int start, vector<bool> &odwiedzone) {
    queue<int> kolejka;
    odwiedzone[start] = true;
    kolejka.push(start);

    int v;
    while (!kolejka.empty()) {
        v = kolejka.front(); kolejka.pop();

        for (const int &sasiad : graf[v]) {
            if (odwiedzone[sasiad]) continue;

            // == Miejsce na przetwarzanie wierzchołka ==
            //cout << "V = " << v << endl;

            odwiedzone[sasiad] = true;
            kolejka.push(sasiad);
        }
    } 
}