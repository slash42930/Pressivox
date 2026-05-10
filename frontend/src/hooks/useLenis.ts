import { useEffect, useRef } from 'react'

export function useLenis() {
  const lenisRef = useRef<unknown>(null)

  useEffect(() => {
    if (typeof window === 'undefined') return

    // Keep smooth scrolling opt-in to avoid background RAF cost on slower machines.
    // Enable via: localStorage.setItem('pressivox.smoothScroll', '1')
    const smoothScrollEnabled = window.localStorage.getItem('pressivox.smoothScroll') === '1'
    if (!smoothScrollEnabled) return

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const lowEndCpu = (navigator.hardwareConcurrency ?? 8) <= 4
    if (prefersReducedMotion || lowEndCpu) return

    // Dynamically import Lenis to avoid SSR issues
    let animationId: number | undefined
    let isDisposed = false
    let isVisible = !document.hidden
    let lenis: { raf: (t: number) => void; destroy: () => void } | null = null

    import('lenis').then(({ default: Lenis }) => {
      if (isDisposed) return

      lenis = new Lenis({
        duration: 1.05,
        easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      }) as { raf: (t: number) => void; destroy: () => void }

      lenisRef.current = lenis

      function raf(time: number) {
        if (!isVisible || !lenis) return
        lenis!.raf(time)
        animationId = requestAnimationFrame(raf)
      }

      animationId = requestAnimationFrame(raf)
    })

    function onVisibilityChange() {
      isVisible = !document.hidden
      if (isVisible && lenis && animationId == null) {
        animationId = requestAnimationFrame(function raf(time: number) {
          if (!isVisible || !lenis) {
            animationId = undefined
            return
          }
          lenis.raf(time)
          animationId = requestAnimationFrame(raf)
        })
      }
      if (!isVisible && animationId != null) {
        cancelAnimationFrame(animationId)
        animationId = undefined
      }
    }

    document.addEventListener('visibilitychange', onVisibilityChange)

    return () => {
      isDisposed = true
      document.removeEventListener('visibilitychange', onVisibilityChange)
      if (animationId != null) cancelAnimationFrame(animationId)
      lenis?.destroy()
    }
  }, [])

  return lenisRef
}
