"""
Weather API integration.
"""

from datetime import datetime, timedelta
from typing import Dict, List
import random

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
            days: Number of days to fetch (max 5 for free tier, 7+ requires daily endpoint)

        Returns:
            List of forecast dictionaries (one per day)
        """
        location = f"{city},{country_code}" if country_code else city

        # OpenWeatherMap free tier: 5-day forecast with 3-hour intervals (40 items max)
        # For 7-day forecast, we'll use daily aggregation or limit to 5 days
        if days > 5:
            # Try to use daily forecast endpoint (requires paid tier)
            # Fall back to 5-day forecast if not available
            try:
                url = f"{self.base_url}/forecast/daily"
                params = {"q": location, "appid": self.api_key, "units": "metric", "cnt": days}
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return [self._normalize_daily_forecast(item) for item in data.get("list", [])]
            except Exception:
                # Fall back to 5-day forecast
                days = 5

        # Use 3-hour forecast endpoint (free tier)
        url = f"{self.base_url}/forecast"
        # Limit to 40 items max (5 days * 8 intervals per day)
        max_items = min(days * 8, 40)
        params = {"q": location, "appid": self.api_key, "units": "metric", "cnt": max_items}

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        forecasts = [self._normalize_forecast(item) for item in data.get("list", [])]

        # Group by day and take one forecast per day (preferably midday)
        daily_forecasts = {}
        for forecast in forecasts:
            forecast_date = forecast["datetime"].date()
            if forecast_date not in daily_forecasts:
                daily_forecasts[forecast_date] = forecast
            else:
                # Prefer forecasts closer to midday (12:00)
                current_hour = forecast["datetime"].hour
                existing_hour = daily_forecasts[forecast_date]["datetime"].hour
                if abs(current_hour - 12) < abs(existing_hour - 12):
                    daily_forecasts[forecast_date] = forecast

        # Return sorted list of daily forecasts
        return sorted(daily_forecasts.values(), key=lambda x: x["datetime"])[:days]

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
            "datetime": datetime.fromtimestamp(weather_data["dt"]),
            "temperature": weather_data["main"]["temp"],
            "feels_like": weather_data["main"]["feels_like"],
            "humidity": weather_data["main"]["humidity"],
            "weather": weather_data["weather"][0]["main"],
            "description": weather_data["weather"][0]["description"],
            "wind_speed": weather_data["wind"]["speed"],
            "visibility": weather_data.get("visibility", 10000) / 1000,  # km
        }

    def _normalize_daily_forecast(self, forecast_data: Dict) -> Dict:
        """Normalize daily forecast data from daily endpoint."""
        return {
            "datetime": datetime.fromtimestamp(forecast_data["dt"]),
            "temperature": forecast_data["temp"]["day"],
            "feels_like": forecast_data["feels_like"]["day"],
            "temp_min": forecast_data["temp"]["min"],
            "temp_max": forecast_data["temp"]["max"],
            "humidity": forecast_data["humidity"],
            "weather": forecast_data["weather"][0]["main"],
            "description": forecast_data["weather"][0]["description"],
            "wind_speed": forecast_data["speed"],
            "precipitation_probability": forecast_data.get("pop", 0) * 100,
            "rain_volume": forecast_data.get("rain", 0),
        }


class MockWeatherClient:
    """Mock weather client for when API key is missing."""

    def get_current_weather(self, city: str, country_code: str = "") -> Dict:
        # Determine "realistic" weather based on city name hash to be consistent
        seed = sum(ord(c) for c in city)
        random.seed(seed)

        conditions = [
            {"main": "Clear", "desc": "clear sky"},
            {"main": "Clouds", "desc": "scattered clouds"},
            {"main": "Rain", "desc": "light rain"},
            {"main": "Clouds", "desc": "overcast clouds"},
        ]

        condition = random.choice(conditions)
        temp = 15 + random.randint(-5, 15)

        return {
            "datetime": datetime.now(),
            "temperature": temp,
            "feels_like": temp - 2,
            "humidity": 60 + random.randint(-10, 20),
            "weather": condition["main"],
            "description": condition["desc"],
            "wind_speed": 5 + random.randint(0, 10),
            "visibility": 10.0,
        }

    def get_forecast(self, city: str, country_code: str = "", days: int = 7) -> List[Dict]:
        seed = sum(ord(c) for c in city)
        random.seed(seed)

        base_temp = 15 + random.randint(-5, 15)
        forecasts = []

        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            daily_temp = base_temp + random.randint(-5, 5)
            conditions = [
                {"main": "Clear", "desc": "clear sky"},
                {"main": "Clouds", "desc": "partly cloudy"},
                {"main": "Rain", "desc": "light rain"},
            ]
            condition = random.choice(conditions)

            forecasts.append(
                {
                    "datetime": date,
                    "temperature": daily_temp,
                    "feels_like": daily_temp - 2,
                    "temp_min": daily_temp - 4,
                    "temp_max": daily_temp + 4,
                    "humidity": 50 + random.randint(0, 30),
                    "weather": condition["main"],
                    "description": condition["desc"],
                    "wind_speed": 5 + random.randint(0, 10),
                    "precipitation_probability": random.randint(0, 40),
                    "rain_volume": 0,
                }
            )

        return forecasts
