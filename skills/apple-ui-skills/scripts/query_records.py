#!/usr/bin/env python3
from pathlib import Path
import argparse,json,re
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; SHARDS=['apple-official.json','ios-fluid.json','ios26.json','macos-community.json','visual.json']
def toks(s): return set(re.findall(r'[a-z0-9.+-]+',(s or '').lower()))
def text(r):
 t=r.get('target',{}); return ' '.join([r.get('id',''),r.get('title',''),r.get('category',''),t.get('platform',''),t.get('component',''),t.get('app') or '',t.get('interaction') or '',' '.join(r.get('tags',[])),' '.join(r.get('applicability',{}).get('osVersions',[])),r.get('evidence',{}).get('class','')]).lower()
def score(r,q,eid):
 if eid and r.get('id')==eid:return 10000
 tx=text(r); rt=toks(tx); s=0
 for x in q:
  if x in rt:s+=5
  elif x in tx:s+=2
  if x in r.get('title','').lower():s+=3
  if x in r.get('id','').lower():s+=4
 return s+float(r.get('evidence',{}).get('confidence',0))
def compact(r): return {k:r[k] for k in ['id','title','target','applicability','evidence','behavior','parameters','portability','warnings'] if k in r}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--query',default=''); ap.add_argument('--id'); ap.add_argument('--platform'); ap.add_argument('--evidence'); ap.add_argument('--limit',type=int,default=3); a=ap.parse_args(); a.limit=max(1,min(a.limit,12))
 rs=[]
 for f in SHARDS: rs+=json.loads((DATA/f).read_text(encoding='utf-8'))['records']
 if a.platform: rs=[r for r in rs if a.platform.lower() in r['target']['platform'].lower()]
 if a.evidence: rs=[r for r in rs if r['evidence']['class'].lower()==a.evidence.lower()]
 q=toks(a.query); ranked=[(score(r,q,a.id),r) for r in rs]; ranked=[x for x in ranked if x[0]>0]; ranked.sort(key=lambda x:(-x[0],-x[1]['evidence']['confidence'],x[1]['id']))
 out=[compact(r) for _,r in ranked[:a.limit]]; print(json.dumps({'query':a.query,'count':len(out),'records':out,'contextNote':'Only matched records returned. If confidence or coverage is insufficient, broaden the query or increase --limit automatically; do not load all shards indiscriminately.'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
