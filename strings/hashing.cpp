#include <bits/stdc++.h>
using namespace std;

const long long POW = 31;
const long long MOD = 1e9+7;

/**
 * @brief Liczy hash z tekstu
 * 
 * @param text Tekst wejściowy
 * @return Hash tekstu jako long long
 */
long long hash_(const string &text) {
    long long result = 0;
    long long p_pow = 1;

    for (const char &ch : text) {
        result = (result + (ch - 'a' + 1) * p_pow) % MOD;
        p_pow = (p_pow * POW) % MOD;
    }
    return result;
}