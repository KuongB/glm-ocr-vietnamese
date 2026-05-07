import React, { useState } from 'react'
import './ResultDisplay.css'
import { Copy, Check, Download, FileX } from 'lucide-react'

function ResultDisplay({ result }) {
  const [copied, setCopied] = useState(false)

  const hasText = result?.text && result.text.trim().length > 0

  const handleCopy = async () => {
    if (!hasText) return
    try {
      await navigator.clipboard.writeText(result.text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = () => {
    if (!hasText) return
    const blob = new Blob([result.text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ocr-result-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="result-display">
      <div className="result-header">
        <h2 className="section-title">Kết quả</h2>
      </div>

      <div className="result-container">
        <div className="result-content">
          {hasText ? (
            <div className="result-text">{result.text}</div>
          ) : (
            <div className="empty-text-state">
              <FileX size={48} className="empty-text-icon" />
              <p>Không tìm thấy văn bản nào trong ảnh này</p>
            </div>
          )}
        </div>

        {hasText && (
          <div className="floating-actions">
            <button className="action-pill" onClick={handleCopy}>
              {copied ? <Check size={16} /> : <Copy size={16} />}
              <span>{copied ? 'Đã chép' : 'Sao chép'}</span>
            </button>
            <button className="action-pill" onClick={handleDownload}>
              <Download size={16} />
              <span>Xuất file</span>
            </button>
          </div>
        )}
      </div>

      <div className="result-meta">
        <div className="meta-item">
          <span className="meta-label">Thời gian xử lý</span>
          <span className="meta-value">
            {result?.processing_time != null ? `${result.processing_time.toFixed(2)}s` : 'N/A'}
          </span>
        </div>

        <div className="meta-item">
          <span className="meta-label">Số ký tự</span>
          <span className="meta-value">
            {hasText ? result.text.length : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  )
}

export default ResultDisplay
