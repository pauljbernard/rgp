"""add organizations and attach teams

Revision ID: 20260403_0024
Revises: 20260402_0023
Create Date: 2026-04-03 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260403_0024"
down_revision = "20260402_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("teams", sa.Column("organization_id", sa.String(length=64), nullable=True))

    bind = op.get_bind()
    now_expr = sa.text("CURRENT_TIMESTAMP")
    organizations = [
        ("org_curriculum", "tenant_demo", "Curriculum Programs"),
        ("org_assessment", "tenant_demo", "Assessment and Quality"),
        ("org_operations", "tenant_demo", "Platform Operations"),
    ]
    for org_id, tenant_id, name in organizations:
        bind.execute(
            sa.text(
                "INSERT INTO organizations (id, tenant_id, name, status, created_at, updated_at) "
                "VALUES (:id, :tenant_id, :name, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"id": org_id, "tenant_id": tenant_id, "name": name},
        )

    team_map = {
        "team_curriculum_science": "org_curriculum",
        "team_curriculum": "org_curriculum",
        "team_science": "org_curriculum",
        "team_literacy": "org_curriculum",
        "team_assessment_quality": "org_assessment",
        "team_assessment": "org_assessment",
        "team_ops": "org_operations",
        "team_delivery_ops": "org_operations",
    }
    for team_id, organization_id in team_map.items():
        bind.execute(
            sa.text("UPDATE teams SET organization_id = :organization_id WHERE id = :team_id"),
            {"organization_id": organization_id, "team_id": team_id},
        )

    bind.execute(
        sa.text(
            "UPDATE teams SET organization_id = 'org_operations' WHERE organization_id IS NULL"
        )
    )

    templates = sa.table(
        "templates",
        sa.column("id", sa.String()),
        sa.column("version", sa.String()),
        sa.column("schema", sa.JSON()),
    )
    current_schema = bind.execute(
        sa.select(templates.c.schema).where(
            templates.c.id == "tmpl_user_registration",
            templates.c.version == "1.0.0",
        )
    ).scalar_one_or_none()
    if isinstance(current_schema, dict):
        updated_schema = dict(current_schema)
        properties = dict(updated_schema.get("properties") or {})
        properties.pop("organization", None)
        properties["organization_id"] = {
            "type": "string",
            "title": "Organization",
            "pattern": r"org_[A-Za-z0-9_-]+$",
        }
        updated_schema["properties"] = properties
        updated_schema["required"] = [
            "display_name",
            "email",
            "organization_id",
            "job_title",
            "requested_team_id",
            "business_justification",
        ]
        bind.execute(
            sa.update(templates)
            .where(
                templates.c.id == "tmpl_user_registration",
                templates.c.version == "1.0.0",
            )
            .values(schema=updated_schema)
        )

    with op.batch_alter_table("teams") as batch_op:
        batch_op.alter_column("organization_id", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("teams") as batch_op:
        batch_op.drop_column("organization_id")
    op.drop_table("organizations")
