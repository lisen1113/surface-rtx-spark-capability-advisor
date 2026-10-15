"""Editable local/cloud/hybrid TCO calculator; all outputs are scenario estimates."""
import math
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from .auth import require_entitled_user
from .catalog import connection

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
    device_cost_allocation_ratio: float = Field(default=1, ge=0, le=1)

    @model_validator(mode="after")
    def residual_cannot_exceed_purchase(self):
        if self.residual_value_cny > self.purchase_price_cny:
            raise ValueError("残值不能高于设备采购价")
        return self


def sku_defaults(sku: dict) -> dict:
    """Budgeting starting points, deliberately not inferred throughput."""
    price = sku["erp_price_cny"]
    if price is None:
        raise HTTPException(422, "该 SKU 缺少导入价格；请先补齐报价")
    memory = int(sku["memory_gb"] or 0)
    # Different sample workloads help a customer begin a conversation. They do
    # not assert that the device can process this many tokens per month.
    sample_monthly = 1 if memory <= 24 else 3 if memory <= 32 else 5 if memory <= 48 else 10 if memory <= 64 else 20
    return {
        "part_number": sku["part_number"], "memory_gb": memory,
        "platform_code": sku["platform_code"], "source_reference": sku["source_reference"],
        "values": {"years": 3, "purchase_price_cny": float(price),
                   "residual_value_cny": round(float(price) * 0.2, 2),
                   "power_watts": 80, "hours_per_day": 8, "days_per_year": 250,
                   "electricity_cny_per_kwh": 0.8,
                   "annual_maintenance_cny": round(float(price) * 0.05, 2),
                   "monthly_tokens_million": sample_monthly,
                   "cloud_cny_per_million_tokens": 30,
                   "hybrid_cloud_share": 1,
                   "device_cost_allocation_ratio": 1},
        "provenance": {"purchase_price_cny": "授权 V3.4 导入工作簿的 ERP 含税参考价；非客户成交价",
                       "monthly_tokens_million": "按内存档选择的演示业务量，非设备吞吐或容量承诺",
                       "cloud_cny_per_million_tokens": "演示占位价格，非云供应商报价；应按模型、地区、输入/输出比例和合同替换",
                       "power_watts": "80W 仅为演示平均功率占位值，不是该 SKU 官方功耗或实测",
                       "residual_value_cny": "设备价格 20% 的演示残值假设",
                       "annual_maintenance_cny": "设备价格每年 5% 的演示运维假设",
                       "hybrid_cloud_share": "默认 100% 云端保留；完成目标设备 PoC 后才可降低",
                       "device_cost_allocation_ratio": "默认将整机成本计入 AI 场景；若设备原本用于其他工作，可按实际分摊"},
        "evidence_level": "engineering_scenario",
        "warning": "除 SKU 导入价外均为可修改的预算示例；不证明模型可运行、吞吐、利用率或节省。",
    }


@router.get("/defaults/{part_number}")
def defaults_for_sku(part_number: str, _user=Depends(require_entitled_user)):
    with connection() as conn:
        row = conn.execute("SELECT * FROM imported_skus WHERE part_number=?", (part_number,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该 Part Number")
    return sku_defaults(dict(row))

@router.post("/calculate")
def calculate(data: TcoInput, _user=Depends(require_entitled_user)):
    electricity = data.power_watts / 1000 * data.hours_per_day * data.days_per_year * data.years * data.electricity_cny_per_kwh
    maintenance = data.annual_maintenance_cny * data.years
    allocated_purchase = (data.purchase_price_cny - data.residual_value_cny) * data.device_cost_allocation_ratio
    local = allocated_purchase + electricity + maintenance
    cloud_monthly = data.monthly_tokens_million * data.cloud_cny_per_million_tokens
    cloud = cloud_monthly * 12 * data.years
    hybrid = local + cloud * data.hybrid_cloud_share
    savings = cloud - local
    local_monthly_operating = (electricity + maintenance) / (12 * data.years)
    monthly_delta = cloud_monthly - local_monthly_operating
    payback = allocated_purchase / monthly_delta if monthly_delta > 0 else None
    period_months = data.years * 12
    required_monthly_tokens = (
        (local_monthly_operating + allocated_purchase / period_months)
        / data.cloud_cny_per_million_tokens
        if data.cloud_cny_per_million_tokens > 0 else None
    )
    payback_status = ("no_cloud_price" if data.cloud_cny_per_million_tokens == 0 else
                      "no_monthly_savings" if monthly_delta <= 0 else
                      "within_period" if payback <= period_months else "beyond_period")
    return {
        "currency": "CNY", "period_years": data.years,
        "local_tco_cny": round(local, 2), "cloud_tco_cny": round(cloud, 2),
        "hybrid_tco_cny": round(hybrid, 2), "local_vs_cloud_savings_cny": round(savings, 2),
        "payback_months": round(payback, 1) if payback is not None else None,
        "payback_status": payback_status,
        "cloud_minus_local_operating_monthly_cny": round(monthly_delta, 2),
        "break_even_monthly_tokens_million_within_period": (
            math.ceil(required_monthly_tokens * 100) / 100
            if required_monthly_tokens is not None else None),
        "breakdown": {"purchase_net_residual": round(data.purchase_price_cny-data.residual_value_cny,2),
                      "purchase_net_residual_allocated": round(allocated_purchase,2), "electricity": round(electricity,2), "maintenance": round(maintenance,2), "cloud": round(cloud,2)},
        "evidence_level": "user_editable_scenario", "limitations": ["不含融资、税务、网络、人员、机房及机会成本，除非用户在维护成本中计入", "Token 单价和用量由用户输入，不代表供应商当前报价", "本地设备性能与利用率未由成本模型推断", "本地与云端模型质量、输入输出比例和任务范围须一致；混合云端比例须由 PoC 验证"],
    }
