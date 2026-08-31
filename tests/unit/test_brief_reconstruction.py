from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[2]
B=ROOT/'.product/briefs'
REQ=['## Probléma','## Célcsoport és kontextus','## Kívánt eredmény','## Scope','## Non-scope','## Érintett rendszerek','## Bizonytalanságok']
FORBIDDEN=['app/','frontend/','GET /','POST /','PUT /','PATCH /','DELETE /','AsyncSession','data-testid','@pytest']
def test_index_and_files():
 d=json.loads((B/'index.json').read_text('utf-8')); assert d['brief_count']==len(d['briefs']); assert len({x['brief_id'] for x in d['briefs']})==len(d['briefs']); assert all((ROOT/x['path']).is_file() for x in d['briefs'])
def test_structure_and_user_stories():
 d=json.loads((B/'index.json').read_text('utf-8'))
 for x in d['briefs']:
  s=(ROOT/x['path']).read_text('utf-8'); assert all(h in s for h in REQ); us=re.findall(r'^- \*\*US-[^:]+:\*\* (.+)$',s,re.M); assert len(us)==x['story_count'] and len(us)>=4; assert all(' szeretn' in u and ', hogy ' in u for u in us); assert not any(v in '\n'.join(us) for v in FORBIDDEN)
def test_no_truncated_or_duplicate_stories():
 texts=[]
 for p in B.glob('BRIEF-*.md'):
  texts += re.findall(r'^- \*\*US-[^:]+:\*\* (.+)$',p.read_text('utf-8'),re.M)
 assert len(texts)==len(set(texts)); assert not any(re.fullmatch(r'.*szeretn(?:ém|ék)[,.;:]?',x.strip()) for x in texts)
