import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import './ImageUploader.css'
import { Upload, Image as ImageIcon } from 'lucide-react'

function ImageUploader({ onImageSelect, imagePreview, disabled }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onImageSelect(acceptedFiles[0])
    }
  }, [onImageSelect])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
    },
    multiple: false,
    disabled
  })

  return (
    <div className="image-uploader">
      <h2 className="section-title">Tải lên ảnh</h2>
      
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
      >
        <input {...getInputProps()} />
        
        {imagePreview ? (
          <div className="image-preview">
            <img src={imagePreview} alt="Preview" />
            <div className="image-overlay">
              <Upload size={24} />
              <p>Nhấp hoặc kéo thả để thay đổi</p>
            </div>
          </div>
        ) : (
          <div className="upload-placeholder">
            <ImageIcon size={64} strokeWidth={1.5} />
            <h3>
              {isDragActive ? 'Thả ảnh vào đây' : 'Kéo thả ảnh vào đây'}
            </h3>
            <p>hoặc</p>
            <button type="button" className="upload-button">
              Chọn ảnh từ máy tính
            </button>
            <p className="file-info">
              Hỗ trợ: PNG, JPG, JPEG, GIF, BMP, WebP (Tối đa 10MB)
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ImageUploader
