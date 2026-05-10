import { Search, FlaskConical, FileText, Clock, InboxIcon } from 'lucide-react'

type EmptyVariant = 'default' | 'search' | 'research' | 'extract' | 'history'

const ICON_MAP: Record<EmptyVariant, { icon: React.ElementType; color: string; bg: string }> = {
  default: {
    icon: InboxIcon,
    color: 'text-slate-500',
    bg: 'bg-slate-800/80 border-slate-700/60',
  },
  search: {
    icon: Search,
    color: 'text-cyan-500/70',
    bg: 'bg-cyan-950/40 border-cyan-800/30',
  },
  research: {
    icon: FlaskConical,
    color: 'text-fuchsia-500/70',
    bg: 'bg-fuchsia-950/40 border-fuchsia-800/30',
  },
  extract: {
    icon: FileText,
    color: 'text-amber-500/70',
    bg: 'bg-amber-950/40 border-amber-800/30',
  },
  history: {
    icon: Clock,
    color: 'text-slate-400/70',
    bg: 'bg-slate-800/60 border-slate-700/40',
  },
}

interface EmptyStateProps {
  message: string
  variant?: EmptyVariant
  action?: { label: string; onClick: () => void }
}

export function EmptyState({ message, variant = 'default', action }: EmptyStateProps) {
  const { icon: Icon, color, bg } = ICON_MAP[variant]

  return (
    <div className="rounded-2xl bg-slate-950/60 border border-dashed border-slate-700/50 px-6 py-10 text-center">
      <div className={`w-10 h-10 rounded-2xl border flex items-center justify-center mx-auto mb-4 ${bg}`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <p className="text-sm text-slate-500 leading-relaxed max-w-xs mx-auto">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-700/60 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-600 hover:bg-slate-800/40 transition-all duration-200"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
