import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool


class BrandBrief(ORMModel):
    name: str
    slug: str
    tier: str | None = None


class MarketplaceBrief(ORMModel):
    slug: str
    name: str


class ListingBrief(ORMModel):
    id: uuid.UUID
    title: str
    price_eur: float
    marketplace: str
    url: str
    image_urls: list[str]
    condition: str
    size_normalized: str | None = None
    category: str


class OpportunityOut(ORMModel):
    id: uuid.UUID
    opportunity_score: float
    recommendation: str
    roi: float
    gross_profit_eur: float
    net_profit_eur: float
    demand_score: float
    liquidity_score: float
    risk_score: float
    roi_score: float
    price_gap_score: float
    purchase_cost_eur: float
    expected_sale_price_eur: float
    purchase_listing: ListingBrief
    sale_listing: ListingBrief
    brand: BrandBrief


class OpportunityDetail(OpportunityOut):
    cost_breakdown: dict
    match_confidence: float
    computed_at: datetime


class BrandAnalytics(ORMModel):
    brand: BrandBrief
    avg_vinted_price_eur: float
    avg_oskelly_price_eur: float
    median_spread_eur: float
    median_roi: float
    demand_trend: str
    liquidity_trend: str
    top_categories: list[dict]
    active_opportunities: int


class AlertCreate(BaseModel):
    name: str
    rule_type: str
    conditions: dict


class AlertOut(ORMModel):
    id: uuid.UUID
    name: str
    rule_type: str
    conditions: dict
    is_active: bool
    last_triggered_at: datetime | None = None


class WatchlistCreate(BaseModel):
    opportunity_id: uuid.UUID | None = None
    listing_id: uuid.UUID | None = None
    notes: str | None = None


class WatchlistOut(ORMModel):
    id: uuid.UUID
    opportunity_id: uuid.UUID | None
    listing_id: uuid.UUID | None
    notes: str | None
    created_at: datetime
