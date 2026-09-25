"""Routes for question and category endpoints — with quiz session token generation."""

import json
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from database import get_connection
from routes.auth import verify_auth_token_from_req

questions_bp = Blueprint("questions", __name__)
SESSION_TTL_MINUTES = 30


@questions_bp.route("/api/categories", methods=["GET"])
def get_categories():
    """Return all categories with their per-difficulty question counts."""
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT c.id, c.key, c.name, c.icon,
                   COUNT(q.id) AS question_count
            FROM categories c
            LEFT JOIN questions q ON q.category_id = c.id
            GROUP BY c.id
            ORDER BY c.id
        """).fetchall()

        result = []
        for r in rows:
            # Per-difficulty breakdown
            diff_rows = conn.execute(
                """SELECT difficulty, COUNT(*) as cnt FROM questions
                   WHERE category_id = ? GROUP BY difficulty""",
                (r["id"],)
            ).fetchall()
            diff_counts = {d["difficulty"]: d["cnt"] for d in diff_rows}
            result.append({
                "key": r["key"],
                "name": r["name"],
                "icon": r["icon"],
                "question_count": r["question_count"],
                "by_difficulty": diff_counts,
            })

        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to fetch categories", "detail": str(e)}), 500


@questions_bp.route("/api/questions", methods=["GET"])
def get_questions():
    """
    GET /api/questions?category=general&difficulty=medium&count=10
    Returns `count` random questions (correct_index stripped).
    Requires authentication via X-Auth-Token or Bearer header.
    Also creates a single-use quiz session token for tamper prevention.
    Response: { questions: [...], session_token: "..." }
    """
    # ── Require Authentication ────────────────────────────────────────────
    player, err = verify_auth_token_from_req(request)
    if err:
        return err
    category_key = request.args.get("category", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    count = request.args.get("count", 10, type=int)

    # ── Input validation ──────────────────────────────────────────────────
    if not category_key:
        return jsonify({"error": "Missing 'category' parameter"}), 400
    if difficulty not in ("easy", "medium", "hard"):
        return jsonify({"error": "Invalid 'difficulty': must be easy | medium | hard"}), 400
    if count < 1 or count > 50:
        return jsonify({"error": "'count' must be between 1 and 50"}), 400

    try:
        conn = get_connection()

        cat = conn.execute(
            "SELECT id, name FROM categories WHERE key = ?", (category_key,)
        ).fetchone()
        if not cat:
            conn.close()
            return jsonify({"error": f"Unknown category '{category_key}'"}), 404

        rows = conn.execute(
            """SELECT id, question, option_0, option_1, option_2, option_3
               FROM questions
               WHERE category_id = ? AND difficulty = ?
               ORDER BY RANDOM() LIMIT ?""",
            (cat["id"], difficulty, count),
        ).fetchall()

        if not rows:
            conn.close()
            return jsonify({
                "error": f"No '{difficulty}' questions available for '{category_key}'"
            }), 404

        questions = [
            {
                "id": r["id"],
                "question": r["question"],
                "options": [r["option_0"], r["option_1"], r["option_2"], r["option_3"]],
            }
            for r in rows
        ]

        # ── Create single-use quiz session ────────────────────────────────
        token = secrets.token_hex(32)
        question_ids_json = json.dumps([q["id"] for q in questions])
        now = datetime.utcnow()
        expires_at = (now + timedelta(minutes=SESSION_TTL_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """INSERT INTO quiz_sessions
               (token, category_id, difficulty, question_ids, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (token, cat["id"], difficulty, question_ids_json, created_at, expires_at),
        )
        conn.commit()
        conn.close()

        return jsonify({"questions": questions, "session_token": token})
    except Exception as e:
        return jsonify({"error": "Failed to fetch questions", "detail": str(e)}), 500


@questions_bp.route("/api/questions/daily", methods=["GET"])
def get_daily_questions():
    """
    GET /api/questions/daily
    Requires X-Auth-Token header.
    Returns 10 mixed random questions for today's Daily Challenge.
    Response: { questions: [...], session_token: "...", is_daily: true }
    """
    player, err = verify_auth_token_from_req(request)
    if err:
        return err

    try:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        conn = get_connection()

        # Check if already completed today
        already = conn.execute(
            "SELECT id FROM daily_challenges WHERE player_id = ? AND completed_date = ?",
            (player["player_id"], today_str)
        ).fetchone()
        if already:
            conn.close()
            return jsonify({
                "daily_completed": True,
                "error": "You have already completed today's Daily Challenge! Come back tomorrow."
            }), 400

        # Fetch 10 random questions across all categories
        rows = conn.execute(
            """SELECT id, question, option_0, option_1, option_2, option_3
               FROM questions
               ORDER BY RANDOM() LIMIT 10"""
        ).fetchall()

        questions = [
            {
                "id": r["id"],
                "question": r["question"],
                "options": [r["option_0"], r["option_1"], r["option_2"], r["option_3"]],
            }
            for r in rows
        ]

        token = secrets.token_hex(32)
        question_ids_json = json.dumps([q["id"] for q in questions])
        now = datetime.utcnow()
        expires_at = (now + timedelta(minutes=SESSION_TTL_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
        created_at = now.strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """INSERT INTO quiz_sessions
               (token, category_id, difficulty, is_daily, question_ids, created_at, expires_at)
               VALUES (?, NULL, 'medium', 1, ?, ?, ?)""",
            (token, question_ids_json, created_at, expires_at),
        )
        conn.commit()
        conn.close()

        return jsonify({"questions": questions, "session_token": token, "is_daily": True})
    except Exception as e:
        return jsonify({"error": "Failed to fetch daily challenge", "detail": str(e)}), 500

