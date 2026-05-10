// Trusted news and reference sources
export const TRUSTED_SITES: string[] = [
  "reuters.com", "apnews.com", "bbc.com", "npr.org", "pbs.org", "wsj.com",
  "nytimes.com", "washingtonpost.com", "ft.com", "economist.com", "bloomberg.com",
  "cnbc.com", "forbes.com", "time.com", "theguardian.com", "thetimes.co.uk",
  "latimes.com", "scmp.com", "nikkei.com", "dw.com", "france24.com",
  "aljazeera.com", "csmonitor.com", "propublica.org", "nature.com", "science.org",
  "scientificamerican.com", "newscientist.com", "nejm.org", "thelancet.com",
  "who.int", "cdc.gov", "un.org", "worldbank.org", "imf.org", "oecd.org",
  "weforum.org", "wikipedia.org", "britannica.com", "mit.edu", "stanford.edu",
  "harvard.edu", "ox.ac.uk", "cam.ac.uk", "openai.com", "google.com",
  "microsoft.com", "ibm.com", "mckinsey.com", "brookings.edu",
]

export const ROMANIAN_NEWS_DOMAINS: string[] = [
  "digi24.ro", "hotnews.ro", "g4media.ro", "stirileprotv.ro", "mediafax.ro",
  "adevarul.ro", "biziday.ro", "romania-insider.com", "zf.ro", "economica.net",
  "profit.ro", "bursa.ro",
]

export const DOMAIN_TAGS: Record<string, string[]> = {
  "reuters.com": ["news","world","business","economy","markets","politics","technology"],
  "apnews.com": ["news","world","politics","sports","business"],
  "bbc.com": ["news","world","sports","football","science","technology"],
  "npr.org": ["news","culture","science","health","politics"],
  "pbs.org": ["news","education","science","nature"],
  "wsj.com": ["business","markets","economy","finance"],
  "nytimes.com": ["news","business","science","health","sports"],
  "washingtonpost.com": ["news","politics","world","economy"],
  "ft.com": ["finance","markets","economy","business"],
  "economist.com": ["economy","business","geopolitics","science"],
  "bloomberg.com": ["markets","finance","economy","business","technology"],
  "cnbc.com": ["markets","business","economy","finance"],
  "forbes.com": ["business","economy","leadership","technology"],
  "time.com": ["news","world","politics","health"],
  "theguardian.com": ["news","world","environment","sports"],
  "thetimes.co.uk": ["news","business","world","sports"],
  "latimes.com": ["news","world","politics","sports"],
  "scmp.com": ["asia","world","economy","business"],
  "nikkei.com": ["asia","economy","markets","business"],
  "dw.com": ["world","news","europe","economy"],
  "france24.com": ["news","world","economy","sports"],
  "aljazeera.com": ["news","world","politics","economy"],
  "csmonitor.com": ["news","world","politics","economy"],
  "propublica.org": ["investigative","policy","justice","politics"],
  "nature.com": ["science","research","biology","medicine"],
  "science.org": ["science","research","biology","technology"],
  "scientificamerican.com": ["science","biology","space","technology"],
  "newscientist.com": ["science","research","technology","health"],
  "nejm.org": ["medicine","health","clinical","research"],
  "thelancet.com": ["medicine","health","publichealth","research"],
  "who.int": ["health","publichealth","disease","medicine"],
  "cdc.gov": ["health","disease","epidemiology","publichealth"],
  "un.org": ["policy","development","economy","climate"],
  "worldbank.org": ["economy","development","finance","data"],
  "imf.org": ["economy","finance","macroeconomics","policy"],
  "oecd.org": ["economy","policy","data","education"],
  "weforum.org": ["economy","technology","policy","future"],
  "wikipedia.org": ["reference","general","history","science","animals","football"],
  "britannica.com": ["reference","general","history","animals","science"],
  "mit.edu": ["research","engineering","ai","technology"],
  "stanford.edu": ["research","ai","technology","science"],
  "harvard.edu": ["research","medicine","policy","economics"],
  "ox.ac.uk": ["research","science","medicine","humanities"],
  "cam.ac.uk": ["research","science","engineering","medicine"],
  "openai.com": ["ai","technology","research","llm"],
  "google.com": ["technology","ai","research","cloud"],
  "microsoft.com": ["technology","ai","cloud","business"],
  "ibm.com": ["technology","ai","enterprise","research"],
  "mckinsey.com": ["business","economy","strategy","industry"],
  "brookings.edu": ["policy","economy","geopolitics","research"],
  "fifa.com": ["football","soccer","worldcup","sports"],
  "uefa.com": ["football","soccer","championsleague","sports"],
  "premierleague.com": ["football","soccer","premierleague","sports"],
  "espn.com": ["sports","football","soccer","basketball","baseball"],
  "skysports.com": ["sports","football","soccer","tennis"],
  "theathletic.com": ["sports","football","soccer","analysis"],
  "goal.com": ["football","soccer","transfers","sports"],
  "nationalgeographic.com": ["animals","wildlife","nature","conservation"],
  "worldwildlife.org": ["animals","wildlife","conservation","biodiversity"],
  "smithsonianmag.com": ["animals","science","history","culture"],
}

