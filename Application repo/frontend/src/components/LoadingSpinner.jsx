import React from 'react'
import './LoadingSpinner.css'

function LoadingSpinner() {
  return (
    <div className="loading-spinner-container">
      <div className="spinner"></div>
      <h3>Đang xử lý...</h3>
      <p>Vui lòng đợi trong giây lát</p>
    </div>
  )
}

export default LoadingSpinner
