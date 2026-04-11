from __future__ import annotations

from flask import Blueprint, jsonify, request

from src.app.keycloak_auth import roles_required
from src.app.services.schedule_generator_service import (
    ScheduleGenerationError,
    ScheduleGeneratorService,
)

schedule_generation_bp = Blueprint('schedule_generation', __name__)


@schedule_generation_bp.get('/preview')
@roles_required('manager', 'admin')
def preview_schedule():
    academic_year = request.args.get('academic_year')
    min_group_size = request.args.get('min_group_size', type=int)

    if not academic_year:
        return jsonify({'error': 'academic_year is required'}), 400

    try:
        result = ScheduleGeneratorService.preview(
            academic_year=academic_year,
            min_group_size=min_group_size,
        )
        return jsonify(result), 200
    except ScheduleGenerationError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': f'Unexpected error: {exc}'}), 500


@schedule_generation_bp.get('/buckets')
@roles_required('manager', 'admin')
def debug_buckets():
    academic_year = request.args.get('academic_year')
    if not academic_year:
        return jsonify({'error': 'academic_year is required'}), 400

    try:
        result = ScheduleGeneratorService.bucket_debug(academic_year=academic_year)
        return jsonify(result), 200
    except ScheduleGenerationError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': f'Unexpected error: {exc}'}), 500


@schedule_generation_bp.post('/generate')
@roles_required('manager', 'admin')
def generate_schedule():
    payload = request.get_json(silent=True) or {}
    academic_year = payload.get('academic_year')
    min_group_size = payload.get('min_group_size')

    if not academic_year:
        return jsonify({'error': 'academic_year is required'}), 400

    try:
        result = ScheduleGeneratorService.generate(
            academic_year=academic_year,
            min_group_size=min_group_size,
        )
        return jsonify(result), 201
    except ScheduleGenerationError as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'error': f'Unexpected error: {exc}'}), 500