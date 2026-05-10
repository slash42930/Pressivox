interface FaviconProps {
  favicon?: string
  className?: string
}

export function Favicon({ favicon, className = 'w-4 h-4' }: FaviconProps) {
  if (!favicon) return null
  return (
    <img
      src={favicon}
      alt=""
      className={`${className} rounded-sm shrink-0 bg-slate-900 border border-slate-700`}
      onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
    />
  )
}
