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

import { useQuery } from '@tanstack/react-query'

export async function fetchForecast(days: number = 7): Promise<WeatherForecast> {
  const response = await fetch(`/api/weather/forecast?days=${days}`)
  if (!response.ok) {
    throw new Error('Failed to fetch forecast')
  }
  return response.json()
}

// React Query hooks
export function useCurrentWeather() {
  return useQuery({
    queryKey: ['weather', 'current'],
    queryFn: fetchCurrentWeather,
    refetchInterval: 300000, // Refetch every 5 minutes
  })
}

export function useWeatherForecast(days: number = 7) {
  return useQuery({
    queryKey: ['weather', 'forecast', days],
    queryFn: () => fetchForecast(days),
    refetchInterval: 300000, // Refetch every 5 minutes
  })
}
