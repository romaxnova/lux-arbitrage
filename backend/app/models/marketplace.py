import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._types import JsonDict, PkUUID


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[uuid.UUID] = mapped_column(PkUUID, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    base_currency: Mapped[str] = mapped_column(String(3), default="EUR")
    buyer_fee_pct: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.05"))
    seller_fee_pct: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.12"))
    default_shipping_eur: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("10.00"))
    country_code: Mapped[str] = mapped_column(String(2), default="EU")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JsonDict, default=dict)

    listings = relationship("Listing", back_populates="marketplace")
