#include <string>
#include <vector>

using namespace std;

/// @brief dajesz pattern dajesz tekst mowi czy jest
/// @param pattern pattern
/// @param text tekst
/// @return czy pattern wystepuje w tekscie
bool kmp(string &pattern, string &text) {
    char sep = '"';
    
    int n = pattern.size() + text.size() + 1;
    vector<int> lps(n, 0);
    string full = pattern + sep + text;
        
    int len = 0;  
    int i = 1;

    while (i < n) {
        if (full[i] == full[len]) {
            len++;
            lps[i] = len;
            i++;
        } else {
            if (len != 0) { 
                len = lps[len - 1];  
            } else {
                lps[i] = 0;
                i++;
            }
        }
    }
    for (i = 0; i < n; i++) {
        if (lps[i] == pattern.size())
            return true;
    }
    return false;
}