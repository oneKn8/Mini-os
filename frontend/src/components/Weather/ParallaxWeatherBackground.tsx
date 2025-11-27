import React, { useEffect, useRef, useMemo } from 'react';
import gsap from 'gsap';

interface ParallaxWeatherBackgroundProps {
  mouseX: number;
  mouseY: number;
  timeOfDay: 'day' | 'night' | 'dusk' | 'dawn';
  weatherCondition?: string;
}

export const ParallaxWeatherBackground: React.FC<ParallaxWeatherBackgroundProps> = ({ 
  mouseX, 
  mouseY, 
  timeOfDay,
  weatherCondition = 'clear'
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<(HTMLDivElement | SVGSVGElement | null)[]>([]);

  // Parallax Factors
  const p1 = 0.02;
  const p2 = 0.05;
  const p3 = 0.08;

  // Memoize stars to prevent re-rendering random positions
  const stars = useMemo(() => {
    return Array.from({ length: 150 }).map(() => ({
      cx: Math.random() * 1000,
      cy: Math.random() * 600,
      r: Math.random() * 2 + 1, // Increased size slightly: 1px to 3px
      opacity: Math.random(), // Base opacity (will be modulated by animation)
      animationDelay: `${Math.random() * 3}s`,
      animationDuration: `${2 + Math.random() * 3}s`
    }));
  }, []);

  const clouds = useMemo(() => {
      return [
          { cx: 100, cy: 100, r: 80, duration: 8000 },
          { cx: 250, cy: 150, r: 100, duration: 10000 },
          { cx: 800, cy: 100, r: 120, duration: 9000 },
          { cx: 500, cy: 80, r: 90, duration: 12000 },
          { cx: 650, cy: 180, r: 70, duration: 11000 },
      ]
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    
    gsap.to(layersRef.current[0], {
      x: mouseX * p1,
      y: mouseY * p1,
      duration: 0.5,
      ease: "power2.out"
    });

    gsap.to(layersRef.current[1], {
      x: mouseX * p2,
      y: mouseY * p2,
      scale: 1.1,
      duration: 0.5,
      ease: "power2.out"
    });

    gsap.to(layersRef.current[2], {
      x: mouseX * p3,
      y: mouseY * p3,
      scale: 1.2,
      duration: 0.5,
      ease: "power2.out"
    });

  }, [mouseX, mouseY]);

  // Background Gradients
  const getGradient = () => {
    switch (timeOfDay) {
      case 'day': return 'from-[#4facfe] via-[#00f2fe] to-[#4facfe]';
      case 'night': return 'from-[#0f172a] via-[#000000] to-[#000000]';
      case 'dusk': return 'from-[#2c3e50] via-[#fd746c] to-[#ff9068]';
      case 'dawn': return 'from-[#16222a] via-[#3a6073] to-[#16222a]';
      default: return 'from-[#0f172a] via-[#000000] to-[#000000]';
    }
  };

  const isCloudy = weatherCondition.toLowerCase().includes('cloud') || weatherCondition.toLowerCase().includes('rain');
  const isRainy = weatherCondition.toLowerCase().includes('rain') || weatherCondition.toLowerCase().includes('drizzle');

  return (
    <div ref={containerRef} className="absolute inset-0 overflow-hidden pointer-events-none z-0 transition-colors duration-1000">
      <style>{`
        @keyframes twinkle {
            0%, 100% { opacity: 0.6; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.2); }
        }
        .animate-twinkle {
            animation-name: twinkle;
            animation-timing-function: ease-in-out;
            animation-iteration-count: infinite;
            transform-box: fill-box;
            transform-origin: center;
        }
      `}</style>

      {/* Base Gradient */}
      <div className={`absolute inset-0 bg-gradient-to-b ${getGradient()} opacity-50 transition-all duration-1000`} />

      {/* Layer 1: Orb/Sun/Moon */}
      <div 
        ref={el => layersRef.current[0] = el}
        className="absolute top-10 right-20 transition-transform duration-75 ease-out"
      >
        <div 
            className={`w-64 h-64 rounded-full blur-[80px] transition-colors duration-1000`} 
            style={{ 
                backgroundColor: timeOfDay === 'night' 
                    ? 'rgba(100, 149, 237, 0.4)'  // Glow
                    : timeOfDay === 'dusk' 
                        ? 'rgba(251, 146, 60, 0.5)' 
                        : 'rgba(251, 191, 36, 0.5)' 
            }}
        />
        {/* Actual Moon/Sun shape */}
         <div 
            className={`w-24 h-24 rounded-full absolute top-20 right-20 blur-md transition-colors duration-1000`} 
            style={{ 
                backgroundColor: timeOfDay === 'night' 
                    ? '#e2e8f0' 
                    : '#fbbf24',
                boxShadow: timeOfDay === 'night' ? '0 0 30px #e2e8f0' : '0 0 50px #fbbf24'
            }}
        />
      </div>

      {/* Layer 2: SVG Shapes (Clouds/Stars) */}
      <svg 
        ref={el => layersRef.current[1] = el}
        className="absolute w-full h-full"
        viewBox="0 0 1000 600"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Clouds - Show more if cloudy, otherwise fewer/fainter */}
        {(isCloudy || timeOfDay !== 'night') && (
            <g fill={timeOfDay === 'night' ? "#4a5568" : "rgba(255,255,255,0.6)"} opacity={isCloudy ? 0.9 : 0.5}>
                {clouds.map((cloud, i) => (
                    <circle 
                        key={i} 
                        cx={cloud.cx} 
                        cy={cloud.cy} 
                        r={cloud.r} 
                        className="animate-pulse" 
                        style={{ animationDuration: `${cloud.duration}ms` }}
                    />
                ))}
                {/* Cloud Connector Lines */}
                <path d="M-50 150 Q 200 50 400 150 T 900 150" stroke={timeOfDay === 'night' ? "#718096" : "rgba(255,255,255,0.4)"} strokeWidth="2" fill="none" opacity="0.6" />
            </g>
        )}

        {/* Stars for Night - Enhanced */}
        {timeOfDay === 'night' && (
             <g fill="#FFF">
                {stars.map((star, i) => (
                    <circle 
                        key={i} 
                        cx={star.cx} 
                        cy={star.cy} 
                        r={star.r} 
                        // Removed inline opacity here so CSS animation controls it fully, 
                        // or we can rely on the animation's opacity range.
                        className="animate-twinkle"
                        style={{
                            animationDelay: star.animationDelay,
                            animationDuration: star.animationDuration
                        }}
                    />
                ))}
             </g>
        )}
      </svg>

      {/* Layer 3: Rain/Snow/Atmosphere */}
      <svg 
        ref={el => layersRef.current[2] = el}
        className="absolute w-full h-full z-10 pointer-events-none"
      >
        <defs>
          <linearGradient id="rainGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#4a90e2" stopOpacity="0" />
            <stop offset="100%" stopColor="#4a90e2" stopOpacity="0.4" />
          </linearGradient>
        </defs>
        
        {isRainy && Array.from({ length: 40 }).map((_, i) => (
          <rect
            key={i}
            x={`${Math.random() * 100}%`}
            y={`${Math.random() * 100}%`}
            width="1"
            height={20 + Math.random() * 30}
            fill="url(#rainGrad)"
            className="animate-rain"
            style={{ 
              animationDuration: `${0.5 + Math.random() * 0.5}s`,
              animationDelay: `${Math.random()}s` 
            }}
          />
        ))}
      </svg>
    </div>
  );
};
