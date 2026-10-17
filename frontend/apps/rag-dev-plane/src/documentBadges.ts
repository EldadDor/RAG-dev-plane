export type DocumentBadge = { label: string; color: string; background: string }

// Inclusive upper bounds. Change thresholds and colors here, without editing components.
export const documentSizeBadges: Array<DocumentBadge & { maxChunks: number }> = [
  { label: 'Small', maxChunks: 25, color: 'var(--badge-green-text)', background: 'var(--badge-green-bg)' },
  { label: 'Medium', maxChunks: 100, color: 'var(--badge-blue-text)', background: 'var(--badge-blue-bg)' },
  { label: 'Big', maxChunks: 500, color: 'var(--badge-yellow-text)', background: 'var(--badge-yellow-bg)' },
  { label: 'Extra-Large', maxChunks: Infinity, color: 'var(--badge-rose-text)', background: 'var(--badge-rose-bg)' },
]
export const unknownDocumentBadge: DocumentBadge = { label: 'Unknown', color: 'var(--badge-gray-text)', background: 'var(--badge-gray-bg)' }

export const documentTypeBadges: Record<string, DocumentBadge> = {
  word: { label: 'Word', color: 'var(--badge-blue-text)', background: 'var(--badge-blue-bg)' },
  pdf: { label: 'PDF', color: 'var(--badge-rose-text)', background: 'var(--badge-rose-bg)' },
  markdown: { label: 'Markdown', color: 'var(--badge-violet-text)', background: 'var(--badge-violet-bg)' },
  html: { label: 'HTML', color: 'var(--badge-orange-text)', background: 'var(--badge-orange-bg)' },
  text: { label: 'Text', color: 'var(--badge-gray-text)', background: 'var(--badge-gray-bg)' },
  code: { label: 'Code', color: 'var(--badge-green-text)', background: 'var(--badge-green-bg)' },
  unknown: unknownDocumentBadge,
}

export function getDocumentTypeBadge(type: string): DocumentBadge {
  return Object.hasOwn(documentTypeBadges, type) ? documentTypeBadges[type] : unknownDocumentBadge
}

export function getDocumentSizeBadge(count: number | null): DocumentBadge {
  if (count === null || !Number.isSafeInteger(count) || count < 0) return unknownDocumentBadge
  return documentSizeBadges.find((badge) => count <= badge.maxChunks) ?? unknownDocumentBadge
}
