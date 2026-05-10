import { render, screen } from '@testing-library/react'
import { describe, expect, test } from 'vitest'

import { StructuredResearchSections } from './Research'
import type { ResearchResponse } from '../types'

function buildResponse(): ResearchResponse {
  return {
    query: 'mercury',
    topic: 'general',
    provider: 'tavily',
    summary: 'Concise mercury summary.',
    summary_points: ['Planet: Mercury is closest to the Sun.'],
    summary_markdown: '- Planet: Mercury is closest to the Sun.',
    results: [
      {
        title: 'Mercury Planet',
        url: 'https://example.com/mercury',
        source: 'example.com',
        snippet: 'Mercury is the smallest planet in the solar system.',
      },
    ],
    selected_sources: [],
    source_count: 1,
    extracted_count: 1,
    ambiguous: false,
    meaning_groups: [],
    sections: {
      concise_summary: 'Concise mercury summary.',
      key_findings: ['Planet: Mercury is closest to the Sun.'],
      detailed_analysis: '- Planet: Mercury is closest to the Sun.',
      sources: [
        {
          title: 'Mercury Planet',
          url: 'https://example.com/mercury',
          source: 'example.com',
          snippet: 'Mercury is the smallest planet in the solar system.',
        },
      ],
      limitations: ['Coverage is limited to top-ranked sources.'],
      suggested_follow_up_queries: ['mercury orbital observations'],
      confidence: 'medium',
    },
  }
}

describe('StructuredResearchSections', () => {
  test('renders structured sections and accessible headings', () => {
    render(<StructuredResearchSections response={buildResponse()} />)

    expect(screen.getByRole('heading', { name: 'Concise Summary' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Key Findings' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Detailed Analysis' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Sources' })).toBeInTheDocument()

    expect(screen.getByText('Coverage is limited to top-ranked sources.')).toBeInTheDocument()
    expect(screen.getByText('mercury orbital observations')).toBeInTheDocument()

    const sourceLink = screen.getByRole('link', { name: /Mercury Planet/i })
    expect(sourceLink).toHaveAttribute('href', 'https://example.com/mercury')
  })
})
