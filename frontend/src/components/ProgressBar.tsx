import { motion } from 'framer-motion'

interface ProgressBarProps {
  active: boolean
  color?: string
}

export function ProgressBar({ active, color = 'bg-cyan-500' }: ProgressBarProps) {
  if (!active) return <div className="h-[2px] w-full" />
  return (
    <div className="h-[2px] w-full overflow-hidden rounded-full bg-slate-800/80 relative">
      <motion.div
        className={`absolute h-full ${color} rounded-full w-[40%] opacity-80`}
        style={{ filter: 'blur(0.5px)' }}
        initial={{ x: '-120%' }}
        animate={{ x: '300%' }}
        transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut', repeatType: 'loop' }}
      />
    </div>
  )
}
