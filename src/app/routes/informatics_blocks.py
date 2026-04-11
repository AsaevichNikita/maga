from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from src.app import db
from src.app.keycloak_auth import roles_required
from src.app.models import Course, InformaticsBlock


informatics_blocks_bp = Blueprint("informatics_blocks", __name__)


def block_to_dict(b: InformaticsBlock) -> dict:
    return {
        "id": b.id,
        "course_id": b.course_id,
        "name": b.name,
        "description": b.description,
        "skills": b.skills or [],
        "created_at": b.created_at.isoformat() if b.created_at else None,
    }


@informatics_blocks_bp.get("/")
def list_blocks():
    blocks = InformaticsBlock.query.order_by(InformaticsBlock.id.asc()).all()
    return jsonify([block_to_dict(b) for b in blocks]), 200


@informatics_blocks_bp.post("/")
@roles_required("manager", "admin")
def create_block():
    data = request.get_json(silent=True) or {}

    course_id = data.get("course_id")
    name = data.get("name")

    if not course_id or not name:
        return jsonify({"error": "course_id and name are required"}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": f"Course {course_id} not found"}), 404

    block = InformaticsBlock(
        course_id=int(course_id),
        name=str(name).strip(),
        description=data.get("description"),
        skills=data.get("skills") or [],
    )

    db.session.add(block)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "IntegrityError", "details": str(e)}), 409

    return jsonify(block_to_dict(block)), 201


@informatics_blocks_bp.get("/<int:block_id>")
def get_block(block_id: int):
    block = InformaticsBlock.query.get(block_id)
    if not block:
        return jsonify({"error": "Not found"}), 404
    return jsonify(block_to_dict(block)), 200


@informatics_blocks_bp.put("/<int:block_id>")
@roles_required("manager", "admin")
def update_block(block_id: int):
    block = InformaticsBlock.query.get(block_id)
    if not block:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}

    if "course_id" in data and data["course_id"] is not None:
        course = Course.query.get(int(data["course_id"]))
        if not course:
            return jsonify({"error": f"Course {data['course_id']} not found"}), 404
        block.course_id = int(data["course_id"])

    if "name" in data and data["name"] is not None:
        block.name = str(data["name"]).strip()

    if "description" in data:
        block.description = data["description"]

    if "skills" in data:
        block.skills = data["skills"] or []

    db.session.commit()
    return jsonify(block_to_dict(block)), 200


@informatics_blocks_bp.delete("/<int:block_id>")
@roles_required("admin")
def delete_block(block_id: int):
    block = InformaticsBlock.query.get(block_id)
    if not block:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(block)
    db.session.commit()
    return jsonify({"status": "deleted", "id": block_id}), 200


@informatics_blocks_bp.get("/by-course/<int:course_id>")
def list_blocks_by_course(course_id: int):
    blocks = InformaticsBlock.query.filter_by(course_id=course_id).order_by(InformaticsBlock.id.asc()).all()
    return jsonify([block_to_dict(b) for b in blocks]), 200
