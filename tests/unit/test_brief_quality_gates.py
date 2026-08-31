import json
import re
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[2]
BRIEFS_DIR = ROOT / '.product' / 'briefs'
INDEX_FILE = BRIEFS_DIR / 'index.json'
EVIDENCE_FILE = ROOT / 'docs' / 'reports' / '2026-08-31-brief-evidence-matrix.md'

REQUIRED_HEADERS = [
    '## Probléma',
    '## Célcsoport és kontextus',
    '## Kívánt eredmény',
    '## Jelenlegi funkciókat lefedő felhasználói történetek',
    '## Scope',
    '## Non-scope',
    '## Érintett rendszerek',
    '## Bizonytalanságok'
]

FORBIDDEN_TERMS = [
    'app/', 'frontend/', 'GET /', 'POST /', 'PUT /', 'PATCH /', 'DELETE /',
    'AsyncSession', 'data-testid', '@pytest', 'SQLAlchemy', 'FastAPI', 'Next.js',
    'Pydantic', 'endpoint', 'router', 'schema_version'
]

def test_qg1_brief_structure_and_headers():
    assert INDEX_FILE.is_file(), 'index.json missing'
    index_data = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    assert index_data['brief_count'] == len(index_data['briefs'])
    
    for brief in index_data['briefs']:
        file_path = ROOT / brief['path']
        assert file_path.is_file(), f'Missing brief file: {file_path}'
        text = file_path.read_text(encoding='utf-8')
        for header in REQUIRED_HEADERS:
            assert header in text, f'Header {header} missing from {brief["brief_id"]}'

def test_qg2_no_truncated_stories():
    for brief_path in BRIEFS_DIR.glob('BRIEF-*.md'):
        text = brief_path.read_text(encoding='utf-8')
        stories = re.findall(r'^- \*\*US-[^:]+:\*\* (.+)$', text, re.M)
        assert len(stories) >= 4, f'Too few stories in {brief_path.name}'
        for s in stories:
            assert ' szeretn' in s and ', hogy ' in s, f'Malformed story syntax: {s}'
            assert not s.strip().endswith(('szeretném', 'szeretnék', 'hogy')), f'Truncated story: {s}'
            assert len(s.split()) >= 8, f'Story too short: {s}'

def test_qg3_no_forbidden_technical_terms():
    for brief_path in BRIEFS_DIR.glob('BRIEF-*.md'):
        text = brief_path.read_text(encoding='utf-8')
        stories = re.findall(r'^- \*\*US-[^:]+:\*\* (.+)$', text, re.M)
        for s in stories:
            for term in FORBIDDEN_TERMS:
                assert term.lower() not in s.lower(), f'Forbidden technical term "{term}" found in {brief_path.name}: {s}'

def test_qg4_no_duplicate_or_excessively_similar_stories():
    all_stories = []
    for brief_path in BRIEFS_DIR.glob('BRIEF-*.md'):
        text = brief_path.read_text(encoding='utf-8')
        all_stories.extend(re.findall(r'^- \*\*US-[^:]+:\*\* (.+)$', text, re.M))
    
    assert len(all_stories) == len(set(all_stories)), 'Exact duplicate stories found!'
    
    max_sim = 0.0
    pair = None
    for i in range(len(all_stories)):
        for j in range(i + 1, len(all_stories)):
            sim = SequenceMatcher(None, all_stories[i], all_stories[j]).ratio()
            if sim > max_sim:
                max_sim = sim
                pair = (all_stories[i], all_stories[j])
    
    assert max_sim < 0.85, f'Excessively similar stories ({max_sim:.3f}): {pair}'

def test_qg5_index_consistency():
    index_data = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
    brief_ids = [b['brief_id'] for b in index_data['briefs']]
    assert len(brief_ids) == len(set(brief_ids)), 'Duplicate brief IDs in index'
    assert index_data['brief_count'] == len(index_data['briefs'])
    
    total_stories = 0
    for b in index_data['briefs']:
        file_path = ROOT / b['path']
        text = file_path.read_text(encoding='utf-8')
        stories = re.findall(r'^- \*\*US-[^:]+:\*\* (.+)$', text, re.M)
        assert len(stories) == b['story_count'], f'Story count mismatch in {b["brief_id"]}'
        total_stories += len(stories)
    
    assert total_stories == sum(b['story_count'] for b in index_data['briefs'])

def test_qg6_evidence_matrix_completeness():
    assert EVIDENCE_FILE.is_file(), 'Evidence matrix missing'
    text = EVIDENCE_FILE.read_text(encoding='utf-8')
    for i in range(1, 30):
        brief_id = f'BRIEF-{i:03d}'
        assert f'## {brief_id}:' in text, f'{brief_id} missing in evidence matrix'
        assert text.count(f'## {brief_id}:') == 1

