from datetime import UTC,datetime,timedelta
from types import SimpleNamespace
from app.tax_service import TaxService
from app.tax_audit import generate_tax_audit_pdf
from app.quota import QuotaStore
from app.accountant_invite import AccountantInviteStore

def test_tax_rules_table_driven():
 from app.product_service import ProductService
 s=TaxService(ProductService(":memory:"))
 for vendor,locale,expected in [("STARBUCKS","US","Meals and Entertainment - 50%"),("Lidl","HU","27% AFA")]:assert s.categorize(vendor,[],locale)["tax_category"]==expected

def test_pdf_content_type():assert generate_tax_audit_pdf({"year":2026,"locale":"US","by_category":[],"grand_total":0}).startswith(b"%PDF")
def test_quota_tenant_isolation_and_limit():
 q=QuotaStore();[q.incr_and_check("a") for _ in range(25)];assert not q.incr_and_check("a")["allowed"];assert q.get_quota("b")["used"]==0
def test_quota_month_rollover():
 now=[datetime(2026,8,31,tzinfo=UTC)];q=QuotaStore(now=lambda:now[0]);q.incr_and_check("a");now[0]=datetime(2026,9,1,tzinfo=UTC);assert q.get_quota("a")["used"]==0
def test_invite_expiry_and_tenant_isolation():
 now=[datetime(2026,1,1,tzinfo=UTC)];s=AccountantInviteStore(now=lambda:now[0]);x=s.create_invite("a",1);assert not s.revoke_invite(x["token"],"b");now[0]+=timedelta(days=2);assert s.resolve_invite(x["token"]) is None
