
import threading
from flask import Blueprint, request, jsonify, session
from database.db import get_db
from routes.utils import login_required

incidents_bp = Blueprint("incidents", __name__)

# Background worker function for sending emails without blocking the server
def dispatch_emails_to_contacts():
    # TODO: Put your actual email/SMTP sending logic here
    print("Sending SOS emails in the background...")

@incidents_bp.route("/sos", methods=["POST"])
@login_required
def trigger_sos():
    # Start the email dispatching in a separate thread so the UI responds instantly
    email_thread = threading.Thread(target=dispatch_emails_to_contacts)
    email_thread.start()
    
    return jsonify({"status": "SOS triggered successfully"}), 200

@incidents_bp.route("/incidents", methods=["POST"])
@login_required
def add_incident():
    data = request.get_json() or {}
    
    description = data.get("description")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    
    if not description:
        return jsonify({"error": "Description is required"}), 400
        
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO incidents 
        (user_id, description, latitude, longitude) 
        VALUES (?, ?, ?, ?)""",
        (session["user_id"], description, latitude, longitude)
    )
    conn.commit()
    incident_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Incident recorded successfully",
        "incident_id": incident_id,
        "status": "active"
    }), 201

@incidents_bp.route("/incidents", methods=["GET"])
@login_required
def get_incidents():
    conn = get_db()
    incidents = conn.execute(
        """SELECT id, description, latitude, longitude, status, created_at 
        FROM incidents WHERE user_id = ? 
        ORDER BY created_at DESC""",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return jsonify([dict(incident) for incident in incidents])

# Support SOS Cancellation
@incidents_bp.route("/incidents/<int:incident_id>/cancel", methods=["PATCH", "PUT"])
@login_required
def cancel_incident(incident_id):
    conn = get_db()
    
    incident = conn.execute(
        "SELECT * FROM incidents WHERE id = ? AND user_id = ?",
        (incident_id, session["user_id"])
    ).fetchone()
    
    if not incident:
        conn.close()
        return jsonify({"error": "Incident not found or unauthorized"}), 404
        
    conn.execute(
        "UPDATE incidents SET status = 'cancelled' WHERE id = ?",
        (incident_id,)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        "message": "SOS incident cancelled successfully",
        "incident_id": incident_id,
        "status": "cancelled"
    }), 200