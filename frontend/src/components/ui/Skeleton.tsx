import type { CSSProperties } from 'react'
import { cn } from '../../lib/utils'

interface SkeletonProps {
  className?: string
  lines?: number
  style?: CSSProperties
}

export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg bg-slate-800/60',
        'before:absolute before:inset-0',
        'before:bg-gradient-to-r before:from-transparent before:via-slate-700/40 before:to-transparent',
        'before:animate-shimmer',
        'before:[background-size:200%_100%]',
        className,
      )}
      style={style}
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="rounded-2xl bg-slate-900/80 border border-white/[0.06] p-5 space-y-3">
      <div className="flex items-start gap-3">
        <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-5/6" />
      <Skeleton className="h-3 w-4/6" />
    </div>
  )
}

/** Matches the SearchCard / ResearchCard layout with score bar, title, meta, snippet */
export function SkeletonResultCard() {
  return (
    <div className="rounded-2xl bg-slate-900/60 border border-white/[0.06] overflow-hidden">
      {/* score bar */}
      <div className="h-0.5 bg-slate-800">
        <Skeleton className="h-0.5 w-1/2 rounded-none" />
      </div>
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-2.5 w-12 rounded" />
            <Skeleton className="h-4 w-4/5 rounded" />
          </div>
          <Skeleton className="h-8 w-10 rounded-lg shrink-0" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-4 rounded-full" />
          <Skeleton className="h-3 w-24 rounded" />
          <Skeleton className="h-4 w-14 rounded-full" />
        </div>
        <div className="space-y-1.5">
          <Skeleton className="h-3 w-full rounded" />
          <Skeleton className="h-3 w-5/6 rounded" />
          <Skeleton className="h-3 w-4/6 rounded" />
        </div>
        <div className="flex gap-2 pt-1">
          <Skeleton className="h-7 w-20 rounded-lg" />
          <Skeleton className="h-7 w-16 rounded-lg" />
        </div>
      </div>
    </div>
  )
}

export function SkeletonText({ lines = 3 }: SkeletonProps) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          className={cn('h-3', i === lines - 1 ? 'w-3/4' : 'w-full')}
        />
      ))}
    </div>
  )
}

/** Skeleton for a research summary key-points list */
export function SkeletonSummary() {
  return (
    <div className="rounded-2xl bg-slate-950 border border-slate-800 p-4 space-y-4">
      <Skeleton className="h-3 w-20 rounded" />
      {[0.9, 1, 0.75, 0.85, 0.6].map((w, i) => (
        <div key={i} className="flex items-start gap-3">
          <Skeleton className="mt-2 w-2 h-2 rounded-full shrink-0" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className={`h-3 rounded`} style={{ width: `${w * 100}%` }} />
            {i % 2 === 0 && <Skeleton className="h-3 w-3/5 rounded" />}
          </div>
        </div>
      ))}
    </div>
  )
}
