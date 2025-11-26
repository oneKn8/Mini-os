import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext: string;
  icon: LucideIcon;
  delay: number;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, subtext, icon: Icon, delay }) => (
  <div 
    className={`
      bg-[#0a0a0a] border border-[#1a1a1a] rounded-xl p-6 
      backdrop-blur-md bg-opacity-80 relative overflow-hidden group
      transition-all duration-300 hover:border-[#333] hover:shadow-2xl hover:shadow-blue-900/10
      animate-slideUp
    `}
    style={{ animationDelay: `${delay}ms`, animationFillMode: 'both' }}
  >
    <div className="flex justify-between items-start mb-4">
      <div className="text-[#a0a0a0] text-sm font-medium">{label}</div>
      <Icon size={18} className="text-[#a0a0a0] group-hover:text-blue-400 transition-colors" />
    </div>
    <div className="text-[#faf9f6] text-3xl font-light mb-1">{value}</div>
    <div className="text-[#a0a0a0] text-xs">{subtext}</div>
    
    <div className="absolute -right-10 -bottom-10 w-24 h-24 bg-blue-500/5 rounded-full blur-xl group-hover:bg-blue-500/10 transition-all duration-500" />
  </div>
);

