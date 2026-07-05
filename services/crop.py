import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from services.gemini import recommend_crop_with_gemini

BASE_DIR = Path(__file__).resolve().parent.parent
CROP_DATA_FILE = BASE_DIR / "crop_data.json"


@lru_cache(maxsize=1)
def load_crop_data() -> dict[str, Any]:
    if not CROP_DATA_FILE.exists():
        return {}
    with CROP_DATA_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def get_crop_profile(crop_name: str) -> dict[str, Any]:
    crop_name = crop_name.strip().lower()
    data = load_crop_data()
    profile = data.get(crop_name)
    if profile:
        return profile

    return {
        "name": crop_name,
        "summary": "No detailed crop profile found. Use general care practices and local guidance.",
        "best_practices": ["Monitor soil moisture", "Inspect for pests", "Ensure adequate sunlight"],
    }


def recommend_crop(soil_type: str, season: str, state: str) -> dict[str, Any]:
    data = load_crop_data()
    soil_key = _normalize(soil_type)
    season_key = _normalize(season)
    state_key = _normalize(state)

    for crop_name, crop_data in data.items():
        conditions = crop_data.get("conditions", {})
        soil_matches = not conditions.get("soil") or any(
            _normalize(option) in soil_key or soil_key in _normalize(option)
            for option in conditions.get("soil", [])
        )
        season_matches = not conditions.get("season") or any(
            _normalize(option) in season_key or season_key in _normalize(option)
            for option in conditions.get("season", [])
        )
        state_matches = not conditions.get("state") or any(
            _normalize(option) in state_key or state_key in _normalize(option)
            for option in conditions.get("state", [])
        )

        if soil_matches and season_matches and state_matches:
            return {
                "recommended_crop": crop_data.get("name", crop_name.title()),
                "reason": crop_data.get("reason", "This crop is a strong fit for the provided soil, season, and state."),
                "source": "local",
                "summary": crop_data.get("summary", "Good choice for the given conditions."),
            }

    ai_recommendation = recommend_crop_with_gemini(soil_type, season, state)
    return {
        "recommended_crop": ai_recommendation.get("crop") if ai_recommendation else "Gemini AI Suggested Crop",
        "reason": ai_recommendation.get("reason") if ai_recommendation else "No local match was found. Use Gemini AI for a better recommendation.",
        "source": "gemini",
        "summary": ai_recommendation.get("summary") if ai_recommendation else "The local crop list does not have a direct match.",
    }
