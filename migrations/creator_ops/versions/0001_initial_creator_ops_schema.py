"""Initial Creator Operations Schema

Revision ID: 0001
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create accounts table
    op.create_table(
        "creator_ops_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("platform_id", sa.String(length=255), nullable=False),
        sa.Column("oauth_scopes", sa.Text(), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=True),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_accounts_id"), "creator_ops_accounts", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_tenant_workspace_platform_handle", "creator_ops_accounts", ["tenant", "workspace", "platform", "handle"]
    )
    op.create_unique_constraint(
        "uq_tenant_workspace_platform_id", "creator_ops_accounts", ["tenant", "workspace", "platform", "platform_id"]
    )

    # Create media table
    op.create_table(
        "creator_ops_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("media_type", sa.String(length=50), nullable=False),
        sa.Column("platform_id", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_processed", sa.Boolean(), nullable=True),
        sa.Column("processing_status", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["creator_ops_accounts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_media_id"), "creator_ops_media", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_media_platform_id", "creator_ops_media", ["tenant", "workspace", "platform", "platform_id"]
    )

    # Create units table
    op.create_table(
        "creator_ops_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.Column("unit_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("start_time_seconds", sa.Integer(), nullable=True),
        sa.Column("end_time_seconds", sa.Integer(), nullable=True),
        sa.Column("speakers", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("transcript_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("nlp_analysis", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["creator_ops_media.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_units_id"), "creator_ops_units", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_unit_media_type_time",
        "creator_ops_units",
        ["tenant", "workspace", "media_id", "unit_type", "start_time_seconds"],
    )

    # Create interactions table
    op.create_table(
        "creator_ops_interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=True),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("interaction_type", sa.String(length=50), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("platform_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["creator_ops_media.id"],
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["creator_ops_units.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_interactions_id"), "creator_ops_interactions", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_interaction_platform_id", "creator_ops_interactions", ["tenant", "workspace", "platform", "platform_id"]
    )

    # Create people table
    op.create_table(
        "creator_ops_people",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("person_type", sa.String(length=50), nullable=False),
        sa.Column("platform_handles", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("profile_image_url", sa.String(length=1000), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_people_id"), "creator_ops_people", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_person_name_type", "creator_ops_people", ["tenant", "workspace", "name", "person_type"]
    )

    # Create topics table
    op.create_table(
        "creator_ops_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("topic_type", sa.String(length=50), nullable=False),
        sa.Column("text", sa.String(length=500), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("start_time_seconds", sa.Integer(), nullable=True),
        sa.Column("end_time_seconds", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["creator_ops_units.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_topics_id"), "creator_ops_topics", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_topic_unit_type_text", "creator_ops_topics", ["tenant", "workspace", "unit_id", "topic_type", "text"]
    )

    # Create claims table
    op.create_table(
        "creator_ops_claims",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("stance", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("uncertainty", sa.Integer(), nullable=True),
        sa.Column("sources", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("fact_check_status", sa.String(length=50), nullable=True),
        sa.Column("start_time_seconds", sa.Integer(), nullable=True),
        sa.Column("end_time_seconds", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["creator_ops_units.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_claims_id"), "creator_ops_claims", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_claim_unit_text", "creator_ops_claims", ["tenant", "workspace", "unit_id", "claim_text"]
    )

    # Create embeddings table
    op.create_table(
        "creator_ops_embeddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant", sa.String(length=255), nullable=False),
        sa.Column("workspace", sa.String(length=255), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("vector_id", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("embedding_type", sa.String(length=50), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["unit_id"],
            ["creator_ops_units.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_creator_ops_embeddings_id"), "creator_ops_embeddings", ["id"], unique=False)
    op.create_unique_constraint(
        "uq_embedding_unit_type", "creator_ops_embeddings", ["tenant", "workspace", "unit_id", "embedding_type"]
    )
    op.create_unique_constraint(
        "uq_embedding_vector_id", "creator_ops_embeddings", ["tenant", "workspace", "vector_id"]
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("creator_ops_embeddings")
    op.drop_table("creator_ops_claims")
    op.drop_table("creator_ops_topics")
    op.drop_table("creator_ops_people")
    op.drop_table("creator_ops_interactions")
    op.drop_table("creator_ops_units")
    op.drop_table("creator_ops_media")
    op.drop_table("creator_ops_accounts")
