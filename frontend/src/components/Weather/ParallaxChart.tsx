import React, { useMemo } from 'react';

interface ParallaxChartProps {
  data: number[];
  mouseX: number;
  mouseY: number;
}

export const ParallaxChart: React.FC<ParallaxChartProps> = ({ data, mouseX, mouseY }) => {
  // Generate SVG path for smooth curve
  const points = useMemo(() => {
    const width = 1000;
    const height = 150;
    const padding = 50;
    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;
    
    if (!data || data.length === 0) return [];

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1; // Avoid division by zero

    return data.map((val, i) => {
      const x = padding + (i / (data.length - 1)) * innerWidth;
      // Invert Y because SVG y=0 is top
      const normalizedY = (val - min) / range;
      const y = height - padding - (normalizedY * innerHeight);
      return { x, y, val };
    });
  }, [data]);

  const pathD = useMemo(() => {
    if (points.length === 0) return "";
    
    let d = `M ${points[0].x} ${points[0].y}`;
    
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? 0 : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2] || p2;

      const cp1x = p1.x + (p2.x - p0.x) * 0.2;
      const cp1y = p1.y + (p2.y - p0.y) * 0.2;
      const cp2x = p2.x - (p3.x - p1.x) * 0.2;
      const cp2y = p2.y - (p3.y - p1.y) * 0.2;

      d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }
    return d;
  }, [points]);

  if (points.length === 0) return null;

  // Area path (closed at bottom)
  const areaD = `${pathD} L ${points[points.length-1].x} 200 L ${points[0].x} 200 Z`;

  // Parallax offsets (pixels)
  const bgX = mouseX * 0.02;
  const bgY = mouseY * 0.02;
  const lineX = mouseX * 0.05;
  const lineY = mouseY * 0.05;
  const dotX = mouseX * 0.10;
  const dotY = mouseY * 0.10;

  return (
    <div className="w-full h-full relative overflow-hidden rounded-xl">
      <svg 
        className="w-full h-full overflow-visible" 
        viewBox="0 0 1000 200" 
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#60a5fa" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#60a5fa" stopOpacity="0" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Layer 1: Grid (Background) - Slow */}
        <g style={{ transform: `translate(${bgX}px, ${bgY}px)`, transition: 'transform 0.1s linear' }}>
          {[0, 1, 2, 3, 4].map(i => (
             <line key={i} x1="0" y1={40 * i + 20} x2="1000" y2={40 * i + 20} stroke="#1a1a1a" strokeWidth="1" />
          ))}
          {points.map((p, i) => (
             <line key={i} x1={p.x} y1="0" x2={p.x} y2="200" stroke="#1a1a1a" strokeWidth="1" strokeDasharray="4 4"/>
          ))}
        </g>

        {/* Layer 2: Area Fill - Mid Speed */}
        <g style={{ transform: `translate(${lineX * 0.5}px, ${lineY * 0.5}px)`, transition: 'transform 0.1s linear' }}>
          <path d={areaD} fill="url(#lineGradient)" />
        </g>

        {/* Layer 3: Main Line - Fast */}
        <g style={{ transform: `translate(${lineX}px, ${lineY}px)`, transition: 'transform 0.1s linear' }}>
          <path 
            d={pathD} 
            fill="none" 
            stroke="#60a5fa" 
            strokeWidth="3" 
            filter="url(#glow)"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>

        {/* Layer 4: Dots - Fastest (Holographic feel) */}
        <g style={{ transform: `translate(${dotX}px, ${dotY}px)`, transition: 'transform 0.1s linear' }}>
          {points.map((p, i) => (
            <g key={i}>
              <circle cx={p.x} cy={p.y} r="6" fill="#000000" stroke="#60a5fa" strokeWidth="2" />
              <circle cx={p.x} cy={p.y} r="3" fill="#60a5fa" />
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
};

