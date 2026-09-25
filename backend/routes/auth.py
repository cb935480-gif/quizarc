"""Authentication routes — username + PIN system with werkzeug hashing & rate limiting."""

from datetime import datetime, timedelta
import secrets
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection

auth_bp = Blueprint("auth", __name__)
SESSION_DAYS = 7

# Rate limiting for failed login attempts: { username_lower: [timestamp, ...] }
FAILED_LOGIN_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 300  # 5 minutes


def _is_rate_limited(username: str) -> bool:
    key = username.lower()
    now = datetime.utcnow()
    attempts = FAILED_LOGIN_ATTEMPTS.get(key, [])
    # Keep only attempts within the window
    recent = [t for t in attempts if (now - t).total_seconds() < LOCKOUT_WINDOW_SECONDS]
    FAILED_LOGIN_ATTEMPTS[key] = recent
    return len(recent) >= MAX_FAILED_ATTEMPTS


def _record_failed_attempt(username: str):
    key = username.lower()
    now = datetime.utcnow()
    attempts = FAILED_LOGIN_ATTEMPTS.get(key, [])
    attempts.append(now)
    FAILED_LOGIN_ATTEMPTS[key] = attempts


def _clear_failed_attempts(username: str):
    key = username.lower()
    FAILED_LOGIN_ATTEMPTS.pop(key, None)


