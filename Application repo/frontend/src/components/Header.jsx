import React from 'react'
import './Header.css'
import { FileText } from 'lucide-react'

function Header() {
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <div className="logo">
            <FileText size={32} />
            <h1>OCR Service</h1>
          </div>
          <p className="tagline">Trích xuất văn bản từ ảnh một cách nhanh chóng và chính xác</p>
        </div>
      </div>
    </header>
  )
}

export default Header
