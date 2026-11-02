"""Deterministic assignment, not procedural texture art. Twenty unique material combinations."""
from pathlib import Path
import json,random,collections
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];TARGET=ROOT/'assets/art/room1_pod_age_full_r28'
variants='abcd';lids=list('bcdabcdabc'+'dabcdabcda');n=20
chosen={11:(0,0,0)};caps=[[5]*4,[5]*4,[7,7,6]];counts=[[0]*4,[0]*4,[0]*3]
for i,v in enumerate(chosen[11]):counts[i][v]+=1
order=[i for i in range(n) if i!=11];rng=random.Random(20261102)
def neighbors(i):
 return [j for j in [i-1,i+1] if j//10==i//10 and 0<=j<n]+([i+10] if i<10 else [i-10])
def search(k):
 if k==len(order):return counts==caps
 i=order[k];l=variants.index(lids[i]);opts=[(l,s,e) for s in range(4) for e in range(3)];rng.shuffle(opts)
 opts.sort(key=lambda t:sum(counts[a][v] for a,v in enumerate(t)))
 for t in opts:
  if t in chosen.values() or any(counts[a][v]>=caps[a][v] for a,v in enumerate(t)):continue
  if any(j in chosen and (chosen[j][1]==t[1] or chosen[j][2]==t[2]) for j in neighbors(i)):continue
  chosen[i]=t
  for a,v in enumerate(t):counts[a][v]+=1
  if search(k+1):return True
  for a,v in enumerate(t):counts[a][v]-=1
  del chosen[i]
 return False
assert search(0)
original=json.loads((ROOT/'assets/art/room1_complete_r19/layout.json').read_text())['pods'];out=[]
for i,pod in enumerate(original):
 l,s,e=[variants[v] for v in chosen[i]];pid=pod['id']
 out.append({'id':pid,'number':int(pod['number']),'lid_variant':l,'side_variant':s,'end_variant':e,'maps':{'lid':f'res://assets/art/room1_pod_age_full_r28/numbered/{pid}_lid.png','shell_side':f'res://assets/art/room1_pod_age_full_r28/variant_{s}/shell_side.png','shell_end':f'res://assets/art/room1_pod_age_full_r28/numbered/{pid}_shell_end.png'}})
report={'pods':out,'unique_combinations':len(set(chosen.values())),'counts_per_role':counts,'P12_retains_r27_A':chosen[11]==(0,0,0),'adjacent_same_side_or_end':False,'model_positions_changed':False}
TARGET.mkdir(parents=True,exist_ok=True);(TARGET/'layout_variants.json').write_text(json.dumps(report,indent=2),encoding='utf8');(HERE/'layout_variants.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('R28_LAYOUT',report['unique_combinations'],'unique combinations;counts',counts)
