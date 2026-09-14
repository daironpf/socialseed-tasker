import { ref } from 'vue'

export type ExportFormat = 'csv' | 'json' | 'svg' | 'png' | 'markdown'

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function downloadText(text: string, filename: string, mime: string) {
  const blob = new Blob([text], { type: mime })
  downloadBlob(blob, filename)
}

export function useExport() {
  const exporting = ref(false)
  async function exportCSV(data: Record<string, any>[], filename: string) {
    exporting.value = true
    try {
      if (data.length === 0) return
      const headers = Object.keys(data[0])
      const csvRows = [
        headers.join(','),
        ...data.map(row =>
          headers.map(h => {
            const val = String(row[h] ?? '')
            return val.includes(',') || val.includes('"') || val.includes('\n')
              ? `"${val.replace(/"/g, '""')}"`
              : val
          }).join(',')
        ),
      ]
      downloadText(csvRows.join('\n'), `${filename}.csv`, 'text/csv')
    } finally {
      exporting.value = false
    }
  }

  async function exportJSON(data: any, filename: string) {
    exporting.value = true
    try {
      const json = JSON.stringify(data, null, 2)
      downloadText(json, `${filename}.json`, 'application/json')
    } finally {
      exporting.value = false
    }
  }

  async function exportSVG(svgElement: SVGSVGElement, filename: string) {
    exporting.value = true
    try {
      const clone = svgElement.cloneNode(true) as SVGSVGElement
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
      const serializer = new XMLSerializer()
      const svgStr = serializer.serializeToString(clone)
      downloadText(svgStr, `${filename}.svg`, 'image/svg+xml')
    } finally {
      exporting.value = false
    }
  }

  async function exportPNG(svgElement: SVGSVGElement, filename: string, scale = 2) {
    exporting.value = true
    try {
      const clone = svgElement.cloneNode(true) as SVGSVGElement
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
      const serializer = new XMLSerializer()
      const svgStr = serializer.serializeToString(clone)
      const svgBlob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' })
      const url = URL.createObjectURL(svgBlob)

      const img = new Image()
      img.src = url
      await new Promise<void>((resolve, reject) => {
        img.onload = () => resolve()
        img.onerror = reject
      })

      const canvas = document.createElement('canvas')
      canvas.width = img.width * scale
      canvas.height = img.height * scale
      const ctx = canvas.getContext('2d')!
      ctx.scale(scale, scale)
      ctx.fillStyle = 'white'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0)

      await new Promise<void>((resolve, reject) => {
        canvas.toBlob((blob) => {
          if (blob) {
            downloadBlob(blob, `${filename}.png`)
          } else {
            reject(new Error('Failed to generate PNG blob'))
          }
          URL.revokeObjectURL(url)
          resolve()
        }, 'image/png')
      })
    } finally {
      exporting.value = false
    }
  }

  async function exportMarkdown(content: string, filename: string) {
    exporting.value = true
    try {
      downloadText(content, `${filename}.md`, 'text/markdown')
    } finally {
      exporting.value = false
    }
  }

  return {
    exporting,
    exportCSV,
    exportJSON,
    exportSVG,
    exportPNG,
    exportMarkdown,
  }
}
