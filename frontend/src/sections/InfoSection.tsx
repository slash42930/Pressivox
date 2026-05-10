import { motion } from 'framer-motion'

export function InfoSection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
    >
      <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 mb-6">
        <h2 className="text-2xl font-semibold mb-2">Product Guide</h2>
        <p className="text-slate-400">
          This page explains what each area does and how to get better results faster.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6">
          <h3 className="text-xl font-semibold mb-4">Core Features</h3>
          <ul className="space-y-3 text-slate-300 text-sm">
            <li>
              <strong>Search:</strong> Finds sources quickly, adds diagnostics, and supports sorting
              plus side-by-side compare.
            </li>
            <li>
              <strong>Research:</strong> Produces structured summaries, selected sources, and
              meaning groups for ambiguous topics.
            </li>
            <li>
              <strong>Extract:</strong> Pulls full page content plus important passages for fast
              review.
            </li>
            <li>
              <strong>Histories:</strong> Reloads session search and extract history cards for
              continuity.
            </li>
          </ul>
        </div>

        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6">
          <h3 className="text-xl font-semibold mb-4">How To Work Faster</h3>
          <ul className="space-y-3 text-slate-300 text-sm">
            <li>
              Use <strong>Analyze Query</strong> before searching if your query is short or broad.
            </li>
            <li>
              Keep <strong>Include Domains</strong> empty unless you need strict source control.
            </li>
            <li>
              Use compare buttons on cards to keep only the strongest 2-3 sources visible.
            </li>
            <li>
              Run Research when you need synthesized context, not just raw links.
            </li>
            <li>
              Use Histories to revisit previous work without retyping prompts.
            </li>
          </ul>
        </div>

        <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 xl:col-span-2">
          <h3 className="text-xl font-semibold mb-4">What Analyzer Does</h3>
          <p className="text-sm text-slate-300 mb-3">
            Analyzer is a lightweight pre-search helper. It does not fetch web results. It checks
            query clarity and gives guidance so your next search call is cleaner.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 text-sm">
            {[
              ['token_count', 'How dense your query is.'],
              ['is_short_query', 'Flags terse inputs.'],
              ['ambiguous_likely', 'Signals multi-meaning intent.'],
              ['suggested_queries', 'Offers better query rewrites.'],
            ].map(([label, desc]) => (
              <div key={label} className="rounded-2xl bg-slate-950 border border-slate-800 p-3">
                <span className="text-slate-400">{label}</span>
                <div className="text-slate-200 mt-1">{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
