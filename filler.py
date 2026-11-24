"""Reference implementation. Bit i denotes row-major tile i; colors 0..5.

Rules: orthogonal adjacency, transitive captures, immutable neutral colors,
no stealing, current and opponent colors unavailable. Noncapturing moves are
allowed. A 12-consecutive-noncapture draw cutoff is a documented simulation rule.
"""
from dataclasses import dataclass
from random import Random

COLORS = 'BRGYKP'
STALL_LIMIT = 12
WEIGHTS = (10, 2, 4, 1)

@dataclass(frozen=True, slots=True)
class Board:
    rows: int
    cols: int
    colors: tuple[int, ...]
    masks: tuple[int, ...] = ()
    full: int = 0
    left: int = 0
    right: int = 0

    def __post_init__(self):
        if not (2 <= self.rows <= 10 and 2 <= self.cols <= 10):
            raise ValueError('Board dimensions must be between 2 and 10')
        colors = tuple(self.colors)
        if len(colors) != self.rows * self.cols or any(not isinstance(c, int) or not 0 <= c < 6 for c in colors):
            raise ValueError('Expected rows × cols colors in 0..5')
        if colors[(self.rows - 1) * self.cols] == colors[self.cols - 1]:
            raise ValueError('Starting corner colors must differ')
        object.__setattr__(self, 'colors', colors)
        object.__setattr__(self, 'masks', tuple(sum(1 << i for i, c in enumerate(colors) if c == k) for k in range(6)))
        object.__setattr__(self, 'full', (1 << len(colors)) - 1)
        object.__setattr__(self, 'left', sum(1 << (r*self.cols) for r in range(self.rows)))
        object.__setattr__(self, 'right', self.left << (self.cols - 1))

    def neighbors(self, bits):
        return (((bits & ~self.left) >> 1) | ((bits & ~self.right) << 1) |
                (bits >> self.cols) | (bits << self.cols)) & self.full

@dataclass(frozen=True, slots=True)
class State:
    p0: int
    p1: int
    c0: int
    c1: int
    turn: int = 0
    stalls: int = 0

    @property
    def owned(self):
        return self.p0, self.p1

    @property
    def colors(self):
        return self.c0, self.c1


def generate_board(rows=7, cols=8, seed=1):
    """Portable xorshift32 generator; excludes left/up colors and matching corners."""
    if not (2 <= rows <= 10 and 2 <= cols <= 10):
        raise ValueError('Board dimensions must be between 2 and 10')
    x = int(seed) & 0xffffffff or 0x9e3779b9
    values = []
    for i in range(rows*cols):
        r, c = divmod(i, cols)
        banned = set()
        if r: banned.add(values[i-cols])
        if c: banned.add(values[i-1])
        if i == (rows-1)*cols: banned.add(values[cols-1])
        choices = [k for k in range(6) if k not in banned]
        x ^= (x << 13) & 0xffffffff
        x ^= x >> 17
        x ^= (x << 5) & 0xffffffff
        x &= 0xffffffff
        values.append(choices[x % len(choices)])
    return Board(rows, cols, tuple(values))


def new_game(board, first=0):
    if first not in (0,1): raise ValueError('Invalid first player')
    a, b = (board.rows - 1) * board.cols, board.cols - 1
    return State(1 << a, 1 << b, board.colors[a], board.colors[b], first)


def score(state):
    return state.p0.bit_count(), state.p1.bit_count()


def terminal(board, state):
    return (state.p0 | state.p1) == board.full or state.stalls >= STALL_LIMIT


def legal_moves(board, state):
    return () if terminal(board, state) else tuple(c for c in range(6) if c not in state.colors)


def captured(board, state, color, player=None):
    """Fixed-point flood fill of neutral tiles of the selected color."""
    player = state.turn if player is None else player
    own = state.owned[player]
    remaining = board.masks[color] & ~(state.p0 | state.p1)
    hit = board.neighbors(own) & remaining
    result = hit
    while hit:
        hit = board.neighbors(hit) & remaining & ~result
        result |= hit
    return result


