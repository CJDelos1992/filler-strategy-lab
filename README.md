# Filler Strategy Lab

**Interactive adversarial search, graph traversal, and reproducible algorithm experiments.**

Filler Strategy Lab is an independent implementation of a two-player competitive flood-fill game. It compares short-sighted territory acquisition with graph-based heuristics and depth-limited minimax search. The project includes a browser-native arena, a Python reference engine, cross-language verification, and a reproducible simulation study.

![Filler Strategy Lab: live board and match controls](docs/preview.png)

## Explore the project

- **Play:** open [`index.html`](index.html) in a modern browser, or serve it from GitHub Pages. Choose human vs AI, AI vs AI (step or autoplay), or local two-player mode. Set the board seed, first player, strategies and search depth; import a custom board if desired.
- **Inspect:** the arena shows immediate capture previews, territory scores, heuristic components, recommended moves, visited search nodes, pruning cutoffs and a move-by-move history.
- **Reproduce:** run the Python simulation or explore [`notebooks/strategy_experiments.ipynb`](notebooks/strategy_experiments.ipynb). All engine and benchmark code is included, with no external runtime dependencies.

## Algorithms

The board is an undirected grid graph with orthogonal adjacency. Each player starts at an opposite corner. At each turn the player selects a color other than either player's current color. A fixed-point flood fill adds all connected neutral tiles of the selected color to the player's territory. The opponent's territory cannot be captured. The match normally ends when all cells are owned; the player with the most tiles wins.

| Strategy | Decision rule |
|---|---|
| Random | Uniform selection among legal colors |
| Greedy | Maximize the number of newly acquired tiles |
| Heuristic | Evaluate every successor state with a graph-based evaluation function |
| Minimax + alpha–beta | Alternate maximizing and minimizing the evaluation at a finite search depth, pruning dominated branches |

### State representation and capture

For a fixed grid graph $G=(V,E)$ with initial color function $c:V\to\{0,1,2,3,4,5\}$, the state is

$$s=(S_1,S_2,c_1,c_2,p,z),$$

where $S_1,S_2$ are disjoint owned sets, $c_1,c_2$ are current colors, $p$ is the player to move, and $z$ is the consecutive zero-gain count. Neutral cells are $N=V\setminus(S_1\cup S_2)$. Legal colors are the four colors distinct from both $c_1$ and $c_2$.

For chosen color $a$, let $C_a=\{v\in N:c(v)=a\}$. Starting from $X_0=S_p$, compute

$$X_{k+1}=X_k\cup\big(\Gamma(X_k)\cap C_a\big)$$

until $X_{k+1}=X_k$, where $\Gamma$ returns all orthogonal neighbors. The new territory is $X_k$. The other territory stays unchanged. This closure is implemented with bitwise operations on row-major integer masks, so a flood-fill expansion does not require constructing a graph object. The Python tests compare capture results with an independently implemented coordinate BFS.

### Heuristic and minimax

The nonterminal position evaluation is

$$H(s)=10D(s)+2F(s)+4R(s)+M(s).$$

Every component is measured as a Player 1 minus Player 2 difference:

| Feature | Definition |
|---|---|
| $D$ | Number of owned tiles |
| $F$ | Number of distinct neutral cells adjacent to each territory |
| $R$ | Number of neutral cells strictly closer to each territory by shortest paths through neutral cells; ties and unreachable cells contribute zero |
| $M$ | Largest immediate capture count available to each player under the same current four legal colors |

The weights are fixed illustrative choices, not fitted parameters. The mobility term is symmetric and is not a prediction of the opponent's future legal colors. The heuristic is measured from Player 1's perspective regardless of whose turn it is.

At full-board terminal states the utility is $10000\,\operatorname{sign}(D)+D$. A stalled match is assigned utility zero. The large constant makes terminal wins and losses dominate all nonterminal heuristic values on supported boards. For depth $d$, minimax applies the recursion

$$V_d(s)=\begin{cases}U(s)&\text{terminal}\\H(s)&d=0\\\max_{a\in A(s)}V_{d-1}(T(s,a))&p=1\\\min_{a\in A(s)}V_{d-1}(T(s,a))&p=2.\end{cases}$$

Move ordering prioritizes immediate gain, breaking ties by color index. Alpha–beta pruning retains the exact minimax result at the selected depth; a test compares it against exhaustive depth-limited search. At most four choices per nonterminal turn give an upper bound of $O(4^d)$ search nodes without pruning, with each node incurring board operations. A depth of 4 means four individual turns (plies), not four turns for each player. Search is not a solution to the entire game tree. The browser uses a Web Worker when available, with a synchronous fallback.

## Computational experiments