export const DOMAIN_VIEW_WEIGHT: Record<string, number> = {
  "bbc.com": 100, "nytimes.com": 94, "theguardian.com": 88, "reuters.com": 82,
  "apnews.com": 78, "washingtonpost.com": 74, "wsj.com": 70, "ft.com": 60,
  "cnbc.com": 58, "bloomberg.com": 57, "npr.org": 52, "aljazeera.com": 50,
  "time.com": 49, "france24.com": 44, "dw.com": 43, "economist.com": 41,
  "digi24.ro": 38, "hotnews.ro": 36, "stirileprotv.ro": 34, "adevarul.ro": 31,
  "g4media.ro": 29, "mediafax.ro": 27, "biziday.ro": 24, "romania-insider.com": 19,
  "zf.ro": 16, "economica.net": 15, "profit.ro": 14, "bursa.ro": 13,
}

export const TOKEN_ALIASES: Record<string, string[]> = {
  football: ["soccer","fifa","uefa","premierleague"],
  soccer: ["football","fifa","uefa"],
  animal: ["animals","wildlife","species","fauna","pets"],
  animals: ["animal","wildlife","species","fauna","pets"],
  economy: ["economic","macroeconomics","markets","finance","gdp","inflation"],
  economic: ["economy","markets","finance"],
  finance: ["economy","markets","banking"],
  ai: ["artificial","intelligence","llm","machine","learning"],
  medicine: ["health","clinical","disease","publichealth"],
  climate: ["environment","sustainability","weather"],
  market: ["markets","economy","finance"],
}

export const STOPWORDS = new Set([
  "the","and","for","with","from","that","this","about","into","latest","news",
  "what","when","where","which","who","how","why","vs","top","best","new",
])

// ─── Helpers ──────────────────────────────────────────────────────────────────

export function normalizeDomain(value = ''): string {
  return String(value || '')
    .toLowerCase()
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .split('/')[0]
    .trim()
}

export function domainFromResult(item: { source?: string; url?: string }): string {
  const sourceDomain = normalizeDomain(item.source || '')
  if (sourceDomain) return sourceDomain
  const urlValue = String(item.url || '')
  if (!urlValue) return ''
  try { return normalizeDomain(new URL(urlValue).hostname) }
  catch { return normalizeDomain(urlValue) }
}

function tokenizeContext(text: string): string[] {
  return (text || '')
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, ' ')
    .split(/\s+/)
    .map(t => t.trim())
    .filter(t => t.length > 2 && !STOPWORDS.has(t))
}

function expandTerms(tokens: string[]): string[] {
  const expanded = new Set(tokens)
  tokens.forEach(token => {
    const aliases = TOKEN_ALIASES[token] || []
    aliases.forEach(a => expanded.add(a))
  })
  return [...expanded]
}

function scoreDomainForTerms(domain: string, terms: string[]): number {
  const tags = DOMAIN_TAGS[domain] || []
  const domainToken = domain.replace(/\.[a-z.]+$/, '').toLowerCase()
  let score = TRUSTED_SITES.includes(domain) ? 1 : 0
  terms.forEach(term => {
    if (!term) return
    if (tags.includes(term)) { score += 8; return }
    if (tags.some(tag => tag.includes(term) || term.includes(tag))) { score += 3 }
    if (domain.includes(term) || domainToken.includes(term)) { score += 2 }
  })
  return score
}

export function getTrustedSitesForTopic(topic = '', query = '', topN = 50): string[] {
  const terms = expandTerms(tokenizeContext(`${topic.trim().toLowerCase()} ${query.trim().toLowerCase()}`))
  const candidates = [...new Set([...TRUSTED_SITES, ...Object.keys(DOMAIN_TAGS)].map(d => d.trim().toLowerCase()).filter(Boolean))]
  const ranked = candidates
    .map(domain => ({ domain, score: scoreDomainForTerms(domain, terms) }))
    .sort((a, b) => b.score - a.score || a.domain.localeCompare(b.domain))
  const strongMatches = ranked.filter(item => item.score > 1).map(item => item.domain)
  const fallback = TRUSTED_SITES.filter(d => !strongMatches.includes(d))
  return [...strongMatches, ...fallback].slice(0, topN)
}
