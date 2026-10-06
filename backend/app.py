"""
app.py - Main Flask application.

Registers all routes (auth, profiles, reviews), configures CORS,
logging, and error handlers.  Run with: python app.py
"""

import os
import re
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS

from config import config
from models import get_db, init_db, recalculate_profile_ratings
from auth import hash_password, verify_password, generate_token, auth_required
from seed_data import seed


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log"),
    ],
)
logger = logging.getLogger(__name__)


@app.before_request
def _start_timer():
    g.start_time = time.time()


@app.after_request
def _log_request(response):
    elapsed_ms = int((time.time() - g.start_time) * 1000)
    logger.info(
        "%s %s - %d - %dms",
        request.method,
        request.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_rating(val, field: str) -> str | None:
    """Return an error string or None if *val* is a valid 1-10 integer."""
    if val is None:
        return f"{field} is required"
    try:
        iv = int(val)
    except (TypeError, ValueError):
        return f"{field} must be an integer"
    if not (config.MIN_RATING <= iv <= config.MAX_RATING):
        return f"{field} must be between {config.MIN_RATING} and {config.MAX_RATING}"
    return None


# ---------------------------------------------------------------------------
# ── AUTH ────────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    """
    POST /api/auth/signup
    Body: { username, email, password }
    Returns 201 { id, username, email, token }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Validation
    errors = {}
    if not username:
        errors["username"] = "Username is required"
    if not email or not EMAIL_RE.match(email):
        errors["email"] = "A valid email is required"
    if len(password) < config.MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters"
    if errors:
        return jsonify({"errors": errors}), 400

    with get_db() as conn:
        # Uniqueness check
        existing = conn.execute(
            "SELECT username, email FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if existing:
            if existing["username"] == username:
                return jsonify({"error": "Username already taken"}), 409
            return jsonify({"error": "Email already registered"}), 409

        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hash_password(password)),
        )
        user_id = cursor.lastrowid
        conn.commit()

    token = generate_token(user_id, username)
    logger.info("AUTH signup - user '%s' created", username)
    return jsonify({"id": user_id, "username": username, "email": email, "token": token}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { email, password }
    Returns 200 { id, username, token }
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(user["id"], user["username"])
    logger.info("AUTH login - user '%s' authenticated", user["username"])
    return jsonify({"id": user["id"], "username": user["username"], "token": token}), 200


# ---------------------------------------------------------------------------
# ── PROFILES ────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@app.route("/api/profiles", methods=["GET"])
def list_profiles():
    """
    GET /api/profiles?limit=20&offset=0&sort=rating|newest
    Returns paginated list of all profiles.
    """
    try:
        limit = min(max(int(request.args.get("limit", config.DEFAULT_PAGE_LIMIT)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except (TypeError, ValueError):
        return jsonify({"error": "limit and offset must be integers"}), 400
    sort = request.args.get("sort", "rating")

    order_clause = "p.avg_overall DESC, p.review_count DESC"
    if sort == "newest":
        order_clause = "p.created_at DESC"

    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS cnt FROM profiles").fetchone()["cnt"]
        rows = conn.execute(
            f"""
            SELECT
                p.id, u.username, p.bio, p.avatar_url,
                p.avg_looks, p.avg_style, p.avg_vibe, p.avg_overall,
                p.review_count, p.created_at
            FROM profiles p
            JOIN users u ON u.id = p.user_id
            ORDER BY {order_clause}
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    profiles = [dict(r) for r in rows]
    return jsonify({"profiles": profiles, "total": total}), 200


@app.route("/api/profiles/<int:profile_id>", methods=["GET"])
def get_profile(profile_id: int):
    """
    GET /api/profiles/:profile_id
    Returns profile info + all reviews (anonymous).
    """
    with get_db() as conn:
        profile = conn.execute(
            """
            SELECT
                p.id, u.id AS user_id, u.username, p.bio, p.avatar_url,
                p.avg_looks, p.avg_style, p.avg_vibe, p.avg_overall,
                p.review_count, p.created_at
            FROM profiles p
            JOIN users u ON u.id = p.user_id
            WHERE p.id = ?
            """,
            (profile_id,),
        ).fetchone()

        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        reviews = conn.execute(
            """
            SELECT
                r.id, r.looks_rating, r.style_rating, r.vibe_rating,
                r.feedback_text, r.created_at, r.updated_at,
                r.reviewer_user_id
            FROM reviews r
            WHERE r.reviewed_profile_id = ?
            ORDER BY r.created_at DESC
            """,
            (profile_id,),
        ).fetchall()

    profile_dict = dict(profile)
    profile_dict["reviews"] = [dict(r) for r in reviews]
    return jsonify(profile_dict), 200


@app.route("/api/profiles", methods=["POST"])
@auth_required
def create_profile():
    """
    POST /api/profiles  (auth required)
    Body: { bio, avatar_url }
    Returns 201 { id, username, bio, avatar_url }
    """
    user_id = g.current_user["user_id"]
    username = g.current_user["username"]
    data = request.get_json(silent=True) or {}
    bio = (data.get("bio") or "").strip()
    avatar_url = (data.get("avatar_url") or "").strip()

    with get_db() as conn:
        # One profile per user
        existing = conn.execute(
            "SELECT id FROM profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            return jsonify({"error": "You already have a profile"}), 409

        cursor = conn.execute(
            "INSERT INTO profiles (user_id, bio, avatar_url) VALUES (?, ?, ?)",
            (user_id, bio or None, avatar_url or None),
        )
        profile_id = cursor.lastrowid
        conn.commit()

    logger.info("PROFILE created - user '%s' profile id=%d", username, profile_id)
    return jsonify({"id": profile_id, "username": username, "bio": bio, "avatar_url": avatar_url}), 201


@app.route("/api/profiles/<int:profile_id>", methods=["PATCH"])
@auth_required
def update_profile(profile_id: int):
    """
    PATCH /api/profiles/:profile_id  (auth required, own profile only)
    Body: { bio?, avatar_url? }
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    with get_db() as conn:
        profile = conn.execute(
            "SELECT id, user_id FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        if profile["user_id"] != user_id:
            return jsonify({"error": "Forbidden – not your profile"}), 403

        # Build dynamic SET clause (only update provided fields)
        updates = {}
        if "bio" in data:
            updates["bio"] = data["bio"]
        if "avatar_url" in data:
            updates["avatar_url"] = data["avatar_url"]

        if not updates:
            return jsonify({"error": "No fields to update"}), 400

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [profile_id]
        conn.execute(
            f"UPDATE profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        conn.commit()

        updated = conn.execute(
            "SELECT id, bio, avatar_url, updated_at FROM profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()

    return jsonify(dict(updated)), 200


@app.route("/api/profiles/<int:profile_id>", methods=["DELETE"])
@auth_required
def delete_profile(profile_id: int):
    """
    DELETE /api/profiles/:profile_id  (auth required, own profile only)
    Cascade-deletes all associated reviews via FK constraints.
    """
    user_id = g.current_user["user_id"]

    with get_db() as conn:
        profile = conn.execute(
            "SELECT id, user_id FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        if profile["user_id"] != user_id:
            return jsonify({"error": "Forbidden – not your profile"}), 403

        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()

    logger.info("PROFILE deleted - profile id=%d", profile_id)
    return jsonify({"success": True}), 200


# ---------------------------------------------------------------------------
# ── REVIEWS ─────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@app.route("/api/profiles/<int:profile_id>/reviews", methods=["POST"])
@auth_required
def create_review(profile_id: int):
    """
    POST /api/profiles/:profile_id/reviews  (auth required)
    Body: { looks_rating, style_rating, vibe_rating, feedback_text? }
    """
    reviewer_user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    # Validate ratings
    errors = {}
    for field in ("looks_rating", "style_rating", "vibe_rating"):
        err = _validate_rating(data.get(field), field)
        if err:
            errors[field] = err
    if errors:
        return jsonify({"errors": errors}), 400

    feedback = (data.get("feedback_text") or "").strip()
    if len(feedback) > config.MAX_FEEDBACK_LENGTH:
        return jsonify({"error": f"Feedback must be ≤ {config.MAX_FEEDBACK_LENGTH} characters"}), 400

    with get_db() as conn:
        profile = conn.execute(
            "SELECT id, user_id FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        # Cannot review own profile
        if profile["user_id"] == reviewer_user_id:
            return jsonify({"error": "You cannot review your own profile"}), 403

        # One review per profile per user
        existing = conn.execute(
            "SELECT id FROM reviews WHERE reviewer_user_id = ? AND reviewed_profile_id = ?",
            (reviewer_user_id, profile_id),
        ).fetchone()
        if existing:
            return jsonify({"error": "You have already reviewed this profile"}), 409

        cursor = conn.execute(
            """
            INSERT INTO reviews
                (reviewer_user_id, reviewed_profile_id,
                 looks_rating, style_rating, vibe_rating, feedback_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reviewer_user_id,
                profile_id,
                int(data["looks_rating"]),
                int(data["style_rating"]),
                int(data["vibe_rating"]),
                feedback or None,
            ),
        )
        review_id = cursor.lastrowid
        recalculate_profile_ratings(conn, profile_id)
        conn.commit()

        review = conn.execute(
            "SELECT id, looks_rating, style_rating, vibe_rating, feedback_text, created_at FROM reviews WHERE id = ?",
            (review_id,),
        ).fetchone()

    logger.info("REVIEW created - review id=%d on profile id=%d", review_id, profile_id)
    return jsonify(dict(review)), 201


@app.route("/api/profiles/<int:profile_id>/reviews", methods=["GET"])
def list_reviews(profile_id: int):
    """
    GET /api/profiles/:profile_id/reviews
    Returns all reviews for a profile (anonymous – no reviewer identity).
    """
    with get_db() as conn:
        profile = conn.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        rows = conn.execute(
            """
            SELECT id, looks_rating, style_rating, vibe_rating, feedback_text,
                   created_at, updated_at
            FROM reviews
            WHERE reviewed_profile_id = ?
            ORDER BY created_at DESC
            """,
            (profile_id,),
        ).fetchall()

    reviews = [dict(r) for r in rows]
    return jsonify({"reviews": reviews, "total": len(reviews)}), 200


@app.route("/api/reviews/<int:review_id>", methods=["PATCH"])
@auth_required
def update_review(review_id: int):
    """
    PATCH /api/reviews/:review_id  (auth required, own review only)
    Body: { looks_rating?, style_rating?, vibe_rating?, feedback_text? }
    """
    user_id = g.current_user["user_id"]
    data = request.get_json(silent=True) or {}

    with get_db() as conn:
        review = conn.execute(
            "SELECT id, reviewer_user_id, reviewed_profile_id FROM reviews WHERE id = ?",
            (review_id,),
        ).fetchone()
        if not review:
            return jsonify({"error": "Review not found"}), 404
        if review["reviewer_user_id"] != user_id:
            return jsonify({"error": "Forbidden – not your review"}), 403

        updates = {}
        for field in ("looks_rating", "style_rating", "vibe_rating"):
            if field in data:
                err = _validate_rating(data[field], field)
                if err:
                    return jsonify({"error": err}), 400
                updates[field] = int(data[field])
        if "feedback_text" in data:
            feedback = (data["feedback_text"] or "").strip()
            if len(feedback) > config.MAX_FEEDBACK_LENGTH:
                return jsonify({"error": f"Feedback must be ≤ {config.MAX_FEEDBACK_LENGTH} chars"}), 400
            updates["feedback_text"] = feedback or None

        if not updates:
            return jsonify({"error": "No fields to update"}), 400

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [review_id]
        conn.execute(
            f"UPDATE reviews SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        recalculate_profile_ratings(conn, review["reviewed_profile_id"])
        conn.commit()

        updated = conn.execute(
            "SELECT id, looks_rating, style_rating, vibe_rating, feedback_text, updated_at FROM reviews WHERE id = ?",
            (review_id,),
        ).fetchone()

    return jsonify(dict(updated)), 200


@app.route("/api/reviews/<int:review_id>", methods=["DELETE"])
@auth_required
def delete_review(review_id: int):
    """
    DELETE /api/reviews/:review_id  (auth required, own review only)
    """
    user_id = g.current_user["user_id"]

    with get_db() as conn:
        review = conn.execute(
            "SELECT id, reviewer_user_id, reviewed_profile_id FROM reviews WHERE id = ?",
            (review_id,),
        ).fetchone()
        if not review:
            return jsonify({"error": "Review not found"}), 404
        if review["reviewer_user_id"] != user_id:
            return jsonify({"error": "Forbidden – not your review"}), 403

        profile_id = review["reviewed_profile_id"]
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        recalculate_profile_ratings(conn, profile_id)
        conn.commit()

    logger.info("REVIEW deleted - review id=%d", review_id)
    return jsonify({"success": True}), 200


# ---------------------------------------------------------------------------
# ── RATING BREAKDOWN ────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@app.route("/api/profiles/<int:profile_id>/rating-breakdown", methods=["GET"])
def rating_breakdown(profile_id: int):
    """
    GET /api/profiles/:profile_id/rating-breakdown
    Returns distribution of each dimension across rating values 1-10.
    """
    with get_db() as conn:
        profile = conn.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        rows = conn.execute(
            "SELECT looks_rating, style_rating, vibe_rating FROM reviews WHERE reviewed_profile_id = ?",
            (profile_id,),
        ).fetchall()

    breakdown: dict[str, dict[int, int]] = {
        "looks": {i: 0 for i in range(1, 11)},
        "style": {i: 0 for i in range(1, 11)},
        "vibe":  {i: 0 for i in range(1, 11)},
    }
    for r in rows:
        breakdown["looks"][r["looks_rating"]] += 1
        breakdown["style"][r["style_rating"]] += 1
        breakdown["vibe"][r["vibe_rating"]]   += 1

    return jsonify(breakdown), 200


# ---------------------------------------------------------------------------
# ── UTILITY: get current user's review for a profile ───────────────────────
# ---------------------------------------------------------------------------

@app.route("/api/profiles/<int:profile_id>/my-review", methods=["GET"])
@auth_required
def my_review(profile_id: int):
    """
    GET /api/profiles/:profile_id/my-review  (auth required)
    Returns the authenticated user's review for this profile, or 404.
    """
    user_id = g.current_user["user_id"]
    with get_db() as conn:
        review = conn.execute(
            """
            SELECT id, looks_rating, style_rating, vibe_rating,
                   feedback_text, created_at, updated_at
            FROM reviews
            WHERE reviewer_user_id = ? AND reviewed_profile_id = ?
            """,
            (user_id, profile_id),
        ).fetchone()

    if not review:
        return jsonify({"error": "No review found"}), 404
    return jsonify(dict(review)), 200


# ---------------------------------------------------------------------------
# ── UTILITY: get profile for currently authenticated user ───────────────────
# ---------------------------------------------------------------------------

@app.route("/api/me/profile", methods=["GET"])
@auth_required
def my_profile():
    """
    GET /api/me/profile  (auth required)
    Returns the authenticated user's profile or 404.
    """
    user_id = g.current_user["user_id"]
    with get_db() as conn:
        profile = conn.execute(
            """
            SELECT p.id, u.username, p.bio, p.avatar_url,
                   p.avg_looks, p.avg_style, p.avg_vibe, p.avg_overall,
                   p.review_count, p.created_at
            FROM profiles p
            JOIN users u ON u.id = p.user_id
            WHERE p.user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if not profile:
        return jsonify({"error": "No profile found"}), 404
    return jsonify(dict(profile)), 200


# ---------------------------------------------------------------------------
# ── ERROR HANDLERS ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    logger.error("Unhandled 500 error: %s", str(e), exc_info=True)
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# ── ENTRY POINT ─────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    seed()
    logger.info("Starting Profile Review API on port %d", config.PORT)
    app.run(debug=config.DEBUG, port=config.PORT)
