export type PIICategory = 'api_key' | 'email' | 'password' | 'token' | 'phone' | 'ssn' | 'credit_card' | 'ip_address' | 'jwt' | 'private_key'

export interface PIIDetection {
  category: PIICategory
  label: string
  severity: 'critical' | 'warning' | 'info'
  match: string
  start: number
  end: number
  masked: string
}

const PATTERNS: { category: PIICategory; label: string; severity: 'critical' | 'warning' | 'info'; regex: RegExp; mask?: (m: string) => string }[] = [
  { category: 'api_key', label: 'API Key', severity: 'critical', regex: /\b(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|glpat-[a-zA-Z0-9\-]{20,}|xox[bpsa]-[a-zA-Z0-9\-]+)\b/g },
  { category: 'jwt', label: 'JWT Token', severity: 'critical', regex: /\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b/g },
  { category: 'private_key', label: 'Private Key', severity: 'critical', regex: /-----BEGIN (RSA |EC )?PRIVATE KEY-----/g },
  { category: 'password', label: 'Password', severity: 'critical', regex: /\b(password|passwd|pwd)\s*[:=]\s*["']?[^\s"']{6,}["']?/gi },
  { category: 'token', label: 'Access Token', severity: 'warning', regex: /\b(token|bearer|authorization)\s*[:=]\s*["']?[^\s"']{8,}["']?/gi },
  { category: 'email', label: 'Email Address', severity: 'warning', regex: /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/g },
  { category: 'phone', label: 'Phone Number', severity: 'info', regex: /\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g },
  { category: 'ssn', label: 'SSN', severity: 'critical', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { category: 'credit_card', label: 'Credit Card', severity: 'critical', regex: /\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b/g },
  { category: 'ip_address', label: 'IP Address', severity: 'info', regex: /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g },
]

function defaultMask(m: string): string {
  if (m.length <= 8) return '[REDACTED]'
  return m.slice(0, 4) + '*'.repeat(m.length - 8) + m.slice(-4)
}

export function detectPII(text: string): PIIDetection[] {
  const detections: PIIDetection[] = []
  for (const p of PATTERNS) {
    let match: RegExpExecArray | null
    const re = new RegExp(p.regex.source, p.regex.flags)
    while ((match = re.exec(text)) !== null) {
      const value = match[0]
      detections.push({
        category: p.category,
        label: p.label,
        severity: p.severity,
        match: value,
        start: match.index,
        end: match.index + value.length,
        masked: defaultMask(value),
      })
    }
  }
  return detections.sort((a, b) => a.start - b.start)
}

export function redactText(text: string): string {
  let result = text
  const detections = detectPII(text)
  for (let i = detections.length - 1; i >= 0; i--) {
    const d = detections[i]
    result = result.slice(0, d.start) + '[REDACTED_SECRET]' + result.slice(d.end)
  }
  return result
}

export function hasCriticalPII(text: string): boolean {
  return detectPII(text).some(d => d.severity === 'critical')
}

export function getSeverityColor(severity: string): string {
  if (severity === 'critical') return 'text-red-600 dark:text-red-400'
  if (severity === 'warning') return 'text-amber-600 dark:text-amber-400'
  return 'text-blue-600 dark:text-blue-400'
}

export function getSeverityBg(severity: string): string {
  if (severity === 'critical') return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
  if (severity === 'warning') return 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
  return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
}
