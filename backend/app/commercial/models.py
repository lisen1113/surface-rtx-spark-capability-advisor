"""Validated inputs. All money and financial assumptions use Decimal."""
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PriceInput(Input):
    product_id: str = Field(min_length=2, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=250)
    kind: Literal["Base", "Add-on", "Bundle", "Included/Metered"]
    monthly_usd: Decimal = Field(ge=0, le=1000000, max_digits=14, decimal_places=6)
    effective_from: date
    effective_to: date | None = None  # exclusive
    seat_limit: int | None = Field(default=None, ge=1, le=1000000)
    prerequisite: str = Field(default="", max_length=1000)
    components: list[str] = Field(default_factory=list, max_length=30)
    source_url: str = Field(min_length=8, max_length=1000)
    source_checked_at: date
    source_reference: str = Field(default="", max_length=500)
    market: str = Field(default="US Public", min_length=2, max_length=80)

    @field_validator("source_url")
    @classmethod
    def https_source(cls, value):
        if not value.startswith("https://"):
            raise ValueError("价格来源必须为 HTTPS")
        return value

    @model_validator(mode="after")
    def period(self):
        if self.effective_to and self.effective_to <= self.effective_from:
            raise ValueError("失效日期必须晚于生效日期")
        if self.kind == "Bundle" and not self.components:
            raise ValueError("Bundle 必须记录所含产品")
        return self


class PolicyInput(Input):
    name: str = Field(min_length=2, max_length=150)
    annual_funding_rate: Decimal = Field(ge=0, le=1, max_digits=9, decimal_places=6)
    residual_rate_24: Decimal = Field(ge=0, le=Decimal("0.8"), max_digits=9, decimal_places=6)
    residual_rate_36: Decimal = Field(ge=0, le=Decimal("0.8"), max_digits=9, decimal_places=6)
    monthly_service_cny: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    recovery_cost_cny: Decimal = Field(ge=0, le=100000, max_digits=12, decimal_places=2)
    minimum_margin: Decimal = Field(ge=0, lt=1, max_digits=9, decimal_places=6)
    terms_reference: str = Field(min_length=2, max_length=1000)
    approved_for_formal: bool = False


class HardwareLine(Input):
    part_number: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1, le=100000)


class ResidualRates(Input):
    months_12: Decimal = Field(default=Decimal('0.50'), ge=0, le=1, decimal_places=6)
    months_24: Decimal = Field(default=Decimal('0.40'), ge=0, le=1, decimal_places=6)
    months_36: Decimal = Field(default=Decimal('0.30'), ge=0, le=1, decimal_places=6)


class RentalRulesInput(Input):
    name: str = Field(default='常规硬件租赁', min_length=2, max_length=150)
    surface_erp_cost_factor: Decimal = Field(default=Decimal('1'), gt=0, le=1, decimal_places=6)
    residual_by_brand: dict[Literal['Surface', 'Apple', 'Think', 'RTX Spark'], ResidualRates]
    terms_reference: str = Field(min_length=2, max_length=1000)
    approved_for_formal: bool = False

    @field_validator('residual_by_brand')
    @classmethod
    def all_brands(cls, value):
        if not {'Surface', 'Apple', 'Think'}.issubset(value):
            raise ValueError('请完整设置 Surface、Apple、Think 的残值比例')
        return value


class SettingsInput(Input):
    usd_cny: Decimal = Field(gt=0, le=100, max_digits=12, decimal_places=6)
    fx_date: date
    fx_reference: str = Field(min_length=2, max_length=500)
    cloud_tax_rate: Decimal = Field(ge=0, le=1, max_digits=9, decimal_places=6)
    software_cost_factor: Decimal = Field(default=Decimal("0.85"), gt=0, le=1, decimal_places=6)
    active_policy_id: str | None = None


class PublicEstimateInput(Input):
    title: str = Field(default="我的 Surface 与订阅方案", min_length=2, max_length=150)
    term_months: Literal[12, 24, 36] = 36
    hardware: list["HardwareLine"] = Field(default_factory=list, max_length=50)
    cloud: list["CloudLine"] = Field(default_factory=list, max_length=30)
    azure_requested: bool = False
    personas: str = Field(default="", max_length=2000)


class CloudLine(Input):
    product_id: str = Field(min_length=2, max_length=100)
    user_group: str = Field(default="全体用户", min_length=1, max_length=100)
    seats: int = Field(ge=1, le=100000)
    # Explicit attestation; never infer licensing eligibility from price alone.
    eligibility_confirmed: bool = False
    eligibility_reference: str = Field(default="", max_length=1000)


