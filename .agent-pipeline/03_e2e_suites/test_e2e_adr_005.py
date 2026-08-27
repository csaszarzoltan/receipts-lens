import os,pytest,httpx
pytestmark=pytest.mark.skipif(not os.getenv("RECEIPTLENS_E2E"),reason="requires running backend")
def test_health():
 r=httpx.get(os.getenv("RECEIPTLENS_API_URL","http://localhost:8000")+"/health");assert r.status_code==200
