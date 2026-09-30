import { describe, it, expect } from 'vitest'
import {
  EDGE_RELATION_COLORS,
  buildBlocksEdges,
  edgeRelationColor,
  edgeRelationLabel,
} from '@/utils/graphUtils'

describe('edgeRelationLabel', () => {
  const labels = { dependency: 'DEPENDS_ON', blocks: 'BLOCKS' }

  it('returns the i18n label for a known relation', () => {
    expect(edgeRelationLabel('dependency', labels)).toBe('DEPENDS_ON')
    expect(edgeRelationLabel('blocks', labels)).toBe('BLOCKS')
  })

  it('falls back to the raw relation when no label exists', () => {
    expect(edgeRelationLabel('mystery', labels)).toBe('mystery')
  })
})

describe('edgeRelationColor', () => {
  it('returns a distinct hex color for every relation', () => {
    const relations = ['component', 'dependency', 'blocks', 'affects', 'code', 'agent', 'pr']
    const colors = relations.map(relation => edgeRelationColor(relation))
    expect(colors.every(color => /^#[0-9a-f]{6}$/i.test(color))).toBe(true)
    expect(new Set(colors).size).toBe(relations.length)
  })

  it('covers the four relations required by the epic', () => {
    expect(EDGE_RELATION_COLORS.dependency).toBeDefined()
    expect(EDGE_RELATION_COLORS.blocks).toBeDefined()
    expect(EDGE_RELATION_COLORS.affects).toBeDefined()
    expect(EDGE_RELATION_COLORS.component).toBeDefined()
  })

  it('falls back to gray for unknown relations', () => {
    expect(edgeRelationColor('mystery')).toBe('#64748b')
  })
})

describe('buildBlocksEdges', () => {
  const issues = [
    { id: 'A', status: 'OPEN', blocks: ['B', 'X'] },
    { id: 'B', status: 'IN_PROGRESS', blocks: [] },
    { id: 'C', status: 'CLOSED', blocks: ['A'] },
    { id: 'D', status: 'OPEN', blocks: ['C'] },
    { id: 'E', status: 'CLOSED' },
  ]

  it('derives the inverse BLOCKS edge from active dependencies', () => {
    expect(buildBlocksEdges(issues)).toEqual([
      { id: 'A-blocks-B', from: 'A', to: 'B', relation: 'blocks' },
    ])
  })

  it('skips blockers and targets that are CLOSED', () => {
    const result = buildBlocksEdges(issues)
    expect(result.some(edge => edge.from === 'C')).toBe(false)
    expect(result.some(edge => edge.to === 'C')).toBe(false)
  })

  it('skips targets that are not part of the issue list', () => {
    const result = buildBlocksEdges(issues)
    expect(result.some(edge => edge.to === 'X')).toBe(false)
  })

  it('skips edges whose source is not visible', () => {
    expect(buildBlocksEdges(issues, new Set(['B']))).toEqual([])
  })

  it('skips edges whose target is not visible', () => {
    expect(buildBlocksEdges(issues, new Set(['A']))).toEqual([])
  })

  it('keeps edges when both endpoints are visible', () => {
    expect(buildBlocksEdges(issues, new Set(['A', 'B']))).toEqual([
      { id: 'A-blocks-B', from: 'A', to: 'B', relation: 'blocks' },
    ])
  })
})