class QuoteInput(Input):
    title: str = Field(min_length=2, max_length=150)
    term_months: Literal[12, 24, 36] = 36
    hardware: list[HardwareLine] = Field(default_factory=list, max_length=100)
    cloud: list[CloudLine] = Field(default_factory=list, max_length=50)
    policy_id: str | None = None
    usd_cny: Decimal = Field(gt=0, le=100, max_digits=12, decimal_places=6)
    fx_reference: str = Field(min_length=2, max_length=500)
    fx_date: date
    # Software pricing is USD excluding tax; ERP hardware is CNY including tax.
    cloud_tax_rate: Decimal = Field(ge=0, le=1, max_digits=9, decimal_places=6)
    service_once_cny: Decimal = Field(default=Decimal("0"), ge=0, le=10000000, decimal_places=2)
    project_discount_cny: Decimal = Field(default=Decimal("0"), ge=0, le=100000000, decimal_places=2)
    discount_reason: str = Field(default="", max_length=1000)
    azure_requested: bool = False
    renewal: Literal["indicative", "locked"] = "indicative"
    renewal_reference: str = Field(default="", max_length=1000)
    valid_until: date
    personas: str = Field(default="", max_length=3000)

    @model_validator(mode="after")
    def lines(self):
        if not self.hardware and not self.cloud:
            raise ValueError("至少选择一项设备或软件")
        for lines, key in ((self.hardware, "part_number"), (self.cloud, "product_id")):
            ids = [(getattr(line, key), getattr(line, "user_group", "")) for line in lines]
            if len(ids) != len(set(ids)):
                raise ValueError("相同产品请合并数量")
        if self.project_discount_cny and not self.discount_reason:
            raise ValueError("整体优惠需要说明原因")
        if self.renewal == "locked" and not self.renewal_reference:
            raise ValueError("跨年锁价需要依据")
        return self


class CompanyProfile(Input):
    company_name: str = Field(min_length=2, max_length=200)
    hk_company_name: str = Field(default="", max_length=200)
    region: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=5, max_length=1000)
    phone: str = Field(min_length=5, max_length=60)
    domain: str = Field(min_length=3, max_length=253)
    contact_name: str = Field(min_length=1, max_length=100)
    contact_email: str = Field(min_length=5, max_length=254)
    contracting_company: str = Field(default="", max_length=200)
    paying_company: str = Field(default="", max_length=200)
    bank_account_name: str = Field(min_length=2, max_length=200)
    bank_name: str = Field(min_length=2, max_length=200)
    bank_account: str = Field(min_length=4, max_length=100)
    bank_code: str = Field(default="", max_length=100)
    invoice_title: str = Field(min_length=2, max_length=200)
    invoice_registration: str = Field(min_length=2, max_length=100)
    invoice_address: str = Field(min_length=5, max_length=1000)
    invoice_email: str = Field(min_length=5, max_length=254)

    @field_validator("contact_email", "invoice_email")
    @classmethod
    def email(cls, value):
        import re
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("邮箱格式无效")
        return value.lower()

    @field_validator("domain")
    @classmethod
    def domain_name(cls, value):
        import re
        value = value.lower().rstrip(".")
        if not re.fullmatch(r"(?=.{3,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", value):
            raise ValueError("请填写域名，例如 company.com，不含 https 或路径")
        return value


class ReviewInput(Input):
    decision: Literal["approve", "reject"]
    reason: str = Field(min_length=2, max_length=2000)
    commercial_reference: str = Field(default="", max_length=2000)


class RecommendInput(Input):
    min_memory_gb: int = Field(default=16, ge=1, le=1024)
    product_type: str = Field(default="Surface 设备", max_length=100)
    max_erp_cny: Decimal | None = Field(default=None, gt=0, le=1000000)


class CloudRecommendInput(Input):
    users: int = Field(ge=1, le=100000)
    copilot_users: int = Field(default=0, ge=0, le=100000)
    desktop_office: bool = True
    security_management: bool = False
    existing_qualifying_base: bool = False

    @model_validator(mode="after")
    def seats(self):
        if self.copilot_users > self.users:
            raise ValueError("Copilot 人数不能超过项目用户人数")
        return self


class AzureContractInput(Input):
    contract_number: str = Field(min_length=2, max_length=100)
    subscription_id: str = Field(min_length=2, max_length=100)
    service_name: str = Field(min_length=2, max_length=200)
    meter: str = Field(min_length=2, max_length=150)
    unit: str = Field(min_length=1, max_length=100)
    unit_price_usd: Decimal = Field(gt=0, le=1000000, decimal_places=6)
    signed_on: date
    starts_on: date
    ends_on: date
    reference: str = Field(min_length=2, max_length=1000)

    @model_validator(mode="after")
    def dates(self):
        if self.starts_on < self.signed_on or self.ends_on < self.starts_on:
            raise ValueError("合同日期顺序无效")
        return self


class UsageInput(Input):
    period_start: date
    period_end: date
    quantity: Decimal = Field(ge=0, le=1000000000000, decimal_places=6)
    source_reference: str = Field(min_length=2, max_length=1000)

    @model_validator(mode="after")
    def dates(self):
        if self.period_end < self.period_start:
            raise ValueError("账期结束不能早于开始")
        return self
