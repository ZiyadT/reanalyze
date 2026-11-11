from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmbeddingConfiguration(Base):
    __tablename__ = "embedding_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(
        CheckConstraint("provider ~ '[^[:space:]]'", name="chk_provider_not_empty"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        CheckConstraint("model_name ~ '[^[:space:]]'", name="chk_model_name_not_empty"),
        nullable=False,
    )
    model_version: Mapped[str | None] = mapped_column(nullable=True)
    dimensions: Mapped[int] = mapped_column(
        CheckConstraint("dimensions > 0", name="chk_dimensions_positive"),
        nullable=False,
    )
    normalization: Mapped[str] = mapped_column(
        CheckConstraint("normalization IN ('none', 'l2')", name="chk_normalization_valid"),
        nullable=False,
    )
    similarity_metric: Mapped[str] = mapped_column(
        CheckConstraint(
            "similarity_metric IN ('cosine', 'dot_product', 'euclidean')",
            name="chk_similarity_metric_valid",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )