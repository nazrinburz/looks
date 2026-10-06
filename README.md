# LooksApp – Profile Review Community

A full-stack community platform where users create profiles and the community rates & reviews them across **Looks**, **Style**, and **Vibe** (1-10 each).

## Features

- 🔐 JWT authentication (signup / login)
- 👤 Profile creation with bio & avatar URL
- 🌐 Browse all profiles — sorted by rating or newest
- ⭐ Rate profiles across 3 dimensions (Looks, Style, Vibe)
- 💬 Leave anonymous constructive text reviews
- 📊 Rating breakdown chart (score distribution per dimension)
- ✏️ Edit & delete your own reviews
- 🗑 Delete your own profile (cascades reviews)
- 🌱 5 pre-loaded profiles with 20 reviews on first run
- 🖼️ Demo profiles use adult portrait photos served by Unsplash under its free license

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.8+, Flask, SQLite |
| Auth | PyJWT, Werkzeug |
| Frontend | React 18 + Vite |
| Styling | Vanilla CSS (dark mode design system) |

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python app.py        # starts on http://localhost:5000 + seeds data
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev          # starts on http://localhost:5173
```

### Tests

```bash
cd backend
pytest tests.py -v   # 12 test cases, all should pass
```

## Project Structure

```
looks_app/
├── backend/
│   ├── app.py          # Flask app + all routes
│   ├── models.py       # SQLite schema + helpers
│   ├── auth.py         # JWT + password hashing
│   ├── seed_data.py    # 5 profiles + 20 reviews
│   ├── config.py       # Environment config
│   ├── tests.py        # 12 pytest cases
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── pages/      # Home, ProfilePage, ReviewPage, EditProfilePage, AuthPage
        ├── components/ # Navbar, ProfileCard, ReviewList, RatingBreakdown
        ├── api.js      # Fetch wrapper
        └── auth.jsx    # Auth context
```

## API

See [backend/README.md](backend/README.md) for full API docs.

Key endpoints:
- `POST /api/auth/signup` · `POST /api/auth/login`
- `GET /api/profiles` · `POST /api/profiles`
- `GET /api/profiles/:id` · `PATCH /api/profiles/:id` · `DELETE /api/profiles/:id`
- `POST /api/profiles/:id/reviews` · `GET /api/profiles/:id/reviews`
- `PATCH /api/reviews/:id` · `DELETE /api/reviews/:id`

## Git History

```
Add project documentation
Connect frontend to backend API
Add pages (feed, profile, review, auth)
Add frontend project structure (React+Vite)
Add seed data (5 profiles + 25 reviews)
Add backend tests (12 cases, all passing)
Add review endpoints (create, edit, delete)
Add profile endpoints (CRUD, browse)
Add authentication endpoints (signup, login)
Add database schema and auth utilities
Add gitignore
```

## Security

- Passwords hashed with PBKDF2-SHA256 (Werkzeug)
- JWT tokens, 24-hour expiry
- Auth required on all write endpoints
- Users can only edit/delete their own content
- Input validation: ratings 1-10, feedback ≤ 500 chars
- No passwords in logs or API responses
