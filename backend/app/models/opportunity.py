import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._types import JsonDict, PkUUID


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(PkUUID, primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("matches.id"), unique=True)
    purchase_listing_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("listings.id"), index=True)
    sale_listing_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("listings.id"), index=True)
    purchase_cost_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    expected_sale_price_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    expected_sale_price_rub: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gross_profit_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    net_profit_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    roi: Mapped[Decimal] = mapped_column(Numeric(8, 4), index=True)
    roi_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    demand_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), index=True)
    liquidity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    price_gap_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), index=True)
    opportunity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), index=True)
    recommendation: Mapped[str] = mapped_column(String(10), index=True)
    cost_breakdown: Mapped[dict] = mapped_column(JsonDict, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    match = relationship("Match", back_populates="opportunity")
    purchase_listing = relationship("Listing", foreign_keys=[purchase_listing_id])
    sale_listing = relationship("Listing", foreign_keys=[sale_listing_id])
