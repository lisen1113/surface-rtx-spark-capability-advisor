from fastapi.testclient import TestClient
from app.main import app
from app.tco import sku_defaults

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

def test_sku_defaults_use_imported_price_but_label_other_values_as_scenarios():
    def sku(memory, price):
        return {"part_number": f"TEST-{memory}", "memory_gb": memory, "platform_code": "S3",
                "erp_price_cny": price, "source_reference": "authorized workbook"}
    small = sku_defaults(sku(24, 25000))
    large = sku_defaults(sku(128, 70000))
    assert small["values"]["purchase_price_cny"] == 25000
    assert large["values"]["purchase_price_cny"] == 70000
    assert small["values"]["monthly_tokens_million"] < large["values"]["monthly_tokens_million"]
    assert small["values"]["hybrid_cloud_share"] == 1
    assert "非设备吞吐" in small["provenance"]["monthly_tokens_million"]
    assert "非云供应商报价" in large["provenance"]["cloud_cny_per_million_tokens"]

def test_device_allocation_and_invalid_residual():
    body={"purchase_price_cny":30000,"residual_value_cny":6000,"device_cost_allocation_ratio":0.5,
          "power_watts":0,"annual_maintenance_cny":0,"monthly_tokens_million":0}
    result=client.post("/api/tco/calculate",json=body).json()
    assert result["local_tco_cny"] == 12000
    assert result["breakdown"]["purchase_net_residual_allocated"] == 12000
    body["residual_value_cny"] = 40000
    assert client.post("/api/tco/calculate",json=body).status_code == 422
