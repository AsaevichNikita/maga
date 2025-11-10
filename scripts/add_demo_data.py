"""Add schedule_slot_id to course_registrations

Revision ID: abc123def456
Revises: previous_revision_id
Create Date: 2025-10-03 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abc123def456'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Добавляем колонку
    op.add_column(
        'course_registrations',
        sa.Column('schedule_slot_id', sa.Integer(), nullable=True)
    )
    
    # 2. Добавляем внешний ключ на schedule_slots
    op.create_foreign_key(
        'fk_course_registrations_schedule_slot',
        'course_registrations', 'schedule_slots',
        ['schedule_slot_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Откат — удаляем внешний ключ и колонку
    op.drop_constraint('fk_course_registrations_schedule_slot', 'course_registrations', type_='foreignkey')
    op.drop_column('course_registrations', 'schedule_slot_id')
