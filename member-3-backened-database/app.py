import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from database.db import init_db
from routes.auth import auth_bp
from routes.contacts import contacts_bp
from routes.incidents import incidents_bp
from routes.notifications import notifications_bp

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-this")

CORS(app, supports_credentials=True)

init_db()

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(contacts_bp, url_prefix="/api")
app.register_blueprint(incidents_bp, url_prefix="/api")
app.register_blueprint(notifications_bp, url_prefix="/api")


@app.route("/")
def home():
    return jsonify({
        "project": "SafeCircle",
        "message": "Backend is running successfully"
    })


if __name__ == "__main__":
    app.run(debug=False)