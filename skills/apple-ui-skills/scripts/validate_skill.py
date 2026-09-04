#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ir');a=ap.parse_args();problems=[]
 for p in ROOT.rglob('*.json'):
  try:json.loads(p.read_text(encoding='utf-8'))
  except Exception as e:problems.append(f'{p.relative_to(ROOT)} invalid JSON: {e}')
 req=['SKILL.md','packs/build.md','packs/core.md','packs/reconstruction.md','packs/visual.md','data/catalog.json','compiler/motion-ir.schema.json','scripts/query_records.py','scripts/compile_motion.py']
 for r in req:
  if not (ROOT/r).exists():problems.append('missing '+r)
 skill=(ROOT/'SKILL.md').read_text(encoding='utf-8'); words=len(skill.split());lines=len(skill.splitlines())
 if words>900:problems.append(f'SKILL.md too large: {words}')
 if 'Do not recursively read this skill directory' not in skill:problems.append('missing recursive read prohibition')
 if 'starting points, not hard limits' not in skill:problems.append('missing adaptive-budget wording')
 if 'need user permission to expand' not in skill:problems.append('missing autonomous expansion wording')
 if a.ir:
  ir=json.loads(Path(a.ir).read_text(encoding='utf-8'))
  try:
   import jsonschema;schema=json.loads((ROOT/'compiler/motion-ir.schema.json').read_text(encoding='utf-8'));jsonschema.Draft202012Validator(schema).validate(ir)
  except ImportError:pass
  except Exception as e:problems.append('IR validation failed: '+str(e))
 if problems:print(json.dumps({'ok':False,'problems':problems},indent=2));sys.exit(1)
 print(json.dumps({'ok':True,'skillWords':words,'skillLines':lines,'jsonFiles':len(list(ROOT.rglob('*.json'))),'note':'Progressive-disclosure checks passed.'},indent=2))
if __name__=='__main__':main()
