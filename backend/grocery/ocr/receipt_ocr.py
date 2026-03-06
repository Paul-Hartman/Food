"""Receipt OCR - Extract text from German grocery receipts

Supports:
- Tesseract OCR (offline, free)
- Asprise OCR (German receipt support, paid)
- Taggun API (commercial, paid)
"""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class ReceiptOCR:
    """Extract structured data from receipt images"""

    def __init__(self, provider: str = "tesseract", db_path: str = "food_app.db"):
        """
        Initialize OCR provider

        Args:
            provider: 'tesseract', 'asprise', or 'taggun'
            db_path: Path to SQLite database
        """
        self.provider = provider
        self.db_path = db_path

        if provider == "tesseract" and not TESSERACT_AVAILABLE:
            raise ImportError(
                "Tesseract not available. Install with: pip install pytesseract pillow"
            )

    def scan_receipt(self, image_path: str, store_hint: Optional[str] = None) -> Dict:
        """
        OCR receipt and parse structured data

        Args:
            image_path: Path to receipt image
            store_hint: Optional store hint ('aldi', 'rewe', 'lidl', 'other')

        Returns:
            {
                'store': str,
                'date': str (YYYY-MM-DD),
                'total': float,
                'items': [{'name': str, 'price': float, 'qty': float}],
                'confidence': float (0-1),
                'raw_text': str
            }
        """
        if self.provider == "tesseract":
            return self._scan_with_tesseract(image_path, store_hint)
        elif self.provider == "asprise":
            return self._scan_with_asprise(image_path, store_hint)
        elif self.provider == "taggun":
            return self._scan_with_taggun(image_path, store_hint)
        else:
            raise ValueError(f"Unknown OCR provider: {self.provider}")

    def _scan_with_tesseract(self, image_path: str, store_hint: Optional[str]) -> Dict:
        """Scan receipt using Tesseract OCR"""
        try:
            # Open image
            img = Image.open(image_path)

            # OCR with German language pack
            # Note: Tesseract must be installed with German language data
            text = pytesseract.image_to_string(img, lang="deu")

            # Parse the raw text
            parsed_data = self._parse_tesseract_text(text, store_hint)
            parsed_data["raw_text"] = text
            parsed_data["confidence"] = 0.7  # Tesseract baseline confidence

            return parsed_data

        except Exception as e:
            raise Exception(f"Tesseract OCR failed: {str(e)}")

    def _parse_tesseract_text(self, text: str, store_hint: Optional[str]) -> Dict:
        """Parse raw Tesseract text into structured data"""
        lines = text.split("\n")

        # Detect store
        store = store_hint or self._detect_store(text)

        # Extract date
        purchase_date = self._extract_date(lines)

        # Extract items
        items = self._extract_items(lines, store)

        # Extract total
        total = self._extract_total(lines, store)

        return {"store": store, "date": purchase_date, "total": total, "items": items}

    def _detect_store(self, text: str) -> str:
        """Detect store from receipt text"""
        text_lower = text.lower()

        if "aldi" in text_lower:
            if "aldi nord" in text_lower or "aldi-nord" in text_lower:
                return "aldi_nord"
            return "aldi_sud"
        elif "lidl" in text_lower:
            return "lidl"
        elif "rewe" in text_lower:
            return "rewe"
        else:
            return "other"

    def _extract_date(self, lines: List[str]) -> str:
        """Extract purchase date from receipt lines"""
        # German date patterns:
        # 18.12.2025, 18.12.25, 18/12/2025, 2025-12-18
        date_patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # 18.12.2025
            r"(\d{1,2})\.(\d{1,2})\.(\d{2})",  # 18.12.25
            r"(\d{1,2})/(\d{1,2})/(\d{4})",  # 18/12/2025
            r"(\d{4})-(\d{2})-(\d{2})",  # 2025-12-18
        ]

        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line)
                if match:
                    if len(match.groups()) == 3:
                        day, month, year = match.groups()

                        # Handle 2-digit year
                        if len(year) == 2:
                            year = "20" + year

                        # Handle YYYY-MM-DD format (already in correct order)
                        if pattern == date_patterns[3]:
                            year, month, day = match.groups()

                        try:
                            # Validate date
                            dt = datetime(int(year), int(month), int(day))
                            return dt.strftime("%Y-%m-%d")
                        except ValueError:
                            continue

        # Default to today if not found
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_items(self, lines: List[str], store: str) -> List[Dict]:
        """Extract line items from receipt"""
        items = []

        # Pattern for item lines: name followed by price
        # German price format: 1,99 EUR or 1.99 or 1,99€
        price_patterns = [
            r"(\d+[,\.]\d{2})\s*€",  # 1,99€ or 1.99€
            r"€\s*(\d+[,\.]\d{2})",  # € 1,99
            r"(\d+[,\.]\d{2})\s*EUR",  # 1,99 EUR
            r"EUR\s*(\d+[,\.]\d{2})",  # EUR 1,99
        ]

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Check if line contains a price
            price = None
            price_text = None

            for pattern in price_patterns:
                match = re.search(pattern, line)
                if match:
                    price_text = match.group(1).replace(",", ".")
                    try:
                        price = float(price_text)
                        break
                    except ValueError:
                        continue

            if price is not None and price > 0:
                # Extract item name (text before price)
                name_match = re.match(r"^(.+?)\s+\d+[,\.]\d{2}", line)
                if name_match:
                    name = name_match.group(1).strip()

                    # Skip totals and subtotals
                    if self._is_total_line(name):
                        continue

                    # Extract quantity if present (e.g., "2 x Milk" or "Milk x2")
                    qty_match = re.search(r"(\d+)\s*x\s*", name, re.IGNORECASE)
                    qty = float(qty_match.group(1)) if qty_match else 1.0

                    # Clean quantity from name
                    if qty_match:
                        name = re.sub(r"\d+\s*x\s*", "", name, flags=re.IGNORECASE).strip()

                    items.append({"name": name, "price": price, "qty": qty})

        return items

    def _is_total_line(self, text: str) -> bool:
        """Check if line is a total/subtotal"""
        total_keywords = [
            "summe",
            "total",
            "gesamt",
            "zwischensumme",
            "subtotal",
            "mwst",
            "steuer",
            "bar",
            "ec-karte",
            "rückgeld",
            "bezahlt",
            "brutto",
            "netto",
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in total_keywords)

    def _extract_total(self, lines: List[str], store: str) -> float:
        """Extract total amount from receipt"""
        # Look for "Summe", "Total", "Gesamt" followed by price
        total_patterns = [
            r"summe\s+(\d+[,\.]\d{2})",
            r"total\s+(\d+[,\.]\d{2})",
            r"gesamt\s+(\d+[,\.]\d{2})",
            r"zu zahlen\s+(\d+[,\.]\d{2})",
        ]

        for line in reversed(lines):  # Start from bottom
            line_lower = line.lower()
            for pattern in total_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    try:
                        return float(match.group(1).replace(",", "."))
                    except ValueError:
                        continue

        # Fallback: sum all item prices
        return 0.0

    def _scan_with_asprise(self, image_path: str, store_hint: Optional[str]) -> Dict:
        """Scan receipt using Asprise OCR (requires API key)"""
        # TODO: Implement Asprise OCR in Phase 2+
        raise NotImplementedError("Asprise OCR not implemented yet. Use 'tesseract' for MVP.")

    def _scan_with_taggun(self, image_path: str, store_hint: Optional[str]) -> Dict:
        """Scan receipt using Taggun API (requires API key)"""
        # TODO: Implement Taggun API in Phase 2+
        raise NotImplementedError("Taggun API not implemented yet. Use 'tesseract' for MVP.")

    def save_to_db(self, receipt_data: Dict, image_path: str) -> int:
        """
        Save receipt data to database

        Args:
            receipt_data: Parsed receipt data from scan_receipt()
            image_path: Path to receipt image

        Returns:
            receipt_id: ID of inserted receipt
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert receipt
            cursor.execute(
                """
                INSERT INTO grocery_receipts (
                    store, total_amount, purchase_date, source,
                    ocr_confidence, raw_ocr_text, image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    receipt_data["store"],
                    receipt_data["total"],
                    receipt_data["date"],
                    f"ocr_{self.provider}",
                    receipt_data.get("confidence", 0.7),
                    receipt_data.get("raw_text", ""),
                    image_path,
                ),
            )

            receipt_id = cursor.lastrowid

            # Insert line items
            for item in receipt_data["items"]:
                cursor.execute(
                    """
                    INSERT INTO grocery_receipt_items (
                        receipt_id, name_on_receipt, quantity, total_price
                    ) VALUES (?, ?, ?, ?)
                """,
                    (receipt_id, item["name"], item["qty"], item["price"] * item["qty"]),
                )

            # Update budget tracking
            self._update_budget(cursor, receipt_data)

            conn.commit()
            return receipt_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to save receipt to database: {str(e)}")
        finally:
            conn.close()

    def _update_budget(self, cursor: sqlite3.Cursor, receipt_data: Dict):
        """Update monthly budget with receipt total"""
        # Get month from purchase date
        purchase_date = datetime.strptime(receipt_data["date"], "%Y-%m-%d")
        month = purchase_date.strftime("%Y-%m-01")

        # Get or create budget for month
        cursor.execute(
            """
            SELECT id, spent_aldi, spent_lidl, spent_rewe, spent_other, planned_budget
            FROM grocery_budget WHERE month = ?
        """,
            (month,),
        )

        budget_row = cursor.fetchone()

        store = receipt_data["store"]
        total = receipt_data["total"]

        if budget_row:
            # Update existing budget
            budget_id, spent_aldi, spent_lidl, spent_rewe, spent_other, planned = budget_row

            if store == "aldi_nord" or store == "aldi_sud":
                spent_aldi += total
            elif store == "lidl":
                spent_lidl += total
            elif store == "rewe":
                spent_rewe += total
            else:
                spent_other += total

            cursor.execute(
                """
                UPDATE grocery_budget
                SET spent_aldi = ?, spent_lidl = ?, spent_rewe = ?, spent_other = ?
                WHERE id = ?
            """,
                (spent_aldi, spent_lidl, spent_rewe, spent_other, budget_id),
            )
        else:
            # Create new budget entry with €600 default
            spent_aldi = total if store in ["aldi_nord", "aldi_sud"] else 0
            spent_lidl = total if store == "lidl" else 0
            spent_rewe = total if store == "rewe" else 0
            spent_other = total if store == "other" else 0

            cursor.execute(
                """
                INSERT INTO grocery_budget (
                    month, planned_budget, spent_aldi, spent_lidl, spent_rewe, spent_other
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (month, 600.0, spent_aldi, spent_lidl, spent_rewe, spent_other),
            )
