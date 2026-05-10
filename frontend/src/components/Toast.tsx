import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle, CheckCircle, Info } from 'lucide-react'

export type ToastKind = 'success' | 'error' | 'info'

interface ToastItem {
  id: string
  message: string
  kind: ToastKind
}

interface ToastContextValue {
  addToast: (message: string, kind?: ToastKind) => void
}

const ToastContext = createContext<ToastContextValue>({ addToast: () => {} })

export function useToast() {
  return useContext(ToastContext)
}

const KIND_STYLES: Record<ToastKind, { border: string; bg: string; text: string; icon: JSX.Element }> = {
  error: {
    border: 'border-red-700',
    bg: 'bg-red-950/90',
    text: 'text-red-200',
    icon: <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />,
  },
  success: {
    border: 'border-emerald-700',
    bg: 'bg-emerald-950/90',
    text: 'text-emerald-200',
    icon: <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />,
  },
  info: {
    border: 'border-slate-700',
    bg: 'bg-slate-900/90',
    text: 'text-slate-200',
    icon: <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />,
  },
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const addToast = useCallback((message: string, kind: ToastKind = 'info') => {
    const id = crypto.randomUUID()
    setToasts(prev => [...prev.slice(-4), { id, message, kind }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 6000)
  }, [])

  const remove = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        <AnimatePresence>
          {toasts.map(t => {
            const s = KIND_STYLES[t.kind]
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, x: 60, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 60, scale: 0.9 }}
                transition={{ type: 'spring', stiffness: 320, damping: 30 }}
                className={`pointer-events-auto rounded-2xl border backdrop-blur-sm px-4 py-3 flex items-start gap-3 shadow-2xl text-sm ${s.bg} ${s.border} ${s.text}`}
              >
                {s.icon}
                <span className="flex-1 leading-5 break-words">{t.message}</span>
                <button
                  onClick={() => remove(t.id)}
                  className="shrink-0 opacity-50 hover:opacity-100 transition-opacity mt-0.5"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}
