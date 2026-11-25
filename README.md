# Filler Strategy Lab

*An applied mathematics passion project inspired by a few too many lost games of Filler.*

After losing a few games of Filler to a friend, I started wondering whether I was making bad decisions or simply failing to think far enough ahead. Rather than practice, I decided to approach the problem as an applied mathematician: formalize the game, develop competing decision strategies, and compare their performance through simulation.

Naturally, this meant playing another 1,024 games. Fortunately, the computer could handle those.

## Explore the project

- **[Research notebook](Filler_Strategy_Analysis.ipynb):** mathematical formulation, Python implementation, verification, reproducible simulation, and results.
- **[Game data](games.csv):** individual outcomes from all 1,024 simulated games.
- **[Interactive application](index.html):** download the HTML file and open it in a browser to play against the strategies or watch them compete. No installation is required.

## Research questions

Can accounting for future territory improve on a strategy that captures as many tiles as possible on each turn? Does anticipating an opponent's response help? And does looking further ahead consistently improve performance?

Filler is a two-player game in which players expand from opposite corners of a board by selecting colors and acquiring neighboring unclaimed tiles. The objective is to finish with more tiles than the opponent. The model uses a 7 × 8 grid, six colors, horizontal and vertical adjacency, and four available colors per turn. Previously acquired tiles cannot be stolen.

| Strategy | Decision rule |
|---|---|
| Random | Select an available color at random. |
| Greedy | Maximize the number of tiles captured immediately. |
| Heuristic | Evaluate the resulting position, including opportunities for future expansion. |
| Minimax | Evaluate possible sequences of alternating moves, accounting for the opponent's responses. |

## Mathematical approach

The game is represented as a grid graph with a deterministic transition between states. For positions where the game has not ended, the heuristic measures the relative advantage of Player 1 using four features:

$$
H(s)=10D(s)+2F(s)+4R(s)+M(s).
$$

| Feature | Player 1 minus Player 2 |
|---|---|
| D | Number of owned tiles. |
| F | Number of distinct unclaimed tiles bordering the territory. |
| R | Number of unclaimed tiles closer to each territory along paths through unclaimed cells. Ties and tiles unreachable by both players contribute zero. |
| M | Largest immediate capture available under the current set of legal colors. |

The coefficients are illustrative rather than estimated or optimized. Minimax extends the evaluation to alternating future moves, with Player 1 maximizing and Player 2 minimizing the value. A depth of two includes the current move and one opponent response. A depth of four includes up to four individual turns. Alpha–beta pruning avoids unnecessary evaluation without changing the minimax value at the specified depth.

The [notebook](Filler_Strategy_Analysis.ipynb) develops the mathematical formulation, explains how the evaluation is calculated, and works through an example where capturing fewer tiles immediately produces a better position.

## Simulation and results

The experiment uses 64 reproducibly generated boards (seeds 1001–1064). For each of four strategy comparisons, both corner assignment and first player are varied, producing four games per board, 256 per comparison, and 1,024 overall. The same boards are used across comparisons.

All results are reported from Strategy A's perspective.

| Strategy A | Strategy B | Wins | Draws | Losses | Win rate | Mean tile margin | Stalled draws |
|---|---|---:|---:|---:|---:|---:|---:|
| Greedy | Random | 245 | 11 | 0 | 95.7% | +29.87 | 11 |
| Heuristic | Greedy | 180 | 49 | 27 | 70.3% | +4.58 | 19 |
| Minimax (depth 2) | Greedy | 211 | 33 | 12 | 82.4% | +5.95 | 13 |
| Minimax (depth 4) | Minimax (depth 2) | 82 | 140 | 34 | 32.0% | +2.46 | 97 |

The heuristic and two-turn minimax strategies outperform greedy play in their respective comparisons. Four-turn minimax wins more often than it loses against two-turn minimax, but 140 games end in draws, including 97 stalled games and 43 completed-board ties. Deeper search is not a guarantee of winning.

Stalled draws are included in the draw column. Mean tile margins include unfinished games. The four games on each board are related observations, so these results are descriptive, not independent-sample statistical inference. The heuristic and two-turn minimax were not directly compared against each other.

## Reproduce the analysis

The repository is intentionally small: this README, one executed Jupyter notebook, the reference CSV, and a self-contained HTML application.

Download or clone the repository, open `Filler_Strategy_Analysis.ipynb` in Jupyter, and run all cells from the repository directory. Python 3.10 or newer is required, along with the following packages:

```bash
python -m pip install jupyter pandas matplotlib
```

The notebook includes 21 Python implementation checks and one optional comparison with the browser engine (requires Node.js). It regenerates all 1,024 game records and verifies agreement with `games.csv`, excluding execution time, without overwriting the dataset. All 22 implementation checks passed in the executed notebook.

## Scope and limitations

- This is an independent model inspired by Filler, not an official GamePigeon implementation. The generated boards exclude identical horizontal or vertical neighbors; their distribution has not been validated against the original game.
- Moves that capture no tiles are permitted. After 12 consecutive such moves, the model declares a draw, regardless of the tile counts. This is a simulation convention, not a verified official rule. It may encourage a player to avoid a loss by stalling.
- The heuristic coefficients were not tuned. Finite-depth search does not establish globally optimal play, and the strategies have not been evaluated against human players.

Future work could include tuning the weights on a set of training boards, evaluation on separate boards, a direct comparison of heuristic and minimax strategies, and sensitivity analysis for the stall rule.

For now, the model suggests that thinking ahead is useful. Whether it helps me win the next game against my friend remains to be seen.

## Project note

This was an AI-assisted passion project. AI tools helped with implementation, testing, and documentation.
