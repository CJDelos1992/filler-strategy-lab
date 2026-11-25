# Filler Strategy Lab

*A little applied mathematics, a lot of Filler, and a slightly excessive response to losing.*

After losing a few too many games of Filler to a friend, I started wondering whether I could get better at it by breaking the game down mathematically. Most people would probably just practice. I built a model, tried a few strategies, and let the computer play against itself.

One thing led to another, and what started as a fun side project turned into 12,032 simulated games. The result is a playable version of Filler and a Python notebook exploring what makes a good move (and what happens when a seemingly clever strategy spends most of its time avoiding defeat).

## Explore the project

- **[Jupyter notebook](Filler_Strategy_Analysis.ipynb):** follow the math, see how the strategies work, and reproduce the experiments.
- **[Game data](games.csv):** individual outcomes from the original 1,024 games; additional experiments are reproducible in the notebook.
- **[Interactive application](index.html):** download the HTML file and open it in a browser to play against the strategies or watch them compete. No installation is required.

## What makes a good move?

Is grabbing the most tiles always the best move, or is it worth giving up a tile or two to get into a better position? What happens if the player starts thinking a few turns ahead? And can the computer find better weights for judging a position than the ones I started with?

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

The initial coefficients are illustrative. The calibration experiment below examines alternative weights on separate boards. Minimax extends the evaluation to alternating future moves, with Player 1 maximizing and Player 2 minimizing the value. A depth of two includes the current move and one opponent response. A depth of four includes up to four individual turns. Alpha–beta pruning avoids unnecessary evaluation without changing the minimax value at the specified depth.

The [notebook](Filler_Strategy_Analysis.ipynb) develops the mathematical formulation, explains how the evaluation is calculated, and works through an example where capturing fewer tiles immediately produces a better position.

## First experiment: how do the strategies compare?

The experiment uses 64 reproducibly generated boards (seeds 1001–1064). For each of four strategy comparisons, both corner assignment and first player are varied, producing four games per board, 256 per comparison, and 1,024 overall. The same boards are used across comparisons.

All results are reported from Strategy A's perspective.

| Strategy A | Strategy B | Wins | Draws | Losses | Win rate | Mean tile margin | Stalled draws |
|---|---|---:|---:|---:|---:|---:|---:|
| Greedy | Random | 245 | 11 | 0 | 95.7% | +29.87 | 11 |
| Heuristic | Greedy | 180 | 49 | 27 | 70.3% | +4.58 | 19 |
| Minimax (depth 2) | Greedy | 211 | 33 | 12 | 82.4% | +5.95 | 13 |
| Minimax (depth 4) | Minimax (depth 2) | 82 | 140 | 34 | 32.0% | +2.46 | 97 |

The heuristic and two-turn minimax strategies outperform greedy play in their respective comparisons. Four-turn minimax wins more often than it loses against two-turn minimax, but 140 games end in draws, including 97 stalled games and 43 completed-board ties. Deeper search is not a guarantee of winning.

Stalled draws are included in the draw column. Mean tile margins include unfinished games. The four games on each board are related observations, so these results are descriptive, not independent-sample statistical inference. The expanded experiment below compares them directly.

## Taking the experiment a little further

The notebook extends the original benchmark to a full tournament, first-player analysis, stopping-rule sensitivity, weight calibration, held-out evaluation, and feature removal. The experiments comprise **12,032 simulated games across 176 distinct generated boards**, with the original data preserved.

### Which strategy performs best?

All ten head-to-head matchups use the original 64 boards (2,560 games in total). A win earns one point, a draw half a point, and a loss zero. The ranking averages the percentage of available points earned against the other four configurations, weighting opponents equally.

| Strategy | Average match points |
|---|---:|
| Minimax (depth 4) | 80.7% |
| Minimax (depth 2) | 72.6% |
| Original heuristic | 61.1% |
| Greedy | 34.3% |
| Random | 1.3% |

### Can the heuristic be improved?

Twelve weight vectors are compared on 48 calibration boards against greedy and two-turn minimax. The selected weights increase the emphasis on frontier expansion from 2 to 6. They are evaluated on 64 different boards with the same two opponent types and balanced corner/turn-order assignments.

| Evaluation metric | Original | Selected |
|---|---:|---:|
| Mean match points | 61.91% | 69.82% |
| Win rate | 48.05% | 49.41% |
| Stalled games | 16.80% | 35.55% |

The selected vector earns 7.91 percentage points more in match points on the held-out boards. However, the increase in stalled games makes the result more nuanced: the strategy improves the chosen objective, not necessarily the quality of play. The notebook also removes each feature from the original evaluation in turn to examine its contribution.

## What did I learn?

- **Looking ahead helps.** Four-turn minimax leads the full tournament under the original model. Two-turn minimax earns 62.1% of head-to-head points against the original heuristic.
- **Turn order matters.** Against greedy, the original heuristic wins 85.9% of games when moving first and 54.7% when moving second.
- **The rules shape behavior.** Changing the stall cutoff from 12 to 6 or 24 moves does not change win, match-point, or stall rates in the two tested matchups. Changing the outcome of a stalled game to favor the current tile leader raises four-turn minimax's win rate against two-turn minimax from 32.0% to 58.6%. This is a hypothetical rule, not a verified rule of Filler.
- **The objective matters.** Calibration improves held-out match points but substantially increases stalls. Removing relative proximity from the original heuristic has the largest adverse effect on match points (−9.38 percentage points) among the four feature-removal tests.

The most interesting result was not simply that thinking ahead helps. It was that the tuned strategy found a way to earn more points largely by drawing more often, rather than by winning many more games. The choice of what to optimize matters just as much as how to optimize it.

## Reproduce the analysis

The repository is intentionally small: this README, one executed Jupyter notebook, the reference CSV, and a self-contained HTML application.

Download or clone the repository, open `Filler_Strategy_Analysis.ipynb` in Jupyter, and run all cells from the repository directory. Python 3.10 or newer is required, along with the following packages:

```bash
python -m pip install jupyter pandas matplotlib numpy
```

The notebook includes 21 Python implementation checks and one optional comparison with the browser engine (requires Node.js). It regenerates all 1,024 game records and verifies agreement with `games.csv`, excluding execution time, without overwriting the dataset. All 22 original implementation checks passed, along with checks for the alternative stopping rules. The notebook also regenerates the expanded experiments; a full run takes longer than the original benchmark. The browser application retains the original weights and stopping convention.

## Scope and limitations

- This is an independent model inspired by Filler, not an official GamePigeon implementation. The generated boards exclude identical horizontal or vertical neighbors; their distribution has not been validated against the original game.
- Moves that capture no tiles are permitted. After 12 consecutive such moves, the model declares a draw, regardless of the tile counts. This is a simulation convention, not a verified official rule. It may encourage a player to avoid a loss by stalling.
- The original heuristic coefficients were illustrative. Calibration tests a limited set of 12 candidates; held-out performance is limited to the same board generator and opponent types. Finite-depth search does not establish globally optimal play, and the strategies have not been evaluated against human players.

Future work could explicitly penalize stalled games during calibration, test alternative board distributions and opponent strategies, and compare the model with human play.

As for the original problem, the model suggests that thinking ahead is useful. Whether I can actually beat my friend is still an open question.

## Project note

This was a fun, AI-assisted side project. AI tools helped with implementation, testing, and documentation.
