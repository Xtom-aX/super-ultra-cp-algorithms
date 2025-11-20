#include <bits/stdc++.h>

using namespace std;

/**
* @brief Liczy najdłuższy wspólny podciąg
*
* @param s1 Pierwszy napis
* @param s2 Drugi napis
*
* @return Najdłuższy wspólny podciąg z dwóch podanych napisów
*/
string lcs(const string &s1, const string &s2) {
    vector<vector<int>> lcs(s1.size()+1, vector<int>(s2.size()+1));

    /* Kierunki:
    * -1 = Nieustalony
    *  0 = s1-1
    *  1 = s2-1
    *  2 = s1-1 && s2-1
    */
    vector<vector<short>> kierunek(s1.size()+1, vector<short>(s2.size()+1, -1));

    for (int i = 0; i <= s1.size(); i++) lcs[i][0] = 0;
    for (int i = 0; i <= s2.size(); i++) lcs[0][i] = 0;

    for (int i = 1; i <= s1.size(); i++) {
        for (int j = 1; j <= s2.size(); j++) {
            if (s1[i-1] == s2[j-1]) {
                lcs[i][j] = lcs[i-1][j-1]+1;
                kierunek[i][j] = 2;
            }
            else {
                if (lcs[i-1][j] > lcs[i][j-1]) {
                    lcs[i][j] = lcs[i-1][j];
                    kierunek[i][j] = 0;
                } else {
                    lcs[i][j] = lcs[i][j-1];
                    kierunek[i][j] = 1;
                }
            }
        }
    }
    int s1Idx = s1.size(), s2Idx = s2.size();
    string wynik = "";
    while (s1Idx > 0 && s2Idx > 0) {
        if (kierunek[s1Idx][s2Idx] == 0)
            s1Idx--;
        else if (kierunek[s1Idx][s2Idx] == 1)
            s2Idx--;
        else { //if (kierunek[s1Idx][s2Idx] == 2)
            wynik += s1[s1Idx-1];

            s1Idx--;
            s2Idx--;
        }
    }
    reverse(wynik.begin(), wynik.end());
    return wynik;
}

int main()
{
    ios_base::sync_with_stdio(0);
    cin.tie(0);

    string s1, s2;
    cin >> s1 >> s2;

    cout << lcs(s1, s2) << '\n';

    return 0;
}