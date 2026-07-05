import os
from typing import Any

import requests

from services.gemini import ask_gemini


def get_weather(city: str) -> dict[str, Any]:
    city_name = (city or "").strip()
    if not city_name:
        return {
            "status": "error",
            "city": "",
            "temperature": "N/A",
            "humidity": "N/A",
            "wind_speed": "N/A",
            "condition": "No city provided",
            "farming_advice": "",
            "message": "Please enter a city name.",
        }

    api_key = os.getenv("WEATHER_API_KEY", "").strip().strip('"').strip("'")
    if not api_key:
        return {
            "status": "error",
            "city": city_name,
            "temperature": "N/A",
            "humidity": "N/A",
            "wind_speed": "N/A",
            "condition": "Unavailable",
            "farming_advice": "",
            "message": "OpenWeather API key is missing. Please set WEATHER_API_KEY in the .env file.",
        }
    if api_key == "your_openweather_api_key_here":
        return {
            "status": "error",
            "city": city_name,
            "temperature": "N/A",
            "humidity": "N/A",
            "wind_speed": "N/A",
            "condition": "Unavailable",
            "farming_advice": "",
            "message": "OpenWeather API key is still using the placeholder value. Please update WEATHER_API_KEY in the .env file.",
        }

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city_name, "appid": api_key, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 404:
            return {
                "status": "error",
                "city": city_name,
                "temperature": "N/A",
                "humidity": "N/A",
                "wind_speed": "N/A",
                "condition": "Unknown",
                "farming_advice": "",
                "message": "City not found. Please enter a valid city name.",
            }

        response.raise_for_status()
        data = response.json()
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather = data.get("weather", [{}])[0]
        temperature = main.get("temp")
        humidity = main.get("humidity")
        wind_speed = wind.get("speed")
        condition = str(weather.get("description", "No data")).capitalize()
        city_display = data.get("name", city_name)

        try:
            advice = ask_gemini(
                f"Give one short farming tip for {city_display} with {condition} weather at {temperature}°C, humidity {humidity}%, and wind speed {wind_speed} m/s."
            )
            if isinstance(advice, dict):
                farming_advice = str(advice.get("summary", "") or "").strip()
            else:
                farming_advice = str(advice).strip()

            if not farming_advice or "Unable to reach Gemini" in farming_advice or "Gemini API key" in farming_advice:
                farming_advice = "Use the current weather to plan irrigation and protect crops from sudden changes."
        except Exception:
            farming_advice = "Use the current weather to plan irrigation and protect crops from sudden changes."

        return {
            "status": "ok",
            "city": city_display,
            "temperature": f"{temperature}°C" if temperature is not None else "N/A",
            "humidity": f"{humidity}%" if humidity is not None else "N/A",
            "wind_speed": f"{wind_speed} m/s" if wind_speed is not None else "N/A",
            "condition": condition or "No data",
            "farming_advice": farming_advice,
            "message": "Weather data loaded successfully.",
        }
    except requests.Timeout:
        return {
            "status": "error",
            "city": city_name,
            "temperature": "N/A",
            "humidity": "N/A",
            "wind_speed": "N/A",
            "condition": "Unavailable",
            "farming_advice": "",
            "message": "No internet connection. Please check your connection and try again.",
        }
    except requests.ConnectionError:
        return {
            "status": "error",
            "city": city_name,
            "temperature": "N/A",
            "humidity": "N/A",
            "wind_speed": "N/A",
            "condition": "Unavailable",
            "farming_advice": "",
            "message": "No internet connection. Please check your connection and try again.",
        }
    except requests.RequestException as exc:
        return {
            "status": "error",
            "city": city_name,
            "temperature": "N/A",
            "humidity": "N/A",
            "wind_speed": "N/A",
            "condition": "Unavailable",
            "farming_advice": "",
            "message": f"The weather service is temporarily unavailable: {exc}",
        }
    except Exception as exc:
        return {
            "status": "error",
            "city": city_name,
            "temperature": "N/A",
            "humidity": "N/A",
            "wind_speed": "N/A",
            "condition": "Unavailable",
            "farming_advice": "",
            "message": f"Unable to process weather data: {exc}",
        }
