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
        "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80",
    },
    {
        "username": "jordan_creative",
        "email": "jordan@example.com",
        "password": "password123",
        "bio": "Designer & artist ☕ Always creating",
        "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=600&q=80",
    },
    {
        "username": "sam_tech",
        "email": "sam@example.com",
        "password": "password123",
        "bio": "Software engineer | Open source contributor",
        "avatar_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=600&q=80",
    },
    {
        "username": "casey_art",
        "email": "casey@example.com",
        "password": "password123",
        "bio": "Photographer & artist 📸 Exploring the world",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80",
    },
    {
        "username": "morgan_travel",
        "email": "morgan@example.com",
        "password": "password123",
        "bio": "Travel blogger ✈️ Adventure seeker",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80",
    },
]

# reviews[i] = list of review dicts for profile i (0-indexed same order as USERS)
# Each reviewer is identified by username (resolved to ID below).
REVIEWS = {
    "alex_fit": [
        {"reviewer": "jordan_creative", "looks": 8, "style": 7, "vibe": 8, "text": "A cleaner fade or slightly longer textured top could frame your face well. Your athletic style already feels consistent."},
        {"reviewer": "sam_tech",        "looks": 7, "style": 8, "vibe": 8, "text": "The gym-ready look suits you. Try one sharper color accent or a more structured jacket to make the outfit feel more intentional."},
        {"reviewer": "casey_art",       "looks": 8, "style": 7, "vibe": 8, "text": "Your energy comes through clearly. A fitted overshirt and coordinated sneakers could elevate the athletic aesthetic without making it feel overdone."},
        {"reviewer": "morgan_travel",   "looks": 8, "style": 8, "vibe": 7, "text": "Strong, active presence. If fitness is one of your goals, consistent strength training could complement the confident style you already have."},
    ],
    "jordan_creative": [
        {"reviewer": "alex_fit",        "looks": 8, "style": 9, "vibe": 8, "text": "The creative direction is strong. A longer hairstyle or more defined shape around the sides could make the overall look even more distinctive."},
        {"reviewer": "sam_tech",        "looks": 8, "style": 8, "vibe": 9, "text": "Great visual identity. Try layering a plain overshirt over the statement piece so the outfit has more depth without losing its artistic edge."},
        {"reviewer": "casey_art",       "looks": 7, "style": 8, "vibe": 8, "text": "Your eye for composition shows in your style. A warmer neutral or one repeated accessory could make the color palette feel more cohesive."},
        {"reviewer": "morgan_travel",   "looks": 8, "style": 9, "vibe": 8, "text": "Polished and expressive. A slightly more tailored fit would sharpen the silhouette while keeping the relaxed creative personality."},
    ],
    "sam_tech": [
        {"reviewer": "alex_fit",        "looks": 7, "style": 6, "vibe": 7, "text": "Cool person, nice tech energy."},
        {"reviewer": "jordan_creative", "looks": 7, "style": 7, "vibe": 8, "text": "Nice vibe, chill person."},
        {"reviewer": "casey_art",       "looks": 6, "style": 6, "vibe": 7, "text": "Tech energy all the way."},
        {"reviewer": "morgan_travel",   "looks": 7, "style": 7, "vibe": 7, "text": "Solid and dependable vibe."},
    ],
    "casey_art": [
        {"reviewer": "alex_fit",        "looks": 8, "style": 8, "vibe": 9, "text": "The artistic presence is memorable. A cleaner hair shape or one bold accessory could give the portrait an even clearer focal point."},
        {"reviewer": "jordan_creative", "looks": 9, "style": 8, "vibe": 9, "text": "Excellent visual storytelling. Try a more deliberate contrast between the outfit and background so the subject stands out in every photo."},
        {"reviewer": "sam_tech",        "looks": 8, "style": 9, "vibe": 8, "text": "Creative and expressive. A consistent jacket or color theme across photos could make the portfolio feel more connected."},
        {"reviewer": "morgan_travel",   "looks": 8, "style": 8, "vibe": 9, "text": "Warm, confident energy. Slightly more directional lighting would highlight the styling and make the images feel more editorial."},
    ],
    "morgan_travel": [
        {"reviewer": "alex_fit",        "looks": 7, "style": 8, "vibe": 9, "text": "Fun energy, love the vibe!"},
        {"reviewer": "jordan_creative", "looks": 8, "style": 7, "vibe": 9, "text": "Inspirational travel content."},
        {"reviewer": "sam_tech",        "looks": 7, "style": 8, "vibe": 8, "text": "Love the adventurous spirit."},
        {"reviewer": "casey_art",       "looks": 8, "style": 7, "vibe": 9, "text": "Wanderlust vibes, great look."},
    ],
}


def refresh_demo_content(conn) -> None:
    """Keep the checked-in demo users safe and consistent across restarts."""
    for user in USERS:
        conn.execute(
            "UPDATE profiles SET avatar_url = ? WHERE user_id = "
            "(SELECT id FROM users WHERE username = ?)",
            (user["avatar_url"], user["username"]),
        )

    for subject_username, review_list in REVIEWS.items():
        for review in review_list:
            conn.execute(
                """
                UPDATE reviews
                SET feedback_text = ?
                WHERE reviewed_profile_id = (SELECT id FROM profiles
                                              WHERE user_id = (SELECT id FROM users WHERE username = ?))
                  AND reviewer_user_id = (SELECT id FROM users WHERE username = ?)
                """,
                (review["text"], subject_username, review["reviewer"]),
            )


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

def seed() -> None:
    """Populate the database with demo data if it is empty."""
    init_db()

    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        if existing["cnt"] > 0:
            refresh_demo_content(conn)
            conn.commit()
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
    print(f"Seeded: {len(USERS)} users, {len(USERS)} profiles, {total_reviews} reviews.")


if __name__ == "__main__":
    seed()
