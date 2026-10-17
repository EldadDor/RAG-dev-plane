import { describe, expect, it } from 'vitest'
import { getDocumentSizeBadge, getDocumentTypeBadge } from './documentBadges'

// Read CSS as test data; Vitest otherwise replaces CSS imports with empty stubs.
// Load the Node built-in at runtime without adding Node types to the browser app.
const fsModule = 'node:fs'
const {readFileSync} = await import(/* @vite-ignore */ fsModule) as {readFileSync: (path: URL, encoding: 'utf8') => string}

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

describe('TH-01/02 semantic palette contrast', () => {
  const css = readFileSync(new URL('./styles.css', import.meta.url), 'utf8')
  const declarations = (block: string) => Object.fromEntries([...block.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map((match) => [match[1], match[2].trim()]))
  const dark = declarations(css.match(/:root, :root\[data-theme="dark"\] \{([^}]+)\}/)![1])
  const palettes = ['dark', 'white', 'new-age'].map((name) => ({name, tokens: name === 'dark' ? dark : {...dark, ...declarations(css.match(new RegExp(':root\\[data-theme="' + name + '"\\] \\{([^}]+)\\}'))![1])}}))
  function luminance(hex: string): number {
    const channels = hex.slice(1).match(/../g)!.map((channel) => parseInt(channel, 16) / 255).map((value) => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
    return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722
  }
  function contrast(foreground: string, background: string) {
    const [light, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
    return (light + .05) / (dark + .05)
  }
  for (const {name, tokens} of palettes) {
    const resolve = (value: string): string => value.startsWith('var(') ? resolve(tokens[value.slice(4, -1)]) : value
    it(`${name}: keeps text readable on surfaces and both ends of message gradients`, () => {
      for (const foreground of ['--text', '--muted', '--body-soft']) {
        for (const background of ['--bg', '--panel', '--surface', '--surface-raised', '--user-start', '--user-end']) {
          expect(contrast(tokens[foreground], tokens[background]), `${foreground} on ${background}`).toBeGreaterThanOrEqual(4.5)
        }
      }
      for (const background of ['--primary-start', '--primary-end']) expect(contrast(tokens['--accent-contrast'], resolve(tokens[background]))).toBeGreaterThanOrEqual(4.5)
      expect(contrast(tokens['--danger'], tokens['--danger-surface'])).toBeGreaterThanOrEqual(4.5)
    })
    it(`${name}: keeps focus/control boundaries and document badge text readable`, () => {
      for (const surface of ['--bg', '--panel', '--surface', '--surface-raised']) {
        expect(contrast(tokens['--focus'], tokens[surface]), `focus on ${surface}`).toBeGreaterThanOrEqual(3)
        expect(contrast(tokens['--control-border'], tokens[surface]), `control border on ${surface}`).toBeGreaterThanOrEqual(3)
      }
      for (const badge of ['green', 'blue', 'yellow', 'rose', 'gray', 'violet', 'orange']) expect(contrast(tokens[`--badge-${badge}-text`], tokens[`--badge-${badge}-bg`]), `${badge} badge`).toBeGreaterThanOrEqual(4.5)
    })
  }
  it('uses semantic colors for badges rather than fixed dark-theme colors', () => {
    expect(getDocumentSizeBadge(0).color).toBe('var(--badge-green-text)')
    expect(getDocumentTypeBadge('pdf').background).toBe('var(--badge-rose-bg)')
  })
})
