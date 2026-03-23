"""add teacher offering slots and registration slot preference

Revision ID: 392a16d639c2
Revises: 07b32b4a2cef
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "392a16d639c2"
down_revision = "07b32b4a2cef"
branch_labels = None
depends_on = None


def _assert_valid_academic_years(bind, table_name: str) -> None:
    invalid_rows = bind.execute(
        text(f"""
            SELECT id, academic_year
            FROM {table_name}
            WHERE academic_year IS NULL
               OR replace(academic_year, '-', '/') !~ '^[0-9]{{4}}/[0-9]{{4}}$'
               OR split_part(replace(academic_year, '-', '/'), '/', 2)::int
                  <> split_part(replace(academic_year, '-', '/'), '/', 1)::int + 1
            ORDER BY id
            LIMIT 20
        """)
    ).fetchall()

    if invalid_rows:
        preview = ", ".join([f"id={row[0]} academic_year={row[1]!r}" for row in invalid_rows])
        raise RuntimeError(
            f"Invalid academic_year values found in {table_name}: {preview}"
        )


def upgrade():
    bind = op.get_bind()

    _assert_valid_academic_years(bind, "course_groups")
    _assert_valid_academic_years(bind, "teacher_offering_slots")

    # -------------------------
    # course_groups
    # -------------------------
    op.add_column("course_groups", sa.Column("academic_year_start", sa.Integer(), nullable=True))
    op.add_column("course_groups", sa.Column("academic_year_end", sa.Integer(), nullable=True))

    bind.execute(text("""
        UPDATE course_groups
        SET academic_year_start = split_part(replace(academic_year, '-', '/'), '/', 1)::int,
            academic_year_end   = split_part(replace(academic_year, '-', '/'), '/', 2)::int
    """))

    op.alter_column("course_groups", "academic_year_start", nullable=False)
    op.alter_column("course_groups", "academic_year_end", nullable=False)

    op.drop_constraint("uq_group_course_name_year", "course_groups", type_="unique")
    op.drop_column("course_groups", "academic_year")

    op.create_check_constraint(
        "check_group_academic_year",
        "course_groups",
        "academic_year_end = academic_year_start + 1",
    )

    op.create_unique_constraint(
        "uq_group_course_name_year",
        "course_groups",
        ["course_id", "name", "academic_year_start", "academic_year_end"],
    )

    # -------------------------
    # teacher_offering_slots
    # -------------------------
    op.add_column("teacher_offering_slots", sa.Column("academic_year_start", sa.Integer(), nullable=True))
    op.add_column("teacher_offering_slots", sa.Column("academic_year_end", sa.Integer(), nullable=True))

    bind.execute(text("""
        UPDATE teacher_offering_slots
        SET academic_year_start = split_part(replace(academic_year, '-', '/'), '/', 1)::int,
            academic_year_end   = split_part(replace(academic_year, '-', '/'), '/', 2)::int
    """))

    op.alter_column("teacher_offering_slots", "academic_year_start", nullable=False)
    op.alter_column("teacher_offering_slots", "academic_year_end", nullable=False)

    op.drop_constraint("uq_teacher_course_year_time", "teacher_offering_slots", type_="unique")
    op.drop_column("teacher_offering_slots", "academic_year")

    op.create_check_constraint(
        "check_offering_academic_year",
        "teacher_offering_slots",
        "academic_year_end = academic_year_start + 1",
    )

    op.create_check_constraint(
        "check_offering_time_range",
        "teacher_offering_slots",
        "end_time > start_time",
    )

    op.create_unique_constraint(
        "uq_teacher_course_year_time",
        "teacher_offering_slots",
        [
            "teacher_id",
            "course_id",
            "academic_year_start",
            "academic_year_end",
            "day_of_week",
            "start_time",
            "end_time",
        ],
    )

    # -------------------------
    # extra time-range checks
    # -------------------------
    op.create_check_constraint(
        "check_schedule_time_range",
        "schedule_slots",
        "end_time > start_time",
    )

    op.create_check_constraint(
        "check_reserved_time_range",
        "reserved_times",
        "end_time > start_time",
    )


def downgrade():
    bind = op.get_bind()

    # -------------------------
    # course_groups
    # -------------------------
    op.add_column("course_groups", sa.Column("academic_year", sa.String(length=9), nullable=True))

    bind.execute(text("""
        UPDATE course_groups
        SET academic_year = academic_year_start::text || '/' || academic_year_end::text
    """))

    op.alter_column("course_groups", "academic_year", nullable=False)

    op.drop_constraint("uq_group_course_name_year", "course_groups", type_="unique")
    op.drop_constraint("check_group_academic_year", "course_groups", type_="check")

    op.drop_column("course_groups", "academic_year_start")
    op.drop_column("course_groups", "academic_year_end")

    op.create_unique_constraint(
        "uq_group_course_name_year",
        "course_groups",
        ["course_id", "name", "academic_year"],
    )

    # -------------------------
    # teacher_offering_slots
    # -------------------------
    op.add_column("teacher_offering_slots", sa.Column("academic_year", sa.String(length=9), nullable=True))

    bind.execute(text("""
        UPDATE teacher_offering_slots
        SET academic_year = academic_year_start::text || '/' || academic_year_end::text
    """))

    op.alter_column("teacher_offering_slots", "academic_year", nullable=False)

    op.drop_constraint("uq_teacher_course_year_time", "teacher_offering_slots", type_="unique")
    op.drop_constraint("check_offering_academic_year", "teacher_offering_slots", type_="check")
    op.drop_constraint("check_offering_time_range", "teacher_offering_slots", type_="check")

    op.drop_column("teacher_offering_slots", "academic_year_start")
    op.drop_column("teacher_offering_slots", "academic_year_end")

    op.create_unique_constraint(
        "uq_teacher_course_year_time",
        "teacher_offering_slots",
        ["teacher_id", "course_id", "academic_year", "day_of_week", "start_time", "end_time"],
    )

    # -------------------------
    # extra time-range checks
    # -------------------------
    op.drop_constraint("check_schedule_time_range", "schedule_slots", type_="check")
    op.drop_constraint("check_reserved_time_range", "reserved_times", type_="check")
