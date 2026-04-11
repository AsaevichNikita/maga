from flask import g

from src.app.models import Teacher, Parent, Assistant


def get_current_subject():
    user = getattr(g, "keycloak_user", None) or {}
    return user.get("sub")


def get_current_teacher():
    sub = get_current_subject()
    if not sub:
        return None
    return Teacher.query.filter_by(keycloak_user_id=sub).first()


def get_current_parent():
    sub = get_current_subject()
    if not sub:
        return None
    return Parent.query.filter_by(keycloak_user_id=sub).first()


def get_current_assistant():
    sub = get_current_subject()
    if not sub:
        return None
    return Assistant.query.filter_by(keycloak_user_id=sub).first()