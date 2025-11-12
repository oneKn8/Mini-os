"""
Weather API integration.
"""

from datetime import datetime
from typing import Dict, List

import requests


class WeatherClient:
    """Weather API client using OpenWeatherMap."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_forecast(self, city: str, country_code: str = "", days: int = 7) -> List[Dict]:
        """
        Get weather forecast for a location.

        Args:
            city: City name
            country_code: ISO country code (optional)
            days: Number of days to fetch

        Returns:
            List of forecast dictionaries
        """
        location = f"{city},{country_code}" if country_code else city

        url = f"{self.base_url}/forecast"
        params = {"q": location, "appid": self.api_key, "units": "metric", "cnt": days * 8}  # 8 forecasts per day

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return [self._normalize_forecast(item) for item in data.get("list", [])]

    def _normalize_forecast(self, forecast_data: Dict) -> Dict:
        """Normalize weather forecast data."""
        return {
            "datetime": datetime.fromtimestamp(forecast_data["dt"]),
            "temperature": forecast_data["main"]["temp"],
            "feels_like": forecast_data["main"]["feels_like"],
            "temp_min": forecast_data["main"]["temp_min"],
            "temp_max": forecast_data["main"]["temp_max"],
            "humidity": forecast_data["main"]["humidity"],
            "weather": forecast_data["weather"][0]["main"],
            "description": forecast_data["weather"][0]["description"],
            "wind_speed": forecast_data["wind"]["speed"],
            "precipitation_probability": forecast_data.get("pop", 0) * 100,
            "rain_volume": forecast_data.get("rain", {}).get("3h", 0),
        }

    def get_current_weather(self, city: str, country_code: str = "") -> Dict:
        """Get current weather for a location."""
        location = f"{city},{country_code}" if country_code else city

        url = f"{self.base_url}/weather"
        params = {"q": location, "appid": self.api_key, "units": "metric"}

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return self._normalize_current_weather(data)

    def _normalize_current_weather(self, weather_data: Dict) -> Dict:
        """Normalize current weather data."""
        return {
            "datetime": datetime.now(),
            "temperature": weather_data["main"]["temp"],
            "feels_like": weather_data["main"]["feels_like"],
            "humidity": weather_data["main"]["humidity"],
            "weather": weather_data["weather"][0]["main"],
            "description": weather_data["weather"][0]["description"],
            "wind_speed": weather_data["wind"]["speed"],
            "visibility": weather_data.get("visibility", 10000) / 1000,  # km
        }
