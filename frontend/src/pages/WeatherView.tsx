import React, { useState, useEffect, useRef } from 'react';
import { 
  Wind, 
  Droplets, 
  MapPin,
  Sun
} from 'lucide-react';
import { ParallaxWeatherBackground } from '../components/Weather/ParallaxWeatherBackground';
import { ParallaxChart } from '../components/Weather/ParallaxChart';
import { StatCard } from '../components/Weather/StatCard';
import { ForecastDay } from '../components/Weather/ForecastDay';
import WeatherIcon from '../components/Weather/WeatherIcon';
import { useWeatherWithRealtime } from '../hooks/useWeather';
import { animateOnMount, staggerAnimation } from '../utils/gsap';

// --- CONSTANTS ---
const THEME = {
  textPrimary: 'text-[#faf9f6]',
  textSecondary: 'text-[#a0a0a0]',
};

export default function WeatherView() {
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [timeOfDay, setTimeOfDay] = useState<'day' | 'night' | 'dusk' | 'dawn'>('day');
  const heroRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);

  // Use real-time weather hook
  const { current, forecast, isLoading } = useWeatherWithRealtime(7);

  useEffect(() => {
    // Calculate time of day
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 7) setTimeOfDay('dawn');
    else if (hour >= 7 && hour < 17) setTimeOfDay('day');
    else if (hour >= 17 && hour < 19) setTimeOfDay('dusk');
    else setTimeOfDay('night');
  }, []);

  // Animate on mount
  useEffect(() => {
    if (heroRef.current) {
      animateOnMount(heroRef.current, {
        opacity: 0,
        y: 30,
        duration: 0.8,
      });
    }
    if (statsRef.current) {
      const statCards = statsRef.current.querySelectorAll('[data-stat-card]');
      if (statCards.length > 0) {
        staggerAnimation(Array.from(statCards), {
          opacity: 0,
          scale: 0.9,
          duration: 0.5,
        }, 0.1);
      }
    }
  }, [current, forecast]);

  const handleMouseMove = (e: React.MouseEvent) => {
    // Normalize mouse position relative to center of screen
    const x = (e.clientX / window.innerWidth - 0.5) * 40; 
    const y = (e.clientY / window.innerHeight - 0.5) * 40;
    setMousePos({ x, y });
  };


  const chartData = forecast?.forecast.map(f => Math.round(f.temperature)) || [72, 75, 68, 70, 78, 80, 74];
  const days = forecast?.forecast.map(f => new Date(f.datetime).toLocaleDateString('en-US', { weekday: 'short' })) || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div 
      className="relative w-full min-h-screen overflow-hidden select-none bg-[#000000] text-[#faf9f6] p-4 md:p-8"
      onMouseMove={handleMouseMove}
    >
      <style>{`
        @keyframes rain {
          0% { transform: translateY(-100px); opacity: 0; }
          50% { opacity: 1; }
          100% { transform: translateY(600px); opacity: 0; }
        }
        .animate-rain {
          animation-name: rain;
          animation-timing-function: linear;
          animation-iteration-count: infinite;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slideUp {
          animation-name: slideUp;
          animation-duration: 0.6s;
          animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
        }
        .scrollbar-hide::-webkit-scrollbar {
            display: none;
        }
        .scrollbar-hide {
            -ms-overflow-style: none;
            scrollbar-width: none;
        }
      `}</style>

      <div className="relative max-w-6xl mx-auto rounded-3xl overflow-hidden border border-border-light/20 shadow-[0_10px_60px_rgba(0,0,0,0.45)] bg-black/60">
        <ParallaxWeatherBackground 
          mouseX={mousePos.x} 
          mouseY={mousePos.y} 
          timeOfDay={timeOfDay} 
          weatherCondition={current?.weather[0]?.main || 'Clear'}
        />

        {/* HEADER */}
        <header className="h-16 flex items-center justify-between px-4 md:px-8 border-b border-[#1a1a1a]/50 backdrop-blur-sm z-40 relative">
          <div className="flex items-center">
            <h1 className={`${THEME.textPrimary} text-lg font-light tracking-wide`}>
              Weather
            </h1>
             <div className="flex items-center ml-4 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
               <MapPin size={12} className="text-blue-400 mr-2" />
               <span className="text-blue-400 text-xs tracking-wider uppercase">
                 {current ? `${current.location.city}, ${current.location.country}` : 'Loading...'}
               </span>
             </div>
          </div>
          <div className="text-xs text-gray-500 font-mono uppercase">
               {timeOfDay} Mode
          </div>
        </header>

        {/* DASHBOARD CONTENT */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 z-40 relative scrollbar-hide">
          <div className="max-w-6xl mx-auto">
            
            {/* HERO SECTION */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            {/* Main Weather Display */}
            <div ref={heroRef} className="col-span-2 relative h-96 rounded-2xl border border-[#1a1a1a] bg-[#0a0a0a]/60 backdrop-blur-xl p-10 flex flex-col justify-between overflow-hidden group animate-slideUp">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                
                <div className="relative z-10 flex justify-between items-start">
                    <div>
                    <h2 className="text-8xl font-thin text-[#faf9f6] tracking-tighter mb-2">
                        {current ? Math.round(current.temperature) : '--'}°
                    </h2>
                    <p className="text-xl text-[#a0a0a0] font-light capitalize">
                        {current ? current.description : 'Loading...'}
                    </p>
                    </div>
                    <div>
                    <WeatherIcon 
                      condition={current?.weather[0]?.main || 'Clear'} 
                      timeOfDay={timeOfDay}
                      size={80}
                      className="text-[#a0a0a0]"
                    />
                    </div>
                </div>
                <div className="relative z-10">
                    <p className="text-[#faf9f6] max-w-md leading-relaxed font-light text-sm opacity-80">
                    {current 
                        ? `Wind speed of ${current.wind_speed}m/s. Humidity at ${current.humidity}%.` 
                        : 'Fetching weather data...'}
                    </p>
                </div>
            </div>

            {/* Right Panel Details */}
            <div ref={statsRef} className="space-y-4">
                <div data-stat-card>
                  <StatCard 
                      icon={Wind} 
                      label="Wind Speed" 
                      value={current ? `${current.wind_speed} m/s` : '--'} 
                      subtext="Direction: N/A" 
                      delay={100} 
                  />
                </div>
                <div data-stat-card>
                  <StatCard 
                      icon={Droplets} 
                      label="Humidity" 
                      value={current ? `${current.humidity}%` : '--'} 
                      subtext={`Dew point: --`} 
                      delay={200} 
                  />
                </div>
                <div data-stat-card>
                  <StatCard 
                      icon={Sun} 
                      label="UV Index" 
                      value="--" 
                      subtext="N/A" 
                      delay={300} 
                  />
                </div>
            </div>
            </div>

            {/* FORECAST ROW */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-8">
            {days.map((day, idx) => (
                <ForecastDay 
                key={idx} 
                day={day} 
                icon={forecast ? forecast.forecast[idx]?.weather[0]?.main || 'Clear' : 'Clear'} 
                temp={chartData[idx] || 0} 
                delay={400 + (idx * 50)} 
                timeOfDay={timeOfDay}
                />
            ))}
            </div>

            {/* HOURLY CHART (PARALLAX ENHANCED) */}
            <div 
            className="w-full h-64 rounded-xl border border-[#1a1a1a] bg-[#0a0a0a]/60 backdrop-blur-md p-6 relative animate-slideUp group" 
            style={{ animationDelay: '800ms', animationFillMode: 'both' }}
            >
            <div className="flex justify-between items-center mb-4">
                <h3 className={`${THEME.textSecondary} text-sm font-medium`}>Temperature Trend (7 Days)</h3>
                <div className="text-xs text-[#444] font-mono">HOVER FOR PARALLAX</div>
            </div>
            <div className="absolute inset-0 top-16 bottom-6 left-6 right-6">
                <ParallaxChart 
                    data={chartData} 
                    mouseX={mousePos.x} 
                    mouseY={mousePos.y} 
                />
            </div>
            
            {/* Time Labels - Static Layer */}
            <div className="absolute bottom-4 left-6 right-6 flex justify-between text-xs text-[#666]">
                {days.map((d, i) => <span key={i}>{d}</span>)}
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
