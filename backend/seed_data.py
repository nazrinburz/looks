"""
seed_data.py - Load mock data for development / demo purposes.

Creates 5 users + 5 profiles + 25 reviews if the database is empty.
Safe to run multiple times – skips seeding if data already exists.

Usage:
    python seed_data.py
"""

import sys
import os

# Make sure backend/ is on the path so config / models / auth import cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import get_db, init_db, recalculate_profile_ratings
from auth import hash_password


# ---------------------------------------------------------------------------
# Seed definitions
# ---------------------------------------------------------------------------

USERS = [
    {
        "username": "alex_fit",
        "email": "alex@example.com",
        "password": "password123",
        "bio": "Fitness enthusiast, gym 6 days a week 💪",
        "avatar_url": "https://i.pravatar.cc/300?img=1",
    },
    {
        "username": "jordan_creative",
        "email": "jordan@example.com",
        "password": "password123",
        "bio": "Designer & artist ☕ Always creating",
        "avatar_url": "https://i.pravatar.cc/300?img=2",
    },
    {
        "username": "sam_tech",
        "email": "sam@example.com",
        "password": "password123",
        "bio": "Software engineer | Open source contributor",
        "avatar_url": "https://i.pravatar.cc/300?img=3",
    },
    {
        "username": "casey_art",
        "email": "casey@example.com",
        "password": "password123",
        "bio": "Photographer & artist 📸 Exploring the world",
        "avatar_url": "https://i.pravatar.cc/300?img=4",
    },
    {
        "username": "morgan_travel",
        "email": "morgan@example.com",
        "password": "password123",
        "bio": "Travel blogger ✈️ Adventure seeker",
        "avatar_url": "https://i.pravatar.cc/300?img=5",
    },
]

# reviews[i] = list of review dicts for profile i (0-indexed same order as USERS)
# Each reviewer is identified by username (resolved to ID below).
REVIEWS = {
    "alex_fit": [
        {"reviewer": "jordan_creative", "looks": 8, "style": 7, "vibe": 8, "text": "Great energy! Really consistent look."},
        {"reviewer": "sam_tech",        "looks": 7, "style": 8, "vibe": 8, "text": "Very consistent, cool style overall."},
        {"reviewer": "casey_art",       "looks": 8, "style": 7, "vibe": 8, "text": "Cool style, solid gym aesthetic."},
        {"reviewer": "morgan_travel",   "looks": 8, "style": 8, "vibe": 7, "text": "Motivational presence."},
    ],
    "jordan_creative": [
        {"reviewer": "alex_fit",        "looks": 8, "style": 9, "vibe": 8, "text": "Excellent aesthetic, very artistic."},
        {"reviewer": "sam_tech",        "looks": 8, "style": 8, "vibe": 9, "text": "Amazing style, love the creative edge."},
        {"reviewer": "casey_art",       "looks": 7, "style": 8, "vibe": 8, "text": "Very artistic, great creative eye."},
        {"reviewer": "morgan_travel",   "looks": 8, "style": 9, "vibe": 8, "text": "Sleek and polished look."},
    ],
    "sam_tech": [
        {"reviewer": "alex_fit",        "looks": 7, "style": 6, "vibe": 7, "text": "Cool person, nice tech energy."},
        {"reviewer": "jordan_creative", "looks": 7, "style": 7, "vibe": 8, "text": "Nice vibe, chill person."},
        {"reviewer": "casey_art",       "looks": 6, "style": 6, "vibe": 7, "text": "Tech energy all the way."},
        {"reviewer": "morgan_travel",   "looks": 7, "style": 7, "vibe": 7, "text": "Solid and dependable vibe."},
    ],
    "casey_art": [
        {"reviewer": "alex_fit",        "looks": 8, "style": 8, "vibe": 9, "text": "Amazing artist, incredible style."},
        {"reviewer": "jordan_creative", "looks": 9, "style": 8, "vibe": 9, "text": "Best vibe, outstanding photography."},
        {"reviewer": "sam_tech",        "looks": 8, "style": 9, "vibe": 8, "text": "Creative and expressive."},
        {"reviewer": "morgan_travel",   "looks": 8, "style": 8, "vibe": 9, "text": "Artistic soul with great style."},
    ],
    "morgan_travel": [
        {"reviewer": "alex_fit",        "looks": 7, "style": 8, "vibe": 9, "text": "Fun energy, love the vibe!"},
        {"reviewer": "jordan_creative", "looks": 8, "style": 7, "vibe": 9, "text": "Inspirational travel content."},
        {"reviewer": "sam_tech",        "looks": 7, "style": 8, "vibe": 8, "text": "Love the adventurous spirit."},
        {"reviewer": "casey_art",       "looks": 8, "style": 7, "vibe": 9, "text": "Wanderlust vibes, great look."},
    ],
}


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

def seed() -> None:
    """Populate the database with demo data if it is empty."""
    init_db()

    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        if existing["cnt"] > 0:
            print("Database already seeded – skipping.")
            return

        print("Seeding database …")

        # 1. Insert users -------------------------------------------------
        user_ids: dict[str, int] = {}
        for u in USERS:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (u["username"], u["email"], hash_password(u["password"])),
            )
            user_id = cursor.lastrowid
            user_ids[u["username"]] = user_id

            # 2. Create matching profile ----------------------------------
            conn.execute(
                "INSERT INTO profiles (user_id, bio, avatar_url) VALUES (?, ?, ?)",
                (user_id, u["bio"], u["avatar_url"]),
            )

        conn.commit()

        # Fetch profile IDs keyed by username
        rows = conn.execute(
            """
            SELECT p.id AS profile_id, u.username
            FROM profiles p
            JOIN users u ON u.id = p.user_id
            """
        ).fetchall()
        profile_ids: dict[str, int] = {r["username"]: r["profile_id"] for r in rows}

        # 3. Insert reviews -----------------------------------------------
        for subject_username, review_list in REVIEWS.items():
            profile_id = profile_ids[subject_username]
            for rv in review_list:
                reviewer_id = user_ids[rv["reviewer"]]
                conn.execute(
                    """
                    INSERT INTO reviews
                        (reviewer_user_id, reviewed_profile_id,
                         looks_rating, style_rating, vibe_rating, feedback_text)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (reviewer_id, profile_id, rv["looks"], rv["style"], rv["vibe"], rv["text"]),
                )
            recalculate_profile_ratings(conn, profile_id)

        conn.commit()

    total_reviews = sum(len(v) for v in REVIEWS.values())
    print(f"✅  Seeded: {len(USERS)} users, {len(USERS)} profiles, {total_reviews} reviews.")


if __name__ == "__main__":
    seed()
