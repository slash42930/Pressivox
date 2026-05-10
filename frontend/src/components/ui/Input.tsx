import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode
  suffix?: React.ReactNode
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, icon, suffix, ...props }, ref) => {
    if (icon || suffix) {
      return (
        <div className="relative flex items-center">
          {icon && (
            <div className="absolute left-3 text-slate-500 pointer-events-none z-10">
              {icon}
            </div>
          )}
          <input
            type={type}
            ref={ref}
            className={cn(
              'flex h-10 w-full rounded-xl border border-slate-700/60 bg-slate-900/80 px-4 py-2 text-sm text-slate-100 placeholder:text-slate-500',
              'transition-all duration-200',
              'focus:outline-none focus:border-cyan-500/50 focus:bg-slate-900 focus:shadow-[0_0_0_1px_rgba(6,182,212,0.3),0_0_20px_rgba(6,182,212,0.08)]',
              'disabled:cursor-not-allowed disabled:opacity-50',
              icon && 'pl-9',
              suffix && 'pr-9',
              className,
            )}
            {...props}
          />
          {suffix && (
            <div className="absolute right-3 text-slate-500 pointer-events-none z-10">
              {suffix}
            </div>
          )}
        </div>
      )
    }

    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          'flex h-10 w-full rounded-xl border border-slate-700/60 bg-slate-900/80 px-4 py-2 text-sm text-slate-100 placeholder:text-slate-500',
          'transition-all duration-200',
          'focus:outline-none focus:border-cyan-500/50 focus:bg-slate-900 focus:shadow-[0_0_0_1px_rgba(6,182,212,0.3),0_0_20px_rgba(6,182,212,0.08)]',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      />
    )
  },
)
Input.displayName = 'Input'
