import { useState, useEffect, useRef } from 'react'
import { Wind, Droplets, MapPin, Sun, Thermometer } from 'lucide-react'
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
  const heroRef = useRef<HTMLDivElement>(null)

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

  return (
    <div
      data-weather-page
      className="relative w-full min-h-screen overflow-hidden select-none bg-black text-zinc-100 p-4 md:p-6"
      onMouseMove={handleMouseMove}
    >
      <div className={clsx(
        "relative max-w-5xl mx-auto rounded-2xl overflow-hidden border bg-zinc-950/80 backdrop-blur-xl",
        isAgentFocused ? "border-blue-500/30" : "border-zinc-800/50"
      )}>
        <ParallaxWeatherBackground
          mouseX={mousePos.x}
          mouseY={mousePos.y}
          timeOfDay={timeOfDay}
          weatherCondition={current?.weather[0]?.main || 'Clear'}
        />

        {/* Header */}
        <header className="h-14 flex items-center justify-between px-5 border-b border-zinc-800/50 backdrop-blur-sm relative z-40">
          <div className="flex items-center gap-4">
            <h1 className="text-base font-medium text-zinc-200">Weather</h1>
            <div
              data-location-badge
              className="flex items-center px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20"
            >
              <MapPin size={11} className="text-blue-400 mr-1.5" />
              <span className="text-blue-400 text-[11px] tracking-wide uppercase">
                {current ? `${current.location.city}` : 'Loading...'}
              </span>
            </div>
          </div>

          {/* Temp Unit Toggle */}
          <div data-temp-unit className="flex items-center gap-1 bg-zinc-900/50 rounded-lg p-0.5 border border-zinc-800/50">
            <button
              onClick={() => updateSetting('tempUnit', 'celsius')}
              className={clsx(
                "px-2.5 py-1 text-xs rounded-md transition-all",
                tempUnit === 'celsius' 
                  ? "bg-zinc-800 text-zinc-200" 
                  : "text-zinc-500 hover:text-zinc-400"
              )}
            >
              °C
            </button>
            <button
              onClick={() => updateSetting('tempUnit', 'fahrenheit')}
              className={clsx(
                "px-2.5 py-1 text-xs rounded-md transition-all",
                tempUnit === 'fahrenheit' 
                  ? "bg-zinc-800 text-zinc-200" 
                  : "text-zinc-500 hover:text-zinc-400"
              )}
            >
              °F
            </button>
          </div>
        </header>

        {/* Main Content */}
        <div className="p-5 relative z-40">
          {/* Hero Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-6">
            {/* Current Weather */}
            <div
              ref={heroRef}
              data-weather-current
              className="lg:col-span-2 rounded-xl border border-zinc-800/50 bg-zinc-900/30 backdrop-blur p-8 flex flex-col justify-between min-h-[280px]"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-7xl font-extralight text-zinc-100 tracking-tight mb-2">
                    {current ? formatTemp(current.temperature) : '--°'}
                  </h2>
                  <p className="text-lg text-zinc-400 font-light capitalize">
                    {current?.description || 'Loading...'}
                  </p>
                </div>
                <WeatherIcon
                  condition={current?.weather[0]?.main || 'Clear'}
                  timeOfDay={timeOfDay}
                  size={64}
                  className="text-zinc-500"
                />
              </div>
              <p className="text-sm text-zinc-500 mt-6">
                {current
                  ? `Wind ${current.wind_speed} m/s · Humidity ${current.humidity}%`
                  : 'Fetching weather data...'}
              </p>
            </div>

            {/* Stats */}
            <div data-weather-stats className="space-y-3">
              <StatCard
                icon={Wind}
                label="Wind Speed"
                value={current ? `${current.wind_speed} m/s` : '--'}
              />
              <StatCard
                icon={Droplets}
                label="Humidity"
                value={current ? `${current.humidity}%` : '--'}
              />
              <StatCard
                icon={Thermometer}
                label="Feels Like"
                value={current?.feels_like ? formatTemp(current.feels_like) : '--'}
              />
              <StatCard
                icon={Sun}
                label="UV Index"
                value="--"
              />
            </div>
          </div>

          {/* Forecast */}
          <div data-weather-forecast className="grid grid-cols-7 gap-2 mb-6">
            {days.map((day, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-zinc-800/50 bg-zinc-900/30 p-3 text-center 
                         hover:bg-zinc-800/30 transition-colors group"
              >
                <p className="text-[10px] text-zinc-600 uppercase mb-2">{day}</p>
                <WeatherIcon
                  condition={forecast?.forecast[idx]?.weather[0]?.main || 'Clear'}
                  timeOfDay="day"
                  size={20}
                  className="mx-auto mb-2 text-zinc-500 group-hover:text-zinc-400 transition-colors"
                />
                <p className="text-sm text-zinc-300 font-medium">
                  {chartData[idx] ? `${Math.round(chartData[idx])}°` : '--'}
                </p>
              </div>
            ))}
          </div>

          {/* Chart */}
          <div
            data-weather-chart
            className="rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-5 relative h-48"
          >
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs text-zinc-500 font-medium">7-Day Trend</h3>
              <span className="text-[10px] text-zinc-700">
                {tempUnit === 'celsius' ? '°C' : '°F'}
              </span>
            </div>
            <div className="absolute inset-0 top-12 bottom-8 left-5 right-5">
              <ParallaxChart
                data={chartData}
                mouseX={mousePos.x}
                mouseY={mousePos.y}
              />
            </div>
            <div className="absolute bottom-3 left-5 right-5 flex justify-between text-[10px] text-zinc-600">
              {days.map((d, i) => (
                <span key={i}>{d}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Minimal stat card
function StatCard({ 
  icon: Icon, 
  label, 
  value 
}: { 
  icon: React.ElementType
  label: string
  value: string 
}) {
  return (
    <div className="rounded-lg border border-zinc-800/50 bg-zinc-900/30 p-4 flex items-center gap-3
                   hover:bg-zinc-800/20 transition-colors">
      <Icon size={16} className="text-zinc-600" />
      <div>
        <p className="text-[10px] text-zinc-600 uppercase">{label}</p>
        <p className="text-sm text-zinc-300">{value}</p>
      </div>
    </div>
  )
}
