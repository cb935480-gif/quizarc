"""
QuizArc — Flask backend
Serves the API and the frontend static files.
Run locally:  python3 app.py
Production:   gunicorn app:app
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from database import init_db
from routes.questions import questions_bp
from routes.scores import scores_bp
from routes.auth import auth_bp

app = Flask(__name__, static_folder=None)
CORS(app)

# Register API blueprints
app.register_blueprint(questions_bp)
app.register_blueprint(scores_bp)
app.register_blueprint(auth_bp)

# Serve frontend static files from ../frontend/
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")


@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.errorhandler(404)
def not_found(e):
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def server_error(e):
    return {"error": "Internal server error"}, 500


# Initialize DB + seed on first run (works for both local and Render)
with app.app_context():
    init_db()
    try:
        from seed import seed_data
        seed_data()
    except Exception:
        pass  # Already seeded


if __name__ == "__main__":
    print("🚀 QuizArc API running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
