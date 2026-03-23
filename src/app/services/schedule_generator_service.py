from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import time
from typing import Any

from sqlalchemy.orm import joinedload, selectinload

from src.app import db
from src.app.models import (
    CourseGroup,
    CourseRegistration,
    RegistrationSlotPreference,
    ScheduleSlot,
    TeacherOfferingSlot,
    parse_academic_year,
)


@dataclass(frozen=True)
class BucketKey:
    course_id: int
    academic_year_start: int
    academic_year_end: int
    day_of_week: int
    start_time: time
    end_time: time

    @property
    def academic_year(self) -> str:
        return f'{self.academic_year_start}/{self.academic_year_end}'

    def as_dict(self) -> dict[str, Any]:
        return {
            'course_id': self.course_id,
            'academic_year': self.academic_year,
            'academic_year_start': self.academic_year_start,
            'academic_year_end': self.academic_year_end,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
        }


@dataclass
class SlotChoice:
    bucket_key: BucketKey
    priority: int
    slot_ids: set[int] = field(default_factory=set)


@dataclass
class RegistrationState:
    registration: CourseRegistration
    bucket_choices: dict[BucketKey, SlotChoice]
    rigid: bool
    level: int
    assigned_slot_id: int | None = None
    assignment_reason: str | None = None

    @property
    def registration_id(self) -> int:
        return self.registration.id

    @property
    def student_id(self) -> int:
        return self.registration.student_id

    @property
    def course_id(self) -> int | None:
        return self.registration.course_id

    def best_priority_for_bucket(self, bucket_key: BucketKey) -> int:
        return self.bucket_choices[bucket_key].priority


@dataclass
class SlotState:
    slot: TeacherOfferingSlot
    capacity: int
    assigned_registration_ids: list[int] = field(default_factory=list)
    total_level: int = 0

    @property
    def remaining_capacity(self) -> int:
        return self.capacity - len(self.assigned_registration_ids)

    @property
    def assigned_count(self) -> int:
        return len(self.assigned_registration_ids)

    @property
    def average_level(self) -> float:
        if not self.assigned_registration_ids:
            return 0.0
        return self.total_level / len(self.assigned_registration_ids)


class ScheduleGenerationError(Exception):
    pass


