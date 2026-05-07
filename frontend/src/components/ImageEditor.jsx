import React, { useState, useRef } from 'react'
import ReactCrop from 'react-image-crop'
import 'react-image-crop/dist/ReactCrop.css'
import './ImageEditor.css'
import { RotateCw, Check, X } from 'lucide-react'

function ImageEditor({ imageSrc, onSave, onCancel }) {
  const [crop, setCrop] = useState()
  const [rotation, setRotation] = useState(0)
  const imageRef = useRef(null)

  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360)
  }

  const handleSave = () => {
    const image = imageRef.current
    if (!image) return

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    const scaleX = image.naturalWidth / image.width
    const scaleY = image.naturalHeight / image.height

    const cropX = (crop?.x || 0) * scaleX
    const cropY = (crop?.y || 0) * scaleY
    const cropWidth = crop?.width ? crop.width * scaleX : image.naturalWidth
    const cropHeight = crop?.height ? crop.height * scaleY : image.naturalHeight

    if (rotation % 180 === 90) {
      canvas.width = cropHeight
      canvas.height = cropWidth
    } else {
      canvas.width = cropWidth
      canvas.height = cropHeight
    }

    ctx.translate(canvas.width / 2, canvas.height / 2)
    ctx.rotate((rotation * Math.PI) / 180)
    ctx.translate(-canvas.width / 2, -canvas.height / 2)

    const drawX = rotation === 90 || rotation === 180 ? canvas.width - cropWidth : 0
    const drawY = rotation === 180 || rotation === 270 ? canvas.height - cropHeight : 0

    ctx.drawImage(
      image,
      cropX,
      cropY,
      cropWidth,
      cropHeight,
      drawX,
      drawY,
      cropWidth,
      cropHeight
    )

    canvas.toBlob((blob) => {
      if (!blob) return
      const file = new File([blob], `edited_${Date.now()}.jpg`, { type: 'image/jpeg' })
      const previewUrl = URL.createObjectURL(blob)
      onSave(file, previewUrl)
    }, 'image/jpeg', 0.95)
  }

  return (
    <div className="image-editor-modal">
      <div className="editor-content">
        <div className="editor-header">
          <h3>Chỉnh sửa ảnh</h3>
          <button onClick={onCancel} className="btn-icon">
            <X size={24} />
          </button>
        </div>
        
        <div className="editor-body">
          <ReactCrop crop={crop} onChange={(c) => setCrop(c)}>
            <img
              ref={imageRef}
              src={imageSrc}
              style={{ transform: `rotate(${rotation}deg)` }}
              alt="Source"
              crossOrigin="anonymous"
            />
          </ReactCrop>
        </div>

        <div className="editor-footer">
          <div className="editor-tools">
            <button className="btn btn-secondary btn-icon-text" onClick={handleRotate}>
              <RotateCw size={18} />
              Xoay 90°
            </button>
          </div>
          <div className="editor-actions">
            <button className="btn btn-secondary" onClick={onCancel}>
              Hủy
            </button>
            <button className="btn btn-primary btn-icon-text" onClick={handleSave}>
              <Check size={18} />
              Áp dụng
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ImageEditor
