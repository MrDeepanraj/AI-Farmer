# AI Farmer Assistant

AI Farmer Assistant is a FastAPI web app that helps farmers make practical decisions with AI. It combines crop recommendations, farming advice, weather insights, and plant disease analysis in one simple dashboard.

## Features
- Crop recommendation based on soil type, season, and location
- AI-powered farm guidance with Gemini
- Weather lookup for any city with farming advice
- Plant disease image analysis with Gemini Vision
- Friendly error handling for missing credentials, invalid uploads, and network issues

## Tech Stack
- Python 3.12+
- FastAPI
- Jinja2 templates
- HTML, CSS, and JavaScript
- Gemini API
- OpenWeather API

## Prerequisites
- Python 3.12 or newer
- Internet access for AI and weather APIs
- API keys for:
  - Gemini: GEMINI_API_KEY
  - OpenWeather: WEATHER_API_KEY

## 1. Create a virtual environment (Windows PowerShell)

From the project root:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 2. Install packages

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure environment variables

Create a file named .env in the project root using the example below:

```env
GEMINI_API_KEY=your_gemini_api_key_here
WEATHER_API_KEY=your_openweather_api_key_here
```

You can also copy the provided example file:

```powershell
Copy-Item .env.example .env
```

## 4. Run the FastAPI app

```powershell
python app.py
```

The app will start at:

```text
http://127.0.0.1:8000/
```

## 5. Open localhost

Open the browser and visit:

```text
http://127.0.0.1:8000/
```

## 6. Test every feature

### Crop Recommendation
1. Open the homepage.
2. Fill in the crop recommendation form.
3. Submit the form.
4. Confirm that a crop recommendation appears.

### Ask AI
1. Scroll to the Ask AI section.
2. Type a farming question such as: "How do I protect maize from pests?"
3. Submit the form.
4. Confirm that structured guidance is shown.

### Weather
1. Enter a city name such as Lagos or Nairobi.
2. Submit the form.
3. Confirm that temperature, humidity, wind speed, and farming advice appear.

### Disease Detection
1. Upload a clear image of a crop leaf or plant.
2. Submit the form.
3. Confirm that the app returns a disease analysis or a friendly error message if the image or API is unavailable.

### Error handling checks
- Try submitting an empty image upload.
- Remove or leave the API keys blank to see the friendly setup messages.
- Disconnect from the internet briefly to verify offline handling.

## Project Structure

```text
AI-Farmer/
├── app.py
├── crop_data.json
├── requirements.txt
├── README.md
├── .env.example
├── services/
│   ├── crop.py
│   ├── gemini.py
│   └── weather.py
├── static/
├── templates/
└── tests/
```

## Run tests

```powershell
pytest -q
```

## Troubleshooting
- If the app does not start, make sure the virtual environment is activated.
- If Gemini or weather features fail, verify the API keys in .env.
- If images do not upload, ensure the file is a supported image type such as JPG, PNG, or WEBP.
- If the browser shows a blank result, check the terminal for error messages and confirm the app is still running.

## License

This project is intended for educational and demonstration purposes.
