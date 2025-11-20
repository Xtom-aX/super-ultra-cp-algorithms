# Optymalizacje
g++ main.cpp -o main -O3 -static -Wall -Wextra

# Więcej informacji
g++ main.cpp -o main -fsanitize=address,undefined -g -Wall -Wextra

# Generatorka
for i in $(seq 1 10);
do
    ./gen > in/$i.in
    ./brut < in/$i.in > out/$i.out
done