from flask import Blueprint, request, jsonify, session
from database.db import get_db
from routes.utils import login_required

contacts_bp = Blueprint("contacts", __name__)

@contacts_bp.route("/contacts", methods=["POST"])
@login_required
def add_contact():
    data = request.get_json() or {}

    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")

    if not name or not phone or not email:
        return jsonify({
            "error": "Name, phone and email are required"
        }), 400

    conn = get_db()

    try:
        cursor = conn.execute(
            """INSERT INTO contacts
            (user_id, name, phone, email)
            VALUES (?, ?, ?, ?)""",
            (session["user_id"], name, phone, email)
        )

        conn.commit()

        return jsonify({
            "message": "Contact added successfully",
            "contact_id": cursor.lastrowid
        }), 201

    finally:
        conn.close()


@contacts_bp.route("/contacts", methods=["GET"])
@login_required
def get_contacts():
    conn = get_db()

    contacts = conn.execute(
        """SELECT id, name, phone, email
        FROM contacts WHERE user_id = ?""",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return jsonify([dict(contact) for contact in contacts])


@contacts_bp.route("/contacts/<int:contact_id>", methods=["DELETE"])
@login_required
def delete_contact(contact_id):
    conn = get_db()

    cursor = conn.execute(
        "DELETE FROM contacts WHERE id = ? AND user_id = ?",
        (contact_id, session["user_id"])
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Contact not found"}), 404

    return jsonify({"message": "Contact deleted successfully"})
