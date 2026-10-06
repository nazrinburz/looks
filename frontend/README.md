# Frontend

React + Vite frontend for the Profile Review Community App.

## Setup

```bash
npm install
cp .env.example .env
npm run dev          # dev server on http://localhost:5173
npm run build        # production bundle
```

## Environment

```
VITE_API_URL=http://localhost:5000/api
```

## Pages

| Route | Page | Description |
|---|---|---|
| `/` | Home | Profile feed, sort controls |
| `/auth` | AuthPage | Login / Signup tabs |
| `/profile/me` | ProfilePage | Authenticated user's profile |
| `/profile/:id` | ProfilePage | Any user's profile + reviews |
| `/profile/:id/review` | ReviewPage | Rate a profile (sliders) |
| `/profile/:id/edit` | EditProfilePage | Edit bio & avatar |
| `/profile/create` | EditProfilePage | Create new profile |

## Components

- **Navbar** – Fixed frosted-glass navbar with auth state
- **ProfileCard** – Grid card with avatar, ratings, review count
- **ReviewList** – Anonymous review cards with edit/delete
- **RatingBreakdown** – Bar chart per rating dimension

## Design

Dark mode design system with:
- CSS custom properties (tokens)
- Inter + Space Grotesk fonts
- Glassmorphism navbar
- Gradient accent colors
- Micro-animations & hover effects
