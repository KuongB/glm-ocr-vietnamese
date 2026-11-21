import React, { useState, useEffect } from 'react'
import './App.css'
import Header from './components/Header'
import ImageUploader from './components/ImageUploader'
import ResultDisplay from './components/ResultDisplay'
import LoadingSpinner from './components/LoadingSpinner'
import ErrorMessage from './components/ErrorMessage'
import ImageEditor from './components/ImageEditor'
import HistorySidebar from './components/HistorySidebar'  
import { extractText } from './services/api'
import logo from './assets/logo_ocr.png'

function App() {
  const [image, setImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [theme, setTheme] = useState('light')
  
  const [showEditor, setShowEditor] = useState(false)
  const [rawImageSrc, setRawImageSrc] = useState(null)
  
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('ocr_history')
    return saved ? JSON.parse(saved) : []
  })

  // Apply theme to document root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  // Local storage persistence for history
  useEffect(() => {
    localStorage.setItem('ocr_history', JSON.stringify(history))
  }, [history])

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'))
  }

  const handleImageSelect = async (file) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      setRawImageSrc(reader.result)
      setShowEditor(true)
    }
    reader.readAsDataURL(file)
  }

  const handleSaveEditedImage = (editedFile, previewUrl) => {
    setImage(editedFile)
    setImagePreview(previewUrl)
    setShowEditor(false)
    setError(null)
    setResult(null)
  }

  const handleCancelEditor = () => {
    setShowEditor(false)
    setRawImageSrc(null)
    if (!image) {
      setImage(null)
      setImagePreview(null)
    }
  }

  const handleExtractText = async () => {
    if (!image) {
      setError('Vui lòng chọn một ảnh trước')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await extractText(image)
      setResult(result)

      if (result.text && result.text.trim().length > 0) {
        setHistory(prev => [
          {
            id: Date.now(),
            text: result.text,
            timestamp: Date.now(),
            processing_time: result.processing_time || 'N/A'
          },
          ...prev
        ])
      }
    } catch (err) {
      setError(err.message || 'Có lỗi xảy ra khi xử lý ảnh')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setImage(null)
    setImagePreview(null)
    setResult(null)
    setError(null)
  }

  const handleClearHistory = () => {
    if (window.confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử?')) {
      setHistory([])
    }
  }

  return (
    <div className="app">
      <img src={logo} alt="OCR Logo" className="corner-logo" />
      <button 
        className="theme-toggle-btn" 
        onClick={toggleTheme}
        aria-label="Toggle theme"
      >
        {theme === 'light' ? '🌙' : '☀️'}
      </button>

      <Header />
      
      <main className="main-content">
        <div className="container">
          <div className="content-grid">
            <div className="upload-section">
              <ImageUploader 
                onImageSelect={handleImageSelect}
                imagePreview={imagePreview}
                disabled={loading}
              />
              
              {error && <ErrorMessage message={error} />}
              
              <div className="action-buttons">
                <button 
                  className="btn btn-primary"
                  onClick={handleExtractText}
                  disabled={!image || loading}
                >
                  {loading ? 'Đang xử lý...' : 'Trích xuất văn bản'}
                </button>
                
                {(image || result) && (
                  <button 
                    className="btn btn-secondary"
                    onClick={handleReset}
                    disabled={loading}
                  >
                    Làm mới
                  </button>
                )}
              </div>
            </div>

            <div className="result-section">
              {loading && <LoadingSpinner />}
              
              {result && !loading && (
                <ResultDisplay result={result} />
              )}
              
              {!loading && !result && !image && (
                <div className="empty-state">
                  <svg 
                    className="empty-icon" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                    />
                  </svg>
                  <h3>Chưa có kết quả</h3>
                  <p>Tải lên một ảnh và nhấn "Trích xuất văn bản" để bắt đầu</p>
                </div>
              )}
            </div>
          </div>

          <HistorySidebar 
            history={history}
            onClear={handleClearHistory}
          />
        </div>
      </main>

      {showEditor && rawImageSrc && (
        <ImageEditor 
          imageSrc={rawImageSrc}
          onSave={handleSaveEditedImage}
          onCancel={handleCancelEditor}
        />
      )}

      <footer className="footer">
        <div className="container">
          <p>© 2026 OCR Service. Powered by GLM-OCR Vietnamese Model.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
