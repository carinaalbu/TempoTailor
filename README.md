# TempoTailor

AI-powered music curation for runners. Enter your target pace and a vibe description to get a curated Spotify playlist.

## Tech Stack

- **Frontend**: React + Vite (TypeScript), Tailwind CSS, Axios
- **Backend**: Python + FastAPI, SQLAlchemy + SQLite, Spotipy, OpenAI SDK (LM Studio)
- **LLM**: Local LM Studio at `http://localhost:1234/v1` (no API keys required)

## Prerequisites

1. **LM Studio** – Run a compatible model locally at `http://localhost:1234`
2. **Spotify Developer App** – Create an app at [Spotify Dashboard](https://developer.spotify.com/dashboard) and add redirect URI: `http://localhost:8000/auth/callback`

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your Spotify credentials
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SPOTIFY_CLIENT_ID` | From Spotify Dashboard |
| `SPOTIFY_CLIENT_SECRET` | From Spotify Dashboard |
| `SPOTIFY_REDIRECT_URI` | `http://localhost:8000/auth/callback` |
| `LM_STUDIO_BASE_URL` | `http://localhost:1234/v1` |
| `DATABASE_URL` | `sqlite:///./tempo_tailor.db` |

## Run Flow

1. Log in with Spotify
2. Enter target pace (e.g. `5:30` or `5.5` min/km) and vibe (e.g. "cyberpunk city run")
3. Generate playlist – AI translates vibe, over-fetches Spotify recommendations, and filters to 20 tracks
4. Save as draft, edit, or publish to Spotify

## Tests

```bash
cd backend && python -m pytest tests/ -v
```
