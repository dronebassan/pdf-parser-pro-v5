import os
import cv2
import numpy as np
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

class OCRService:
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize OCR service
        
        Args:
            tesseract_path: Path to tesseract executable (optional)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Try to detect tesseract installation
        try:
            pytesseract.get_tesseract_version()
            self.available = True
        except:
            print("Warning: Tesseract not found. OCR functionality will be limited.")
            self.available = False
    
    def is_scanned_pdf(self, pdf_path: str, sample_pages: int = 3) -> bool:
        """
        Determine if PDF is likely scanned (image-based) by checking text extraction
        
        Args:
            pdf_path: Path to PDF file
            sample_pages: Number of pages to sample for detection
            
        Returns:
            True if likely scanned, False if text-based
        """
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                pages_to_check = min(len(pdf.pages), sample_pages)
                total_text_length = 0
                
                for i in range(pages_to_check):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        total_text_length += len(page_text.strip())
                
                # If very little text extracted, likely scanned
                avg_text_per_page = total_text_length / pages_to_check
                return avg_text_per_page < 100  # Threshold for scanned detection
                
        except Exception as e:
            print(f"Error checking if PDF is scanned: {e}")
            return False
    
    def extract_text_from_pdf(self, pdf_path: str, language: str = 'eng') -> List[OCRResult]:
        """
        Extract text from PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            language: Tesseract language code (default: 'eng')
            
        Returns:
            List of OCRResult objects, one per page
        """
        if not self.available:
            return []
        
        results = []
        
        try:
            # Convert PDF pages to images
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page as high-resolution image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)
                
                # Perform OCR
                ocr_result = self._extract_text_from_image(
                    processed_image, page_num + 1, language
                )
                results.append(ocr_result)
                
                pix = None
            
            pdf_document.close()
            return results
            
        except Exception as e:
            print(f"Error during OCR extraction: {e}")
            return []
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Optional: Apply morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(cleaned)
            
            return processed_image
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return image  # Return original if preprocessing fails
    
    def _extract_text_from_image(
        self, 
        image: Image.Image, 
        page_number: int, 
        language: str = 'eng'
    ) -> OCRResult:
        """
        Extract text from a single image using Tesseract
        
        Args:
            image: PIL Image object
            page_number: Page number for reference
            language: Tesseract language code
            
        Returns:
            OCRResult object
        """
        try:
            # Get detailed OCR data including confidence and bounding boxes
            ocr_data = pytesseract.image_to_data(
                image, 
                lang=language, 
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text_parts = []
            bounding_boxes = []
            confidences = []
            
            for i in range(len(ocr_data['text'])):
                word = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])
                
                if word and conf > 0:  # Only include words with confidence > 0
                    text_parts.append(word)
                    confidences.append(conf)
                    
                    # Store bounding box information
                    bounding_boxes.append({
                        'text': word,
                        'confidence': conf,
                        'x': ocr_data['left'][i],
                        'y': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i]
                    })
            
            # Combine text and calculate average confidence
            extracted_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return OCRResult(
                text=extracted_text,
                confidence=avg_confidence / 100.0,  # Convert to 0-1 scale
                page_number=page_number,
                bounding_boxes=bounding_boxes
            )
            
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                page_number=page_number,
                bounding_boxes=[]
            )
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract tables from scanned PDF using OCR and table detection
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of detected tables
        """
        if not self.available:
            return []
        
        tables = []
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Render page as image
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to OpenCV format
                image = Image.open(io.BytesIO(img_data))
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Detect tables using simple line detection
                page_tables = self._detect_tables_in_image(cv_image, page_num + 1)
                tables.extend(page_tables)
                
                pix = None
            
            pdf_document.close()
            return tables
            
        except Exception as e:
            print(f"Error extracting tables from scanned PDF: {e}")
            return []
    
    def _detect_tables_in_image(self, image: np.ndarray, page_number: int) -> List[Dict]:
        """
        Detect and extract tables from image using line detection
        
        Args:
            image: OpenCV image array
            page_number: Page number for reference
            
        Returns:
            List of detected tables
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            # Detect horizontal lines
            horizontal_lines = cv2.morphologyEx(
                gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2
            )
            
            # Detect vertical lines
            vertical_lines = cv2.morphologyEx(
                gray, cv2.MORPH_OPEN, vertical_kernel, iterations=2
            )
            
            # Combine lines to form table structure
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours (potential tables)
            contours, _ = cv2.findContours(
                table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            tables = []
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area > 1000:  # Filter small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Extract table region
                    table_region = gray[y:y+h, x:x+w]
                    
                    # Perform OCR on table region
                    table_text = pytesseract.image_to_string(table_region)
                    
                    if table_text.strip():
                        tables.append({
                            'page': page_number,
                            'table_number': i + 1,
                            'text': table_text,
                            'bounding_box': {'x': x, 'y': y, 'width': w, 'height': h},
                            'extraction_method': 'ocr'
                        })
            
            return tables
            
        except Exception as e:
            print(f"Error detecting tables in image: {e}")
            return []
    
    def enhance_library_extraction(
        self, 
        pdf_path: str, 
        library_text: str, 
        confidence_threshold: float = 0.3
    ) -> Tuple[str, float]:
        """
        Enhance library text extraction with OCR for missing content
        
        Args:
            pdf_path: Path to PDF file
            library_text: Text extracted by library method
            confidence_threshold: Min confidence for OCR enhancement
            
        Returns:
            Tuple of (enhanced_text, confidence_score)
        """
        if not self.available:
            return library_text, 1.0
        
        # Check if library extraction seems incomplete
        if len(library_text.strip()) > 500:  # Library extraction seems good
            return library_text, 1.0
        
        try:
            # Perform OCR extraction
            ocr_results = self.extract_text_from_pdf(pdf_path)
            
            # Combine OCR text from all pages
            ocr_text_parts = []
            total_confidence = 0
            valid_pages = 0
            
            for result in ocr_results:
                if result.confidence > confidence_threshold:
                    ocr_text_parts.append(result.text)
                    total_confidence += result.confidence
                    valid_pages += 1
            
            if not ocr_text_parts:
                return library_text, 0.5
            
            ocr_text = '\n\n'.join(ocr_text_parts)
            avg_confidence = total_confidence / valid_pages if valid_pages > 0 else 0
            
            # Choose better extraction
            if len(ocr_text.strip()) > len(library_text.strip()) * 1.5:
                return ocr_text, avg_confidence
            else:
                # Combine both if OCR adds significant content
                combined_text = library_text + '\n\n--- OCR ENHANCEMENT ---\n\n' + ocr_text
                return combined_text, (1.0 + avg_confidence) / 2
                
        except Exception as e:
            print(f"Error enhancing library extraction with OCR: {e}")
            return library_text, 0.8

def create_ocr_service(tesseract_path: Optional[str] = None) -> OCRService:
    """
    Factory function to create OCR service
    
    Args:
        tesseract_path: Optional path to tesseract executable
        
    Returns:
        OCRService instance
    """
    return OCRService(tesseract_path)