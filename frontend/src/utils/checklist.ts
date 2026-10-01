export interface ChecklistItem {
  key: string
  checked: boolean
}

export const CHECKBOX_LINE = /^- \[([xX ])\] (.+)$/m

export function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

export function unescapeHtml(str: string): string {
  return str
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/&amp;/g, '&')
}

export function checklistKey(text: string): string {
  return text.replace(/\s+/g, ' ').trim().toLowerCase()
}

export function checklistKeyFromEscaped(escapedText: string): string {
  return checklistKey(unescapeHtml(escapedText))
}

export function parseChecklistItems(content: string): ChecklistItem[] {
  const items: ChecklistItem[] = []
  for (const line of content.split('\n')) {
    const match = CHECKBOX_LINE.exec(line)
    if (match) {
      items.push({ key: checklistKey(match[2]), checked: match[1].toLowerCase() === 'x' })
    }
  }
  return items
}

export function isChecklistItemChecked(item: ChecklistItem, overrides: Record<string, boolean>): boolean {
  if (Object.prototype.hasOwnProperty.call(overrides, item.key)) {
    return overrides[item.key]
  }
  return item.checked
}
