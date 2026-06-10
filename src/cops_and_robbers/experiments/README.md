# Eksperymenty

Ten katalog zawiera skrypty do uruchamiania eksperymentów bez interfejsu Pygame.
Każdy eksperyment symuluje wiele gier bot-vs-bot, zapisuje wyniki do CSV, a
`plot_results.py` generuje wykresy PNG z gotowych CSV.

Eksperymenty używają tego samego modelu gry co aplikacja: graf nieskierowany,
policjanci ruszają się pierwsi, w jednej rundzie najpierw wykonują wspólny ruch
policjanci, potem rusza złodziej. Złapanie następuje, gdy po dowolnym ruchu
policjant i złodziej stoją na tym samym wierzchołku.

## Instalacja

```bash
pip install -r requirements.txt
pip install -e .
```

Do rysowania wykresów potrzebny jest `matplotlib`, uwzględniony w
`requirements.txt`.

## Wspólne założenia

- Domyślny wybór pozycji startowych to `placement=heuristic`, nie losowy start.
- Policjanci startują na centralnych wierzchołkach, czyli o minimalnej
  ekscentryczności; przy remisie preferowany jest większy stopień.
- Złodziej startuje na wierzchołku maksymalizującym odległość do najbliższego
  policjanta; przy remisie preferowany jest większy stopień.
- `random` placement nadal istnieje jako opcja, ale nie jest używany w głównych
  eksperymentach.
- Każda gra dostaje osobny graf i osobne ziarna losowości wyprowadzone z
  `--seed`.
- Generator `any` nie losuje jednostajnie po wszystkich spójnych grafach:
  najpierw tworzy losowe drzewo rozpinające, potem dodaje losowe krawędzie.
- Generator `tree` tworzy losowe drzewo.
- Generator `planar` zaczyna od drzewa i dodaje tylko takie krawędzie, które nie
  psują planarności.

## Eksperyment 2: macierz bot-vs-bot

Plik:

```bash
python -m cops_and_robbers.experiments.exp2_bot_matrix
```

Cel: porównać strategie ruchu policjanta i złodzieja przy tej samej heurystyce
startowej.

Porównywane strategie:

```text
policjant: random, greedy, minimax(d=3)
złodziej: random, greedy, minimax(d=3)
```

Każda para strategii jest testowana osobno, np. `greedy` policjant kontra
`minimax(d=3)` złodziej.

Domyślna konfiguracja:

```text
liczba policjantów: 1
typ grafu: any
liczba gier: 100 na komórkę macierzy i kubełek
placement: heuristic
limit rund: T=max(20, round(5n/3))
```

Kubełki grafów:

```text
n12_sparse: n=12, m=18, T=20
n12_dense:  n=12, m=30, T=20
n30_sparse: n=30, m=45, T=50
n30_dense:  n=30, m=75, T=50
```

Wynik CSV:

```text
src/results/exp2_bot_matrix.csv
```

Wykresy PNG są generowane osobno dla każdego kubełka:

```text
src/results/exp2_bot_matrix_n12_sparse.png
src/results/exp2_bot_matrix_n12_dense.png
src/results/exp2_bot_matrix_n30_sparse.png
src/results/exp2_bot_matrix_n30_dense.png
```

Interpretacja: wynik mówi, jak często policjant wygrywa przeciwko danej
strategii złodzieja na losowych grafach z danego kubełka. To nie jest dowód
optymalności strategii; minimax jest ograniczony głębokością.

## Eksperyment 3: wpływ rozmiaru grafu

Plik:

```bash
python -m cops_and_robbers.experiments.exp3_size_sweep
```

Cel: sprawdzić, jak skuteczność strategii policjanta zmienia się wraz z
rozmiarem grafu.

Domyślna konfiguracja:

```text
n: 5, 8, 10, 15, 20, 25, 30
m: round(1.5n), z clampem do legalnego zakresu
T: max(10, 2n)
liczba policjantów: 1
typ grafu: any
liczba gier: 100 na punkt
placement: heuristic
```

Domyślnie porównywane są strategie policjanta:

```text
random
greedy
minimax(d=3)
```

Są dwa warianty złodzieja:

```text
greedy
minimax(d=3)
```

Czyli eksperyment tworzy dwa zestawy krzywych:

```text
policjanci random/greedy/minimax kontra złodziej greedy
policjanci random/greedy/minimax kontra złodziej minimax(d=3)
```

