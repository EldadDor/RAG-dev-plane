export type DocumentBadge = { label: string; color: string; background: string }

// Inclusive upper bounds. Change thresholds and colors here, without editing components.
export const documentSizeBadges: Array<DocumentBadge & { maxChunks: number }> = [
  { label: 'Small', maxChunks: 25, color: '#a7f3d0', background: '#153b32' },
  { label: 'Medium', maxChunks: 100, color: '#bfdbfe', background: '#1c3559' },
  { label: 'Big', maxChunks: 500, color: '#fde68a', background: '#453617' },
  { label: 'Extra-Large', maxChunks: Infinity, color: '#fecdd3', background: '#482634' },
]
export const unknownDocumentBadge: DocumentBadge = { label: 'Unknown', color: '#cbd5e1', background: '#293548' }

export const documentTypeBadges: Record<string, DocumentBadge> = {
  word: { label: 'Word', color: '#bfdbfe', background: '#1c3559' },
  pdf: { label: 'PDF', color: '#fecdd3', background: '#482634' },
  markdown: { label: 'Markdown', color: '#c4b5fd', background: '#352650' },
  html: { label: 'HTML', color: '#fed7aa', background: '#492d1b' },
  text: { label: 'Text', color: '#cbd5e1', background: '#293548' },
  code: { label: 'Code', color: '#a7f3d0', background: '#153b32' },
  unknown: unknownDocumentBadge,
}

export function getDocumentTypeBadge(type: string): DocumentBadge {
  return Object.hasOwn(documentTypeBadges, type) ? documentTypeBadges[type] : unknownDocumentBadge
}

export function getDocumentSizeBadge(count: number | null): DocumentBadge {
  if (count === null || !Number.isSafeInteger(count) || count < 0) return unknownDocumentBadge
  return documentSizeBadges.find((badge) => count <= badge.maxChunks) ?? unknownDocumentBadge
}
