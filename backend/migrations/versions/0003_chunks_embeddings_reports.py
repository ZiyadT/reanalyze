"""Add document chunks, chunk embeddings, and saved research reports.

Revision ID: 0003_chunks_embeddings_reports
Revises: 0002_users_workspaces_documents
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0003_chunks_embeddings_reports"
down_revision = "0002_users_workspaces_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunks_document_index"
        ),
        sa.CheckConstraint(
            "chunk_index >= 0", name="chk_document_chunk_index_nonnegative"
        ),
        sa.CheckConstraint(
            "page_start > 0", name="chk_document_chunk_page_start_positive"
        ),
        sa.CheckConstraint(
            "page_end >= page_start", name="chk_document_chunk_page_range"
        ),
    )
    op.create_index(
        "ix_document_chunks_document_id", "document_chunks", ["document_id"]
    )

    op.create_table(
        "chunk_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_chunk_id", sa.Integer(), nullable=False),
        sa.Column("embedding_configuration_id", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_chunk_id"], ["document_chunks.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["embedding_configuration_id"],
            ["embedding_configurations.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "document_chunk_id",
            "embedding_configuration_id",
            name="uq_chunk_embeddings_chunk_configuration",
        ),
    )
    op.create_index(
        "ix_chunk_embeddings_document_chunk_id",
        "chunk_embeddings",
        ["document_chunk_id"],
    )
    op.create_index(
        "ix_chunk_embeddings_embedding_configuration_id",
        "chunk_embeddings",
        ["embedding_configuration_id"],
    )
    op.execute(
        """
        CREATE FUNCTION validate_chunk_embedding_dimensions()
        RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
            expected_dimensions integer;
        BEGIN
            SELECT dimensions
            INTO expected_dimensions
            FROM embedding_configurations
            WHERE id = NEW.embedding_configuration_id;

            IF expected_dimensions IS NULL THEN
                RAISE EXCEPTION 'Embedding configuration % does not exist',
                    NEW.embedding_configuration_id;
            END IF;

            IF vector_dims(NEW.embedding) <> expected_dimensions THEN
                RAISE EXCEPTION
                    'Embedding has % dimensions; configuration % requires %',
                    vector_dims(NEW.embedding),
                    NEW.embedding_configuration_id,
                    expected_dimensions;
            END IF;

            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER chunk_embedding_dimensions_valid
        BEFORE INSERT OR UPDATE OF embedding, embedding_configuration_id
        ON chunk_embeddings
        FOR EACH ROW EXECUTE FUNCTION validate_chunk_embedding_dimensions()
        """
    )

    op.create_table(
        "research_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("report_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "length(trim(title)) > 0", name="chk_report_title_not_empty"
        ),
    )
    op.create_index(
        "ix_research_reports_workspace_id", "research_reports", ["workspace_id"]
    )


def downgrade() -> None:
    op.drop_table("research_reports")
    op.execute("DROP TRIGGER chunk_embedding_dimensions_valid ON chunk_embeddings")
    op.execute("DROP FUNCTION validate_chunk_embedding_dimensions()")
    op.drop_table("chunk_embeddings")
    op.drop_table("document_chunks")
