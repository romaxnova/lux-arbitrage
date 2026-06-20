import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._types import JsonDict, JsonList, PkUUID


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("marketplace_id", "external_id", name="uq_listing_marketplace_external"),)

    id: Mapped[uuid.UUID] = mapped_column(PkUUID, primary_key=True, default=uuid.uuid4)
    marketplace_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("marketplaces.id"), index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(PkUUID, ForeignKey("products.id"), nullable=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("brands.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500))
    normalized_title: Mapped[str] = mapped_column(String(500), index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_raw: Mapped[str | None] = mapped_column(String(50), nullable=True)
    size_normalized: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    size_system: Mapped[str | None] = mapped_column(String(10), nullable=True)
    condition: Mapped[str] = mapped_column(String(30), default="good")
    price_original: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency_original: Mapped[str] = mapped_column(String(3))
    price_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2), index=True)
    price_rub: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    seller_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    listing_url: Mapped[str] = mapped_column(Text)
    image_urls: Mapped[list] = mapped_column(JsonList, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_data: Mapped[dict] = mapped_column(JsonDict, default=dict)

    marketplace = relationship("Marketplace", back_populates="listings")
    brand = relationship("Brand", back_populates="listings")
    price_history = relationship("PriceHistory", back_populates="listing")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[uuid.UUID] = mapped_column(PkUUID, primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("listings.id"), index=True)
    price_eur: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_rub: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    listing = relationship("Listing", back_populates="price_history")
