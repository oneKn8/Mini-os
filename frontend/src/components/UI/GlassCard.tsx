import { ReactNode } from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { clsx } from 'clsx'

interface GlassCardProps extends HTMLMotionProps<"div"> {
  children: ReactNode
  className?: string
  hoverEffect?: boolean
  variant?: 'default' | 'dark' | 'light'
  noBorder?: boolean
}

export default function GlassCard({ 
  children, 
  className, 
  hoverEffect = false,
  variant = 'default',
  noBorder = false,
  ...props 
}: GlassCardProps) {
  
  const bgClass = {
    default: 'bg-surface/60',
    dark: 'bg-black/40',
    light: 'bg-white/5'
  }[variant]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        "backdrop-blur-xl rounded-2xl shadow-lg relative overflow-hidden",
        !noBorder && "border border-white/5",
        bgClass,
        hoverEffect && "hover:bg-surface/80 hover:border-white/10 hover:shadow-xl hover:shadow-black/50 transition-all duration-300 cursor-default",
        className
      )}
      {...props}
    >
      {/* Subtle inner glow gradient for depth */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-50 pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col">
        {children}
      </div>
    </motion.div>
  )
}
