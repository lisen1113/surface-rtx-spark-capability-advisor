"""Editable local/cloud/hybrid TCO calculator; all outputs are scenario estimates."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/tco", tags=["tco"])

class TcoInput(BaseModel):
    years: int = Field(default=3, ge=1, le=10)
    purchase_price_cny: float = Field(ge=0)
    residual_value_cny: float = Field(default=0, ge=0)
    power_watts: float = Field(default=80, ge=0)
    hours_per_day: float = Field(default=8, ge=0, le=24)
    days_per_year: int = Field(default=250, ge=0, le=366)
    electricity_cny_per_kwh: float = Field(default=0.8, ge=0)
    annual_maintenance_cny: float = Field(default=0, ge=0)
    monthly_tokens_million: float = Field(default=10, ge=0)
    cloud_cny_per_million_tokens: float = Field(default=30, ge=0)
    hybrid_cloud_share: float = Field(default=0.25, ge=0, le=1)

@router.post("/calculate")
def calculate(data: TcoInput):
    electricity = data.power_watts / 1000 * data.hours_per_day * data.days_per_year * data.years * data.electricity_cny_per_kwh
    maintenance = data.annual_maintenance_cny * data.years
    local = data.purchase_price_cny - data.residual_value_cny + electricity + maintenance
    cloud_monthly = data.monthly_tokens_million * data.cloud_cny_per_million_tokens
    cloud = cloud_monthly * 12 * data.years
    hybrid = local + cloud * data.hybrid_cloud_share
    savings = cloud - local
    local_monthly_operating = (electricity + maintenance) / (12 * data.years)
    monthly_delta = cloud_monthly - local_monthly_operating
    payback = data.purchase_price_cny / monthly_delta if monthly_delta > 0 else None
    return {
        "currency": "CNY", "period_years": data.years,
        "local_tco_cny": round(local, 2), "cloud_tco_cny": round(cloud, 2),
        "hybrid_tco_cny": round(hybrid, 2), "local_vs_cloud_savings_cny": round(savings, 2),
        "payback_months": round(payback, 1) if payback is not None else None,
        "breakdown": {"purchase_net_residual": round(data.purchase_price_cny-data.residual_value_cny,2), "electricity": round(electricity,2), "maintenance": round(maintenance,2), "cloud": round(cloud,2)},
        "evidence_level": "user_editable_scenario", "limitations": ["不含融资、税务、网络、人员、机房及机会成本，除非用户在维护成本中计入", "Token 单价和用量由用户输入，不代表供应商当前报价", "本地设备性能与利用率未由成本模型推断"],
    }
