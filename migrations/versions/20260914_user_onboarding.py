"""Registra a conclusão do guia inicial por usuário.

Revision ID: 20260914guide
Revises: 20260912mono
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa


revision = "20260914guide"
down_revision = "20260912mono"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "onboarding_completed_at" not in columns:
        op.add_column("users", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "onboarding_completed_at" in columns:
        op.drop_column("users", "onboarding_completed_at")
