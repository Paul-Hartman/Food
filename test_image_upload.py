"""
Test script for product image upload with background removal.
"""

import io

import requests
from PIL import Image, ImageDraw


# Create a simple test image (red circle on white background)
def create_test_image():
    img = Image.new("RGB", (200, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill="red", outline="darkred", width=3)

    # Save to BytesIO
    img_io = io.BytesIO()
    img.save(img_io, format="PNG")
    img_io.seek(0)
    return img_io


def test_upload_product_image():
    """Test uploading an image to an existing product."""
    print("Testing product image upload...")

    # Create test image
    test_img = create_test_image()

    # First, let's try with the Nutella product (barcode: 3017620422003)
    url = "http://127.0.0.1:8000/api/products/upload-image/"

    files = {"image": ("test.png", test_img, "image/png")}
    data = {"barcode": "3017620422003", "remove_background": "true", "optimize": "true"}

    response = requests.post(url, files=files, data=data)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_add_product_with_image():
    """Test creating a new product with an image."""
    print("\nTesting add product with image...")

    # Create test image
    test_img = create_test_image()

    url = "http://127.0.0.1:8000/api/products/add-with-image/"

    files = {"image": ("test_product.png", test_img, "image/png")}
    data = {
        "barcode": "TEST123456",
        "name": "Test Product",
        "brand": "Test Brand",
        "description": "A test product for image upload",
        "remove_background": "true",
    }

    response = requests.post(url, files=files, data=data)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    try:
        test_upload_product_image()
        test_add_product_with_image()
        print("\n✓ Tests completed!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
