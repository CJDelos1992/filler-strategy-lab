import random
import json
import subprocess
from pathlib import Path
from collections import deque
import pytest
from filler import *


def slow_capture(b,s,c):
    """Independent coordinate BFS oracle; no bit-shift logic."""
    owned={i for i in range(b.rows*b.cols) if s.owned[s.turn] >> i & 1}
    other={i for i in range(b.rows*b.cols) if s.owned[1-s.turn] >> i & 1}
    q=deque(owned); seen=set(owned); result=set()
    while q:
        i=q.popleft(); r,col=divmod(i,b.cols)
        for x,y in [(r-1,col),(r+1,col),(r,col-1),(r,col+1)]:
            if 0<=x<b.rows and 0<=y<b.cols:
                j=x*b.cols+y
                if j not in seen and j not in other and b.colors[j]==c:
                    seen.add(j); result.add(j); q.append(j)
    return sum(1<<i for i in result)


def test_no_wraparound():
    b=generate_board(3,4,1)
    assert b.neighbors(1<<3)==(1<<2)|(1<<7)
    assert b.neighbors(1<<4)==(1<<0)|(1<<5)|(1<<8)


def test_connected_capture_and_no_stealing():
    b=Board(3,3,(2,2,4,2,1,3,0,2,3));s=new_game(b)
    assert captured(b,s,2).bit_count()==4
    t=apply_move(b,s,2)
    assert score(t)==(5,1) and t.p1==s.p1 and t.turn==1
    assert s.p0.bit_count()==1
    with pytest.raises(ValueError): apply_move(b,t,2)
    with pytest.raises(ValueError): apply_move(b,t,4)


def test_stall_rule_and_terminal():
    b=generate_board(2,2,5);s=new_game(b)
    for i in range(12):
        c=next(c for c in legal_moves(b,s) if not captured(b,s,c))
        s=apply_move(b,s,c)
    assert terminal(b,s) and not legal_moves(b,s) and score(s)==(1,1)
    assert evaluate(b,s)==0
    b=generate_board(3,3,1); s=State(7,1<<8,0,1,0,STALL_LIMIT)
    assert score(s)==(3,1) and terminal(b,s) and evaluate(b,s)==0


def test_validation():
    with pytest.raises(ValueError): Board(2,2,(0,1,1,0))
    with pytest.raises(ValueError): generate_board(1,1)


@pytest.mark.parametrize('size',[(2,2),(3,4),(7,8),(10,10)])
def test_random_games_invariants_and_bfs(size):
    rng=random.Random(11)
    for seed in range(12):
        b=generate_board(*size,seed);s=new_game(b,seed%2)
        for i in range(3000):
            if terminal(b,s):break
            for c in legal_moves(b,s): assert captured(b,s,c)==slow_capture(b,s,c)
            c=rng.choice(legal_moves(b,s));t=apply_move(b,s,c)
            assert not(t.p0&t.p1) and (t.p0|t.p1)&~b.full==0
            assert s.p0&t.p0==s.p0 and s.p1&t.p1==s.p1
            assert t.owned[1-s.turn]==s.owned[1-s.turn] and t.turn==1-s.turn
            assert t.colors[0]!=t.colors[1]
            s=t
        else: pytest.fail('game failed to terminate')


@pytest.mark.parametrize('seed',range(12))
def test_pruned_equals_exhaustive(seed):
    b=generate_board(5,5,seed);s=new_game(b,seed%2)
    for _ in range(3):s=apply_move(b,s,choose_move(b,s,'greedy')['color'])
    a=choose_move(b,s,depth=4);z=choose_move(b,s,depth=4,prune=False)
    assert (a['color'],a['value'])==(z['color'],z['value'])
    assert a['nodes']<=z['nodes']


def test_terminal_win_dominates():
    b=generate_board(2,2,4); s=State(7,8,0,1)
    assert terminal(b,s) and evaluate(b,s)==10002


def test_js_python_parity():
    root=Path(__file__).resolve().parent
    html=(root/'index.html').read_text(encoding='utf-8')
    engine=html.split('<script id="engine-code">',1)[1].split('</script>',1)[0]
    parity="const F=module.exports;const results=[];\nfor(let seed=0;seed<12;seed++){\n const b=F.generate(7,8,seed);let s=F.newGame(b,seed%2);const steps=[];\n for(let i=0;i<8;i++){const a=F.choose(b,s,'minimax',3);steps.push([F.score(s),F.features(b,s),F.legal(b,s),F.legal(b,s).map(c=>F.count(F.captured(b,s,c))),a]);s=F.apply(b,s,a.color);}\n results.push([b.colors,steps]);\n}\nconsole.log(JSON.stringify(results));\n"
    js=subprocess.run(['node','-e',engine+'\n'+parity],capture_output=True,text=True,check=True)
    actual=json.loads(js.stdout)
    expected=[]
    for seed in range(12):
        b=generate_board(7,8,seed);s=new_game(b,seed%2)
        steps=[]
        for _ in range(8):
            a=choose_move(b,s,'minimax',3)
            steps.append([list(score(s)),list(features(b,s)),list(legal_moves(b,s)),[captured(b,s,c).bit_count() for c in legal_moves(b,s)],a])
            s=apply_move(b,s,a['color'])
        expected.append([list(b.colors),steps])
    assert actual==expected
