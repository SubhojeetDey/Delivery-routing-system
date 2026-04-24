import requests
import json,settings
from datetime import datetime

weather_codes = {
    0: "Sunny ☀️",
    1: "Mainly Clear 🌤️",
    2: "Partly Cloudy ⛅",
    3: "Cloudy ☁️",
    45: "Fog 🌫️",
    48: "Depositing Rime Fog 🌫️",
    51: "Light Drizzle 🌦️",
    53: "Moderate Drizzle 🌦️",
    55: "Heavy Drizzle 🌧️",
    61: "Light Rain 🌧️",
    63: "Moderate Rain 🌧️",
    65: "Heavy Rain 🌧️",
    71: "Snow ❄️",
    80: "Rain Showers 🌧️",
    95: "Thunderstorm ⛈️"
}


def get_forecast(lon,lat):
    Clear = [1,2,3]
    Rain = [51,53,55,61,63,65,80,95]
    Heatwave = [0]
    Fog = [45,48,71]
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&forecast_days=2"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        "&timezone=auto"
        "&current=temperature_2m,weathercode"
    )
    req = requests.get(url)
    data = req.json()
    weather_code = data["current"]["weathercode"]
    if weather_code:
        if weather_code in Clear:
            return "Clear"
        if weather_code in Rain:
            return "Rain"
        if weather_code in Heatwave:
            return "Heatwave"
        if weather_code in Fog:
            return "Fog"


def get_traffic(lon,lat):

    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={settings.api_key}&point={lat},{lon}"

    res = requests.get(url)
    data = res.json()
    flow = data["flowSegmentData"]
    current = flow["currentSpeed"]
    free = flow["freeFlowSpeed"]

    ratio = current/free

    if ratio > 0.75:
        return "Low"
    elif ratio > 0.5:
        return "Medium"
    elif ratio > 0.25:
        return "High"
    else:
        return "VeryHigh"


        