def apply_move(board, state, color):
    if color not in legal_moves(board, state):
        raise ValueError('Illegal move')
    add = captured(board, state, color)
    stalls = 0 if add else state.stalls + 1
    if state.turn == 0:
        return State(state.p0 | add, state.p1, color, state.c1, 1, stalls)
    return State(state.p0, state.p1 | add, state.c0, color, 0, stalls)


def potential(board, state):
    """Difference in neutral cells closer to P0 vs P1 by obstacle-aware BFS.
    Both searches travel through neutral cells only; tied/unreachable cells get 0.
    """
    neutral = board.full & ~(state.p0 | state.p1)
    f0, f1 = state.p0, state.p1
    seen0 = seen1 = assigned = 0
    value = 0
    while f0 or f1:
        f0 = board.neighbors(f0) & neutral & ~seen0
        f1 = board.neighbors(f1) & neutral & ~seen1
        seen0 |= f0; seen1 |= f1
        a, b = f0 & ~assigned, f1 & ~assigned
        value += (a & ~b).bit_count() - (b & ~a).bit_count()
        assigned |= a | b
        if assigned == neutral: break
    return value


def features(board, state):
    a, b = score(state)
    neutral = board.full & ~(state.p0 | state.p1)
    frontier = (board.neighbors(state.p0) & neutral).bit_count() - (board.neighbors(state.p1) & neutral).bit_count()
    moves = [c for c in range(6) if c not in state.colors]
    best = [max((captured(board, state, c, p).bit_count() for c in moves), default=0) for p in (0,1)]
    return a-b, frontier, potential(board, state), best[0]-best[1]


def evaluate(board, state, weights=WEIGHTS):
    if terminal(board, state):
        if (state.p0 | state.p1) != board.full: return 0
        a,b = score(state)
        # Terminal wins/losses dominate any nonterminal heuristic on supported boards.
        return (10000 if a>b else -10000 if b>a else 0) + (a-b)
    return sum(w*f for w,f in zip(weights, features(board,state)))


def choose_move(board, state, strategy='minimax', depth=4, rng=None, prune=True):
    """Return a decision dictionary. Depth is measured in individual turns.
    All search values are from P0's perspective. Tie order is gain then color.
    No transposition cache; prune=False provides a verification baseline.
    """
    if strategy not in ('random','greedy','heuristic','minimax'):
        raise ValueError('Unknown strategy')
    moves = legal_moves(board,state)
    if not moves: return {'color':None,'value':evaluate(board,state),'nodes':0,'cutoffs':0}
    depth = int(depth)
    if not 1 <= depth <= 8: raise ValueError('Depth must be 1..8')
    def ordered(s):
        return sorted(legal_moves(board,s), key=lambda c:(-captured(board,s,c).bit_count(),c))
    if strategy == 'random':
        color = (rng or Random()).choice(moves)
        return {'color':color,'value':None,'nodes':0,'cutoffs':0}
    if strategy == 'greedy':
        color = ordered(state)[0]
        return {'color':color,'value':None,'nodes':0,'cutoffs':0}
    if strategy == 'heuristic': depth = 1
    nodes = cutoffs = 0
    def search(s,d,alpha,beta):
        nonlocal nodes,cutoffs
        nodes += 1
        if d == 0 or terminal(board,s): return evaluate(board,s)
        maximizing = s.turn == 0
        value = -float('inf') if maximizing else float('inf')
        for c in ordered(s):
            v = search(apply_move(board,s,c),d-1,alpha,beta)
            if maximizing: value=max(value,v); alpha=max(alpha,value)
            else: value=min(value,v); beta=min(beta,value)
            if prune and alpha >= beta:
                cutoffs += 1
                break
        return value
    maximizing = state.turn == 0
    best = -float('inf') if maximizing else float('inf')
    color = None
    alpha,beta = -float('inf'),float('inf')
    for c in ordered(state):
        value = search(apply_move(board,state,c),depth-1,alpha,beta)
        if color is None or (value>best if maximizing else value<best):
            best,color=value,c
        if maximizing: alpha=max(alpha,best)
        else: beta=min(beta,best)
    return {'color':color,'value':best,'nodes':nodes,'cutoffs':cutoffs}
