import os
import smtplib
import ssl
from email.message import EmailMessage

from flask import Blueprint, request, jsonify, session
from database.db import get_db
from routes.utils import login_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications/emergency", methods=["POST"])
@login_required
def send_emergency_notification():

    data = request.get_json() or {}
    incident_id = data.get("incident_id")

    if not incident_id:
        return jsonify({"error": "Incident ID is required"}), 400

    conn = get_db()

    try:
        # Verify that this incident belongs to the logged-in user
        incident = conn.execute(
            "SELECT * FROM incidents WHERE id = ? AND user_id = ?",
            (incident_id, request_user_id())
        ).fetchone()

        if incident is None:
            return jsonify({"error": "Incident not found"}), 404

        # Get trusted contacts with email addresses
        contacts = conn.execute(
            "SELECT name, email FROM contacts WHERE user_id = ?",
            (request_user_id(),)
        ).fetchall()

        contacts = [c for c in contacts if c["email"]]

    finally:
        conn.close()

    if not contacts:
        return jsonify({"error": "No trusted contacts with email addresses found"}), 400

    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender or not password:
        return jsonify({"error": "Email configuration is missing"}), 500

    message_text = (
        "EMERGENCY SOS ALERT\n\n"
        "An emergency SOS alert has been triggered.\n"
        f"Incident description: {incident['description']}\n"
        "Please contact the user immediately.\n\n"
        "This is an automated SafeCircle notification."
    )

    if incident["latitude"] is not None and incident["longitude"] is not None:
        message_text += (
            f"\nLocation: https://www.google.com/maps?q="
            f"{incident['latitude']},{incident['longitude']}"
        )

        sent_count = 0

    try:
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            context=context,
            timeout=20
        ) as server:

            server.login(sender, password)
            print("GMAIL LOGIN SUCCESSFUL")

            for contact in contacts:
                email = EmailMessage()
                email["Subject"] = "Emergency SOS Alert - SafeCircle"
                email["From"] = sender
                email["To"] = contact["email"]

                email.set_content(
                    f"Hello {contact['name']},\n\n{message_text}"
                )

                server.send_message(email)
                sent_count += 1

        print("EMAILS SENT:", sent_count)

    except Exception as error:
        print("EMAIL ERROR:", repr(error))

        return jsonify({
            "error": "Unable to send emergency emails. Check Gmail configuration."
        }), 500

    return jsonify({
        "message": "Emergency emails sent successfully",
        "emails_sent": sent_count
    }), 200

def request_user_id():
    return session["user_id"]

