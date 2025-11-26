import React from 'react';
import { LucideIcon } from 'lucide-react';

interface ForecastDayProps {
  day: string;
  icon: LucideIcon;
  temp: number;
  delay: number;
}

export const ForecastDay: React.FC<ForecastDayProps> = ({ day, icon: Icon, temp, delay }) => (
  <div 
    className="flex flex-col items-center justify-center p-4 rounded-lg hover:bg-[#1a1a1a] transition-colors cursor-pointer animate-slideUp"
    style={{ animationDelay: `${delay}ms`, animationFillMode: 'both' }}
  >
    <span className="text-[#a0a0a0] text-xs mb-2">{day}</span>
    <Icon size={24} className="mb-2 text-blue-300" />
    <span className="text-[#faf9f6] font-medium">{temp}°</span>
  </div>
);

