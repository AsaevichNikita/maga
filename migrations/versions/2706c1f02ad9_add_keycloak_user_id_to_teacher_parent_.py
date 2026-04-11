"""add keycloak_user_id to teacher parent assistant

Revision ID: 2706c1f02ad9
Revises: 392a16d639c2
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa

revision = '2706c1f02ad9'
down_revision = '392a16d639c2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('teachers', sa.Column('keycloak_user_id', sa.String(length=64), nullable=True))
    op.add_column('parents', sa.Column('keycloak_user_id', sa.String(length=64), nullable=True))
    op.add_column('assistants', sa.Column('keycloak_user_id', sa.String(length=64), nullable=True))

    op.create_index('ix_teachers_keycloak_user_id', 'teachers', ['keycloak_user_id'], unique=True)
    op.create_index('ix_parents_keycloak_user_id', 'parents', ['keycloak_user_id'], unique=True)
    op.create_index('ix_assistants_keycloak_user_id', 'assistants', ['keycloak_user_id'], unique=True)


def downgrade():
    op.drop_index('ix_assistants_keycloak_user_id', table_name='assistants')
    op.drop_index('ix_parents_keycloak_user_id', table_name='parents')
    op.drop_index('ix_teachers_keycloak_user_id', table_name='teachers')

    op.drop_column('assistants', 'keycloak_user_id')
    op.drop_column('parents', 'keycloak_user_id')
    op.drop_column('teachers', 'keycloak_user_id')
