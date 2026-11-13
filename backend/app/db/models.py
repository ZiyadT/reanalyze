from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(trim(email)) > 0", name="chk_user_email_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="owner")
    documents: Mapped[list["Document"]] = relationship(back_populates="owner")


class Workspace(Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "id", name="uq_workspaces_owner_id"),
        CheckConstraint("length(trim(name)) > 0", name="chk_workspace_name_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["User"] = relationship(back_populates="workspaces")
    reports: Mapped[list["ResearchReport"]] = relationship(back_populates="workspace")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "id", name="uq_documents_owner_id"),
        CheckConstraint(
            "length(trim(original_filename)) > 0",
            name="chk_document_filename_not_empty",
        ),
        CheckConstraint(
            "length(trim(storage_key)) > 0", name="chk_document_storage_key_not_empty"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class WorkspaceDocument(Base):
    __tablename__ = "workspace_documents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["owner_user_id", "workspace_id"],
            ["workspaces.owner_user_id", "workspaces.id"],
            name="fk_workspace_documents_workspace_owner",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["owner_user_id", "document_id"],
            ["documents.owner_user_id", "documents.id"],
            name="fk_workspace_documents_document_owner",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "owner_user_id",
            "workspace_id",
            "document_id",
            name="uq_workspace_documents_membership",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    workspace_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EmbeddingConfiguration(Base):
    __tablename__ = "embedding_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(
        CheckConstraint("provider ~ '[^[:space:]]'", name="chk_provider_not_empty"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        CheckConstraint(
            "model_name ~ '[^[:space:]]'", name="chk_model_name_not_empty"
        ),
        nullable=False,
    )
    model_version: Mapped[str | None] = mapped_column(nullable=True)
    dimensions: Mapped[int] = mapped_column(
        CheckConstraint("dimensions > 0", name="chk_dimensions_positive"),
        nullable=False,
    )
    normalization: Mapped[str] = mapped_column(
        CheckConstraint(
            "normalization IN ('none', 'l2')", name="chk_normalization_valid"
        ),
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

    chunk_embeddings: Mapped[list["ChunkEmbedding"]] = relationship(
        back_populates="configuration"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunks_document_index"
        ),
        CheckConstraint(
            "chunk_index >= 0", name="chk_document_chunk_index_nonnegative"
        ),
        CheckConstraint(
            "page_start > 0", name="chk_document_chunk_page_start_positive"
        ),
        CheckConstraint("page_end >= page_start", name="chk_document_chunk_page_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")
    embeddings: Mapped[list["ChunkEmbedding"]] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "document_chunk_id",
            "embedding_configuration_id",
            name="uq_chunk_embeddings_chunk_configuration",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_chunk_id: Mapped[int] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    embedding_configuration_id: Mapped[int] = mapped_column(
        ForeignKey("embedding_configurations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunk: Mapped["DocumentChunk"] = relationship(back_populates="embeddings")
    configuration: Mapped["EmbeddingConfiguration"] = relationship(
        back_populates="chunk_embeddings"
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="chk_report_title_not_empty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="reports")
