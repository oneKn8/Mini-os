"""
Weather API routes
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.database import get_db
from backend.api.models import User, UserPreferences
from backend.integrations.weather import WeatherClient, MockWeatherClient

router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_client() -> Union[WeatherClient, MockWeatherClient]:
    """Get weather client or mock if API key is not configured."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return MockWeatherClient()
    return WeatherClient(api_key)


def get_user_location(db: Session, user: User) -> tuple[str, str]:
    """Get user location from User model or use defaults."""
    if user and user.location_city:
        city = user.location_city
        country = user.location_country or ""
        return city, country

    # Default location
    return "New York", "US"


@router.get("/current")
async def get_current_weather(db: Session = Depends(get_db)):
    """Get current weather for user's location."""
    import logging

    logger = logging.getLogger(__name__)

    # TODO: Get user from session/auth token
    user = db.query(User).first()

    # Get location
    if user:
        city, country = get_user_location(db, user)
    else:
        city, country = "New York", "US"

    client = get_weather_client()

    try:
        weather = client.get_current_weather(city, country)
        # Ensure datetime is string for JSON serialization
        dt = weather["datetime"]

        weather_main = weather["weather"]
        weather_desc = weather["description"]

        return {
            "location": {"city": city, "country": country},
            "datetime": dt.isoformat() if isinstance(dt, datetime) else str(dt),
            "temperature": weather["temperature"],
            "feels_like": weather["feels_like"],
            "humidity": weather["humidity"],
            "weather": [{"id": 800, "main": weather_main, "description": weather_desc, "icon": "01d"}],
            "description": weather_desc,
            "wind_speed": weather["wind_speed"],
            "visibility": weather.get("visibility"),
        }
    except Exception as e:
        logger.error(f"Failed to fetch current weather for {city}, {country}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather: {str(e)}")


@router.get("/forecast")
async def get_weather_forecast(
    days: int = 7,
    db: Session = Depends(get_db),
):
    """Get weather forecast for user's location."""
    import logging

    logger = logging.getLogger(__name__)

    # TODO: Get user from session/auth token
    user = db.query(User).first()

    if days < 1 or days > 7:
        days = 7

    # Get location
    if user:
        city, country = get_user_location(db, user)
    else:
        city, country = "New York", "US"

    client = get_weather_client()

    try:
        forecast = client.get_forecast(city, country, days)
        return {
            "location": {"city": city, "country": country},
            "forecast": [
                {
                    "datetime": item["datetime"].isoformat()
                    if isinstance(item["datetime"], datetime)
                    else str(item["datetime"]),
                    "temperature": item["temperature"],
                    "feels_like": item["feels_like"],
                    "temp_min": item["temp_min"],
                    "temp_max": item["temp_max"],
                    "humidity": item["humidity"],
                    "weather": [
                        {"id": 800, "main": item["weather"], "description": item["description"], "icon": "01d"}
                    ],
                    "description": item["description"],
                    "wind_speed": item["wind_speed"],
                    "precipitation_probability": item.get("precipitation_probability", 0),
                    "rain_volume": item.get("rain_volume", 0),
                }
                for item in forecast
            ],
        }
    except Exception as e:
        logger.error(f"Failed to fetch forecast for {city}, {country}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast: {str(e)}")