def verify_auth_token_from_req(req):
    """
    Helper to extract and verify X-Auth-Token or Authorization Bearer header.
    Returns (player_row, None) or (None, error_response_tuple).
    """
    token = req.headers.get("X-Auth-Token") or ""
    if not token and req.headers.get("Authorization"):
        auth_hdr = req.headers.get("Authorization")
        if auth_hdr.startswith("Bearer "):
            token = auth_hdr[7:].strip()
    if not token and req.args:
        token = req.args.get("auth_token", "")
    if not token and req.is_json and req.get_json(silent=True):
        token = req.get_json(silent=True).get("auth_token", "")

    if not token:
        return None, (jsonify({"error": "Authentication required. Please log in first."}), 401)

    try:
        conn = get_connection()
        row = conn.execute(
            """SELECT at.token, at.expires_at, p.id AS player_id, p.username
               FROM auth_tokens at
               JOIN players p ON p.id = at.player_id
               WHERE at.token = ?""",
            (token,)
        ).fetchone()
        conn.close()

        if not row:
            return None, (jsonify({"error": "Invalid auth token. Please log in again."}), 401)

        exp = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() > exp:
            return None, (jsonify({"error": "Auth token expired. Please log in again."}), 401)

        return row, None
    except Exception as e:
        return None, (jsonify({"error": "Authentication check failed", "detail": str(e)}), 500)


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    """
    POST /api/auth/register
    Body: { username: str, pin: str (4-10 digits) }
    Returns: { username, auth_token }
    """
    try:
        data     = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        pin      = str(data.get("pin") or "").strip()

        if not username or not (2 <= len(username) <= 30):
            return jsonify({"error": "Username must be 2–30 characters"}), 400
        if not pin or not pin.isdigit() or not (4 <= len(pin) <= 10):
            return jsonify({"error": "PIN must be 4–10 digits (numbers only)"}), 400

        conn = get_connection()
        if conn.execute("SELECT id FROM players WHERE LOWER(username) = LOWER(?)", (username,)).fetchone():
            conn.close()
            return jsonify({"error": "Username already taken"}), 409

        pin_hash = generate_password_hash(pin)
        conn.execute(
            "INSERT INTO players (username, pin_hash) VALUES (?, ?)",
            (username, pin_hash),
        )
        player_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        token      = secrets.token_hex(32)
        expires_at = (datetime.utcnow() + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO auth_tokens (token, player_id, expires_at) VALUES (?, ?, ?)",
            (token, player_id, expires_at),
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Registered successfully", "username": username, "auth_token": token}), 201

    except Exception as e:
        return jsonify({"error": "Registration failed", "detail": str(e)}), 500


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { username: str, pin: str }
    Returns: { username, auth_token }
    """
    try:
        data     = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        pin      = str(data.get("pin") or "").strip()

        if not username or not pin:
            return jsonify({"error": "Username and PIN are required"}), 400

        # Rate limiting check
        if _is_rate_limited(username):
            return jsonify({
                "error": "Too many failed login attempts. Please wait 5 minutes before trying again."
            }), 429

        conn   = get_connection()
        player = conn.execute(
            "SELECT id, username, pin_hash FROM players WHERE LOWER(username) = LOWER(?)", (username,)
        ).fetchone()

        if not player or not check_password_hash(player["pin_hash"], pin):
            conn.close()
            _record_failed_attempt(username)
            return jsonify({"error": "Invalid username or PIN"}), 401

        # Successful login -> clear rate limit counter
        _clear_failed_attempts(username)

        token      = secrets.token_hex(32)
        expires_at = (datetime.utcnow() + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO auth_tokens (token, player_id, expires_at) VALUES (?, ?, ?)",
            (token, player["id"], expires_at),
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Logged in", "username": player["username"], "auth_token": token})

    except Exception as e:
        return jsonify({"error": "Login failed", "detail": str(e)}), 500


@auth_bp.route("/api/auth/verify", methods=["GET"])
def verify():
    """
    GET /api/auth/verify
    Header: X-Auth-Token: <token>  OR  Authorization: Bearer <token>  OR  ?token=<token>
    """
    player, err = verify_auth_token_from_req(request)
    if err:
        return err
    return jsonify({"valid": True, "username": player["username"], "player_id": player["player_id"]})


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    Header: X-Auth-Token: <token> or Body: { auth_token: str }
    """
    data  = request.get_json(silent=True) or {}
    token = (data.get("auth_token") or "").strip() or request.headers.get("X-Auth-Token", "")
    if not token:
        return jsonify({"error": "No token provided"}), 400

    try:
        conn = get_connection()
        conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Logged out"})
    except Exception as e:
        return jsonify({"error": "Logout failed", "detail": str(e)}), 500


@auth_bp.route("/api/user/profile", methods=["GET"])
def get_user_profile():
    """
    GET /api/user/profile
    Header: X-Auth-Token: <token>
    Returns user level, XP, streak, daily challenge status, global rank, total quizzes, and recent activity.
    """
    player, err = verify_auth_token_from_req(request)
    if err:
        return err

    try:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        conn = get_connection()
        row = conn.execute(
            """SELECT id, username, xp, current_streak, best_streak, last_active_date
               FROM players WHERE id = ?""",
            (player["player_id"],)
        ).fetchone()

        if not row:
            conn.close()
            return jsonify({"error": "Player not found"}), 404

        daily_row = conn.execute(
            "SELECT id FROM daily_challenges WHERE player_id = ? AND completed_date = ?",
            (player["player_id"], today_str)
        ).fetchone()

        # Global Rank calculation
        rank_val = conn.execute(
            "SELECT COUNT(*) + 1 FROM players WHERE xp > ?", (row["xp"] or 0,)
        ).fetchone()[0]

        # Total Quizzes calculation
        total_quizzes = conn.execute(
            "SELECT COUNT(*) FROM scores WHERE player_id = ?", (player["player_id"],)
        ).fetchone()[0]

        # Recent 3 quiz attempts
        recent_rows = conn.execute(
            """SELECT s.category_id, s.difficulty, s.score, s.total_questions, s.xp_earned, s.created_at, s.is_daily,
                      c.name AS category_name, c.icon AS category_icon
               FROM scores s
               LEFT JOIN categories c ON c.id = s.category_id
               WHERE s.player_id = ?
               ORDER BY s.id DESC LIMIT 3""",
            (player["player_id"],)
        ).fetchall()

        conn.close()

        recent_activity = [
            {
                "category_name": r["category_name"] or ("Daily Challenge" if r["is_daily"] else "Practice"),
                "category_icon": r["category_icon"] or "🌟" if r["is_daily"] else "🎯",
                "difficulty": r["difficulty"],
                "score": r["score"],
                "total_questions": r["total_questions"],
                "xp_earned": r["xp_earned"],
                "created_at": r["created_at"],
            }
            for r in recent_rows
        ]

        xp = row["xp"] or 0
        level = 1 + (xp // 100)
        xp_in_level = xp % 100

        return jsonify({
            "player_id": row["id"],
            "username": row["username"],
            "xp": xp,
            "level": level,
            "xp_in_level": xp_in_level,
            "xp_needed": 100,
            "current_streak": row["current_streak"] or 0,
            "best_streak": row["best_streak"] or 0,
            "daily_completed": bool(daily_row),
            "global_rank": rank_val,
            "total_quizzes": total_quizzes,
            "recent_activity": recent_activity
        })
    except Exception as e:
        return jsonify({"error": "Failed to fetch user profile", "detail": str(e)}), 500



