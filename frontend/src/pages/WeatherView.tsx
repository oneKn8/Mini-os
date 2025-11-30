import { useState, useEffect } from 'react'
import { Wind, Droplets, MapPin, Sun, Eye, Gauge, Sunrise, Sunset, CloudRain, Wind as WindIcon } from 'lucide-react'
import { clsx } from 'clsx'
import { ParallaxWeatherBackground } from '../components/Weather/ParallaxWeatherBackground'
import { ParallaxChart } from '../components/Weather/ParallaxChart'
import WeatherIcon from '../components/Weather/WeatherIcon'
import { useWeatherWithRealtime } from '../hooks/useWeather'
import { useSettingsStore, convertTemperature } from '../store/settingsStore'
import { useScreenUpdates } from '../store/screenController'

export default function WeatherView() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const [timeOfDay, setTimeOfDay] = useState<'day' | 'night' | 'dusk' | 'dawn'>('day')

  // Settings and data
  const { tempUnit, updateSetting } = useSettingsStore()
  const { current, forecast } = useWeatherWithRealtime(7)
  const { isAgentFocused } = useScreenUpdates('/weather')

  // Calculate time of day
  useEffect(() => {
    const hour = new Date().getHours()
    if (hour >= 5 && hour < 7) setTimeOfDay('dawn')
    else if (hour >= 7 && hour < 17) setTimeOfDay('day')
    else if (hour >= 17 && hour < 19) setTimeOfDay('dusk')
    else setTimeOfDay('night')
  }, [])

  const handleMouseMove = (e: React.MouseEvent) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 40
    const y = (e.clientY / window.innerHeight - 0.5) * 40
    setMousePos({ x, y })
  }

  // Format temperature with unit
  const formatTemp = (celsius: number) => {
    const value = convertTemperature(celsius)
    return `${Math.round(value)}°`
  }

  const chartData = forecast?.forecast.map(f => convertTemperature(f.temperature)) || []
  const days = forecast?.forecast.map(f =>
    new Date(f.datetime).toLocaleDateString('en-US', { weekday: 'short' })
  ) || []

  // Generate hourly forecast (simulated - you can extend backend for real hourly data)
  const hourlyForecast = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    temp: current?.temperature ? current.temperature + (Math.random() * 4 - 2) : 0,
    condition: current?.weather[0]?.main || 'Clear'
  }))

  return (
    <div
      data-weather-page
      className="relative w-full min-h-full bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 text-zinc-100"
      onMouseMove={handleMouseMove}
    >
      <div className={clsx(
        "relative w-full min-h-full",
        isAgentFocused && "ring-1 ring-inset ring-blue-500/20"
      )}>
        <ParallaxWeatherBackground
          mouseX={mousePos.x}
          mouseY={mousePos.y}
          timeOfDay={timeOfDay}
          weatherCondition={current?.weather[0]?.main || 'Clear'}
        />

        {/* Header */}
        <header className="sticky top-0 z-50 h-16 flex items-center justify-between px-6 border-b border-zinc-800/50 backdrop-blur-xl bg-zinc-950/80">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold text-zinc-100">Weather</h1>
            <div
              data-location-badge
              className="flex items-center px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20"
            >
              <MapPin size={14} className="text-blue-400 mr-2" />
              <span className="text-blue-400 text-sm font-medium">
                {current ? `${current.location.city}` : 'Loading...'}
              </span>
            </div>
          </div>

          {/* Temp Unit Toggle */}
          <div data-temp-unit className="flex items-center gap-1 bg-zinc-900/50 rounded-lg p-0.5 border border-zinc-800/50">
            <button
              onClick={() => updateSetting('tempUnit', 'celsius')}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-md transition-all font-medium",
                tempUnit === 'celsius'
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-500 hover:text-zinc-300"
              )}
            >
              °C
            </button>
            <button
              onClick={() => updateSetting('tempUnit', 'fahrenheit')}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-md transition-all font-medium",
                tempUnit === 'fahrenheit'
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-500 hover:text-zinc-300"
              )}
            >
              °F
            </button>
          </div>
        </header>

        {/* Main Content */}
        <div className="relative z-40 px-6 py-8 space-y-8 max-w-7xl mx-auto">
          {/* Hero Current Weather */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Current Temperature Card */}
            <div
              data-component="weather-widget"
              data-weather-current
              className="lg:col-span-2 rounded-2xl border border-zinc-800/50 bg-zinc-900/40 backdrop-blur-xl p-10 flex flex-col justify-between min-h-[320px]"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-8xl font-extralight text-zinc-50 tracking-tight mb-3">
                    {current ? formatTemp(current.temperature) : '--°'}
                  </h2>
                  <p className="text-2xl text-zinc-300 font-light capitalize mb-2">
                    {current?.description || 'Loading...'}
                  </p>
                  <p className="text-sm text-zinc-500">
                    Feels like {current?.feels_like ? formatTemp(current.feels_like) : '--'}
                  </p>
                </div>
                <WeatherIcon
                  condition={current?.weather[0]?.main || 'Clear'}
                  timeOfDay={timeOfDay}
                  size={96}
                  className="text-zinc-400"
                />
              </div>
              <div className="flex items-center gap-6 text-sm text-zinc-400 mt-8">
                <div className="flex items-center gap-2">
                  <Wind size={16} className="text-zinc-500" />
                  <span>{current?.wind_speed || '--'} m/s</span>
                </div>
                <div className="flex items-center gap-2">
                  <Droplets size={16} className="text-zinc-500" />
                  <span>{current?.humidity || '--'}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <Eye size={16} className="text-zinc-500" />
                  <span>10 km</span>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div data-weather-stats className="space-y-4">
              <StatCard
                icon={Wind}
                label="Wind Speed"
                value={current ? `${current.wind_speed} m/s` : '--'}
                subvalue="SW 15°"
              />
              <StatCard
                icon={Droplets}
                label="Humidity"
                value={current ? `${current.humidity}%` : '--'}
                subvalue="Comfortable"
              />
              <StatCard
                icon={Gauge}
                label="Pressure"
                value="1013 hPa"
                subvalue="Normal"
              />
              <StatCard
                icon={Sun}
                label="UV Index"
                value="3"
                subvalue="Moderate"
              />
            </div>
          </div>

          {/* Hourly Forecast */}
          <div className="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 backdrop-blur-xl p-6">
            <h3 className="text-lg font-semibold text-zinc-200 mb-4">Hourly Forecast</h3>
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
              {hourlyForecast.slice(0, 12).map((hour, idx) => (
                <div
                  key={idx}
                  className="flex-shrink-0 w-20 rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-4 text-center hover:bg-zinc-800/40 transition-colors"
                >
                  <p className="text-xs text-zinc-500 mb-2">{hour.hour}</p>
                  <WeatherIcon
                    condition={hour.condition}
                    timeOfDay="day"
                    size={24}
                    className="mx-auto mb-2 text-zinc-400"
                  />
                  <p className="text-sm text-zinc-200 font-medium">
                    {formatTemp(hour.temp)}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* 7-Day Forecast */}
          <div className="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 backdrop-blur-xl p-6">
            <h3 className="text-lg font-semibold text-zinc-200 mb-4">7-Day Forecast</h3>
            <div data-weather-forecast className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
              {days.map((day, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-4 text-center hover:bg-zinc-800/40 transition-colors group"
                >
                  <p className="text-xs text-zinc-500 uppercase mb-3 font-medium">{day}</p>
                  <WeatherIcon
                    condition={forecast?.forecast[idx]?.weather[0]?.main || 'Clear'}
                    timeOfDay="day"
                    size={32}
                    className="mx-auto mb-3 text-zinc-400 group-hover:text-zinc-300 transition-colors"
                  />
                  <p className="text-lg text-zinc-100 font-semibold mb-1">
                    {chartData[idx] ? `${Math.round(chartData[idx])}°` : '--'}
                  </p>
                  <p className="text-xs text-zinc-600">
                    {chartData[idx] ? `${Math.round(chartData[idx] - 5)}°` : '--'}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Temperature Chart */}
          <div
            data-weather-chart
            className="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 backdrop-blur-xl p-6 relative h-64"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-zinc-200">Temperature Trend</h3>
              <span className="text-sm text-zinc-500">
                {tempUnit === 'celsius' ? 'Celsius' : 'Fahrenheit'}
              </span>
            </div>
            <div className="absolute inset-0 top-16 bottom-12 left-6 right-6">
              <ParallaxChart
                data={chartData}
                mouseX={mousePos.x}
                mouseY={mousePos.y}
              />
            </div>
            <div className="absolute bottom-4 left-6 right-6 flex justify-between text-xs text-zinc-600">
              {days.map((d, i) => (
                <span key={i}>{d}</span>
              ))}
            </div>
          </div>

          {/* Additional Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Sun Times */}
            <div className="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 backdrop-blur-xl p-6">
              <h3 className="text-lg font-semibold text-zinc-200 mb-6">Sun & Moon</h3>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-orange-500/10">
                      <Sunrise size={20} className="text-orange-400" />
                    </div>
                    <div>
                      <p className="text-sm text-zinc-500">Sunrise</p>
                      <p className="text-base text-zinc-200 font-medium">6:45 AM</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-zinc-600">12h 34m ago</p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-blue-500/10">
                      <Sunset size={20} className="text-blue-400" />
                    </div>
                    <div>
                      <p className="text-sm text-zinc-500">Sunset</p>
                      <p className="text-base text-zinc-200 font-medium">7:32 PM</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-zinc-600">in 5h 21m</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Wind & Precipitation */}
            <div className="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 backdrop-blur-xl p-6">
              <h3 className="text-lg font-semibold text-zinc-200 mb-6">Wind & Rain</h3>
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <WindIcon size={18} className="text-zinc-400" />
                      <span className="text-sm text-zinc-400">Wind Direction</span>
                    </div>
                    <span className="text-base text-zinc-200 font-medium">SW</span>
                  </div>
                  <div className="h-2 bg-zinc-800/50 rounded-full overflow-hidden">
                    <div className="h-full w-2/3 bg-gradient-to-r from-blue-500 to-cyan-500"></div>
                  </div>
                  <p className="text-xs text-zinc-600 mt-1">Gusts up to {current?.wind_speed ? (current.wind_speed * 1.5).toFixed(1) : '--'} m/s</p>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <CloudRain size={18} className="text-zinc-400" />
                      <span className="text-sm text-zinc-400">Precipitation</span>
                    </div>
                    <span className="text-base text-zinc-200 font-medium">0%</span>
                  </div>
                  <div className="h-2 bg-zinc-800/50 rounded-full overflow-hidden">
                    <div className="h-full w-0 bg-gradient-to-r from-blue-500 to-blue-600"></div>
                  </div>
                  <p className="text-xs text-zinc-600 mt-1">No rain expected</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Enhanced stat card
function StatCard({
  icon: Icon,
  label,
  value,
  subvalue
}: {
  icon: React.ElementType
  label: string
  value: string
  subvalue?: string
}) {
  return (
    <div className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-5 hover:bg-zinc-800/30 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-lg bg-zinc-800/50">
          <Icon size={18} className="text-zinc-400" />
        </div>
      </div>
      <div>
        <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">{label}</p>
        <p className="text-2xl text-zinc-100 font-semibold">{value}</p>
        {subvalue && <p className="text-xs text-zinc-600 mt-1">{subvalue}</p>}
      </div>
    </div>
  )
}
