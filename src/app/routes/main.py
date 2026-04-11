from flask import Blueprint, g, jsonify

from src.app import db
from src.app.current_user import get_current_assistant, get_current_parent, get_current_teacher
from src.app.keycloak_auth import keycloak_required, roles_required
from src.app.models import Assistant, Parent, Teacher


main_bp = Blueprint("main", __name__)


@main_bp.route('/schedule', methods=['GET'])
def get_schedule():
    return jsonify([])


@main_bp.get("/")
def api_root():
    return jsonify({
        "service": "schedule-system",
        "status": "ok",
        "api_prefix": "/api",
    })


@main_bp.get("/health")
def api_health():
    return jsonify({"status": "ok"})


@main_bp.get("/me")
@keycloak_required
def me():
    return jsonify({
        "status": "ok",
        "user": g.keycloak_user,
    })


@main_bp.get("/manager-only")
@roles_required("manager", "admin")
def manager_only():
    return jsonify({
        "status": "ok",
        "message": "Access granted for manager/admin",
        "user": g.keycloak_user,
    })


@main_bp.get("/teacher-only")
@roles_required("teacher", "admin")
def teacher_only():
    return jsonify({
        "status": "ok",
        "message": "Access granted for teacher/admin",
        "user": g.keycloak_user,
    })


def _normalized_email(value):
    return (value or "").strip().lower()


def _has_any_role(*roles):
    current_roles = set(g.keycloak_roles or [])
    return bool(current_roles.intersection(set(roles)))


def _ensure_can_link_personal_account(entity_email: str | None, self_role: str):
    if _has_any_role("admin", "manager"):
        return None

    if not _has_any_role(self_role):
        return jsonify({
            "error": "Forbidden",
            "message": f"Only admin/manager or the same authenticated {self_role} can link this account",
        }), 403

    token_email = _normalized_email((g.keycloak_user or {}).get("email"))
    target_email = _normalized_email(entity_email)

    if not token_email or not target_email:
        return jsonify({
            "error": "Forbidden",
            "message": "Self-link requires matching email in both Keycloak token and domain profile",
        }), 403

    if token_email != target_email:
        return jsonify({
            "error": "Forbidden",
            "message": "You can only link your own profile",
            "token_email": token_email,
            "target_email": target_email,
        }), 403

    return None


@main_bp.post("/link/teacher/<int:teacher_id>")
@roles_required("admin", "manager", "teacher")
def link_teacher_account(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found"}), 404

    permission_error = _ensure_can_link_personal_account(teacher.email, "teacher")
    if permission_error:
        return permission_error

    subject = g.keycloak_user.get("sub")
    if not subject:
        return jsonify({"error": "No keycloak subject"}), 400

    if teacher.keycloak_user_id and teacher.keycloak_user_id != subject:
        return jsonify({
            "error": "Teacher profile is already linked to another Keycloak account",
            "teacher_id": teacher.id,
        }), 400

    existing = Teacher.query.filter_by(keycloak_user_id=subject).first()
    if existing and existing.id != teacher.id:
        return jsonify({
            "error": "This Keycloak account is already linked to another teacher",
            "linked_teacher_id": existing.id,
        }), 400

    teacher.keycloak_user_id = subject
    db.session.commit()

    return jsonify({
        "status": "ok",
        "message": "Teacher linked",
        "teacher_id": teacher.id,
        "keycloak_user_id": teacher.keycloak_user_id,
    })


@main_bp.post("/link/parent/<int:parent_id>")
@roles_required("admin", "manager", "parent")
def link_parent_account(parent_id):
    parent = Parent.query.get(parent_id)
    if not parent:
        return jsonify({"error": "Parent not found"}), 404

    permission_error = _ensure_can_link_personal_account(parent.email, "parent")
    if permission_error:
        return permission_error

    subject = g.keycloak_user.get("sub")
    if not subject:
        return jsonify({"error": "No keycloak subject"}), 400

    if parent.keycloak_user_id and parent.keycloak_user_id != subject:
        return jsonify({
            "error": "Parent profile is already linked to another Keycloak account",
            "parent_id": parent.id,
        }), 400

    existing = Parent.query.filter_by(keycloak_user_id=subject).first()
    if existing and existing.id != parent.id:
        return jsonify({
            "error": "This Keycloak account is already linked to another parent",
            "linked_parent_id": existing.id,
        }), 400

    parent.keycloak_user_id = subject
    db.session.commit()

    return jsonify({
        "status": "ok",
        "message": "Parent linked",
        "parent_id": parent.id,
        "keycloak_user_id": parent.keycloak_user_id,
    })


@main_bp.post("/link/assistant/<int:assistant_id>")
@roles_required("admin", "manager", "assistant")
def link_assistant_account(assistant_id):
    assistant = Assistant.query.get(assistant_id)
    if not assistant:
        return jsonify({"error": "Assistant not found"}), 404

    permission_error = _ensure_can_link_personal_account(assistant.email, "assistant")
    if permission_error:
        return permission_error

    subject = g.keycloak_user.get("sub")
    if not subject:
        return jsonify({"error": "No keycloak subject"}), 400

    if assistant.keycloak_user_id and assistant.keycloak_user_id != subject:
        return jsonify({
            "error": "Assistant profile is already linked to another Keycloak account",
            "assistant_id": assistant.id,
        }), 400

    existing = Assistant.query.filter_by(keycloak_user_id=subject).first()
    if existing and existing.id != assistant.id:
        return jsonify({
            "error": "This Keycloak account is already linked to another assistant",
            "linked_assistant_id": existing.id,
        }), 400

    assistant.keycloak_user_id = subject
    db.session.commit()

    return jsonify({
        "status": "ok",
        "message": "Assistant linked",
        "assistant_id": assistant.id,
        "keycloak_user_id": assistant.keycloak_user_id,
    })


@main_bp.get("/whoami/domain")
@keycloak_required
def whoami_domain():
    teacher = get_current_teacher()
    parent = get_current_parent()
    assistant = get_current_assistant()

    return jsonify({
        "status": "ok",
        "keycloak_user": g.keycloak_user,
        "teacher": {
            "id": teacher.id,
            "email": teacher.email,
        } if teacher else None,
        "parent": {
            "id": parent.id,
            "email": parent.email,
        } if parent else None,
        "assistant": {
            "id": assistant.id,
            "email": assistant.email,
        } if assistant else None,
    })
