import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import BASE_DIR, UPLOAD_DIR
from services.crop import recommend_crop
from services.gemini import analyze_disease_image, ask_gemini
from services.weather import get_weather

app = FastAPI(title="AI Farmer Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def build_error_response(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/recommend-crop")
async def recommend_crop_endpoint(
    soil_type: str = Form(...),
    season: str = Form(...),
    state: str = Form(...),
) -> JSONResponse:
    if not soil_type.strip() or not season.strip() or not state.strip():
        return build_error_response("Please fill in all crop recommendation fields.")

    try:
        result = recommend_crop(soil_type, season, state)
    except Exception as exc:
        return build_error_response(f"Unable to generate a crop recommendation: {exc}")

    return JSONResponse(
        {
            "status": "ok",
            "recommended_crop": result.get("recommended_crop"),
            "reason": result.get("reason"),
            "summary": result.get("summary"),
            "source": result.get("source", "local"),
        }
    )


@app.post("/chat")
async def chat_endpoint(question: str = Form(...)) -> JSONResponse:
    if not question or not question.strip():
        return build_error_response("Please enter a farming question.")

    try:
        reply = ask_gemini(question)
    except Exception as exc:
        return build_error_response(f"Unable to contact Gemini right now: {exc}")

    if isinstance(reply, dict) and reply.get("status") == "error":
        return build_error_response(reply.get("message") or "Unable to contact Gemini right now.")

    if isinstance(reply, dict):
        return JSONResponse({"status": "ok", **reply})

    return JSONResponse({"status": "ok", "summary": str(reply), "prevention": "", "monitoring": "", "when_to_seek_help": ""})


@app.post("/detect-disease")
async def detect_disease_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    if file is None or not getattr(file, "filename", None):
        return build_error_response("Please upload an image file.")

    extension = Path(file.filename).suffix.lower() or ".jpg"
    if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return build_error_response("Unsupported image type. Please upload a JPG, PNG, or WEBP image.")

    content = await file.read()
    if not content:
        return build_error_response("The uploaded file is empty.")

    safe_name = f"{uuid.uuid4().hex}{extension}"
    upload_path = UPLOAD_DIR / safe_name

    try:
        with upload_path.open("wb") as buffer:
            buffer.write(content)
    except OSError as exc:
        return build_error_response(f"Unable to save the uploaded image: {exc}")

    mime_type = file.content_type or "image/jpeg"
    if not mime_type.startswith("image/"):
        return build_error_response("The selected file is not a valid image.")

    try:
        result = analyze_disease_image(str(upload_path), mime_type=mime_type)
    except Exception as exc:
        return build_error_response(f"Unable to analyze the image right now: {exc}")

    if isinstance(result, dict) and result.get("status") == "error":
        return build_error_response(result.get("message") or "Unable to analyze the image right now.")

    return JSONResponse({"status": "ok", "image_url": f"/uploads/{safe_name}", **result})


@app.get("/weather")
async def weather_endpoint(city: str | None = None) -> JSONResponse:
    result = get_weather(city or "Lagos")
    if isinstance(result, dict) and result.get("status") == "error":
        return build_error_response(result.get("message") or "Unable to get weather data right now.")
    return JSONResponse(result)


@app.post("/weather")
async def weather_post_endpoint(city: str = Form(...)) -> JSONResponse:
    if not city or not city.strip():
        return build_error_response("Please enter a city name.")

    try:
        result = get_weather(city)
    except Exception as exc:
        return build_error_response(f"Unable to get weather data right now: {exc}")

    if isinstance(result, dict) and result.get("status") == "error":
        return build_error_response(result.get("message") or "Unable to get weather data right now.")

    return JSONResponse(result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
