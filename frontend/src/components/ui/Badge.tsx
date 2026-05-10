import { forwardRef, type HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors select-none',
  {
    variants: {
      variant: {
        default: 'bg-slate-800 text-slate-300 border border-slate-700/60',
        cyan: 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/40',
        fuchsia: 'bg-fuchsia-950/60 text-fuchsia-300 border border-fuchsia-800/40',
        amber: 'bg-amber-950/60 text-amber-300 border border-amber-800/40',
        emerald: 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/40',
        red: 'bg-red-950/60 text-red-300 border border-red-800/40',
        purple: 'bg-purple-950/60 text-purple-300 border border-purple-800/40',
        gradient: 'bg-gradient-to-r from-cyan-900/60 to-fuchsia-900/60 text-slate-200 border border-cyan-700/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => (
    <span ref={ref} className={cn(badgeVariants({ variant }), className)} {...props} />
  ),
)
Badge.displayName = 'Badge'

export { badgeVariants }
