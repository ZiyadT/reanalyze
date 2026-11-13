"""Add users, workspaces, documents, and workspace membership.

Revision ID: 0002_users_workspaces_documents
Revises: 0001_embedding_configurations
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_users_workspaces_documents"
down_revision = "0001_embedding_configurations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(email)) > 0", name="chk_user_email_not_empty"
        ),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.UniqueConstraint("owner_user_id", "id", name="uq_workspaces_owner_id"),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name="chk_workspace_name_not_empty"
        ),
    )
    op.create_index(
        "ix_workspaces_owner_user_id", "workspaces", ["owner_user_id"]
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.UniqueConstraint("owner_user_id", "id", name="uq_documents_owner_id"),
        sa.CheckConstraint(
            "length(trim(original_filename)) > 0",
            name="chk_document_filename_not_empty",
        ),
        sa.CheckConstraint(
            "length(trim(storage_key)) > 0",
            name="chk_document_storage_key_not_empty",
        ),
    )
    op.create_index("ix_documents_owner_user_id", "documents", ["owner_user_id"])

    op.create_table(
        "workspace_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id", "workspace_id"],
            ["workspaces.owner_user_id", "workspaces.id"],
            name="fk_workspace_documents_workspace_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id", "document_id"],
            ["documents.owner_user_id", "documents.id"],
            name="fk_workspace_documents_document_owner",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "owner_user_id",
            "workspace_id",
            "document_id",
            name="uq_workspace_documents_membership",
        ),
    )
    op.create_index(
        "ix_workspace_documents_workspace_id",
        "workspace_documents",
        ["workspace_id"],
    )
    op.create_index(
        "ix_workspace_documents_document_id",
        "workspace_documents",
        ["document_id"],
    )
    op.execute(
        """
        CREATE FUNCTION remove_workspace_documents_when_archived()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            DELETE FROM workspace_documents
            WHERE workspace_id = NEW.id;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER workspace_archive_removes_documents
        AFTER UPDATE OF archived_at ON workspaces
        FOR EACH ROW
        WHEN (OLD.archived_at IS NULL AND NEW.archived_at IS NOT NULL)
        EXECUTE FUNCTION remove_workspace_documents_when_archived()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER workspace_archive_removes_documents ON workspaces")
    op.execute("DROP FUNCTION remove_workspace_documents_when_archived()")
    op.drop_table("workspace_documents")
    op.drop_table("documents")
    op.drop_table("workspaces")
    op.drop_table("users")
