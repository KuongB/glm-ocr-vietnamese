import React, { useState } from 'react'
import './HistorySidebar.css'
import { Clock, Trash2, X, Copy, Check, Download } from 'lucide-react'

function HistorySidebar({ history, onClear }) {
  const [selectedItem, setSelectedItem] = useState(null)
  const [copied, setCopied] = useState(false)

  if (!history || history.length === 0) return null

  const handleCloseModal = () => {
    setSelectedItem(null)
    setCopied(false)
  }

  const handleCopy = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Không thể sao chép:', err)
    }
  }

  const handleDownload = (text) => {
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `history-ocr-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <div className="history-container">
        <div className="history-header">
          <h3>
            <Clock size={20} />
            Lịch sử trích xuất
          </h3>
          <button className="clear-btn" onClick={onClear}>
            <Trash2 size={16} />
            Xóa lịch sử
          </button>
        </div>

        <div className="history-grid">
          {history.map((item) => (
            <div 
              key={item.id} 
              className="history-card" 
              onClick={() => setSelectedItem(item)}
            >
              <div className="history-text-preview">
                {item.text}
              </div>
              <div className="history-meta">
                <span>{new Date(item.timestamp).toLocaleString('vi-VN')}</span>
                <span>{item.text.length} ký tự</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedItem && (
        <div className="history-modal-overlay" onClick={handleCloseModal}>
          <div className="history-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="history-modal-header">
              <div className="header-info">
                <h3>Chi tiết kết quả</h3>
              </div>
              <button className="modal-close-btn" onClick={handleCloseModal}>
                <X size={20} />
              </button>
            </div>
            
            <div className="history-modal-actions">
              <button 
                className={`action-btn ${copied ? 'copied' : ''}`} 
                onClick={() => handleCopy(selectedItem.text)}
              >
                {copied ? <Check size={18} /> : <Copy size={18} />}
                <span>{copied ? 'Đã chép' : 'Sao chép'}</span>
              </button>
              <button 
                className="action-btn" 
                onClick={() => handleDownload(selectedItem.text)}
              >
                <Download size={18} />
                <span>Xuất file</span>
              </button>
            </div>

            <div className="history-modal-body">
              <div className="history-modal-text">
                {selectedItem.text}
              </div>
            </div>

            <div className="history-modal-footer">
              <div className="history-modal-meta-item">
                <span className="meta-label">Thời gian lưu</span>
                <span className="meta-value">
                  {new Date(selectedItem.timestamp).toLocaleString('vi-VN')}
                </span>
              </div>
              <div className="history-modal-meta-item">
                <span className="meta-label">Số ký tự</span>
                <span className="meta-value">
                  {selectedItem.text.length}
                </span>
              </div>
              <div className="history-modal-meta-item">
                <span className="meta-label">Thời gian xử lý</span>
                <span className="meta-value">
                  {selectedItem.processing_time.toFixed(2) || 'N/A'}s
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default HistorySidebar
