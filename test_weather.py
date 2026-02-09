#!/usr/bin/env python3

import requests

# Coordinates for Hamburg, Germany
lat, lon = 53.5511, 9.9937

url = f"https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": lat,
    "longitude": lon,
    "current_weather": True
}

response = requests.get(url, params=params)
data = response.json()
print(data["current_weather"])
