# TempoTailor

AI-powered music curation for runners. Enter your target pace and a vibe description to get a curated Spotify playlist tuned to your cadence—no more skipping mid-run.

## What the app does

1. **Pace to BPM** – Converts your target pace (e.g. 5:30 min/km) into the ideal BPM for your run.
2. **Vibe translation** – An LLM turns your natural language (e.g. "cyberpunk city run", "chill morning jog") into Spotify-style parameters: energy, valence, danceability, genres, and optional release year.
3. **Curated quality** – Deezer discovers BPM-matched tracks; an LLM judge filters them to the 20 that best fit your vibe. You save as draft, edit, or publish to Spotify.

## LLMs & tools used to build it

- **Cursor** – AI-assisted coding.
- **LLM**: Local [LM Studio](https://lmstudio.ai/) (OpenAI-compatible API) with models like Qwen 2.5 7B Instruct—no cloud API keys required.
- **Music discovery**: [Deezer API](https://developers.deezer.com/) for BPM-filtered charts and search.
- **Playback & playlists**: [Spotify Web API](https://developer.spotify.com/documentation/web-api) (OAuth, playlist creation, ISRC-based track resolution).
- **Stack**: React + Vite (TypeScript), Tailwind CSS, FastAPI, SQLAlchemy + SQLite, Spotipy, httpx.

## Why both Deezer and Spotify?

**Deezer** is used for discovery because its search API supports BPM filters (`bpm_min`, `bpm_max`), so you can query by genre and tempo in one call. Charts and search are public (no auth required), and tracks include BPM and ISRC for cross-platform matching.

**Spotify** is used for playlists because users log in with Spotify and expect playlists in their library. Spotify’s API doesn’t support BPM-based search—you’d have to fetch recommendations and filter by audio features, which is slower and less direct. Spotify is where users actually listen, so playlists need to live there.

**Flow:** Deezer discovers BPM-matched tracks → we resolve them to Spotify via ISRC → Spotify stores the playlist in the user’s account.

## Technical hurdles

### 1. Cursor hallucination: Deezer BPM search

While building the discovery flow, Cursor claimed the Deezer API doesn’t support BPM-based search—suggesting we’d have to fetch tracks and filter client-side. That would have been slow and wasteful.

**How I got past it:** I asked Cursor to search for up-to-date Deezer API docs. It turned out Deezer _does_ support BPM filters via advanced search: `genre:"pop" bpm_min:"120" bpm_max:"130"`. I used that and avoided the workaround entirely.

---

## Prerequisites

1. **LM Studio** – Run a compatible model locally at `http://localhost:1234`
2. **Spotify Developer App** – Create an app at [Spotify Dashboard](https://developer.spotify.com/dashboard) and add redirect URI: `http://localhost:8000/auth/callback`
