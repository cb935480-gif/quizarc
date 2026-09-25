"""Routes for score submission, XP & streak tracking, and leaderboard."""

import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from database import get_connection
from routes.auth import verify_auth_token_from_req

scores_bp = Blueprint("scores", __name__)

XP_PER_CORRECT = {"easy": 10, "medium": 15, "hard": 25}


@scores_bp.route("/api/scores", methods=["POST"])
def submit_scores():
    """
    POST /api/scores
    Requires X-Auth-Token header.
    Body: {
        category?:     str,           ← optional if is_daily
        difficulty?:   str,
        session_token: str,           ← required (anti-tamper)
        answers:       [{question_id, selected_index}, ...],
    }
    Calculates score, base XP, daily bonus XP, updates player's XP and streak.
    """
    player_auth, err = verify_auth_token_from_req(request)
    if err:
        return err

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Request body must be valid JSON"}), 400

        player_name   = player_auth["username"]
        player_id     = player_auth["player_id"]
        category_key  = (data.get("category") or "").strip()
        difficulty    = (data.get("difficulty") or "").strip()
        answers       = data.get("answers")
        session_token = (data.get("session_token") or "").strip()

        if not answers or not isinstance(answers, list) or len(answers) == 0:
            return jsonify({"error": "Missing or empty 'answers' array"}), 400
        if not session_token:
            return jsonify({"error": "Missing 'session_token' — start a fresh quiz"}), 400

        conn = get_connection()

        # ── Validate session token ────────────────────────────────────────
        session = conn.execute(
            "SELECT * FROM quiz_sessions WHERE token = ?", (session_token,)
        ).fetchone()

        if not session:
            conn.close()
            return jsonify({"error": "Invalid session token"}), 403
        if session["used"]:
            conn.close()
            return jsonify({"error": "Session already used — duplicate submission rejected"}), 403

        now = datetime.utcnow()
        expires_at = datetime.strptime(session["expires_at"], "%Y-%m-%d %H:%M:%S")
        if now > expires_at:
            conn.close()
            return jsonify({"error": "Session expired — please start a new quiz"}), 403

        is_daily = bool(session["is_daily"])
        cat_id   = session["category_id"]

        if not is_daily:
            cat = conn.execute(
                "SELECT id FROM categories WHERE key = ?", (category_key,)
            ).fetchone()
            if not cat or cat["id"] != cat_id:
                conn.close()
                return jsonify({"error": "Session category mismatch"}), 403
            if session["difficulty"] != difficulty:
                conn.close()
                return jsonify({"error": "Session difficulty mismatch"}), 403
        else:
            difficulty = session["difficulty"] or "medium"

        session_q_ids = set(json.loads(session["question_ids"]))

        # ── Validate submitted answer list ────────────────────────────────
        submitted_q_ids = []
        for ans in answers:
            qid = ans.get("question_id")
            if not isinstance(qid, int):
                conn.close()
                return jsonify({"error": f"Invalid question_id: {qid!r}"}), 400
            sel = ans.get("selected_index")
            if sel is not None and sel not in (0, 1, 2, 3):
                conn.close()
                return jsonify({"error": f"selected_index must be 0-3 or null, got: {sel}"}), 400
            submitted_q_ids.append(qid)

        if len(submitted_q_ids) != len(set(submitted_q_ids)):
            conn.close()
            return jsonify({"error": "Duplicate question IDs in answers — submission rejected"}), 400

        for qid in submitted_q_ids:
            if qid not in session_q_ids:
                conn.close()
                return jsonify({"error": f"Question ID {qid} was not part of this quiz session"}), 403

        # ── Fetch correct answers & question text for Review ─────────────
        placeholders = ",".join("?" * len(submitted_q_ids))
        rows = conn.execute(
            f"""SELECT id, question, option_0, option_1, option_2, option_3, correct_index
                FROM questions WHERE id IN ({placeholders})""",
            submitted_q_ids,
        ).fetchall()

        q_map = {
            r["id"]: {
                "question": r["question"],
                "options": [r["option_0"], r["option_1"], r["option_2"], r["option_3"]],
                "correct_index": r["correct_index"],
            }
            for r in rows
        }

        # ── Score answers & calculate XP ─────────────────────────────────
        score = 0
        breakdown = []
        for ans in answers:
            qid        = ans["question_id"]
            selected   = ans.get("selected_index")
            q_info     = q_map[qid]
            correct_i  = q_info["correct_index"]
            is_correct = (selected == correct_i)
            if is_correct:
                score += 1

            breakdown.append({
                "question_id":   qid,
                "question":      q_info["question"],
                "options":       q_info["options"],
                "correct_index": correct_i,
                "selected_index": selected,
                "correct":       is_correct,
            })

        total = len(answers)
        xp_unit = XP_PER_CORRECT.get(difficulty, 15)
        base_xp = score * xp_unit
        bonus_xp = int(base_xp * 0.5) if is_daily else 0
        total_xp_earned = base_xp + bonus_xp

        # ── Update Player's XP, Streak, and last_active_date ──────────────
        player_row = conn.execute(
            "SELECT xp, current_streak, best_streak, last_active_date FROM players WHERE id = ?",
            (player_id,)
        ).fetchone()

        old_xp = player_row["xp"] or 0
        old_level = 1 + (old_xp // 100)
        new_xp = old_xp + total_xp_earned
        new_level = 1 + (new_xp // 100)
        leveled_up = new_level > old_level

        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        last_active = player_row["last_active_date"] or ""

        current_streak = player_row["current_streak"] or 0
        if last_active == yesterday_str:
            current_streak += 1
        elif last_active == today_str:
            pass  # already active today
        else:
            current_streak = 1  # streak reset / start fresh

        best_streak = max(player_row["best_streak"] or 0, current_streak)

        conn.execute(
            """UPDATE players
               SET xp = ?, current_streak = ?, best_streak = ?, last_active_date = ?
               WHERE id = ?""",
            (new_xp, current_streak, best_streak, today_str, player_id)
        )

        # ── Log Daily Challenge completion if applicable ──────────────────
        if is_daily:
            conn.execute(
                """INSERT OR REPLACE INTO daily_challenges
                   (player_id, completed_date, score, xp_earned)
                   VALUES (?, ?, ?, ?)""",
                (player_id, today_str, score, total_xp_earned)
            )

        # ── Commit score record ───────────────────────────────────────────
        conn.execute("UPDATE quiz_sessions SET used = 1 WHERE token = ?", (session_token,))
        conn.execute(
            """INSERT INTO scores
               (player_name, player_id, category_id, difficulty,
                score, total_questions, xp_earned, is_daily, verified, session_token)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
            (player_name, player_id, cat_id, difficulty,
             score, total, total_xp_earned, 1 if is_daily else 0, session_token),
        )
        conn.commit()
        conn.close()

        return jsonify({
            "score":           score,
            "total":           total,
            "xp_earned":       total_xp_earned,
            "base_xp":         base_xp,
            "bonus_xp":        bonus_xp,
            "is_daily":        is_daily,
            "new_xp":          new_xp,
            "level":           new_level,
            "leveled_up":      leveled_up,
            "current_streak":  current_streak,
            "best_streak":     best_streak,
            "player_name":     player_name,
            "breakdown":       breakdown,
        })

    except Exception as e:
        return jsonify({"error": "Failed to submit score", "detail": str(e)}), 500


@scores_bp.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    """
    GET /api/leaderboard?type=xp  OR  GET /api/leaderboard?type=category&category=general
    Supports Global XP Leaderboard and Category High Score Leaderboard.
    """
    lb_type = request.args.get("type", "xp").strip()
    category_key = request.args.get("category", "general").strip()
    limit = request.args.get("limit", 20, type=int)

    if limit < 1 or limit > 100:
        return jsonify({"error": "'limit' must be between 1 and 100"}), 400

    try:
        conn = get_connection()

        if lb_type == "xp":
            rows = conn.execute(
                """SELECT username AS player_name, xp, current_streak, best_streak
                   FROM players
                   ORDER BY xp DESC, best_streak DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            conn.close()

            return jsonify([
                {
                    "player_name": r["player_name"],
                    "xp": r["xp"],
                    "level": 1 + (r["xp"] // 100),
                    "current_streak": r["current_streak"],
                    "best_streak": r["best_streak"],
                    "verified": True,
                }
                for r in rows
            ])

        else:
            cat = conn.execute(
                "SELECT id FROM categories WHERE key = ?", (category_key,)
            ).fetchone()
            if not cat:
                conn.close()
                return jsonify({"error": f"Unknown category '{category_key}'"}), 404

            rows = conn.execute(
                """SELECT player_name, score, total_questions, difficulty, created_at, verified, xp_earned
                   FROM scores
                   WHERE category_id = ?
                   ORDER BY score DESC, created_at ASC
                   LIMIT ?""",
                (cat["id"], limit),
            ).fetchall()
            conn.close()

            return jsonify([
                {
                    "player_name":     r["player_name"],
                    "score":           r["score"],
                    "total_questions": r["total_questions"],
                    "difficulty":      r["difficulty"],
                    "xp_earned":       r["xp_earned"],
                    "created_at":      r["created_at"],
                    "verified":        bool(r["verified"]),
                }
                for r in rows
            ])
    except Exception as e:
        return jsonify({"error": "Failed to fetch leaderboard", "detail": str(e)}), 500

