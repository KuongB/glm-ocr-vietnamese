import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds
})

/**
 * Convert file to base64
 */
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => {
      // Remove the data URL prefix (e.g., "data:image/png;base64,")
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = (error) => reject(error)
  })
}

/**
 * Extract text from image file
 * @param {File} imageFile - The image file to extract text from
 * @param {string} language - Target language (default: 'vi')
 * @returns {Promise<object>} - OCR result
 */
export const extractText = async (imageFile, language = 'vi') => {
  try {
    const imageB64 = await fileToBase64(imageFile)
    
    const response = await api.post('/ocr/extract', {
      image_b64: imageB64,
      language: language,
    })
    
    return response.data
  } catch (error) {
    if (error.response) {
      // Server responded with error
      throw new Error(error.response.data.detail || 'Server error occurred')
    } else if (error.request) {
      // Request made but no response
      throw new Error('Không thể kết nối đến server. Vui lòng kiểm tra lại.')
    } else {
      // Something else happened
      throw new Error(error.message || 'Có lỗi xảy ra')
    }
  }
}

/**
 * Upload image file directly (using multipart/form-data)
 * @param {File} imageFile - The image file to upload
 * @returns {Promise<object>} - OCR result
 */
export const uploadAndExtract = async (imageFile) => {
  try {
    const formData = new FormData()
    formData.append('file', imageFile)
    
    const response = await axios.post(`${API_BASE_URL}/ocr/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    })
    
    return response.data
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.detail || 'Server error occurred')
    } else if (error.request) {
      throw new Error('Không thể kết nối đến server. Vui lòng kiểm tra lại.')
    } else {
      throw new Error(error.message || 'Có lỗi xảy ra')
    }
  }
}

/**
 * Get supported languages
 * @returns {Promise<array>} - List of supported languages
 */
export const getSupportedLanguages = async () => {
  try {
    const response = await api.get('/ocr/supported-languages')
    return response.data.languages
  } catch (error) {
    console.error('Failed to fetch languages:', error)
    return []
  }
}

/**
 * Health check
 * @returns {Promise<object>} - Health status
 */
export const healthCheck = async () => {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    throw new Error('Health check failed')
  }
}

export default api
