import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._types import PkUUID


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("source_listing_id", "target_listing_id", name="uq_match_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PkUUID, primary_key=True, default=uuid.uuid4)
    source_listing_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("listings.id"), index=True)
    target_listing_id: Mapped[uuid.UUID] = mapped_column(PkUUID, ForeignKey("listings.id"), index=True)
    match_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    brand_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    title_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    image_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    category_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    size_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    match_method: Mapped[str] = mapped_column(String(30), default="hybrid")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_listing = relationship("Listing", foreign_keys=[source_listing_id])
    target_listing = relationship("Listing", foreign_keys=[target_listing_id])
    opportunity = relationship("Opportunity", back_populates="match", uselist=False)
