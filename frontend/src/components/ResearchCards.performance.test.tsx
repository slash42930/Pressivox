import { render, screen } from '@testing-library/react'
import { describe, expect, test } from 'vitest'

import { ResearchCards } from './ResearchCards'
import type { SearchResult } from '../types'

describe('ResearchCards performance', () => {
  test('renders a large result set within a bounded time', () => {
    const results: SearchResult[] = Array.from({ length: 300 }, (_, i) => ({
      title: `Result ${i}`,
      url: `https://example.com/${i}`,
      source: 'example.com',
      snippet: `Snippet for result ${i} with enough text to render card content safely.`,
      score: 0.9,
    }))

    const started = performance.now()
    render(
      <ResearchCards
        results={results}
        compareItems={[]}
        onToggleCompare={() => {}}
        onCopyLink={() => {}}
      />,
    )
    const elapsed = performance.now() - started

    expect(screen.getByText('Result 0')).toBeInTheDocument()
    expect(screen.getByText('Result 299')).toBeInTheDocument()
    expect(elapsed).toBeLessThan(5000)
  })
})
