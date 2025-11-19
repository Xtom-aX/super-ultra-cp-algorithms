#include <bits/stdc++.h>
using namespace std;

/**
 * @brief Oblicza odległości do wszystkich wierzchołków z wierzchołka `start`
 * 
 * @param graf Graf reprezentowany jako lista sąsiedztwa
 * @param start Wierzchołek startowy
 * @return `vector<int>` Odległość do wierzchołka v -> odleglosc[v]
 */
vector<int> dijkstra(const vector<vector<pair<int, int>>> &graf, const int start) {
    
    // Odległość do wierzchołka v -> odleglosc[v]
    vector<int> odleglosc(graf.size(), numeric_limits<int>::max());
	odleglosc[start] = 0;

    // Kolejka priorytetowa wierzchołków posortowana po odległościach
	priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> kolejka;
	kolejka.push({0, start});

	int v, odl;
	while (!kolejka.empty()) {
		v = kolejka.top().second;
		odl = kolejka.top().first;
		kolejka.pop();

        // Jeśli odległość nie jest aktualna - pomiń
		if (odleglosc[v] != odl)
			continue;

        // Dla każdego sąsiada wierzchołka v
		for (pair<int, int> krawedz : graf[v]) {
            // Jeśli znaleziono krótszą trasę do wierzchołka v
			if (odl + krawedz.second < odleglosc[krawedz.first]) {
				odleglosc[krawedz.first] = odl + krawedz.second;
				kolejka.push({odleglosc[krawedz.first], krawedz.first});
			}
		}
	}

    return odleglosc;
}