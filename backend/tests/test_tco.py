from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_tco_uses_editable_assumptions_and_breakdown():
    body=client.post("/api/tco/calculate",json={"years":3,"purchase_price_cny":30000,"residual_value_cny":6000,"power_watts":100,"hours_per_day":10,"days_per_year":300,"electricity_cny_per_kwh":1,"annual_maintenance_cny":1000,"monthly_tokens_million":100,"cloud_cny_per_million_tokens":20,"hybrid_cloud_share":0.25}).json()
    assert body["local_tco_cny"]==27900
    assert body["cloud_tco_cny"]==72000
    assert body["hybrid_tco_cny"]==45900
    assert body["evidence_level"]=="user_editable_scenario"

def test_tco_does_not_claim_payback_when_cloud_is_cheaper():
    body=client.post("/api/tco/calculate",json={"purchase_price_cny":50000,"monthly_tokens_million":1,"cloud_cny_per_million_tokens":1}).json()
    assert body["payback_months"] is None

def test_tco_rejects_invalid_hybrid_share():
    assert client.post("/api/tco/calculate",json={"purchase_price_cny":1,"hybrid_cloud_share":2}).status_code==422
