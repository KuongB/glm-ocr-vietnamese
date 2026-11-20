"""Quick smoke test for the deployed Modal OCR endpoint.

Usage:
    python test-api-glm.py <image-path> [endpoint-url]

The endpoint URL may also be supplied through the MODAL_API_URL
environment variable. It defaults to the development endpoint.
"""

import base64
import os
import sys

import requests

DEFAULT_URL = "https://kuongb--glm-ocr-api-ocr-endpoint-dev.modal.run"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2

    image_path = sys.argv[1]
    url = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.environ.get("MODAL_API_URL", DEFAULT_URL)
    )

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    response = requests.post(url, json={"image_b64": image_b64}, timeout=120)

    print(f"Status: {response.status_code}")
    try:
        print(response.json())
    except ValueError:
        print(response.text)

    return 0 if response.ok else 1


if __name__ == "__main__":
    sys.exit(main())
