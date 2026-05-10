import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 disabled:pointer-events-none disabled:opacity-50 select-none',
  {
    variants: {
      variant: {
        default:
          'bg-gradient-to-r from-cyan-600 to-cyan-500 text-white hover:from-cyan-500 hover:to-cyan-400 shadow-glow-sm hover:shadow-glow-cyan active:scale-[0.98]',
        secondary:
          'bg-slate-800/80 text-slate-200 border border-slate-700/60 hover:bg-slate-700/80 hover:border-slate-600/60 active:scale-[0.98]',
        ghost:
          'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 active:scale-[0.98]',
        destructive:
          'bg-red-900/50 text-red-300 border border-red-800/50 hover:bg-red-800/50 hover:border-red-700/50 active:scale-[0.98]',
        outline:
          'border border-slate-700/60 text-slate-300 hover:border-cyan-500/40 hover:text-slate-100 hover:bg-slate-800/40 active:scale-[0.98]',
        gradient:
          'bg-gradient-to-r from-cyan-600 via-blue-600 to-fuchsia-600 text-white hover:brightness-110 shadow-lg active:scale-[0.98]',
        fuchsia:
          'bg-gradient-to-r from-fuchsia-700 to-purple-700 text-white hover:from-fuchsia-600 hover:to-purple-600 shadow-glow-fuchsia active:scale-[0.98]',
        amber:
          'bg-amber-600/80 text-white border border-amber-500/30 hover:bg-amber-500/80 active:scale-[0.98]',
        link:
          'text-cyan-400 underline-offset-4 hover:underline hover:text-cyan-300 p-0 h-auto',
      },
      size: {
        sm: 'h-8 px-3 py-1 text-xs rounded-lg',
        default: 'h-10 px-4 py-2',
        lg: 'h-11 px-6 py-2.5 text-base rounded-2xl',
        xl: 'h-12 px-8 py-3 text-base rounded-2xl',
        icon: 'h-9 w-9 rounded-xl',
        'icon-sm': 'h-8 w-8 rounded-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(buttonVariants({ variant, size, className }))} {...props} />
  ),
)
Button.displayName = 'Button'

export { buttonVariants }
