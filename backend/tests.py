"""
tests.py - Backend test suite (12 core cases).

Run with: pytest tests.py -v
"""

import pytest
import sys
import os
import tempfile

# Make sure we run against the test module, not the installed copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use a temporary file-based DB so all connections share the same schema.
# (SQLite :memory: creates a separate DB per connection, which breaks tests.)
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = _db_path
os.environ["JWT_SECRET"] = "test-secret"

from app import app as flask_app
from models import init_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a fresh test client backed by an in-memory database."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        with flask_app.app_context():
            init_db()
        yield c


# Helper – sign up a fresh user and return (client, token, user_id)
def _signup(client, username, email, password="password123"):
    resp = client.post(
        "/api/auth/signup",
        json={"username": username, "email": email, "password": password},
    )
    data = resp.get_json()
    return resp, data


def _login(client, email, password="password123"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp, resp.get_json()


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. AUTH TESTS
# ---------------------------------------------------------------------------

class TestAuth:
    def test_signup_valid(self, client):
        """Signup creates a user and returns a JWT token."""
        resp, data = _signup(client, "test_user_1", "test1@example.com")
        assert resp.status_code == 201
        assert "token" in data
        assert data["username"] == "test_user_1"
        assert "password" not in data
        assert "password_hash" not in data

    def test_signup_duplicate_username(self, client):
        """Signing up with a taken username returns 409."""
        _signup(client, "dup_user", "dup@example.com")
        resp, data = _signup(client, "dup_user", "dup2@example.com")
        assert resp.status_code == 409
        assert "error" in data

    def test_login_valid(self, client):
        """Valid credentials return a token and user info."""
        _signup(client, "login_user", "login@example.com")
        resp, data = _login(client, "login@example.com")
        assert resp.status_code == 200
        assert "token" in data
        assert "username" in data

    def test_login_invalid_credentials(self, client):
        """Wrong password returns 401."""
        _signup(client, "bad_pw_user", "badpw@example.com")
        resp, data = _login(client, "badpw@example.com", password="wrongpassword")
        assert resp.status_code == 401
        assert "error" in data


# Monotonic counter so autouse fixtures get unique usernames in the shared DB
_counter = 0

def _unique(base):
    global _counter
    _counter += 1
    return f"{base}_{_counter}"


# ---------------------------------------------------------------------------
# 2. PROFILE TESTS
# ---------------------------------------------------------------------------

class TestProfiles:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Create a user + profile for profile tests."""
        uname = _unique("profile_user")
        resp, data = _signup(client, uname, f"{uname}@example.com")
        self.token = data["token"]
        self.user_id = data["id"]

        # Create profile
        create_resp = client.post(
            "/api/profiles",
            json={"bio": "Test bio", "avatar_url": "https://ui-avatars.com/api/?name=test"},
            headers=_auth_headers(self.token),
        )
        self.profile_id = create_resp.get_json().get("id")

    def test_create_profile(self, client):
        """Creates profile with bio and avatar_url, returns 201."""
        # Sign up a new user (different from autouse fixture user)
        _, u = _signup(client, "new_profile_user", "newprofile@example.com")
        token = u["token"]
        resp = client.post(
            "/api/profiles",
            json={"bio": "A new bio", "avatar_url": "https://ui-avatars.com/api/?name=newtest"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["bio"] == "A new bio"
        assert "id" in data

    def test_get_all_profiles(self, client):
        """GET /api/profiles returns list + total."""
        resp = client.get("/api/profiles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "profiles" in data
        assert "total" in data
        assert isinstance(data["profiles"], list)

    def test_get_single_profile(self, client):
        """GET /api/profiles/:id returns profile with reviews list."""
        resp = client.get(f"/api/profiles/{self.profile_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == self.profile_id
        assert "reviews" in data
        assert isinstance(data["reviews"], list)

    def test_edit_profile(self, client):
        """PATCH own profile updates bio."""
        resp = client.patch(
            f"/api/profiles/{self.profile_id}",
            json={"bio": "Updated bio"},
            headers=_auth_headers(self.token),
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["bio"] == "Updated bio"


# ---------------------------------------------------------------------------
# 3. REVIEW TESTS
# ---------------------------------------------------------------------------

class TestReviews:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Two users: owner (with a profile) and reviewer."""
        oname = _unique("review_owner")
        _, owner_data = _signup(client, oname, f"{oname}@example.com")
        self.owner_token = owner_data["token"]
        self.owner_id = owner_data["id"]

        create_resp = client.post(
            "/api/profiles",
            json={"bio": "Profile to be reviewed", "avatar_url": "https://ui-avatars.com/api/?name=review"},
            headers=_auth_headers(self.owner_token),
        )
        self.profile_id = create_resp.get_json().get("id")

        rname = _unique("reviewer_user")
        _, reviewer_data = _signup(client, rname, f"{rname}@example.com")
        self.reviewer_token = reviewer_data["token"]

    def test_post_review_valid(self, client):
        """Posting a valid review returns 201 with all rating fields."""
        resp = client.post(
            f"/api/profiles/{self.profile_id}/reviews",
            json={"looks_rating": 8, "style_rating": 7, "vibe_rating": 9,
                  "feedback_text": "Great vibe!"},
            headers=_auth_headers(self.reviewer_token),
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["looks_rating"] == 8
        assert data["style_rating"] == 7
        assert data["vibe_rating"]  == 9

    def test_post_review_invalid_rating(self, client):
        """Ratings outside 1-10 are rejected with 400."""
        resp = client.post(
            f"/api/profiles/{self.profile_id}/reviews",
            json={"looks_rating": 11, "style_rating": 0, "vibe_rating": 5},
            headers=_auth_headers(self.reviewer_token),
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "errors" in data

    def test_cannot_review_own_profile(self, client):
        """Profile owner cannot submit a review on their own profile."""
        resp = client.post(
            f"/api/profiles/{self.profile_id}/reviews",
            json={"looks_rating": 9, "style_rating": 9, "vibe_rating": 9},
            headers=_auth_headers(self.owner_token),
        )
        assert resp.status_code == 403

    def test_rating_aggregation(self, client):
        """After posting a review, the profile's avg ratings are updated."""
        # Fresh profile for clean aggregation
        _, agg_user = _signup(client, "agg_owner", "agg_owner@example.com")
        create_resp = client.post(
            "/api/profiles",
            json={"bio": "Aggregation test", "avatar_url": ""},
            headers=_auth_headers(agg_user["token"]),
        )
        agg_profile_id = create_resp.get_json()["id"]

        # Reviewer posts a review
        _, reviewer = _signup(client, "agg_reviewer", "agg_reviewer@example.com")
        client.post(
            f"/api/profiles/{agg_profile_id}/reviews",
            json={"looks_rating": 8, "style_rating": 6, "vibe_rating": 10},
            headers=_auth_headers(reviewer["token"]),
        )

        # Fetch profile and check averages
        resp = client.get(f"/api/profiles/{agg_profile_id}")
        data = resp.get_json()
        assert data["avg_looks"]   == 8.0
        assert data["avg_style"]   == 6.0
        assert data["avg_vibe"]    == 10.0
        assert data["review_count"] == 1
        expected_overall = round((8 + 6 + 10) / 3, 2)
        assert data["avg_overall"] == expected_overall
