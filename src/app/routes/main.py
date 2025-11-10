from flask import Blueprint, jsonify
from src.app import db  # ✅ Правильный импорт

main_bp = Blueprint('main', __name__)

@main_bp.route('/schedule', methods=['GET'])
def get_schedule():
    """Возвращает расписание."""
    return jsonify([])