class ScheduleGeneratorService:
    DEFAULT_MIN_GROUP_SIZE = 4

    @classmethod
    def preview(cls, academic_year: str, min_group_size: int | None = None) -> dict[str, Any]:
        return cls._run(academic_year=academic_year, persist=False, min_group_size=min_group_size)

    @classmethod
    def generate(cls, academic_year: str, min_group_size: int | None = None) -> dict[str, Any]:
        return cls._run(academic_year=academic_year, persist=True, min_group_size=min_group_size)

    @classmethod
    def bucket_debug(cls, academic_year: str) -> dict[str, Any]:
        context = cls._build_context(academic_year=academic_year)
        bucket_rows = []
        for bucket_key, bucket_data in context['bucket_ordered'].items():
            bucket_rows.append({
                **bucket_key.as_dict(),
                'course_name': bucket_data['course_name'],
                'slot_ids': [slot.id for slot in bucket_data['slots']],
                'teachers_count': len(bucket_data['slots']),
                'rigid_count': bucket_data['rigid_count'],
                'total_demand': bucket_data['total_demand'],
                'demand_per_teacher': bucket_data['demand_per_teacher'],
                'registrations': bucket_data['registration_ids'],
            })
        return {
            'academic_year': context['academic_year_label'],
            'academic_year_start': context['academic_year_start'],
            'academic_year_end': context['academic_year_end'],
            'buckets': bucket_rows,
        }

    @classmethod
    def _run(cls, academic_year: str, persist: bool, min_group_size: int | None) -> dict[str, Any]:
        min_group_size = max(1, min_group_size or cls.DEFAULT_MIN_GROUP_SIZE)
        context = cls._build_context(academic_year=academic_year)

        if persist and context['existing_generated_groups_count'] > 0:
            raise ScheduleGenerationError(
                'В этом учебном году уже есть автосгенерированные группы. '
                'Сначала очистите их вручную или запускайте preview.'
            )

        simulation = cls._simulate(
            academic_year=context['academic_year_label'],
            registration_states=context['registration_states'],
            slot_states=context['slot_states'],
            bucket_ordered=context['bucket_ordered'],
            min_group_size=min_group_size,
        )

        if persist:
            cls._persist_simulation(
                academic_year_start=context['academic_year_start'],
                academic_year_end=context['academic_year_end'],
                simulation=simulation,
                registration_states=context['registration_state_map'],
                slot_states=context['slot_states'],
            )

        return {
            'academic_year': context['academic_year_label'],
            'persisted': persist,
            'min_group_size': min_group_size,
            **simulation,
        }

    @classmethod
    def _build_context(cls, academic_year: str) -> dict[str, Any]:
        academic_year_start, academic_year_end = parse_academic_year(academic_year)
        academic_year_label = f'{academic_year_start}/{academic_year_end}'

        active_slots = (
            TeacherOfferingSlot.query.options(
                joinedload(TeacherOfferingSlot.teacher),
                joinedload(TeacherOfferingSlot.course),
                joinedload(TeacherOfferingSlot.classroom),
            )
            .filter(
                TeacherOfferingSlot.academic_year_start == academic_year_start,
                TeacherOfferingSlot.academic_year_end == academic_year_end,
                TeacherOfferingSlot.is_active.is_(True),
            )
            .all()
        )

        if not active_slots:
            raise ScheduleGenerationError('Для указанного учебного года нет активных teacher offering slots.')

        cls._validate_offering_slots(active_slots)

        active_slot_ids = {slot.id for slot in active_slots}
        slot_states = {
            slot.id: SlotState(slot=slot, capacity=cls._effective_slot_capacity(slot))
            for slot in active_slots
        }

        registrations = (
            CourseRegistration.query.options(
                joinedload(CourseRegistration.student),
                joinedload(CourseRegistration.course),
                selectinload(CourseRegistration.slot_preferences)
                .joinedload(RegistrationSlotPreference.offering_slot)
                .joinedload(TeacherOfferingSlot.teacher),
                selectinload(CourseRegistration.slot_preferences)
                .joinedload(RegistrationSlotPreference.offering_slot)
                .joinedload(TeacherOfferingSlot.course),
                selectinload(CourseRegistration.slot_preferences)
                .joinedload(RegistrationSlotPreference.offering_slot)
                .joinedload(TeacherOfferingSlot.classroom),
            )
            .filter(CourseRegistration.status == 'pending')
            .all()
        )

        registration_states: list[RegistrationState] = []
        registration_state_map: dict[int, RegistrationState] = {}
        registration_ids_by_bucket: dict[BucketKey, list[int]] = defaultdict(list)
        rigid_count_by_bucket: dict[BucketKey, int] = defaultdict(int)
        bucket_slots: dict[BucketKey, list[TeacherOfferingSlot]] = defaultdict(list)
        seen_slot_ids_by_bucket: dict[BucketKey, set[int]] = defaultdict(set)
        course_names: dict[int, str] = {}

        for slot in active_slots:
            bucket_key = cls._bucket_key(slot)
            if slot.id not in seen_slot_ids_by_bucket[bucket_key]:
                bucket_slots[bucket_key].append(slot)
                seen_slot_ids_by_bucket[bucket_key].add(slot.id)
            course_names[slot.course_id] = slot.course.name if slot.course else f'Course #{slot.course_id}'

        skipped_registrations = []
        for registration in registrations:
            bucket_choices: dict[BucketKey, SlotChoice] = {}
            for pref in registration.slot_preferences:
                slot = pref.offering_slot
                if not slot or slot.id not in active_slot_ids or not slot.is_active:
                    continue

                if (
                    slot.academic_year_start != academic_year_start
                    or slot.academic_year_end != academic_year_end
                ):
                    continue

                bucket_key = cls._bucket_key(slot)
                if bucket_key not in bucket_choices:
                    bucket_choices[bucket_key] = SlotChoice(
                        bucket_key=bucket_key,
                        priority=pref.priority,
                        slot_ids={slot.id},
                    )
                else:
                    bucket_choices[bucket_key].priority = min(bucket_choices[bucket_key].priority, pref.priority)
                    bucket_choices[bucket_key].slot_ids.add(slot.id)

            if not bucket_choices:
                skipped_registrations.append({
                    'registration_id': registration.id,
                    'student_id': registration.student_id,
                    'reason': 'У заявки нет активных slot preferences в указанном учебном году.',
                })
                continue

            rigid = len(bucket_choices) == 1
            state = RegistrationState(
                registration=registration,
                bucket_choices=bucket_choices,
                rigid=rigid,
                level=registration.level or 0,
            )
            registration_states.append(state)
            registration_state_map[registration.id] = state

            for bucket_key in bucket_choices:
                registration_ids_by_bucket[bucket_key].append(registration.id)
                if rigid:
                    rigid_count_by_bucket[bucket_key] += 1

        if not registration_states:
            raise ScheduleGenerationError('Нет pending-заявок с активными slot preferences для указанного года.')

        bucket_ordered_items = []
        for bucket_key, slots in bucket_slots.items():
            teachers_count = len(slots)
            total_demand = len(registration_ids_by_bucket.get(bucket_key, []))
            demand_per_teacher = total_demand / teachers_count if teachers_count else 0
            bucket_ordered_items.append((
                bucket_key,
                {
                    'slots': sorted(slots, key=lambda s: (s.priority, s.id)),
                    'teachers_count': teachers_count,
                    'rigid_count': rigid_count_by_bucket.get(bucket_key, 0),
                    'total_demand': total_demand,
                    'demand_per_teacher': round(demand_per_teacher, 4),
                    'registration_ids': registration_ids_by_bucket.get(bucket_key, []),
                    'course_name': course_names.get(bucket_key.course_id, f'Course #{bucket_key.course_id}'),
                }
            ))

        bucket_ordered_items.sort(
            key=lambda item: (
                -item[1]['rigid_count'],
                -item[1]['demand_per_teacher'],
                -item[1]['total_demand'],
                item[0].course_id,
                item[0].day_of_week,
                item[0].start_time,
            )
        )

        existing_generated_groups_count = (
            CourseGroup.query.filter(
                CourseGroup.academic_year_start == academic_year_start,
                CourseGroup.academic_year_end == academic_year_end,
                CourseGroup.source_offering_slot_id.isnot(None),
            ).count()
        )

        return {
            'academic_year_label': academic_year_label,
            'academic_year_start': academic_year_start,
            'academic_year_end': academic_year_end,
            'registration_states': registration_states,
            'registration_state_map': registration_state_map,
            'slot_states': slot_states,
            'bucket_ordered': dict(bucket_ordered_items),
            'skipped_registrations': skipped_registrations,
            'existing_generated_groups_count': existing_generated_groups_count,
        }

    @classmethod
    def _simulate(
        cls,
        academic_year: str,
        registration_states: list[RegistrationState],
        slot_states: dict[int, SlotState],
        bucket_ordered: dict[BucketKey, dict[str, Any]],
        min_group_size: int,
    ) -> dict[str, Any]:
        state_map = {state.registration_id: state for state in registration_states}
        student_assignments: dict[int, list[dict[str, Any]]] = defaultdict(list)
        bucket_report: list[dict[str, Any]] = []

        for bucket_key, bucket_meta in bucket_ordered.items():
            candidate_states = [
                state_map[reg_id]
                for reg_id in bucket_meta['registration_ids']
                if state_map[reg_id].assigned_slot_id is None
            ]

            rigid_queue = [state for state in candidate_states if state.rigid]
            flex_queue = [state for state in candidate_states if not state.rigid]

            sort_key = lambda state: (
                state.best_priority_for_bucket(bucket_key),
                -state.level,
                state.registration_id,
            )
            rigid_queue.sort(key=sort_key)
            flex_queue.sort(key=sort_key)

            bucket_assigned = []
            bucket_rejected = []

            for queue_name, queue in (('rigid', rigid_queue), ('flex', flex_queue)):
                for state in queue:
                    if cls._has_time_conflict(student_assignments[state.student_id], bucket_key):
                        bucket_rejected.append({
                            'registration_id': state.registration_id,
                            'student_id': state.student_id,
                            'reason': 'Конфликт по времени с другим уже назначенным курсом',
                            'queue': queue_name,
                        })
                        continue

                    chosen_slot_id = cls._pick_best_slot(state, bucket_key, slot_states)
                    if chosen_slot_id is None:
                        bucket_rejected.append({
                            'registration_id': state.registration_id,
                            'student_id': state.student_id,
                            'reason': 'Во всех выбранных слотах этого временного окна закончились места',
                            'queue': queue_name,
                        })
                        continue

                    state.assigned_slot_id = chosen_slot_id
                    state.assignment_reason = f'assigned_from_{queue_name}_queue'
                    slot_state = slot_states[chosen_slot_id]
                    slot_state.assigned_registration_ids.append(state.registration_id)
                    slot_state.total_level += state.level

                    student_assignments[state.student_id].append({
                        'registration_id': state.registration_id,
                        'slot_id': chosen_slot_id,
                        'day_of_week': bucket_key.day_of_week,
                        'start_time': bucket_key.start_time,
                        'end_time': bucket_key.end_time,
                    })
                    bucket_assigned.append({
                        'registration_id': state.registration_id,
                        'student_id': state.student_id,
                        'slot_id': chosen_slot_id,
                        'queue': queue_name,
                    })

            bucket_report.append({
                **bucket_key.as_dict(),
                'course_name': bucket_meta['course_name'],
                'rigid_count': bucket_meta['rigid_count'],
                'total_demand': bucket_meta['total_demand'],
                'demand_per_teacher': bucket_meta['demand_per_teacher'],
                'assigned': bucket_assigned,
                'rejected_in_bucket': bucket_rejected,
            })

        warnings = []
        cls._rebalance_underfilled_slots(
            registration_states=registration_states,
            slot_states=slot_states,
            student_assignments=student_assignments,
            min_group_size=min_group_size,
            warnings=warnings,
        )

        assigned_rows = []
        unassigned_rows = []
        by_course = defaultdict(lambda: {'assigned': 0, 'unassigned': 0})

        for state in sorted(registration_states, key=lambda s: s.registration_id):
            if state.assigned_slot_id is None:
                reason = cls._build_unassigned_reason(state, slot_states, student_assignments)
                unassigned_rows.append({
                    'registration_id': state.registration_id,
                    'student_id': state.student_id,
                    'student_name': cls._student_name(state.registration),
                    'course_id': state.course_id,
                    'course_name': state.registration.course.name if state.registration.course else None,
                    'level': state.level,
                    'reason': reason,
                })
                by_course[state.course_id]['unassigned'] += 1
                continue

            slot_state = slot_states[state.assigned_slot_id]
            assigned_rows.append({
                'registration_id': state.registration_id,
                'student_id': state.student_id,
                'student_name': cls._student_name(state.registration),
                'course_id': state.course_id,
                'course_name': state.registration.course.name if state.registration.course else None,
                'level': state.level,
                'slot_id': slot_state.slot.id,
                'teacher_id': slot_state.slot.teacher_id,
                'teacher_name': cls._teacher_name(slot_state.slot),
                'classroom_id': slot_state.slot.classroom_id,
                'classroom_name': slot_state.slot.classroom.name if slot_state.slot.classroom else None,
                'day_of_week': slot_state.slot.day_of_week,
                'start_time': slot_state.slot.start_time.strftime('%H:%M'),
                'end_time': slot_state.slot.end_time.strftime('%H:%M'),
                'assignment_reason': state.assignment_reason,
            })
            by_course[state.course_id]['assigned'] += 1

        group_previews = []
        for slot_id, slot_state in sorted(slot_states.items(), key=lambda item: item[0]):
            if not slot_state.assigned_registration_ids:
                continue

            levels = [state_map[reg_id].level for reg_id in slot_state.assigned_registration_ids]
            group_previews.append({
                'slot_id': slot_id,
                'course_id': slot_state.slot.course_id,
                'course_name': slot_state.slot.course.name if slot_state.slot.course else None,
                'teacher_id': slot_state.slot.teacher_id,
                'teacher_name': cls._teacher_name(slot_state.slot),
                'classroom_id': slot_state.slot.classroom_id,
                'classroom_name': slot_state.slot.classroom.name if slot_state.slot.classroom else None,
                'day_of_week': slot_state.slot.day_of_week,
                'start_time': slot_state.slot.start_time.strftime('%H:%M'),
                'end_time': slot_state.slot.end_time.strftime('%H:%M'),
                'capacity': slot_state.capacity,
                'assigned_count': slot_state.assigned_count,
                'remaining_capacity': slot_state.remaining_capacity,
                'average_level': round(sum(levels) / len(levels), 2) if levels else 0,
                'min_level_in_group': min(levels) if levels else None,
                'max_level_in_group': max(levels) if levels else None,
                'underfilled': 0 < slot_state.assigned_count < min_group_size,
                'group_name_preview': cls._build_group_name(slot_state.slot),
                'academic_year': f'{slot_state.slot.academic_year_start}/{slot_state.slot.academic_year_end}',
                'registration_ids': list(slot_state.assigned_registration_ids),
            })

        totals = {
            'total_registrations_in_scope': len(registration_states),
            'assigned': len(assigned_rows),
            'unassigned': len(unassigned_rows),
            'groups_to_create': len(group_previews),
        }

        return {
            'summary': totals,
            'bucket_report': bucket_report,
            'group_previews': group_previews,
            'assigned_registrations': assigned_rows,
            'unassigned_registrations': unassigned_rows,
            'course_stats': [
                {
                    'course_id': course_id,
                    'assigned': values['assigned'],
                    'unassigned': values['unassigned'],
                }
                for course_id, values in sorted(by_course.items(), key=lambda item: (item[0] or 0))
            ],
            'warnings': warnings,
        }

    @classmethod
    def _rebalance_underfilled_slots(
        cls,
        registration_states: list[RegistrationState],
        slot_states: dict[int, SlotState],
        student_assignments: dict[int, list[dict[str, Any]]],
        min_group_size: int,
        warnings: list[dict[str, Any]],
    ) -> None:
        state_map = {state.registration_id: state for state in registration_states}
        underfilled_slot_ids = [
            slot_id
            for slot_id, slot_state in slot_states.items()
            if 0 < slot_state.assigned_count < min_group_size
        ]

        for slot_id in underfilled_slot_ids:
            slot_state = slot_states[slot_id]
            assigned_ids = list(slot_state.assigned_registration_ids)

            movable_first = sorted(
                assigned_ids,
                key=lambda reg_id: (
                    state_map[reg_id].rigid,
                    state_map[reg_id].best_priority_for_bucket(cls._bucket_key(slot_state.slot)),
                    -state_map[reg_id].level,
                )
            )

            for reg_id in movable_first:
                if slot_state.assigned_count >= min_group_size:
                    break
                state = state_map[reg_id]
                alternative_slot_id = cls._find_alternative_slot(
                    state=state,
                    current_slot_id=slot_id,
                    slot_states=slot_states,
                    student_assignments=student_assignments,
                )
                if alternative_slot_id is None:
                    continue
                cls._move_assignment(
                    state=state,
                    from_slot_id=slot_id,
                    to_slot_id=alternative_slot_id,
                    slot_states=slot_states,
                    student_assignments=student_assignments,
                )

            if 0 < slot_state.assigned_count < min_group_size:
                warnings.append({
                    'type': 'underfilled_group',
                    'slot_id': slot_id,
                    'course_id': slot_state.slot.course_id,
                    'course_name': slot_state.slot.course.name if slot_state.slot.course else None,
                    'assigned_count': slot_state.assigned_count,
                    'min_group_size': min_group_size,
                    'message': (
                        'Группа оставлена маленькой, потому что не всех детей удалось '
                        'перераспределить без потери жёстких временных предпочтений.'
                    ),
                })

    @classmethod
    def _find_alternative_slot(
        cls,
        state: RegistrationState,
        current_slot_id: int,
        slot_states: dict[int, SlotState],
        student_assignments: dict[int, list[dict[str, Any]]],
    ) -> int | None:
        current_assignment = next(
            (item for item in student_assignments[state.student_id] if item['registration_id'] == state.registration_id),
            None,
        )
        remaining_assignments = [
            item
            for item in student_assignments[state.student_id]
            if item['registration_id'] != state.registration_id
        ]

        choices = sorted(
            state.bucket_choices.values(),
            key=lambda choice: (choice.priority, choice.bucket_key.day_of_week, choice.bucket_key.start_time),
        )
        for choice in choices:
            if current_assignment and cls._same_window(current_assignment, choice.bucket_key):
                continue
            if cls._has_time_conflict(remaining_assignments, choice.bucket_key):
                continue
            temp_state = deepcopy(state)
            temp_state.assigned_slot_id = None
            temp_state.bucket_choices = {choice.bucket_key: choice}
            target_slot_id = cls._pick_best_slot(temp_state, choice.bucket_key, slot_states, excluded_slot_ids={current_slot_id})
            if target_slot_id is not None:
                return target_slot_id
        return None

    @classmethod
    def _move_assignment(
        cls,
        state: RegistrationState,
        from_slot_id: int,
        to_slot_id: int,
        slot_states: dict[int, SlotState],
        student_assignments: dict[int, list[dict[str, Any]]],
    ) -> None:
        from_slot = slot_states[from_slot_id]
        to_slot = slot_states[to_slot_id]

        from_slot.assigned_registration_ids.remove(state.registration_id)
        from_slot.total_level -= state.level

        to_slot.assigned_registration_ids.append(state.registration_id)
        to_slot.total_level += state.level
        state.assigned_slot_id = to_slot_id
        state.assignment_reason = 'rebalanced_to_avoid_tiny_group'

        for item in student_assignments[state.student_id]:
            if item['registration_id'] == state.registration_id:
                item['slot_id'] = to_slot_id
                item['day_of_week'] = to_slot.slot.day_of_week
                item['start_time'] = to_slot.slot.start_time
                item['end_time'] = to_slot.slot.end_time
                break

    @classmethod
    def _pick_best_slot(
        cls,
        state: RegistrationState,
        bucket_key: BucketKey,
        slot_states: dict[int, SlotState],
        excluded_slot_ids: set[int] | None = None,
    ) -> int | None:
        excluded_slot_ids = excluded_slot_ids or set()
        choice = state.bucket_choices.get(bucket_key)
        if not choice:
            return None

        candidates: list[tuple[Any, int]] = []
        for slot_id in choice.slot_ids:
            if slot_id in excluded_slot_ids:
                continue
            slot_state = slot_states.get(slot_id)
            if slot_state is None or slot_state.remaining_capacity <= 0:
                continue
            level_distance = abs(slot_state.average_level - state.level) if slot_state.assigned_count else 0
            fill_ratio = slot_state.assigned_count / slot_state.capacity if slot_state.capacity else 1
            score = (
                level_distance,
                fill_ratio,
                slot_state.slot.priority,
                slot_state.slot.id,
            )
            candidates.append((score, slot_id))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    @classmethod
    def _persist_simulation(
        cls,
        academic_year_start: int,
        academic_year_end: int,
        simulation: dict[str, Any],
        registration_states: dict[int, RegistrationState],
        slot_states: dict[int, SlotState],
    ) -> None:
        try:
            for group_preview in simulation['group_previews']:
                slot_state = slot_states[group_preview['slot_id']]
                slot = slot_state.slot
                levels = [
                    registration_states[reg_id].level
                    for reg_id in slot_state.assigned_registration_ids
                ]

                group = CourseGroup(
                    course_id=slot.course_id,
                    lead_teacher_id=slot.teacher_id,
                    source_offering_slot_id=slot.id,
                    name=cls._build_group_name(slot),
                    academic_year_start=academic_year_start,
                    academic_year_end=academic_year_end,
                    is_active=True,
                    min_level=min(levels) if levels else None,
                    max_level=max(levels) if levels else None,
                )
                db.session.add(group)
                db.session.flush()

                schedule_slot = ScheduleSlot(
                    group_id=group.id,
                    day_of_week=slot.day_of_week,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    classroom_id=slot.classroom_id,
                )
                db.session.add(schedule_slot)
                db.session.flush()

                for reg_id in slot_state.assigned_registration_ids:
                    reg_state = registration_states[reg_id]
                    reg_state.registration.group_id = group.id
                    reg_state.registration.preferred_slot_id = schedule_slot.id
                    reg_state.registration.status = 'approved'

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def _validate_offering_slots(cls, active_slots: list[TeacherOfferingSlot]) -> None:
        teacher_windows: dict[tuple[int, int, int, int], list[TeacherOfferingSlot]] = defaultdict(list)
        classroom_windows: dict[tuple[int, int, int, int], list[TeacherOfferingSlot]] = defaultdict(list)

        for slot in active_slots:
            if slot.start_time >= slot.end_time:
                raise ScheduleGenerationError(
                    f'Некорректный слот #{slot.id}: start_time должен быть меньше end_time.'
                )
            if slot.max_groups != 1:
                raise ScheduleGenerationError(
                    f'Слот #{slot.id} имеет max_groups={slot.max_groups}. '
                    'Текущая версия генератора поддерживает только max_groups = 1.'
                )
            teacher_windows[
                (slot.teacher_id, slot.academic_year_start, slot.academic_year_end, slot.day_of_week)
            ].append(slot)
            if slot.classroom_id:
                classroom_windows[
                    (slot.classroom_id, slot.academic_year_start, slot.academic_year_end, slot.day_of_week)
                ].append(slot)

        for key, slots in teacher_windows.items():
            cls._ensure_no_overlap(slots, entity_name=f'teacher_id={key[0]}')
        for key, slots in classroom_windows.items():
            cls._ensure_no_overlap(slots, entity_name=f'classroom_id={key[0]}')

    @classmethod
    def _ensure_no_overlap(cls, slots: list[TeacherOfferingSlot], entity_name: str) -> None:
        ordered = sorted(slots, key=lambda slot: (slot.start_time, slot.end_time, slot.id))
        for left, right in zip(ordered, ordered[1:]):
            if left.end_time > right.start_time:
                raise ScheduleGenerationError(
                    'Найдены пересекающиеся offering slots: '
                    f'{entity_name}, slot #{left.id} и slot #{right.id}.'
                )

    @classmethod
    def _effective_slot_capacity(cls, slot: TeacherOfferingSlot) -> int:
        course_capacity = slot.course.max_students if slot.course and slot.course.max_students else 0
        classroom_capacity = slot.classroom.capacity if slot.classroom else None

        if slot.course and slot.course.use_classroom_capacity and classroom_capacity:
            capacity = min(course_capacity, classroom_capacity)
        elif classroom_capacity:
            capacity = min(course_capacity, classroom_capacity)
        else:
            capacity = course_capacity

        if capacity <= 0:
            raise ScheduleGenerationError(
                f'У слота #{slot.id} вычислилась некорректная вместимость ({capacity}).'
            )
        return capacity

    @classmethod
    def _bucket_key(cls, slot: TeacherOfferingSlot) -> BucketKey:
        return BucketKey(
            course_id=slot.course_id,
            academic_year_start=slot.academic_year_start,
            academic_year_end=slot.academic_year_end,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
        )

    @classmethod
    def _has_time_conflict(cls, assignments: list[dict[str, Any]], bucket_key: BucketKey) -> bool:
        for assignment in assignments:
            if assignment['day_of_week'] != bucket_key.day_of_week:
                continue
            if assignment['start_time'] < bucket_key.end_time and bucket_key.start_time < assignment['end_time']:
                return True
        return False

    @classmethod
    def _same_window(cls, assignment: dict[str, Any], bucket_key: BucketKey) -> bool:
        return (
            assignment['day_of_week'] == bucket_key.day_of_week
            and assignment['start_time'] == bucket_key.start_time
            and assignment['end_time'] == bucket_key.end_time
        )

    @classmethod
    def _student_name(cls, registration: CourseRegistration) -> str:
        student = registration.student
        if not student:
            return f'Student #{registration.student_id}'
        return f'{student.lastname} {student.firstname} {student.surname or ""}'.strip()

    @classmethod
    def _teacher_name(cls, slot: TeacherOfferingSlot) -> str:
        teacher = slot.teacher
        if not teacher:
            return f'Teacher #{slot.teacher_id}'
        return f'{teacher.lastname} {teacher.firstname} {teacher.surname or ""}'.strip()

    @classmethod
    def _build_group_name(cls, slot: TeacherOfferingSlot) -> str:
        course_name = slot.course.name if slot.course else f'Course #{slot.course_id}'
        classroom_name = slot.classroom.name if slot.classroom else 'без аудитории'
        return (
            f'{course_name} — д{slot.day_of_week} '
            f'{slot.start_time.strftime("%H:%M")}-{slot.end_time.strftime("%H:%M")} '
            f'— {classroom_name}'
        )

    @classmethod
    def _build_unassigned_reason(
        cls,
        state: RegistrationState,
        slot_states: dict[int, SlotState],
        student_assignments: dict[int, list[dict[str, Any]]],
    ) -> str:
        choices = sorted(
            state.bucket_choices.values(),
            key=lambda choice: (choice.priority, choice.bucket_key.day_of_week, choice.bucket_key.start_time),
        )

        reasons = []
        other_assignments = [
            item
            for item in student_assignments[state.student_id]
            if item['registration_id'] != state.registration_id
        ]
        for choice in choices:
            if cls._has_time_conflict(other_assignments, choice.bucket_key):
                reasons.append(
                    f'окно {choice.bucket_key.day_of_week} '
                    f'{choice.bucket_key.start_time.strftime("%H:%M")}-{choice.bucket_key.end_time.strftime("%H:%M")}: конфликт по времени'
                )
                continue

            remaining = sum(
                slot_states[slot_id].remaining_capacity
                for slot_id in choice.slot_ids
                if slot_id in slot_states
            )
            if remaining <= 0:
                reasons.append(
                    f'окно {choice.bucket_key.day_of_week} '
                    f'{choice.bucket_key.start_time.strftime("%H:%M")}-{choice.bucket_key.end_time.strftime("%H:%M")}: мест нет'
                )

        if not reasons:
            return 'не удалось подобрать место по доступным slot preferences'
        return '; '.join(reasons)
