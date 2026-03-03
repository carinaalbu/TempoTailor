"""LLM services using local LM Studio (OpenAI-compatible API)."""

import json
from pathlib import Path

from openai import OpenAI

from app.core.config import settings

_LOG_PATH = Path(__file__).resolve().parents[1].parent.parent / "debug-ed1f52.log"

# #region agent log
def _log(loc: str, msg: str, data: dict, hid: str):
    try:
        with open(_LOG_PATH, "a") as f:
            f.write(json.dumps({"sessionId": "ed1f52", "location": loc, "message": msg, "data": data, "timestamp": __import__("time").time() * 1000, "hypothesisId": hid}) + "\n")
    except Exception:
        pass
# #endregion
from app.schemas.llm import VibeTranslation, JudgeResult

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=settings.lm_studio_base_url_normalized,
            api_key="lm-studio",  # Not used by LM Studio
        )
    return _client


VIBE_SYSTEM = """You translate natural language "vibe" descriptions into Spotify API parameters.
Output valid JSON matching this schema:
{
  "target_energy": 0.0-1.0,
  "target_valence": 0.0-1.0,
  "target_danceability": 0.0-1.0,
  "seed_genres": ["genre1", "genre2"],
  "seed_artists": [],
  "seed_tracks": []
}
Use only Spotify-valid genre names (e.g. pop, rock, electronic, hip-hop, indie).
Output ONLY the JSON object. No reasoning, explanation, or markdown."""

JUDGE_SYSTEM = """You are a harsh music curator. Given a list of tracks and a vibe description, select exactly 20 tracks that best match the vibe.
Drop any tracks that don't fit. Output valid JSON:
{
  "track_ids": ["id1", "id2", ...],
  "vibe_score": 1-100,
  "curator_note": "Brief note about the selection"
}
Return ONLY the JSON object, no markdown or extra text."""


def translate_vibe(vibe_prompt: str) -> VibeTranslation:
    client = _get_client()
    # #region agent log
    _log("llm_service.py:translate_vibe", "before_api_call", {"vibe_len": len(vibe_prompt)}, "H1")
    # #endregion
    try:
        resp = client.chat.completions.create(
            model=settings.lm_studio_model or "",
            messages=[
                {"role": "system", "content": VIBE_SYSTEM},
                {"role": "user", "content": vibe_prompt},
            ],
            max_tokens=512,
        )
    except Exception as e:
        # #region agent log
        _log("llm_service.py:translate_vibe", "api_exception", {"error": str(e)}, "H2")
        # #endregion
        raise RuntimeError(f"LLM request failed: {e}") from e
    # #region agent log
    choices_len = len(resp.choices) if resp.choices else 0
    c0 = resp.choices[0] if (resp.choices and len(resp.choices) > 0) else None
    content_is_none = c0.message.content is None if c0 else "no_choices"
    _log("llm_service.py:translate_vibe", "after_api_call", {"choices_len": choices_len, "content_is_none": content_is_none}, "H1")
    # #endregion
    if not resp.choices or len(resp.choices) == 0:
        raise RuntimeError(
            "LLM returned no response. Ensure LM Studio is running with a model loaded and ready."
        )
    content = resp.choices[0].message.content
    if content is None:
        raise RuntimeError(
            "LLM returned empty content. Ensure LM Studio has a model loaded and ready."
        )
    text = content.strip()
    # Strip <think>...</think>
    if "<think>" in text:
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        else:
            idx = text.find("{")
            text = text[idx:] if idx >= 0 else text.split("<think>", 1)[-1].strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    # Extract JSON if model output reasoning before the object (e.g. DeepSeek R1 without think tags)
    if not text.strip().startswith("{"):
        idx = text.find("{")
        if idx >= 0:
            text = text[idx:]
    try:
        data = json.loads(text)
        return VibeTranslation.model_validate(data)
    except (json.JSONDecodeError, Exception) as e:
        # #region agent log
        _log("llm_service.py:translate_vibe", "parse_error", {"raw_text_preview": text[:500], "error": str(e)}, "H1")
        # #endregion
        raise ValueError(f"Invalid LLM vibe output: {e}") from e


def judge_tracks(
    track_list: list[dict],
    vibe_prompt: str,
) -> JudgeResult:
    """Filter tracks to exactly 20. track_list items must have 'id' and 'name'."""
    # #region agent log
    _log("llm_service.py:judge_tracks", "entry", {"track_list_len": len(track_list or [])}, "H1")
    # #endregion
    client = _get_client()
    tracks_str = "\n".join(
        f"- {t.get('id', '')} | {t.get('name', 'Unknown')} - {t.get('artists', [{}])[0].get('name', '')}"
        for t in track_list[:40]
    )
    user_msg = f"Vibe: {vibe_prompt}\n\nTracks:\n{tracks_str}\n\nSelect exactly 20 track IDs that best match the vibe."
    resp = client.chat.completions.create(
        model=settings.lm_studio_model or "",
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=512,
    )
    # #region agent log
    jc0 = resp.choices[0] if resp.choices else None
    _log("llm_service.py:judge_tracks", "after_api_call", {"choices_len": len(resp.choices or []), "content_is_none": jc0.message.content is None if jc0 else "no_choices"}, "H1")
    # #endregion
    if not resp.choices:
        raise RuntimeError("LLM returned no response for track filtering.")
    jcontent = resp.choices[0].message.content
    if jcontent is None:
        raise RuntimeError("LLM returned empty content for track filtering.")
    text = jcontent.strip()
    if "<think>" in text:
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        else:
            idx = text.find("{")
            text = text[idx:] if idx >= 0 else text.split("<think>", 1)[-1].strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    # Extract JSON if model output reasoning before the object
    if not text.strip().startswith("{"):
        idx = text.find("{")
        if idx >= 0:
            text = text[idx:]
    try:
        data = json.loads(text)
        result = JudgeResult.model_validate(data)
    except (json.JSONDecodeError, Exception) as e:
        raise ValueError(f"Invalid LLM judge output: {e}") from e
    # Ensure exactly 20 - truncate or pad from input if needed
    if len(result.track_ids) > 20:
        result.track_ids = result.track_ids[:20]
    elif len(result.track_ids) < 20 and track_list:
        ids_seen = set(result.track_ids)
        for t in track_list:
            if len(result.track_ids) >= 20:
                break
            tid = t.get("id")
            if tid and tid not in ids_seen:
                result.track_ids.append(tid)
                ids_seen.add(tid)
    return result
