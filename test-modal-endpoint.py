"""
Test Script for Modal OCR Endpoint

Usage:
    python test-modal-endpoint.py path/to/image.jpg
    python test-modal-endpoint.py path/to/image.jpg https://custom-modal-url.modal.run
"""

import sys
import base64
import requests
import time
from pathlib import Path

def test_modal_endpoint(image_path: str, modal_url: str = None):
    """Test the Modal OCR endpoint with an image"""
    
    # Default Modal URL (update this with your actual endpoint)
    if not modal_url:
        modal_url = "https://your-username--glm-ocr-api-ocr-endpoint.modal.run"
    
    print(f"🔍 Testing Modal OCR Endpoint")
    print(f"📍 URL: {modal_url}")
    print(f"🖼️  Image: {image_path}")
    print("-" * 60)
    
    # Check if image exists
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"❌ Error: Image file not found: {image_path}")
        return
    
    # Read and encode image
    print("📤 Reading and encoding image...")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    print(f"✅ Image encoded: {len(image_b64)} characters")
    
    # Prepare request
    payload = {
        "image_b64": image_b64
    }
    
    # Send request
    print("🚀 Sending request to Modal...")
    print("⏳ This may take 20-30s on first request (cold start)...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            modal_url,
            json=payload,
            timeout=90  # Allow time for cold start
        )
        
        elapsed_time = time.time() - start_time
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            extracted_text = result.get("text", "")
            
            print("-" * 60)
            print(f"✅ SUCCESS!")
            print(f"⏱️  Processing time: {elapsed_time:.2f}s")
            print(f"📝 Extracted text ({len(extracted_text)} characters):")
            print("-" * 60)
            print(extracted_text)
            print("-" * 60)
            
            # Save result to file
            output_file = image_file.stem + "_ocr_result.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            print(f"💾 Result saved to: {output_file}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout! The model may still be starting up.")
        print("💡 Try again in a few seconds.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        print("💡 Check your internet connection and Modal URL.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test-modal-endpoint.py <image_path> [modal_url]")
        print("\nExample:")
        print("  python test-modal-endpoint.py image.jpg")
        print("  python test-modal-endpoint.py image.jpg https://custom-url.modal.run")
        sys.exit(1)
    
    image_path = sys.argv[1]
    modal_url = sys.argv[2] if len(sys.argv) > 2 else None
    
    test_modal_endpoint(image_path, modal_url)
