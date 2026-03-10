import React, { useState } from 'react'
import './App.css'
import Header from './components/Header'
import ImageUploader from './components/ImageUploader'
import ResultDisplay from './components/ResultDisplay'
import LoadingSpinner from './components/LoadingSpinner'
import ErrorMessage from './components/ErrorMessage'
import { extractText } from './services/api'

function App() {
  const [image, setImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleImageSelect = async (file) => {
    setImage(file)
    setError(null)
    setResult(null)

    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setImagePreview(reader.result)
    }
    reader.readAsDataURL(file)
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

  return (
    <div className="app">
      <Header />
      
      <main className="main-content">
        <div className="container">
          <div className="content-grid">
            {/* Left side: Upload section */}
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

            {/* Right side: Result section */}
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
        </div>
      </main>

      <footer className="footer">
        <div className="container">
          <p>© 2026 OCR Service. Powered by GLM-OCR Vietnamese Model.</p>
        </div>
      </footer>
    </div>
  )
}

export default App
