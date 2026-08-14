"""BDD regression contract for US-001 through US-009."""
from types import SimpleNamespace

import pytest

from app.accounting_workspace import AccountingWorkspace
from app.advanced_workspace import AdvancedWorkspace
from app.automation_service import AutomationService
from app.export_workflow import ExportWorkflow
from app.product_service import Actor, ProductConflict, ProductService
from app.quality_service import QualityService


def parsed(vendor='Shop',total=10,confidence=.5):
 return SimpleNamespace(merchant=vendor,date='2026-08-01',total=total,tax=1,currency='CHF',items=[],confidence={'vendor':confidence,'date':confidence,'total':confidence,'tax':confidence,'currency':confidence,'line_items':confidence})
@pytest.fixture
def env(tmp_path):
 s=ProductService(tmp_path/'db.sqlite');a=Actor('t','admin');adv=AdvancedWorkspace(s);acc=AccountingWorkspace(s)
 return s,a,adv,acc,ExportWorkflow(s,acc),QualityService(s),AutomationService(s,adv)
def make(env,**kw):return env[0].create_receipt(env[1],parsed(**kw),'r.png')['receipt_id']

def test_us_001_review_filter_and_stale_version(env):
 s,a,*_=env; rid=make(env,total=99,confidence=.4); q=s.list_reviews(a,'total',.8,sort='amount_desc');assert q['total']==1 and q['items'][0]['receipt_id']==rid
 s.correct(a,rid,{'total':100},1,False)
 with pytest.raises(ProductConflict):s.correct(a,rid,{'total':101},1,False)
 assert s.get_receipt(a,rid)['receipt']['total']==100

def test_us_002_preflight_blocks_and_idempotent_export(env):
 s,a,_adv,_acc,ex,*_=env; good=make(env,confidence=.9); bad=make(env,confidence=.9)
 s.correct(a,bad,{'currency':None},1,True)
 prep=ex.prepare(a,[good,bad],None);assert len(prep['valid_ids'])==1 and len(prep['blocked'])==1
 first=ex.execute(a,prep['preparation_id'],[x['receipt_id'] for x in prep['warnings']],'key');second=ex.execute(a,prep['preparation_id'],[x['receipt_id'] for x in prep['warnings']],'key')
 assert first==second and 'receipt_id,vendor,date,total,currency' in ex.artifact('t',first['run_id'])

def test_us_003_audit_history_is_redacted(env):
 _s,a,adv,*_=env;rid=make(env);adv.record_history(a,rid,'receipt.corrected',{'total':1},{'total':2});events=adv.history('t',rid)
 assert events[0]['action']=='receipt.corrected' and 'image_bytes' not in str(events)

def test_us_004_confidence_filter_sort_and_pagination(env):
 s,a,*_=env
 for i in range(5):make(env,total=i+1,confidence=.2)
 make(env,total=100,confidence=.95)
 q=s.list_reviews(a,'total',.8,sort='amount_desc',limit=3);assert q['total']==5 and len(q['items'])==3 and q['items'][0]['receipt']['total']==5
 with pytest.raises(ValueError):s.list_reviews(a,'bad',.8)

def test_us_005_benchmark_counts_and_profile(env):
 *_,quality,_=env; a=env[1];cases=[{'expected':{'total':i},'predicted':{'total':i},'confidence':{'total':.9}} for i in range(200)]
 report=quality.evaluate(a,'golden-v1',cases);m=report['fields']['total'];assert m['evaluated']==200 and sum(m[k] for k in ['true_clear','false_clear','true_review','false_review'])==200
 profile=quality.publish(a,report['report_id'],{'total':.8});assert quality.active('t')['version']==profile['version']

def test_us_006_ocr_box_provenance(env):
 _s,_a,adv,*_=env;rid=make(env);adv.store_asset('t',rid,b'PNG','image/png','r.png',[{'text':'10.00','confidence':.9,'x':.1,'y':.2,'width':.2,'height':.1}]);asset=adv.asset('t',rid)
 assert asset and asset.boxes[0]['text']=='10.00'

def test_us_007_inbound_attachment_states(env):
 *_,acc,_ex,_quality,_auto=env; a=env[1];mail=acc.receive_email('t','a@example.com','Receipts',[{'filename':'a.png','content_type':'image/png','size':10},{'filename':'x.exe','content_type':'application/octet-stream','size':5}])
 assert mail['status']=='queued' and len(mail['attachments'])==2

def test_us_008_rule_preview_has_no_mutation(env):
 s,a,_adv,_acc,_ex,_quality,auto=env;rid=make(env,vendor='Coffee'); rule=auto.create(a,'Coffee',{'vendor_contains':'Coffee'},{'tags':['meal']},10);before=s.get_receipt(a,rid)
 preview=auto.preview(a,rule['rule_id'],1);assert preview['match_count']==1 and s.get_receipt(a,rid)==before
 assert auto.activate(a,rule['rule_id'],1,preview['preview_token'])['status']=='active'

def test_us_009_rollback_preserves_later_edits(env):
 s,a,_adv,_acc,_ex,_quality,auto=env;r1=make(env);r2=make(env);rule=auto.create(a,'Tag',{}, {'tags':['x']},10);p=auto.preview(a,rule['rule_id'],1);auto.activate(a,rule['rule_id'],1,p['preview_token']);run=auto.run(a,rule['rule_id'],1,[r1,r2]);s.correct(a,r2,{'total':20},2,False)
 preview=auto.rollback_preview('t',run['run_id']);assert r1 in preview['eligible'] and r2 in preview['conflicts'];result=auto.rollback(a,run['run_id'],preview['eligible']);assert result['rolled_back']==1
