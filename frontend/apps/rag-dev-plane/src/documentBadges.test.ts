import { describe, expect, it } from 'vitest'
import { getDocumentSizeBadge, getDocumentTypeBadge } from './documentBadges'

describe('document badges', () => {
  it.each([[0, 'Small'], [25, 'Small'], [26, 'Medium'], [100, 'Medium'], [101, 'Big'], [500, 'Big'], [501, 'Extra-Large'], [Number.MAX_SAFE_INTEGER, 'Extra-Large']])('classifies boundary count %s as %s', (count, label) => {
    expect(getDocumentSizeBadge(count as number).label).toBe(label)
  })
  it.each([null, -1, 1.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1])('does not classify invalid or missing count %s as Small', (count) => {
    expect(getDocumentSizeBadge(count).label).toBe('Unknown')
  })
  it('handles all canonical types and future or inherited object keys safely', () => {
    for (const type of ['word', 'pdf', 'markdown', 'html', 'text', 'code']) expect(getDocumentTypeBadge(type).label).not.toBe('Unknown')
    for (const type of ['unknown', 'future', 'constructor', '__proto__']) expect(getDocumentTypeBadge(type).label).toBe('Unknown')
  })
})
