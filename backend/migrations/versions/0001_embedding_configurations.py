"""Create immutable embedding configurations.

Revision ID: 0001_embedding_configurations
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_embedding_configurations"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "embedding_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=True),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("normalization", sa.String(), nullable=False),
        sa.Column("similarity_metric", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("provider ~ '[^[:space:]]'", name="chk_provider_not_empty"),
        sa.CheckConstraint(
            "model_name ~ '[^[:space:]]'", name="chk_model_name_not_empty"
        ),
        sa.CheckConstraint("dimensions > 0", name="chk_dimensions_positive"),
        sa.CheckConstraint(
            "normalization IN ('none', 'l2')", name="chk_normalization_valid"
        ),
        sa.CheckConstraint(
            "similarity_metric IN ('cosine', 'dot_product', 'euclidean')",
            name="chk_similarity_metric_valid",
        ),
    )
    op.execute(
        """
        CREATE FUNCTION prevent_embedding_configuration_update()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Embedding configurations are immutable; create a new configuration';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER embedding_configuration_immutable
        BEFORE UPDATE ON embedding_configurations
        FOR EACH ROW EXECUTE FUNCTION prevent_embedding_configuration_update()
        """
    )


def downgrade() -> None:
    op.drop_table("embedding_configurations")
    op.execute("DROP FUNCTION prevent_embedding_configuration_update()")
