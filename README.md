# Filler Strategy Lab

**A quantitative study of competing strategies in a two-player territory-capture game.**

Filler Strategy Lab explores how different decision-making strategies affect performance in a competitive color-filling game. The project combines mathematical modeling, optimization, and simulation with an interactive application in which users can play against the strategies and explore their decisions.

## Project objective

Does looking ahead at an opponent's possible responses improve outcomes relative to maximizing immediate gains? How much does incorporating information about future territory improve performance?

The objective is to compare increasingly informed strategies under a common set of game rules and starting conditions.

## Game and strategies

Two players start in opposite corners of a 7 × 8 board with six colors. On each turn, a player selects a color different from both players' current colors and acquires adjacent unclaimed tiles of that color, including connected tiles of the same color. Previously acquired territory cannot be taken by the opponent. When the entire board has been captured, the player with the most tiles wins.

| Strategy | Decision rule |
|---|---|
| Random | Select an available color at random. |
| Greedy | Maximize the number of tiles captured on the current turn. |
| Heuristic | Select the color that produces the most favorable position according to a weighted evaluation function. |
| Minimax | Evaluate possible sequences of moves while assuming the opponent also chooses favorable moves. |

The interactive application supports human versus AI, AI versus AI, and two-player games. Users can change the strategies and search depth, generate reproducible boards, import custom boards, and inspect suggested moves.

To play locally, download [index.html](index.html) and open it in a modern browser. No installation is required.

## Mathematical model

Each game state includes the two players' territories, their current colors, whose turn it is, and the number of consecutive moves without a capture. Tiles are adjacent horizontally and vertically, but not diagonally.

For positions where the game has not ended, the heuristic evaluates the relative advantage of Player 1:

$$
H(s) = 10D(s) + 2F(s) + 4R(s) + M(s)
$$

| Component | Interpretation (Player 1 minus Player 2) |
|---|---|
| D | Number of owned tiles. |
| F | Number of unclaimed tiles bordering each player's territory. |
| R | Number of unclaimed tiles closer to each player, measured along paths through unclaimed territory; ties and unreachable tiles are excluded. |
| M | Largest immediate capture available to each player under the current set of legal colors. |

The coefficients are illustrative weights, not statistically estimated or optimized parameters. A positive evaluation favors Player 1; a negative evaluation favors Player 2.

Minimax extends this approach by considering possible future moves. Player 1 attempts to maximize the evaluation, while Player 2 attempts to minimize it. A search depth of four considers up to four individual turns, alternating between players. Alpha–beta pruning avoids examining branches that cannot change the selected decision at that depth.

When the full board is captured, wins and losses receive a large positive or negative utility, with the final tile difference added. A tie or stalled game receives zero utility. This prioritizes winning over improving the heuristic score.

## Simulation design

The strategies were compared using 64 reproducibly generated boards (seeds 1001–1064). Each matchup was played four times per board, crossing corner assignment and first player so that each strategy occupies both corners and moves first equally often.

The experiment consists of **1,024 games**, with 256 games per matchup. Results are reported from Strategy A's perspective. No external data are required.

| Strategy A | Strategy B | Wins | Draws | Losses | Win rate | Mean tile margin |
|---|---|---:|---:|---:|---:|---:|
| Greedy | Random | 245 | 11 | 0 | 95.7% | +29.87 |
| Heuristic | Greedy | 180 | 49 | 27 | 70.3% | +4.58 |
| Minimax (depth 2) | Greedy | 211 | 33 | 12 | 82.4% | +5.95 |
| Minimax (depth 4) | Minimax (depth 2) | 82 | 140 | 34 | 32.0% | +2.47 |

The heuristic won 70.3% of games against the greedy strategy, while two-turn minimax won 82.4%. Four-turn minimax won more often than it lost against two-turn minimax, but the high draw rate limits the strength of that comparison.

These findings are descriptive and specific to the simulated board distribution and chosen model parameters. Games played on the same board are related observations, and the reported win rates are not independent-sample statistical estimates. Tile margins include unfinished draws.

## Repository files and reproducibility

The project is intentionally organized into six files:

| File | Purpose |
|---|---|
| [README.md](README.md) | Research objective, model, methods, and findings. |
| [index.html](index.html) | Standalone interactive application. |
| [filler.py](filler.py) | Python implementation of the game and decision strategies. |
| [experiment.py](experiment.py) | Reproducible simulation and summary calculations. |
| [games.csv](games.csv) | Original game-level results for all 1,024 simulations. |
| [test_filler.py](test_filler.py) | Tests of game rules, capture logic, and agreement between Python and the browser application. |

The simulation requires Python 3.10 or newer and uses only the Python standard library. Run the following from the repository directory:

```bash
python experiment.py --boards 64 --start-seed 1001 --workers 4
```

This generates a new game-level CSV and summary JSON in the `results/` directory without replacing the original dataset. The seed reproduces the boards and game outcomes; measured execution times can differ.

To run the 22 correctness tests, install pytest and ensure Node.js is available for the browser-engine comparison:

```bash
python -m pip install pytest
python -m pytest -q
```

## Assumptions and limitations

- The game is an independent implementation inspired by Filler, not an official GamePigeon product.
- The board generator excludes identical horizontally or vertically adjacent colors; the generated distribution has not been validated against the original game.
- A game is classified as a draw after 12 consecutive moves without capturing any tiles. This is a simulation safeguard rather than a verified official rule. It affected 11, 19, 13, and 97 games in the respective matchups above.
- The heuristic weights have not been optimized, and finite-depth search does not guarantee an optimal strategy for the entire game.

Potential extensions include tuning the evaluation weights on training boards, evaluating performance on held-out boards, and assessing sensitivity to the stall rule.