The included simulation uses 64 deterministic 7×8 boards (seeds 1001–1064). For each matchup and seed, four games cross strategy assignment to the two corners with which player moves first. There are 256 games per matchup, 1,024 games overall. Random choices use a separate seeded Python RNG. No external data are used.

| Strategy A | Strategy B | A wins | Draws | B wins | A win rate | Mean raw tile margin | Stalled games |
|---|---|---:|---:|---:|---:|---:|---:|
| Greedy | Random | 245 | 11 | 0 | 95.7% | +29.871 | 11 |
| Heuristic | Greedy | 180 | 49 | 27 | 70.3% | +4.582 | 19 |
| Minimax (depth 2) | Greedy | 211 | 33 | 12 | 82.4% | +5.949 | 13 |
| Minimax (depth 4) | Minimax (depth 2) | 82 | 140 | 34 | 32.0% | +2.465 | 97 |

On this board distribution, the heuristic and two-ply minimax substantially outperform the greedy baseline. Four-ply minimax beats two-ply minimax more often than it loses, but a majority of their matches end in draws. In particular, 97 of 256 games in that comparison reach the explicit stall cutoff. Deeper lookahead should not be interpreted as a guarantee of a win. These results are descriptive; the four games for a given seed are related and should not be treated as independent samples for inference. Raw tile margin includes unfinished draws and is distinct from game outcome.

The full dataset is in [`results/games.csv`](results/games.csv), with aggregate metrics in [`results/summary.json`](results/summary.json). Search node counts exclude the root; wall-clock times are machine-specific and may vary across runs.

## Reproduce locally

**Requirements:** Python 3.10+ and a modern browser supporting JavaScript BigInt. Node.js is needed for the cross-language tests. `pytest` is needed only for tests; Jupyter is optional.

```bash
# Run simulation study (64 boards × 4 assignments × 4 comparisons)
python scripts/benchmark.py --boards 64 --start-seed 1001 --workers 4

# Rebuild the standalone browser app with the new benchmark summary
python scripts/build_site.py

# Run correctness tests (including JS/Python parity)
python -m pip install pytest
python -m pytest -q

# Serve locally if preferred over opening the HTML directly
python -m http.server 8000
# Then open http://localhost:8000/
```

A quick Python example:

```python
from filler.engine import generate_board, new_game, choose_move, apply_move, score, COLORS

board = generate_board(7, 8, seed=2026)
state = new_game(board)
choice = choose_move(board, state, strategy="minimax", depth=4)
print(COLORS[choice["color"]], choice)
state = apply_move(board, state, choice["color"])
print(score(state))
```

Optional browser integration test:

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/smoke_browser.py
```

### Repository structure

```text
filler/                    Python reference engine
web/                       Browser engine, interface, CSS, HTML template
scripts/benchmark.py       Seeded, crossed-assignment simulation
scripts/build_site.py      Rebuild standalone index.html
notebooks/                 Worked analysis and search examples
tests/                     BFS oracle, invariants, search, parity, browser smoke test
results/                   Game-level dataset and summary statistics
docs/                      Interface screenshot
index.html                 Self-contained static demo, ready for deployment
```

### Deploy the demo to GitHub Pages

Upload this directory's contents into a GitHub repository, then open **Settings → Pages → Build and deployment → Deploy from a branch**. Select the `main` branch and `/ (root)`, and save. The generated `index.html` already contains all necessary JavaScript, CSS and benchmark data. No web server or Python runtime is required in production. Link the published GitHub Pages URL from a portfolio website.

## Scope, assumptions and limitations

This is an independent educational project inspired by Filler; it is not an official GamePigeon implementation. Its precise rules are based on the supplied game description with explicit modeling assumptions:

- Four-neighbor adjacency, transitive same-color capture, distinct starting colors and no stealing of owned tiles. The current player's own color and the opponent's current color are excluded from legal actions.
- Zero-gain color changes are allowed. To guarantee termination, the simulation declares a draw after **12 consecutive zero-gain moves**, regardless of the tile count. This is a project-specific safeguard, not a verified official rule. It can materially affect strategic behavior and benchmark results.
- Generated boards avoid matching horizontal/vertical adjacent colors and use a reproducible, row-major xorshift32 generator. This is not a claim about the distribution of boards generated by the original app. Custom boards may include contiguous same-color cells.
- There is no exact full-game solver, screenshot recognition, online multiplayer, or connection to the original app. The weights have not been tuned or validated against human play. The browser uses the same rules as the reference engine but search runtime depends on the device.

Potential extensions include an alternative progress-required ruleset, sensitivity analysis for the stall cutoff and heuristic weights, a transposition table, Monte Carlo tree search, and a held-out evaluation of optimized parameters.
