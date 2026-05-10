import { forwardRef, type HTMLAttributes, type ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  glow?: 'cyan' | 'fuchsia' | 'amber' | 'none'
  variant?: 'default' | 'elevated' | 'ghost' | 'bordered'
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, glow = 'none', variant = 'default', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl transition-all duration-300',
        variant === 'default' && 'bg-slate-900/80 border border-white/[0.06] shadow-card',
        variant === 'elevated' && 'bg-slate-900 border border-white/[0.08] shadow-card-hover',
        variant === 'ghost' && 'bg-slate-900/40 border border-white/[0.04]',
        variant === 'bordered' && 'bg-slate-950/60 border border-slate-800',
        glow === 'cyan' && 'hover:border-cyan-500/30 hover:shadow-glow-cyan',
        glow === 'fuchsia' && 'hover:border-fuchsia-500/30 hover:shadow-glow-fuchsia',
        glow === 'amber' && 'hover:border-amber-500/30',
        className,
      )}
      {...props}
    />
  ),
)
Card.displayName = 'Card'

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-6 pt-6 pb-4', className)} {...props} />
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('font-display text-lg font-semibold leading-tight text-slate-100', className)}
      {...props}
    />
  )
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-sm text-slate-400 mt-1', className)} {...props} />
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('px-6 pb-6', className)} {...props} />
}

export function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex items-center px-6 pb-6 pt-0 gap-2', className)} {...props} />
  )
}

interface StatCardProps {
  label: string
  value: string | number
  icon?: ReactNode
  color?: 'cyan' | 'fuchsia' | 'amber' | 'slate'
  change?: string
  className?: string
}

export function StatCard({ label, value, icon, color = 'cyan', change, className }: StatCardProps) {
  const colorMap = {
    cyan: 'text-cyan-400',
    fuchsia: 'text-fuchsia-400',
    amber: 'text-amber-400',
    slate: 'text-slate-300',
  }
  return (
    <Card className={cn('p-5', className)}>
      <div className="flex items-start justify-between mb-3">
        <div className={cn('text-sm font-medium text-slate-400', className)}>{label}</div>
        {icon && (
          <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center bg-slate-800', colorMap[color])}>
            {icon}
          </div>
        )}
      </div>
      <div className={cn('text-2xl font-display font-bold', colorMap[color])}>{value}</div>
      {change && <div className="text-xs text-slate-500 mt-1">{change}</div>}
    </Card>
  )
}
