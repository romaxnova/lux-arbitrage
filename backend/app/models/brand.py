import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._types import JsonDict, JsonList, PkUUID


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(PkUUID, primary_key=True, default=uuid.uuid4)
    canonical_name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    aliases: Mapped[list] = mapped_column(JsonList, default=list)
    tier: Mapped[str] = mapped_column(String(50), default="luxury")
    demand_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("50.00"))
    counterfeit_risk: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("30.00"))
    metadata_: Mapped[dict] = mapped_column("metadata", JsonDict, default=dict)

    listings = relationship("Listing", back_populates="brand")
    products = relationship("Product", back_populates="brand")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(PkUUID, primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("brands.id"), index=True)
    canonical_title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_line: Mapped[str | None] = mapped_column(String(150), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JsonDict, default=dict)

    brand = relationship("Brand", back_populates="products")
