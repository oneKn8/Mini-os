export interface WeatherCurrent {
  location: { city: string, country: string }
  datetime: string
  temperature: number
  feels_like: number
  humidity: number
  weather: Array<{ id: number, main: string, description: string, icon: string }>
  description: string
  wind_speed: number
  visibility?: number
}

export interface ForecastItem {
  datetime: string
  temperature: number
  feels_like: number
  temp_min: number
  temp_max: number
  humidity: number
  weather: Array<{ id: number, main: string, description: string, icon: string }>
  description: string
  wind_speed: number
  precipitation_probability: number
  rain_volume: number
}

export interface WeatherForecast {
  location: { city: string, country: string }
  forecast: ForecastItem[]
}

export async function fetchCurrentWeather(): Promise<WeatherCurrent> {
  const response = await fetch('/api/weather/current')
  if (!response.ok) {
    throw new Error('Failed to fetch current weather')
  }
  return response.json()
}

export async function fetchForecast(days: number = 7): Promise<WeatherForecast> {
  const response = await fetch(`/api/weather/forecast?days=${days}`)
  if (!response.ok) {
    throw new Error('Failed to fetch forecast')
  }
  return response.json()
}