Wynik CSV:

```text
src/results/exp3_size_sweep.csv
```

Wykresy PNG:

```text
src/results/exp3_size_sweep_robber_greedy.png
src/results/exp3_size_sweep_robber_minimax.png
```

Interpretacja: eksperyment pokazuje, czy dana strategia policjanta traci
skuteczność, gdy graf rośnie. Osobne wykresy dla złodzieja greedy i minimax
pozwalają odróżnić łatwego przeciwnika od silniejszego przeciwnika.

## Eksperyment 4: liczba policjantów i typ grafu

Plik:

```bash
python -m cops_and_robbers.experiments.exp4_cops_x_type
```

Cel: sprawdzić, jak liczba policjantów wpływa na wygraną na różnych typach
grafów.

Porównywane wartości:

```text
liczba policjantów k: 1, 2, 3
typy grafów: any, tree, planar
```

Domyślna konfiguracja:

```text
bot policjanta: minimax(d=3, adaptive)
bot złodzieja: minimax(d=3, adaptive)
liczba gier: 20 na konfigurację
placement: heuristic
limit rund: T=max(20, round(5n/3))
```

Kubełki grafów:

```text
n12_sparse: n=12, m=18, T=20
n12_dense:  n=12, m=30, T=20
n30_sparse: n=30, m=45, T=50
n30_dense:  n=30, m=75, T=50
```

Dla drzew liczba krawędzi jest automatycznie ustawiana na `n-1`. Dla grafów
planarnych liczba krawędzi jest ograniczana przez limit planarny `3n-6`.

Adaptive minimax:

```text
root branching <= 50  -> używa depth 3
51..350               -> obcina do depth 2
>350                  -> obcina do depth 1
```

To jest konieczne głównie dla wielu policjantów, bo liczba wspólnych ruchów
policji jest iloczynem liczby legalnych ruchów każdego policjanta.

Wynik CSV:

```text
src/results/exp4_cops_x_type.csv
```

Wykres PNG:

```text
src/results/exp4_cops_x_type.png
```

Interpretacja: eksperyment jest empirycznym testem zachowania botów, nie
dowodem twierdzeń teoretycznych. Dla drzew spodziewamy się bardzo wysokiej
skuteczności już dla `k=1`. Dla grafów planarnych twierdzenie Aignera-Fromme'a
mówi, że 3 policjantów wystarcza w grze optymalnej, ale tutaj testujemy
ograniczonego minimaxa.

## Uruchamianie pełnego zestawu

Pełny zestaw eksperymentów i wykresów:

```bash
python scripts/run_full_experiments.py --workers 4
```

Domyślne wyniki:

```text
CSV i PNG: src/results/
log:       src/results/full_experiments.log
```

Lżejszy przebieg:

```bash
python scripts/run_full_experiments.py --workers 4 --exp2-games 50 --exp3-games 50 --exp4-games 10
```

## Benchmark czasu

Przed pełnym uruchomieniem można odpalić reprezentatywne próbki najcięższych
wariantów:

```bash
python scripts/benchmark_experiments.py --workers 4
```

Domyślnie zapisuje wyniki i log do:

```text
tmp_bench/
```

## Same wykresy

Jeżeli CSV-y już istnieją, można ponownie wygenerować tylko PNG:

```bash
python -m cops_and_robbers.experiments.plot_results --results-dir src/results --exp 2 3 4
```

To nie uruchamia symulacji ponownie.

## Najważniejsze kolumny CSV

```text
n, m, T
n_cops
graph_type
cop_strategy
robber_strategy
n_games
cop_wins
robber_wins
win_rate
mean_rounds
mean_seconds_per_game
placement
bucket
```

W `exp4` dodatkowo zapisywana jest kolumna `k`, równa liczbie policjantów.

## Korzystanie z poziomu kodu

`runner.py` można importować z notebooka lub własnego skryptu:

```python
from cops_and_robbers.experiments.runner import BotSpec, simulate_batch

summary = simulate_batch(
    n=15,
    m=22,
    T=30,
    n_cops=2,
    cop_spec=BotSpec("minimax", depth=3),
    robber_spec=BotSpec("greedy"),
    n_games=500,
    master_seed=2025,
    graph_type="planar",
    placement="heuristic",
)
print(summary.as_dict())
```
