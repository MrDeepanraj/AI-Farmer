import base64
import json
import mimetypes
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=True)


def _get_api_key() -> str:
    for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        api_key = os.getenv(key_name, "").strip().strip('"').strip("'")
        if api_key:
            return api_key
    return ""


API_KEY = _get_api_key()


def _import_google_sdk():
    try:
        import google.genai as genai  # type: ignore

        return genai
    except Exception:
        try:
            import google.generativeai as genai  # type: ignore

            return genai
        except Exception:
            return None


def _build_gemini_client(api_key: str):
    if not api_key:
        return None

    google_sdk = _import_google_sdk()
    if google_sdk is None:
        return None

    if hasattr(google_sdk, "Client"):
        return google_sdk.Client(api_key=api_key)

    if hasattr(google_sdk, "configure"):
        google_sdk.configure(api_key=api_key)
        if hasattr(google_sdk, "GenerativeModel"):
            return google_sdk.GenerativeModel("gemini-2.0-flash")

    return google_sdk


GENAI_CLIENT = _build_gemini_client(API_KEY)


def _get_model_names() -> list[str]:
    return ["gemini-3.5-flash"]


def _get_vision_model_names() -> list[str]:
    return ["gemini-3.5-flash"]


def _call_gemini(prompt: str):
    if not API_KEY:
        return None, "Gemini API key is missing. Set GEMINI_API_KEY in the environment or .env file."

    if API_KEY == "your_gemini_api_key_here":
        return None, "Gemini API key is still using the placeholder value. Please update GEMINI_API_KEY in the .env file."

    if GENAI_CLIENT is not None:
        try:
            if hasattr(GENAI_CLIENT, "interactions") and hasattr(GENAI_CLIENT.interactions, "create"):
                response = GENAI_CLIENT.interactions.create(
                    model="gemini-2.0-flash",
                    input=prompt,
                )
                output_text = getattr(response, "output_text", None)
                if output_text:
                    return output_text, None
            elif hasattr(GENAI_CLIENT, "generate_content"):
                response = GENAI_CLIENT.generate_content(prompt)
                if hasattr(response, "text"):
                    return response.text, None
                if isinstance(response, dict):
                    return response.get("text") or "", None
        except Exception as exc:
            error_message = str(exc)
            if "401" in error_message or "Unauthorized" in error_message:
                return None, "Gemini returned Unauthorized. Check your API key, access permissions, and whether the key is valid for gemini-2.0-flash."
            return None, "Gemini is temporarily unavailable. Please try again later."

    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            f"?key={API_KEY}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [part.get("text", "") for part in parts if isinstance(part, dict)]
            return "".join(text_parts), None
        return None, "Gemini did not return any content."
    except Exception as exc:
        error_message = str(exc)
        if "401" in error_message or "Unauthorized" in error_message:
            return None, "Gemini returned Unauthorized. Check your API key, access permissions, and whether the key is valid for gemini-2.0-flash."
        return None, "Gemini is temporarily unavailable. Please try again later."


def generate_advice(crop, weather, symptoms, crop_profile, disease_tip):
    prompt = (
        f"You are a helpful agricultural advisor. "
        f"The user is growing {crop}. "
        f"Weather: {weather}. "
        f"Crop profile: {crop_profile}. "
        f"Symptoms: {symptoms or 'None provided'}. "
        f"Disease guidance: {disease_tip}. "
        f"Give concise practical advice for the farmer."
    )
    response, error = _call_gemini(prompt)
    if response is not None:
        return response
    return error or "Unable to contact Gemini API."


def recommend_crop_with_gemini(soil_type, season, state):
    prompt = (
        f"Recommend one suitable crop for a farm with soil type '{soil_type}', season '{season}', and state '{state}'. "
        f"Reply in plain text with a short crop name, a reason, and one sentence summary."
    )
    response, error = _call_gemini(prompt)
    if response is None:
        return None
    return {"crop": response.split("\n")[0], "reason": response, "summary": response}


def normalize_gemini_response(response: str) -> dict[str, str]:
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            summary = str(payload.get("summary") or "").strip()
            prevention_items = payload.get("prevention") or []
            monitoring_items = payload.get("monitoring") or []
            help_text = str(payload.get("when_to_seek_help") or "").strip()

            prevention_text = ""
            if isinstance(prevention_items, list):
                prevention_text = " | ".join(
                    str(
                        item.get("method") or item.get("title") or item.get("technique") or item
                    )
                    if isinstance(item, dict)
                    else str(item)
                    for item in prevention_items
                    if item is not None
                )
            elif prevention_items:
                prevention_text = str(prevention_items)

            monitoring_text = ""
            if isinstance(monitoring_items, list):
                monitoring_text = " | ".join(
                    str(
                        item.get("technique") or item.get("method") or item.get("title") or item
                    )
                    if isinstance(item, dict)
                    else str(item)
                    for item in monitoring_items
                    if item is not None
                )
            elif monitoring_items:
                monitoring_text = str(monitoring_items)

            return {
                "summary": summary,
                "prevention": prevention_text,
                "monitoring": monitoring_text,
                "when_to_seek_help": help_text,
            }
    except Exception:
        pass

    return {
        "summary": cleaned,
        "prevention": "",
        "monitoring": "",
        "when_to_seek_help": "",
    }


