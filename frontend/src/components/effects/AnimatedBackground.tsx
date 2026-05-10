import { useRef, useEffect } from 'react'
import { cn } from '../../lib/utils'

/**
 * Animated background with gradient mesh orbs.
 * Inspired by Aceternity UI noise-texture + Magic UI background patterns.
 */
export function AnimatedBackground({ className }: { className?: string }) {
  return (
    <div
      className={cn('pointer-events-none fixed inset-0 -z-10 overflow-hidden', className)}
      aria-hidden
    >
      {/* Primary ambient orbs — static, no float animation to avoid continuous GPU repaint */}
      <div className="absolute -top-[30%] -left-[10%] w-[600px] h-[600px] rounded-full bg-cyan-900/[0.12] blur-[130px]" />
      <div className="absolute -bottom-[20%] -right-[10%] w-[700px] h-[700px] rounded-full bg-fuchsia-900/[0.10] blur-[140px]" />
      <div className="absolute top-[40%] left-[30%] w-[400px] h-[400px] rounded-full bg-blue-900/[0.07] blur-[120px]" />

      {/* Subtle grid */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(6,182,212,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.3) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_30%,rgba(3,7,18,0.6)_100%)]" />
    </div>
  )
}

/**
 * Spotlight card effect — Aceternity UI style.
 * Shows a radial spotlight following mouse position.
 */
export function SpotlightCard({
  className,
  children,
  spotlightColor = 'rgba(6,182,212,0.08)',
}: {
  className?: string
  children: React.ReactNode
  spotlightColor?: string
}) {
  const divRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const div = divRef.current
    if (!div) return

    let rafId: number | null = null

    function onMouseMove(e: MouseEvent) {
      if (rafId !== null) return
      rafId = requestAnimationFrame(() => {
        const rect = div!.getBoundingClientRect()
        div!.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`)
        div!.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`)
        rafId = null
      })
    }

    div.addEventListener('mousemove', onMouseMove)
    return () => {
      div.removeEventListener('mousemove', onMouseMove)
      if (rafId !== null) cancelAnimationFrame(rafId)
    }
  }, [])

  return (
    <div
      ref={divRef}
      style={{ '--spotlight-color': spotlightColor } as React.CSSProperties}
      className={cn(
        'relative overflow-hidden',
        'before:pointer-events-none before:absolute before:inset-0 before:rounded-[inherit] before:opacity-0 before:transition-opacity before:duration-500',
        'before:bg-[radial-gradient(400px_at_var(--mouse-x,50%)_var(--mouse-y,50%),var(--spotlight-color),transparent)]',
        'hover:before:opacity-100',
        className,
      )}
    >
      {children}
    </div>
  )
}

/**
 * Section reveal animation wrapper.
 */
export function RevealSection({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode
  className?: string
  delay?: number
}) {
  return (
    <div
      className={cn('animate-fade-up opacity-0', className)}
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}
    >
      {children}
    </div>
  )
}
