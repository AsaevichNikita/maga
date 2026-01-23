"""add course_teachers and refactor teacher relation

Revision ID: dcb753e9a846
Revises: ce31c60401ae
Create Date: 2025-11-10 22:20:46.640611

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcb753e9a846'
down_revision: Union[str, Sequence[str], None] = 'ce31c60401ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### Drop old table if exists ###
    op.drop_table('course_teachers')

    # ### Add teacher_id to courses ###
    op.add_column('courses', sa.Column('teacher_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'courses', 'teachers', ['teacher_id'], ['id'], ondelete='SET NULL')

    # ### Add teacher_id to schedule_slots safely ###
    op.add_column('schedule_slots', sa.Column('teacher_id', sa.Integer(), nullable=True))  # Сначала nullable
    op.create_foreign_key(None, 'schedule_slots', 'teachers', ['teacher_id'], ['id'], ondelete='CASCADE')

    # Заполняем существующие строки дефолтным teacher_id = 1 (или NULL, если хотите оставить)
    op.execute("UPDATE schedule_slots SET teacher_id = 1 WHERE teacher_id IS NULL")

    # После этого можно сделать NOT NULL
    op.alter_column('schedule_slots', 'teacher_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # ### Remove teacher_id from schedule_slots ###
    op.drop_constraint(None, 'schedule_slots', type_='foreignkey')
    op.drop_column('schedule_slots', 'teacher_id')

    # ### Remove teacher_id from courses ###
    op.drop_constraint(None, 'courses', type_='foreignkey')
    op.drop_column('courses', 'teacher_id')

    # ### Recreate course_teachers table ###
    op.create_table(
        'course_teachers',
        sa.Column('course_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('teacher_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('course_teachers_course_id_fkey'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], name=op.f('course_teachers_teacher_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('course_id', 'teacher_id', name=op.f('course_teachers_pkey'))
    )

