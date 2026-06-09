# Eksperymenty

Skrypty do przeprowadzenia eksperymentów zaprojektowanych
pod prezentację. Każdy skrypt zapisuje wynik do pliku CSV w katalogu `results/`,
a osobne narzędzie generuje z nich wykresy PNG.

## Instalacja

Skrypty korzystają tylko z pakietów już używanych w projekcie
(`networkx`) plus opcjonalnie `matplotlib` do rysowania wykresów:

```bash
pip install matplotlib
```

## Uruchamianie

Wszystkie skrypty uruchamiamy z katalogu głównego projektu (tego, w którym
znajduje się katalog `cops_and_robbers/`):

```bash
# Eksperyment 2 — macierz bot vs bot (slajd 15)
python -m cops_and_robbers.experiments.exp2_bot_matrix

# Eksperyment 3 — wpływ rozmiaru grafu (slajd 16)
python -m cops_and_robbers.experiments.exp3_size_sweep

# Eksperyment 4 — liczba policjantów × typ grafu (slajd 17)
python -m cops_and_robbers.experiments.exp4_cops_x_type

# Wykresy z zapisanych CSV
python -m cops_and_robbers.experiments.plot_results
```

Każdy skrypt akceptuje `--help` z pełną listą opcji.

## Domyślne parametry

Domyślne wartości odpowiadają sugestiom z placeholderów WIP w prezentacji.

### Eksperyment 2 — Macierz bot vs bot
- `n=12`, `m=18`, `T=30`, `n_cops=1`
- `N=1000` gier na komórkę macierzy
- `placement=heuristic`
- Strategie: `random`, `greedy`, `minimax(d=3)`
- Czas: ~kilka minut (głównie z powodu komórek z minimax)

Szybsza wersja (bez minimax):
```bash
python -m cops_and_robbers.experiments.exp2_bot_matrix --no-minimax --games 1000
```

### Eksperyment 3 — Wpływ rozmiaru grafu
- `n ∈ {5, 8, 10, 15, 20, 25, 30}`, `m/n ≈ 1.5`, `T = 2n`
- `N=200` gier na punkt, `n_cops=1`
- `placement=heuristic`
- Domyślnie porównuje strategie policjanta: `random` vs `greedy` vs `minimax(d=2)`
- Domyślny przeciwnik (robber) to `greedy`
- Czas: ~kilka minut

Aby porównać strategie *złodzieja* przy ustalonym policjancie:
```bash
python -m cops_and_robbers.experiments.exp3_size_sweep --compare robber-strategies
```

### Eksperyment 4 — Liczba policjantów × typ grafu
- `n=12`, `m=18` (auto-clampowane do n−1 dla drzew), `T=30`
- `k ∈ {1, 2, 3}` × typy `{any, tree, planar}`
- `N=200` gier na konfigurację
- `placement=heuristic`
- Boty domyślnie `minimax` z głębokościami z presetu *Expert*
  (`d_cop = 5` dla `k=1`, `d=3` dla `k=2,3`)
- Czas: ~kilka minut

Szybsza wersja (boty greedy):
```bash
python -m cops_and_robbers.experiments.exp4_cops_x_type --bot greedy
```

## Pliki wyjściowe

Wszystkie skrypty zapisują do `results/` (parametr `--output-dir`):

| Eksperyment | CSV                          | PNG                          |
| ----------- | ---------------------------- | ---------------------------- |
| 2           | `exp2_bot_matrix.csv`        | `exp2_bot_matrix.png`        |
| 3           | `exp3_size_sweep.csv`        | `exp3_size_sweep.png`        |
| 4           | `exp4_cops_x_type.csv`       | `exp4_cops_x_type.png`       |

Kolumny w CSV-ach: `n, m, T, n_cops, graph_type, cop_strategy,
robber_strategy, n_games, cop_wins, robber_wins, win_rate, mean_rounds,
mean_seconds_per_game, placement`.

## Reprodukowalność

Każdy skrypt akceptuje `--seed`. Z tego ziarna wyprowadzane są:
- ziarno generatora grafu dla każdej gry,
- ziarno wyboru pozycji startowych,
- ziarna botów (osobne dla policjantów i złodzieja).

Pełna rozgrywka jest deterministyczna przy tym samym `--seed` i tej samej
konfiguracji.

## Wybór pozycji startowych

Flaga `--placement`:
- `heuristic` (domyślnie) — pozycje startowe wybierane jak w aplikacji w trybie BvB:
  policjanci na centralnych wierzchołkach o minimalnej ekscentryczności,
  złodziej na wierzchołku maksymalizującym minimalną odległość do policjantów.
- `random` — losowe różne wierzchołki dla policjantów i złodzieja.

## Szybki podgląd (smoke test)

```bash
python -m cops_and_robbers.experiments.exp2_bot_matrix --games 20 --no-minimax
python -m cops_and_robbers.experiments.exp3_size_sweep --games 20 --no-minimax --n-values 5 10 15
python -m cops_and_robbers.experiments.exp4_cops_x_type --games 20 --bot greedy
python -m cops_and_robbers.experiments.plot_results
```

## Korzystanie z poziomu kodu

`runner.py` jest pomyślany jako biblioteka — możesz importować z niego
funkcje w notebooku Jupyter, własnym skrypcie itp.

```python
from cops_and_robbers.experiments.runner import BotSpec, simulate_batch

summary = simulate_batch(
    n=15, m=22, T=30, n_cops=2,
    cop_spec=BotSpec("minimax", depth=3),
    robber_spec=BotSpec("greedy"),
    n_games=500, master_seed=2025,
    graph_type="planar",
)
print(summary.as_dict())
```
