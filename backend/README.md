# Backend API

Flask REST API for the Profile Review Community App.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
python app.py          # starts server + seeds data automatically
```

## Testing

```bash
pytest tests.py -v
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET` | dev secret | JWT signing key (change in prod!) |
| `DATABASE_URL` | `./database.db` | SQLite file path |
| `FLASK_DEBUG` | `False` | Enable debug mode |
| `FLASK_PORT` | `5000` | Server port |
| `CORS_ORIGINS` | localhost/127.0.0.1:5173,3000 | Allowed CORS origins |

## API Reference

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/signup` | ❌ | Create account |
| POST | `/api/auth/login` | ❌ | Login, get token |

### Profiles

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/profiles` | ❌ | List all profiles |
| GET | `/api/profiles/:id` | ❌ | View profile + reviews |
| POST | `/api/profiles` | ✅ | Create profile |
| PATCH | `/api/profiles/:id` | ✅ (own) | Update profile |
| DELETE | `/api/profiles/:id` | ✅ (own) | Delete profile |
| GET | `/api/me/profile` | ✅ | Get own profile |

### Reviews

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/profiles/:id/reviews` | ✅ | Post a review |
| GET | `/api/profiles/:id/reviews` | ❌ | List reviews |
| PATCH | `/api/reviews/:id` | ✅ (own) | Edit review |
| DELETE | `/api/reviews/:id` | ✅ (own) | Delete review |
| GET | `/api/profiles/:id/my-review` | ✅ | Get your review |
| GET | `/api/profiles/:id/rating-breakdown` | ❌ | Score distribution |

## Logging

Logs are written to `logs/app.log` and the console.

Format: `[YYYY-MM-DD HH:MM:SS] LEVEL - METHOD /path - STATUS - Xms`

## Demo profile images

The five seeded demo profiles use stable adult portrait URLs from
[Unsplash](https://unsplash.com/license). These images replace the local
illustrated placeholders and are refreshed when `seed_data.py` runs. User-created
profiles are not changed.
