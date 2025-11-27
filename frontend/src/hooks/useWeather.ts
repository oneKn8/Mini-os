import { useEffect } from 'react'
import { useCurrentWeather, useWeatherForecast } from '../api/weather'
import { useRealtime } from '../contexts/RealtimeContext'

export function useWeatherWithRealtime(days: number = 7) {
  const { data: current, isLoading: currentLoading, error: currentError, refetch: refetchCurrent } = useCurrentWeather()
  const { data: forecast, isLoading: forecastLoading, error: forecastError, refetch: refetchForecast } = useWeatherForecast(days)
  const { sseWeatherLastMessage } = useRealtime()

  // Listen for real-time weather updates
  useEffect(() => {
    if (sseWeatherLastMessage?.type === 'weather_updated') {
      refetchCurrent()
      refetchForecast()
    }
  }, [sseWeatherLastMessage, refetchCurrent, refetchForecast])

  return {
    current,
    forecast,
    isLoading: currentLoading || forecastLoading,
    error: currentError || forecastError,
    refetch: () => {
      refetchCurrent()
      refetchForecast()
    },
  }
}

