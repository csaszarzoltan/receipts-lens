"""FastAPI router for the mobile_receipts feature (see app/feature_specs.py)."""
from app.feature_core import make_router
from app.feature_specs import SPECS

router = make_router(SPECS["mobile_receipts"])
