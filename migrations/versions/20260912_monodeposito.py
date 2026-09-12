"""Esquema inicial monodepósito.

Revision ID: 20260912mono
Revises:
Create Date: 2026-09-12
"""
from alembic import op

from app.extensions import db
from app import models  # noqa: F401


revision = "20260912mono"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    db.metadata.create_all(bind=op.get_bind())


def downgrade():
    db.metadata.drop_all(bind=op.get_bind())
