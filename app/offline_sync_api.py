"""FastAPI router for the offline_sync feature (see app/feature_specs.py)."""
from app.feature_core import make_router
from app.feature_specs import SPECS

router = make_router(SPECS["offline_sync"])
