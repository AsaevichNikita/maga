from flask import Blueprint, jsonify
from src.app import db  # ✅ Правильный импорт

main_bp = Blueprint('main', __name__)

@main_bp.route('/schedule', methods=['GET'])
def get_schedule():
    """Возвращает расписание."""
    return jsonify([])
@main_bp.get("/")
def api_root():
    return jsonify({
        "service": "schedule-system",
        "status": "ok",
        "api_prefix": "/api"
    })

@main_bp.get("/health")
def api_health():
    return jsonify({"status": "ok"})