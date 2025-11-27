import { motion } from 'framer-motion'

interface LogoProps {
  className?: string
  showText?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: { icon: 20, text: 'text-sm' },
  md: { icon: 28, text: 'text-lg' },
  lg: { icon: 40, text: 'text-2xl' },
}

export default function Logo({ className = '', showText = true, size = 'md' }: LogoProps) {
  const { icon: iconSize, text: textSize } = sizeMap[size]

  return (
    <motion.div
      className={`flex items-center gap-3 ${className}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative flex items-center justify-center shrink-0">
        <img
          src="/logo-icon.svg"
          alt="Ops Center Logo"
          width={iconSize}
          height={iconSize}
          className="drop-shadow-[0_0_8px_rgba(76,110,245,0.5)]"
        />
        <div className="absolute inset-0 bg-accent-primary/20 rounded-full blur-md animate-pulse"></div>
      </div>
      {showText && (
        <motion.div
          className="flex flex-col"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
        >
          <span className={`font-bold tracking-tight text-white ${textSize}`}>
            Ops Center
          </span>
          <span className="text-[10px] text-text-tertiary uppercase tracking-wider">
            System Online
          </span>
        </motion.div>
      )}
    </motion.div>
  )
}

