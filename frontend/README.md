# OCR Service - Frontend

Modern React frontend for OCR text extraction service with beautiful UI/UX.

## Features

- 🎨 Modern and intuitive user interface
- 📤 Drag & drop image upload
- 🖼️ Image preview before processing
- 📋 One-click copy to clipboard
- 💾 Download results as text file
- ⚡ Real-time processing status
- 📱 Fully responsive design
- 🎯 Vietnamese language optimized

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

## Configuration

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000/api
```

### API Endpoints

The frontend expects the following backend endpoints:

- `POST /api/ocr/extract` - Extract text from base64 image
- `POST /api/ocr/upload` - Upload and extract text
- `GET /api/ocr/supported-languages` - Get supported languages
- `GET /api/health` - Health check

## Building for Production

### Build

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview

```bash
npm run preview
```

### Deploy

The `dist/` folder can be deployed to any static hosting service:

- Vercel
- Netlify
- GitHub Pages
- AWS S3 + CloudFront
- Firebase Hosting

Example deployment to Netlify:

```bash
npm run build
netlify deploy --prod --dir=dist
```

## Docker Deployment

### Create Dockerfile

```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Build and run

```bash
docker build -t ocr-frontend .
docker run -p 80:80 ocr-frontend
```

## Customization

### Styling

Global styles are in `src/index.css`. Component-specific styles are in their respective CSS files.

CSS variables for easy theming:

```css
:root {
  --primary-color: #3b82f6;
  --success-color: #10b981;
  --error-color: #ef4444;
  /* ... more variables */
}
```

### API Integration

Modify `src/services/api.js` to customize API calls:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development

### Code Style

The project uses ESLint for code quality. Run:

```bash
npm run lint
```

### Component Guidelines

- Keep components small and focused
- Use functional components with hooks
- Follow React best practices
- Add PropTypes or TypeScript for type checking

## Troubleshooting

### CORS Issues

If you encounter CORS errors, ensure your backend allows requests from `http://localhost:3000`:

```python
# backend/app/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    # ... add your frontend URLs
]
```

### API Connection Failed

1. Check if backend is running on http://localhost:8000
2. Verify `VITE_API_URL` in `.env`
3. Check browser console for detailed errors

### Build Errors

1. Delete `node_modules` and `package-lock.json`
2. Run `npm install` again
3. Clear cache: `npm cache clean --force`

## Performance Optimization

- Images are lazy loaded
- Code splitting with dynamic imports
- Optimized bundle size with Vite
- Gzip compression in production

## License

MIT

## Support

For issues and questions, please check the documentation or create an issue in the repository.
