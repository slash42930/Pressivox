import { useState, useEffect } from 'react'
import { cn } from '../../lib/utils'

interface TypewriterTextProps {
  words: string[]
  className?: string
  cursorClassName?: string
  typingSpeed?: number
  deletingSpeed?: number
  pauseDuration?: number
}

/**
 * React Bits inspired typewriter component.
 * Cycles through an array of words with a blinking cursor.
 */
export function TypewriterText({
  words,
  className,
  cursorClassName,
  typingSpeed = 80,
  deletingSpeed = 40,
  pauseDuration = 2000,
}: TypewriterTextProps) {
  const [displayText, setDisplayText] = useState('')
  const [wordIndex, setWordIndex] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    // Respect prefers-reduced-motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplayText(words[0])
      return
    }

    const currentWord = words[wordIndex % words.length]
    let timeout: ReturnType<typeof setTimeout>

    if (!isDeleting && displayText === currentWord) {
      timeout = setTimeout(() => setIsDeleting(true), pauseDuration)
    } else if (isDeleting && displayText === '') {
      setIsDeleting(false)
      setWordIndex(i => i + 1)
    } else {
      timeout = setTimeout(
        () => {
          setDisplayText(prev =>
            isDeleting ? prev.slice(0, -1) : currentWord.slice(0, prev.length + 1),
          )
        },
        isDeleting ? deletingSpeed : typingSpeed,
      )
    }

    return () => clearTimeout(timeout)
  }, [displayText, isDeleting, wordIndex, words, typingSpeed, deletingSpeed, pauseDuration])

  return (
    <span className={className}>
      {displayText}
      <span
        className={cn(
          'inline-block w-0.5 h-[1em] ml-0.5 bg-current align-middle animate-pulse',
          cursorClassName,
        )}
      />
    </span>
  )
}

interface WordRevealProps {
  text: string
  className?: string
  wordClassName?: string
  delay?: number
  stagger?: number
}

/**
 * Motion Primitives – word-by-word reveal animation.
 */
export function WordReveal({ text, className, wordClassName, delay = 0, stagger = 0.06 }: WordRevealProps) {
  const words = text.split(' ')
  return (
    <span className={cn('inline-flex flex-wrap gap-x-[0.25em]', className)}>
      {words.map((word, i) => (
        <span
          key={i}
          className={cn('animate-fade-up opacity-0', wordClassName)}
          style={{
            animationDelay: `${delay + i * stagger}s`,
            animationFillMode: 'forwards',
            animationDuration: '0.5s',
          }}
        >
          {word}
        </span>
      ))}
    </span>
  )
}

interface GradientTextProps {
  children: React.ReactNode
  className?: string
  animate?: boolean
}

export function GradientText({ children, className, animate }: GradientTextProps) {
  return (
    <span
      className={cn(
        'bg-gradient-to-r from-cyan-400 via-blue-400 to-fuchsia-400 bg-clip-text text-transparent',
        animate && 'bg-[length:200%_auto] animate-gradient-shift',
        className,
      )}
    >
      {children}
    </span>
  )
}
