# OCR Service - Frontend

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **Axios** - HTTP client
- **react-dropzone** - File upload
- **lucide-react** - Icon library

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── Header.jsx
│   │   ├── ImageUploader.jsx
│   │   ├── ResultDisplay.jsx
│   │   ├── LoadingSpinner.jsx
│   │   └── ErrorMessage.jsx
│   ├── services/        # API services
│   │   └── api.js
│   ├── App.jsx          # Main app component
│   ├── App.css
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## Setup

### 1. Install dependencies

```bash
npm install
```

or using yarn:

```bash
yarn install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your backend API URL
```

### 3. Run development server

```bash
npm run dev
```

The app will be available at http://localhost:3000

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Usage

1. **Upload Image**: Drag & drop an image or click to select from your computer
2. **Extract Text**: Click "Trích xuất văn bản" button
3. **View Results**: See extracted text with processing time and metadata
4. **Copy/Download**: Use the copy or download buttons to save results

## Supported Image Formats

- PNG
- JPG/JPEG
- GIF
- BMP
- WebP

Maximum file size: 10MB


