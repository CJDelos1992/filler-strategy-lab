#!/usr/bin/env python3
"""Paired simulations on reproducible boards, each strategy plays both corners.
Strategy A goes first in half of games; assignment and first turn are crossed.
"""
import argparse, json, csv, time, random, statistics, sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parent
from filler import *

MATCHUPS=[('greedy','random'),('heuristic','greedy'),('minimax:2','greedy'),('minimax:4','minimax:2')]

def play(task):
    a,z,seed,swap,first=task
    b=generate_board(7,8,seed);s=new_game(b,first)
    players=[a,z] if not swap else [z,a]
    rng=random.Random(seed*100+swap*2+first)
    nodes=[0,0];moves=[0,0];cutoffs=[0,0];turns=0
    start=time.perf_counter()
    while not terminal(b,s):
        p=s.turn; strategy,_,depth=players[p].partition(':')
        choice=choose_move(b,s,strategy,int(depth or 1),rng)
        nodes[p]+=choice['nodes'];cutoffs[p]+=choice['cutoffs'];moves[p]+=1
        s=apply_move(b,s,choice['color']);turns+=1
    sa,sz=score(s);i=1 if swap else 0
    if swap:sa,sz=sz,sa
    outcome=0 if s.stalls>=STALL_LIMIT else (1 if sa>sz else -1 if sa<sz else 0)
    return dict(strategy_a=a,strategy_b=z,seed=seed,a_corner='top-right' if swap else 'bottom-left',a_first=(first==i),a_score=sa,b_score=sz,margin=sa-sz,outcome=outcome,turns=turns,stall=s.stalls>=STALL_LIMIT,a_nodes=nodes[i],a_cutoffs=cutoffs[i],a_moves=moves[i],elapsed_ms=round((time.perf_counter()-start)*1000,3))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--boards',type=int,default=64);ap.add_argument('--start-seed',type=int,default=1001);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--output',type=Path,default=ROOT/'results');args=ap.parse_args()
    if args.boards<1:ap.error('--boards must be positive')
    args.output.mkdir(exist_ok=True,parents=True)
    tasks=[(a,z,seed,swap,first) for a,z in MATCHUPS for seed in range(args.start_seed,args.start_seed+args.boards) for swap in (0,1) for first in (0,1)]
    with ProcessPoolExecutor(max_workers=args.workers) as pool: games=list(pool.map(play,tasks,chunksize=4))
    with (args.output/'games.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(games[0]));writer.writeheader();writer.writerows(games)
    summary=[]
    for a,z in MATCHUPS:
        g=[r for r in games if r['strategy_a']==a and r['strategy_b']==z];n=len(g)
        wins=sum(r['outcome']>0 for r in g);ties=sum(r['outcome']==0 for r in g);loss=n-wins-ties
        summary.append(dict(strategy_a=a,strategy_b=z,games=n,wins=wins,ties=ties,losses=loss,win_rate=wins/n,mean_margin=round(statistics.mean(r['margin'] for r in g),3),stall_games=sum(r['stall'] for r in g),mean_a_nodes_per_move=round(sum(r['a_nodes'] for r in g)/sum(r['a_moves'] for r in g),2)))
    out=dict(boards=args.boards,start_seed=args.start_seed,board_size=[7,8],games_per_board_per_matchup=4,total_games=len(games),weights=list(WEIGHTS),stall_limit=STALL_LIMIT,matchups=summary)
    (args.output/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
