import React, { useState } from 'react'
import './ResultDisplay.css'
import { Copy, Check, Download } from 'lucide-react'

function ResultDisplay({ result }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = () => {
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
        <div className="result-actions">
          <button
            className="icon-button"
            onClick={handleCopy}
            title="Sao chép"
          >
            {copied ? <Check size={20} /> : <Copy size={20} />}
          </button>
          <button
            className="icon-button"
            onClick={handleDownload}
            title="Tải xuống"
          >
            <Download size={20} />
          </button>
        </div>
      </div>

      <div className="result-content">
        <div className="result-text">
          {result.text || 'Không có văn bản nào được phát hiện'}
        </div>
      </div>

      <div className="result-meta">
        <div className="meta-item">
          <span className="meta-label">Thời gian xử lý:</span>
          <span className="meta-value">{result.processing_time?.toFixed(2)}s</span>
        </div>
        {result.confidence && (
          <div className="meta-item">
            <span className="meta-label">Độ tin cậy:</span>
            <span className="meta-value">{(result.confidence * 100).toFixed(1)}%</span>
          </div>
        )}
        <div className="meta-item">
          <span className="meta-label">Số ký tự:</span>
          <span className="meta-value">{result.text?.length || 0}</span>
        </div>
      </div>

      {copied && (
        <div className="toast">
          <Check size={16} />
          <span>Đã sao chép vào clipboard</span>
        </div>
      )}
    </div>
  )
}

export default ResultDisplay
