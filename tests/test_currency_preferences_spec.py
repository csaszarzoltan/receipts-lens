from app.advanced_workspace import AdvancedWorkspace
from app.product_service import ProductService

def test_base_currency_defaults_and_partial_updates_are_merged():
 w=AdvancedWorkspace(ProductService(":memory:")); assert w.preferences("t","admin")["base_currency"]=="USD"
 assert w.save_preferences("t","admin",{"base_currency":"huf"})["base_currency"]=="HUF"
 assert w.save_preferences("t","admin",{"compact":True})["base_currency"]=="HUF"
