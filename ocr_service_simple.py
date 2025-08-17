import os
import pytesseract
import fitz
from PIL import Image
import io
import base64
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import tempfile

@dataclass
class OCRResult:
    text: str
    confidence: float
    page_number: int
    bounding_boxes: List[Dict]

class SimpleOCRService:
    """Simplified OCR service for Railway deployment without heavy OpenCV dependencies"""
    
    def __init__(self):
        self.available = self._check_tesseract_availability()
    
    def _check_tesseract_availability(self) -> bool:
        """Check if Tesseract is available"""
        try:
            pytesseract.pytesseract.tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
            return True
        except Exception:
            return False
    
    def extract_text_from_pdf(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> List[OCRResult]:
        """Extract text from PDF using OCR"""
        if not self.available:
            raise RuntimeError("OCR service not available - Tesseract not found")
        
        results = []
        
        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)
            
            # Process specified pages or all pages
            pages_to_process = page_numbers if page_numbers else range(len(doc))
            
            for page_num in pages_to_process:
                if page_num >= len(doc):
                    continue
                    
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Perform OCR
                ocr_text = pytesseract.image_to_string(image, config='--psm 6')
                
                # Get confidence (simplified)
                try:
                    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                except:
                    avg_confidence = 80  # Default confidence
                
                # Create result
                result = OCRResult(
                    text=ocr_text.strip(),
                    confidence=avg_confidence / 100.0,
                    page_number=page_num,
                    bounding_boxes=[]  # Simplified - no bounding boxes
                )
                
                results.append(result)
            
            doc.close()
            return results
            
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {str(e)}")
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """Detect if PDF is scanned (image-based)"""
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            image_pages = 0
            
            # Check first 3 pages for speed
            pages_to_check = min(3, total_pages)
            
            for page_num in range(pages_to_check):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # If page has very little text, likely scanned
                if len(text.strip()) < 50:
                    image_pages += 1
            
            doc.close()
            
            # If majority of checked pages have little text, consider it scanned
            return image_pages > (pages_to_check / 2)
            
        except Exception:
            return False
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image bytes"""
        if not self.available:
            return ""
        
        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, config='--psm 6')
            return text.strip()
        except Exception:
            return ""

def create_simple_ocr_service() -> SimpleOCRService:
    """Factory function to create OCR service"""
    return SimpleOCRService()