def _build_local_fallback(question: str) -> dict[str, str]:
    lowered = (question or "").lower()
    if any(word in lowered for word in ["pest", "insect", "aphid", "whitefly", "bug"]):
        summary = "Inspect plants often, remove affected leaves, and use gentle pest-control measures such as neem spray or physical removal."
        prevention = "Keep fields clean, rotate crops, and avoid overcrowding plants."
        monitoring = "Check the undersides of leaves every few days and act early when infestations appear."
    elif any(word in lowered for word in ["disease", "fungus", "blight", "mold", "rot"]):
        summary = "Improve airflow around crops, avoid wetting leaves, and remove damaged tissue promptly to slow the spread."
        prevention = "Water at the soil level, prune crowded growth, and sanitize tools between uses."
        monitoring = "Inspect new lesions or discoloration regularly and separate affected plants if needed."
    elif any(word in lowered for word in ["water", "irrig", "dry"]):
        summary = "Water deeply but less often, and adjust watering to the soil moisture and crop stage."
        prevention = "Mulch the soil and check moisture before irrigating to avoid waste or stress."
        monitoring = "Look for wilting, dry leaf tips, and uneven growth as signs to adjust irrigation."
    else:
        summary = "Monitor crop health regularly, keep the field clean, and act early when symptoms or pests appear."
        prevention = "Use good sanitation, balanced nutrition, and timely field observation."
        monitoring = "Check leaves, stems, and roots every few days for changes in color, growth, or damage."

    return {
        "status": "ok",
        "summary": summary,
        "prevention": prevention,
        "monitoring": monitoring,
        "when_to_seek_help": "Contact a local agricultural extension officer if symptoms spread quickly or crop loss increases.",
    }


def ask_gemini(question: str) -> dict[str, str]:
    prompt = (
        "You are a helpful agricultural assistant. "
        f"Answer this farming question clearly and practically: {question}. "
        "Return a valid JSON object with these exact keys: "
        "summary, prevention, monitoring, when_to_seek_help."
    )
    response, error = _call_gemini(prompt)
    if response is not None:
        payload = normalize_gemini_response(response)
        return {"status": "ok", **payload}

    fallback = _build_local_fallback(question)
    if error and "api key" in error.lower():
        fallback["summary"] = (
            error + " For now, here is practical general advice you can use immediately."
        )
    else:
        fallback["summary"] = (
            "Gemini is temporarily unavailable, so here is practical general guidance you can use right away: "
            + fallback["summary"]
        )

    return fallback


def build_disease_payload(mime_type: str, encoded_image: str) -> dict:
    return {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an agricultural plant disease expert. "
                            "Analyze this crop image. Return a valid JSON object with these exact keys: "
                            "disease_name, symptoms, treatment, organic_solution, chemical_solution. "
                            "Keep values concise and practical."
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": encoded_image,
                        }
                    },
                ]
            }
        ]
    }


def parse_disease_analysis(text: str) -> dict[str, str]:
    sections = {
        "disease_name": "",
        "symptoms": "",
        "treatment": "",
        "organic_solution": "",
        "chemical_solution": "",
    }

    if not text:
        return sections

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            for key in sections:
                value = payload.get(key) or payload.get(key.replace("_", "-")) or payload.get(key.replace("_", " "))
                if value:
                    sections[key] = str(value).strip()
            return sections
    except Exception:
        pass

    label_map = {
        "disease name": "disease_name",
        "symptoms": "symptoms",
        "treatment": "treatment",
        "organic solution": "organic_solution",
        "chemical solution": "chemical_solution",
    }

    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        for label, key in label_map.items():
            if line.lower().startswith(label + ":") or line.lower().startswith(label + "-"):
                value = line.split(":", 1)[1].strip() if ":" in line else line.split("-", 1)[1].strip()
                sections[key] = re.sub(r"\s+", " ", value).strip()
                break

    if not any(sections.values()):
        disease_match = re.search(r"(?:disease|infection|blight|rust|mold|spot|rot)\s*(?:name)?\s*[:\-]\s*([A-Za-z0-9 /()&-]+)", cleaned, re.IGNORECASE)
        if disease_match:
            sections["disease_name"] = disease_match.group(1).strip()

    return sections


def analyze_disease_image(image_path: str, mime_type: str | None = None) -> dict[str, str]:
    api_key = _get_api_key()
    if not api_key:
        return {
            "status": "error",
            "message": "Gemini API key is missing. Please set GEMINI_API_KEY in the .env file before analyzing images.",
            "disease_name": "",
            "symptoms": "",
            "treatment": "",
            "organic_solution": "",
            "chemical_solution": "",
        }
    if api_key == "your_gemini_api_key_here":
        return {
            "status": "error",
            "message": "Gemini API key is still using the placeholder value. Please update GEMINI_API_KEY in the .env file.",
            "disease_name": "",
            "symptoms": "",
            "treatment": "",
            "organic_solution": "",
            "chemical_solution": "",
        }

    if mime_type is None:
        mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    payload = build_disease_payload(mime_type, encoded_image)

    model_names = _get_vision_model_names()
    last_error = None

    for model_name in model_names:
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
                params={"key": api_key},
                json=payload,
                timeout=40,
            )
            if response.status_code == 404:
                last_error = (
                    "Gemini 3.5 Flash is not available for this API key. "
                    "Please verify that your key has access to Gemini 3.5 Flash."
                )
                break
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = parse_disease_analysis(text)
            return parsed
        except requests.Timeout:
            last_error = "No internet connection. Please check your connection and try again."
            break
        except requests.ConnectionError:
            last_error = "No internet connection. Please check your connection and try again."
            break
        except requests.RequestException:
            last_error = "Gemini Vision is temporarily unavailable. Please try again later."
            break
        except Exception:
            last_error = "Gemini Vision returned an unexpected error. Please try again later."
            break

    return {
        "status": "error",
        "message": last_error or "Gemini could not analyze the image right now. Please try again shortly.",
        "disease_name": "",
        "symptoms": "",
        "treatment": "",
        "organic_solution": "",
        "chemical_solution": "",
    }
