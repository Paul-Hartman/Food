# OCR Setup Guide - Tesseract Installation

The receipt OCR feature requires Tesseract OCR engine to be installed on your system.

## Windows Installation

### Option 1: Download Installer (Recommended)

1. Download the latest Tesseract installer from:
   https://github.com/UB-Mannheim/tesseract/wiki

1. Run the installer (tesseract-ocr-w64-setup-5.x.x.exe)

1. During installation:

   - Accept the license
   - Keep the default installation path: `C:\Program Files\Tesseract-OCR`
   - Make sure to select "Add to PATH" option

1. Verify installation:

   ```cmd
   tesseract --version
   ```

### Option 2: Using Chocolatey

If you have Chocolatey package manager:

```cmd
choco install tesseract
```

### Option 3: Using Scoop

If you have Scoop package manager:

```cmd
scoop install tesseract
```

## Linux Installation

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### Fedora

```bash
sudo dnf install tesseract
```

### Arch Linux

```bash
sudo pacman -S tesseract
```

## macOS Installation

### Using Homebrew

```bash
brew install tesseract
```

## Verify Installation

After installation, verify Tesseract is working:

```bash
tesseract --version
```

You should see output like:

```
tesseract 5.3.0
 leptonica-1.82.0
  libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.1.3) : libpng 1.6.37 : libtiff 4.4.0 : zlib 1.2.12 : libwebp 1.2.4 : libopenjp2 2.5.0
```

## Testing OCR

Once Tesseract is installed, you can test the OCR functionality:

```python
python manage.py shell
```

```python
from recipes.receipt_ocr import extract_text_from_image

# Test with a sample image
text = extract_text_from_image("path/to/receipt.jpg")
print(text)
```

## Troubleshooting

### Windows: "tesseract is not recognized"

If you get this error, manually add Tesseract to your PATH:

1. Open System Properties → Advanced → Environment Variables
1. Under System Variables, find "Path"
1. Click Edit
1. Add: `C:\Program Files\Tesseract-OCR`
1. Click OK and restart your terminal

### Linux/Mac: "tesseract: command not found"

Make sure Tesseract is in your PATH:

```bash
which tesseract
```

If not found, you may need to add it to your PATH or reinstall.

### Poor OCR Accuracy

For better OCR results:

- Use high-resolution images (300 DPI or higher)
- Ensure good lighting
- Keep the receipt flat and straight
- Clean the receipt image (no wrinkles or shadows)

## Language Support

By default, Tesseract includes English language data. For other languages:

### Windows

Download language data from:
https://github.com/tesseract-ocr/tessdata

Copy .traineddata files to: `C:\Program Files\Tesseract-OCR\tessdata\`

### Linux/Mac

```bash
# For French
sudo apt-get install tesseract-ocr-fra

# For Spanish
sudo apt-get install tesseract-ocr-spa

# For German
sudo apt-get install tesseract-ocr-deu
```

## API Usage

Once Tesseract is installed, you can use the OCR endpoints:

### Extract Data from Receipt (Preview)

```bash
curl -X POST http://localhost:8000/api/receipts/extract-ocr/ \
  -F "receipt_image=@receipt.jpg"
```

### Upload Receipt with Auto-Extraction

```bash
curl -X POST http://localhost:8000/api/receipts/upload-with-ocr/ \
  -F "receipt_image=@receipt.jpg" \
  -F "expense_category_id=1"
```

## What the OCR Extracts

The OCR system automatically extracts:

- **Store name** (from top of receipt)
- **Purchase date** (various date formats)
- **Purchase time** (if present)
- **Total amount**
- **Subtotal** (if shown)
- **Tax amount** (if shown)
- **Line items** with names, quantities, and prices

All extracted data is returned in structured JSON format for easy processing.
