"""
Weather tools for the conversational agent.

Provides tools for current weather and forecast queries.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WeatherOutput(BaseModel):
    """Output schema for current weather."""

    location: str = Field(description="Location name")
    temperature: float = Field(description="Temperature in Celsius")
    feels_like: float = Field(description="Feels like temperature in Celsius")
    description: str = Field(description="Weather description")
    humidity: int = Field(description="Humidity percentage")
    wind_speed: float = Field(description="Wind speed in m/s")
    icon: str = Field(description="Weather icon code", default="")
    timestamp: str = Field(description="Timestamp of the weather data")


class ForecastDay(BaseModel):
    """Single day forecast."""

    date: str = Field(description="Date in YYYY-MM-DD format")
    day_name: str = Field(description="Day name (Monday, Tuesday, etc.)")
    temp_high: float = Field(description="High temperature")
    temp_low: float = Field(description="Low temperature")
    description: str = Field(description="Weather description")
    precipitation_chance: int = Field(description="Chance of precipitation (%)", default=0)


class ForecastOutput(BaseModel):
    """Output schema for weather forecast."""

    location: str = Field(description="Location name")
    days: List[ForecastDay] = Field(description="Daily forecasts", default_factory=list)
    summary: str = Field(description="Overall forecast summary")


def _get_user_location():
    """Get user's saved location from database."""
    try:
        from backend.api.database import SessionLocal
        from backend.api.models import User

        db = SessionLocal()
        try:
            user = db.query(User).first()
            if user and user.location_city:
                return user.location_city, user.location_country or "US"
            return None, None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to get user location: {e}")
        return None, None


def _get_weather_client():
    """Get the weather client."""
    try:
        from backend.integrations.weather import WeatherClient, MockWeatherClient

        api_key = os.getenv("WEATHER_API_KEY")
        if api_key:
            return WeatherClient(api_key)
        return MockWeatherClient()
    except ImportError:
        logger.warning("Weather client not available")
        return None


@tool
def get_current_weather(city: Optional[str] = None, country: Optional[str] = None) -> WeatherOutput:
    """
    Get the current weather for a location.

    If no location is provided, uses the user's saved location.

    Args:
        city: City name (optional, uses saved location if not provided)
        country: Country code like US, UK (optional)

    Returns:
        Current weather conditions including temperature, humidity, and description
    """
    # Get location
    if not city:
        city, country = _get_user_location()
        if not city:
            return WeatherOutput(
                location="Unknown",
                temperature=0,
                feels_like=0,
                description="No location set. Please set your location first.",
                humidity=0,
                wind_speed=0,
                timestamp=datetime.now().isoformat(),
            )

    if not country:
        country = "US"

    client = _get_weather_client()
    if not client:
        return WeatherOutput(
            location=f"{city}, {country}",
            temperature=20,
            feels_like=20,
            description="Weather service temporarily unavailable",
            humidity=50,
            wind_speed=5,
            timestamp=datetime.now().isoformat(),
        )

    try:
        weather = client.get_current_weather(city, country)
        return WeatherOutput(
            location=f"{city}, {country}",
            temperature=round(weather.get("temperature", 0), 1),
            feels_like=round(weather.get("feels_like", 0), 1),
            description=weather.get("description", "").capitalize(),
            humidity=weather.get("humidity", 0),
            wind_speed=round(weather.get("wind_speed", 0), 1),
            icon=weather.get("icon", ""),
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return WeatherOutput(
            location=f"{city}, {country}",
            temperature=0,
            feels_like=0,
            description=f"Error fetching weather: {str(e)}",
            humidity=0,
            wind_speed=0,
            timestamp=datetime.now().isoformat(),
        )


@tool
def get_weather_forecast(city: Optional[str] = None, country: Optional[str] = None, days: int = 5) -> ForecastOutput:
    """
    Get the weather forecast for upcoming days.

    Args:
        city: City name (optional, uses saved location if not provided)
        country: Country code like US, UK (optional)
        days: Number of days to forecast (1-7, default: 5)

    Returns:
        Multi-day weather forecast with temperatures and conditions
    """
    # Get location
    if not city:
        city, country = _get_user_location()
        if not city:
            return ForecastOutput(
                location="Unknown", days=[], summary="No location set. Please set your location first."
            )

    if not country:
        country = "US"

    days = min(max(days, 1), 7)  # Clamp between 1 and 7

    client = _get_weather_client()
    if not client:
        return ForecastOutput(
            location=f"{city}, {country}", days=[], summary="Weather service temporarily unavailable"
        )

    try:
        forecast_data = client.get_forecast(city, country, days)

        if not forecast_data:
            return ForecastOutput(location=f"{city}, {country}", days=[], summary="No forecast data available")

        forecast_days = []
        for item in forecast_data[:days]:
            dt = item.get("datetime")
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            elif not isinstance(dt, datetime):
                dt = datetime.now()

            forecast_days.append(
                ForecastDay(
                    date=dt.strftime("%Y-%m-%d"),
                    day_name=dt.strftime("%A"),
                    temp_high=round(item.get("temp_max", item.get("temperature", 0)), 1),
                    temp_low=round(item.get("temp_min", item.get("temperature", 0)), 1),
                    description=item.get("description", "").capitalize(),
                    precipitation_chance=item.get("precipitation_probability", 0),
                )
            )

        # Create summary
        if forecast_days:
            temps = [d.temp_high for d in forecast_days]
            avg_temp = sum(temps) / len(temps)
            summary = f"Expect temperatures around {avg_temp:.0f}°C over the next {len(forecast_days)} days."

            # Check for rain
            rainy_days = [d for d in forecast_days if d.precipitation_chance > 50]
            if rainy_days:
                summary += f" Rain likely on {', '.join(d.day_name for d in rainy_days[:2])}."
        else:
            summary = "No forecast data available."

        return ForecastOutput(location=f"{city}, {country}", days=forecast_days, summary=summary)

    except Exception as e:
        logger.error(f"Forecast API error: {e}")
        return ForecastOutput(location=f"{city}, {country}", days=[], summary=f"Error fetching forecast: {str(e)}")
