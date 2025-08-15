import os
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pdfplumber
import fitz
import pandas as pd
from tempfile import NamedTemporaryFile
import base64

from llm_service import LLMService, create_llm_service, ParseResult
from performance_tracker import PerformanceTracker, PerformanceMetrics

class ParseStrategy(Enum):
    LIBRARY_ONLY = "library_only"
    LLM_ONLY = "llm_only"
    LIBRARY_FIRST = "library_first"
    LLM_FIRST = "llm_first"
    HYBRID = "hybrid"
    AUTO = "auto"
    PAGE_BY_PAGE = "page_by_page"  # New strategy for individual page processing

@dataclass
class ConfidenceScoring:
    text_confidence: float
    table_confidence: float
    image_confidence: float
    overall_confidence: float
    reasons: List[str]

@dataclass
class SmartParseResult:
    text: str
    tables: List[Dict]
    images: List[Dict]
    method_used: str
    provider_used: Optional[str]
    confidence: ConfidenceScoring
    processing_time: float
    fallback_triggered: bool
    performance_comparison: Optional[Dict]

class SmartParser:
    def __init__(
        self,
        default_strategy: ParseStrategy = ParseStrategy.AUTO,
        confidence_threshold: float = 0.7,
        enable_performance_tracking: bool = True
    ):
        self.default_strategy = default_strategy
        self.confidence_threshold = confidence_threshold
        self.performance_tracker = PerformanceTracker() if enable_performance_tracking else None
        
        # Initialize LLM services
        self.llm_services = {}
        for provider in ["openai", "anthropic", "gemini"]:
            service = create_llm_service(provider)
            if service:
                self.llm_services[provider] = service
    
    def parse_pdf(
        self,
        pdf_path: str,
        strategy: Optional[ParseStrategy] = None,
        preferred_llm_provider: str = "openai"
    ) -> SmartParseResult:
        """Parse PDF using smart strategy with fallback logic"""
        
        strategy = strategy or self.default_strategy
        start_time = time.time()
        
        # Get file metadata
        file_size = os.path.getsize(pdf_path)
        page_count = self._get_page_count(pdf_path)
        
        if strategy == ParseStrategy.LIBRARY_ONLY:
            return self._parse_with_library(pdf_path, file_size, page_count)
        
        elif strategy == ParseStrategy.LLM_ONLY:
            return self._parse_with_llm(pdf_path, file_size, page_count, preferred_llm_provider)
        
        elif strategy == ParseStrategy.LIBRARY_FIRST:
            return self._parse_library_first(pdf_path, file_size, page_count, preferred_llm_provider)
        
        elif strategy == ParseStrategy.LLM_FIRST:
            return self._parse_llm_first(pdf_path, file_size, page_count, preferred_llm_provider)
        
        elif strategy == ParseStrategy.HYBRID:
            return self._parse_hybrid(pdf_path, file_size, page_count, preferred_llm_provider)
        
        elif strategy == ParseStrategy.AUTO:
            return self._parse_auto(pdf_path, file_size, page_count, preferred_llm_provider)
        
        elif strategy == ParseStrategy.PAGE_BY_PAGE:
            return self._parse_page_by_page(pdf_path, file_size, page_count, preferred_llm_provider)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _parse_with_library(self, pdf_path: str, file_size: int, page_count: int) -> SmartParseResult:
        """Parse using only library methods"""
        start_time = time.time()
        
        try:
            text = self._extract_text_library(pdf_path)
            tables = self._extract_tables_library(pdf_path)
            images = self._extract_images_library(pdf_path)
            
            # Check if text extraction was poor and try OCR enhancement
            if len(text.strip()) < 200 and page_count > 0:
                try:
                    from ocr_service import create_ocr_service
                    ocr_service = create_ocr_service()
                    if ocr_service and ocr_service.available:
                        enhanced_text, ocr_confidence = ocr_service.enhance_library_extraction(
                            pdf_path, text, confidence_threshold=0.3
                        )
                        if len(enhanced_text.strip()) > len(text.strip()) * 1.2:
                            text = enhanced_text
                            print(f"Enhanced text extraction with OCR (confidence: {ocr_confidence:.2f})")
                except Exception as e:
                    print(f"OCR enhancement failed: {e}")
            
            confidence = self._calculate_library_confidence(text, tables, images)
            processing_time = time.time() - start_time
            
            # Record performance
            if self.performance_tracker:
                self.performance_tracker.record_performance(
                    method="library",
                    provider=None,
                    processing_time=processing_time,
                    text_length=len(text),
                    tables_count=len(tables),
                    images_count=len(images),
                    confidence_score=confidence.overall_confidence,
                    file_size=file_size,
                    page_count=page_count,
                    success=True
                )
            
            return SmartParseResult(
                text=text,
                tables=tables,
                images=images,
                method_used="library",
                provider_used=None,
                confidence=confidence,
                processing_time=processing_time,
                fallback_triggered=False,
                performance_comparison=None
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Record failed performance
            if self.performance_tracker:
                self.performance_tracker.record_performance(
                    method="library",
                    provider=None,
                    processing_time=processing_time,
                    text_length=0,
                    tables_count=0,
                    images_count=0,
                    confidence_score=0.0,
                    file_size=file_size,
                    page_count=page_count,
                    success=False,
                    error_message=str(e)
                )
            
            return SmartParseResult(
                text="",
                tables=[],
                images=[],
                method_used="library",
                provider_used=None,
                confidence=ConfidenceScoring(0, 0, 0, 0, [f"Error: {str(e)}"]),
                processing_time=processing_time,
                fallback_triggered=False,
                performance_comparison=None
            )
    
    def _parse_with_llm(
        self,
        pdf_path: str,
        file_size: int,
        page_count: int,
        provider: str = "openai"
    ) -> SmartParseResult:
        """Parse using only LLM methods"""
        start_time = time.time()
        
        if provider not in self.llm_services:
            # Fallback to any available provider
            if self.llm_services:
                provider = list(self.llm_services.keys())[0]
            else:
                return SmartParseResult(
                    text="",
                    tables=[],
                    images=[],
                    method_used="llm",
                    provider_used=provider,
                    confidence=ConfidenceScoring(0, 0, 0, 0, ["No LLM service available"]),
                    processing_time=time.time() - start_time,
                    fallback_triggered=False,
                    performance_comparison=None
                )
        
        try:
            llm_service = self.llm_services[provider]
            result = llm_service.parse_with_llm(pdf_path)
            
            confidence = self._calculate_llm_confidence(result)
            
            # Record performance
            if self.performance_tracker:
                self.performance_tracker.record_performance(
                    method="llm",
                    provider=provider,
                    processing_time=result.processing_time,
                    text_length=len(result.text),
                    tables_count=len(result.tables),
                    images_count=len(result.images),
                    confidence_score=result.confidence_score,
                    file_size=file_size,
                    page_count=page_count,
                    success=True
                )
            
            return SmartParseResult(
                text=result.text,
                tables=result.tables,
                images=result.images,
                method_used="llm",
                provider_used=provider,
                confidence=confidence,
                processing_time=result.processing_time,
                fallback_triggered=False,
                performance_comparison=None
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Record failed performance
            if self.performance_tracker:
                self.performance_tracker.record_performance(
                    method="llm",
                    provider=provider,
                    processing_time=processing_time,
                    text_length=0,
                    tables_count=0,
                    images_count=0,
                    confidence_score=0.0,
                    file_size=file_size,
                    page_count=page_count,
                    success=False,
                    error_message=str(e)
                )
            
            return SmartParseResult(
                text="",
                tables=[],
                images=[],
                method_used="llm",
                provider_used=provider,
                confidence=ConfidenceScoring(0, 0, 0, 0, [f"Error: {str(e)}"]),
                processing_time=processing_time,
                fallback_triggered=False,
                performance_comparison=None
            )
    
    def _parse_library_first(
        self,
        pdf_path: str,
        file_size: int,
        page_count: int,
        preferred_llm_provider: str
    ) -> SmartParseResult:
        """Try library first, fallback to LLM if needed"""
        
        # Try library first
        library_result = self._parse_with_library(pdf_path, file_size, page_count)
        
        # Check if fallback is needed
        if self._should_fallback_to_llm(library_result):
            llm_result = self._parse_with_llm(pdf_path, file_size, page_count, preferred_llm_provider)
            
            # Compare and choose better result
            if llm_result.confidence.overall_confidence > library_result.confidence.overall_confidence:
                llm_result.fallback_triggered = True
                llm_result.performance_comparison = self._create_comparison(library_result, llm_result)
                return llm_result
        
        return library_result
    
    def _parse_llm_first(
        self,
        pdf_path: str,
        file_size: int,
        page_count: int,
        preferred_llm_provider: str
    ) -> SmartParseResult:
        """Try LLM first, fallback to library if needed
        
        Note: This strategy is mainly useful when:
        - You have unlimited budget and want maximum accuracy
        - Speed is more important than cost
        - You're dealing with documents where library methods consistently fail
        - You need the highest possible quality regardless of cost
        
        For cost-conscious applications, LIBRARY_FIRST is usually better.
        """
        
        # Try LLM first
        llm_result = self._parse_with_llm(pdf_path, file_size, page_count, preferred_llm_provider)
        
        # Check if fallback is needed
        if self._should_fallback_to_library(llm_result):
            library_result = self._parse_with_library(pdf_path, file_size, page_count)
            
            # Compare and choose better result
            if library_result.confidence.overall_confidence > llm_result.confidence.overall_confidence:
                library_result.fallback_triggered = True
                library_result.performance_comparison = self._create_comparison(library_result, llm_result)
                return library_result
        
        return llm_result
    
    def _parse_hybrid(
        self,
        pdf_path: str,
        file_size: int,
        page_count: int,
        preferred_llm_provider: str
    ) -> SmartParseResult:
        """Use both methods and combine results"""
        
        library_result = self._parse_with_library(pdf_path, file_size, page_count)
        llm_result = self._parse_with_llm(pdf_path, file_size, page_count, preferred_llm_provider)
        
        # Combine results intelligently
        combined_text = self._combine_text(library_result.text, llm_result.text)
        combined_tables = self._combine_tables(library_result.tables, llm_result.tables)
        combined_images = self._combine_images(library_result.images, llm_result.images)
        
        # Calculate hybrid confidence
        hybrid_confidence = self._calculate_hybrid_confidence(library_result, llm_result)
        
        return SmartParseResult(
            text=combined_text,
            tables=combined_tables,
            images=combined_images,
            method_used="hybrid",
            provider_used=preferred_llm_provider,
            confidence=hybrid_confidence,
            processing_time=library_result.processing_time + llm_result.processing_time,
            fallback_triggered=False,
            performance_comparison=self._create_comparison(library_result, llm_result)
        )
    
    def _parse_auto(
        self,
        pdf_path: str,
        file_size: int,
        page_count: int,
        preferred_llm_provider: str
    ) -> SmartParseResult:
        """Auto-select best strategy based on document characteristics"""
        
        # Quick analysis to determine best strategy
        strategy = self._determine_best_strategy(pdf_path, file_size, page_count)
        
        if strategy == ParseStrategy.LIBRARY_FIRST:
            return self._parse_library_first(pdf_path, file_size, page_count, preferred_llm_provider)
        elif strategy == ParseStrategy.LLM_FIRST:
            return self._parse_llm_first(pdf_path, file_size, page_count, preferred_llm_provider)
        elif strategy == ParseStrategy.PAGE_BY_PAGE:
            return self._parse_page_by_page(pdf_path, file_size, page_count, preferred_llm_provider)
        else:
            return self._parse_hybrid(pdf_path, file_size, page_count, preferred_llm_provider)
    
    def _determine_best_strategy(self, pdf_path: str, file_size: int, page_count: int) -> ParseStrategy:
        """Determine the best parsing strategy based on document characteristics"""
        
        # For large documents, use page-by-page processing
        if page_count > 20:  # Large documents - analyze each page individually
            return ParseStrategy.PAGE_BY_PAGE
        
        # Simple heuristics for strategy selection
        if page_count > 50:  # Very large documents - prefer library for speed
            return ParseStrategy.LIBRARY_FIRST
        
        if file_size > 50 * 1024 * 1024:  # Files > 50MB - prefer library
            return ParseStrategy.LIBRARY_FIRST
        
        # Check if it might be scanned or have blurry text
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # Even if very little text extracted (likely scanned), try library first
                # Library methods can often handle scanned documents surprisingly well
                # Only fallback to LLM if library method fails or has low confidence
                return ParseStrategy.LIBRARY_FIRST
                
        except Exception as e:
            print(f"Error determining strategy: {e}")
            return ParseStrategy.LIBRARY_FIRST
    
    def _is_potentially_blurry(self, pdf_path: str) -> bool:
        """Check if PDF might have blurry or low-quality text"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first few pages
                pages_to_check = min(3, len(pdf.pages))
                total_text_length = 0
                total_words = 0
                
                for i in range(pages_to_check):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        total_text_length += len(page_text.strip())
                        total_words += len(page_text.split())
                
                # If average words per page is very low, might be blurry
                avg_words_per_page = total_words / pages_to_check if pages_to_check > 0 else 0
                avg_text_per_page = total_text_length / pages_to_check if pages_to_check > 0 else 0
                
                # Heuristics for blurry text detection
                if avg_words_per_page < 20 or avg_text_per_page < 200:
                    return True
                
                return False
                
        except:
            return False
    
    def _should_fallback_to_llm(self, library_result: SmartParseResult) -> bool:
        """Determine if fallback to LLM is needed"""
        if not self.llm_services:
            return False
        
        # Check for poor text extraction (potential blurry text)
        text_quality_issues = (
            library_result.confidence.overall_confidence < self.confidence_threshold or
            (len(library_result.text.strip()) < 100 and len(library_result.tables) == 0) or
            self._has_blurry_text_indicators(library_result.text)
        )
        
        return text_quality_issues
    
    def _has_blurry_text_indicators(self, text: str) -> bool:
        """Check if text has indicators of being blurry or low quality"""
        if not text.strip():
            return True
        
        # Check for common blurry text indicators
        text_lower = text.lower()
        
        # Check for excessive spaces or broken words
        words = text.split()
        if len(words) > 0:
            # Check for words with excessive spaces or broken characters
            broken_words = sum(1 for word in words if len(word) == 1 or '  ' in word)
            if broken_words > len(words) * 0.1:  # More than 10% broken words
                return True
            
            # Check for very short average word length (might indicate OCR issues)
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length < 3.0:  # Average word length less than 3 characters
                return True
        
        # Check for excessive special characters or numbers (OCR artifacts)
        special_char_ratio = sum(1 for char in text if not char.isalnum() and not char.isspace()) / len(text) if text else 0
        if special_char_ratio > 0.3:  # More than 30% special characters
            return True
        
        return False
    
    def _should_fallback_to_library(self, llm_result: SmartParseResult) -> bool:
        """Determine if fallback to library is needed"""
        return (
            llm_result.confidence.overall_confidence < self.confidence_threshold or
            len(llm_result.text.strip()) < 50
        )
    
    def _calculate_library_confidence(self, text: str, tables: List, images: List) -> ConfidenceScoring:
        """Calculate confidence score for library extraction"""
        reasons = []
        
        # Text confidence
        text_confidence = 0.8 if len(text.strip()) > 100 else 0.4
        if len(text.strip()) > 1000:
            text_confidence = 0.9
        reasons.append(f"Text extracted: {len(text)} characters")
        
        # Table confidence
        table_confidence = 0.9 if len(tables) > 0 else 0.6
        reasons.append(f"Tables found: {len(tables)}")
        
        # Image confidence
        image_confidence = 0.8 if len(images) > 0 else 0.7
        reasons.append(f"Images extracted: {len(images)}")
        
        # Overall confidence
        overall_confidence = (text_confidence + table_confidence + image_confidence) / 3
        
        return ConfidenceScoring(
            text_confidence=text_confidence,
            table_confidence=table_confidence,
            image_confidence=image_confidence,
            overall_confidence=overall_confidence,
            reasons=reasons
        )
    
    def _calculate_llm_confidence(self, result: ParseResult) -> ConfidenceScoring:
        """Calculate confidence score for LLM extraction"""
        reasons = [f"LLM confidence score: {result.confidence_score}"]
        
        # Use LLM's own confidence as base
        base_confidence = result.confidence_score
        
        return ConfidenceScoring(
            text_confidence=base_confidence,
            table_confidence=base_confidence,
            image_confidence=base_confidence,
            overall_confidence=base_confidence,
            reasons=reasons
        )
    
    def _calculate_hybrid_confidence(
        self,
        library_result: SmartParseResult,
        llm_result: SmartParseResult
    ) -> ConfidenceScoring:
        """Calculate confidence score for hybrid approach"""
        
        # Take the maximum confidence for each component
        text_confidence = max(library_result.confidence.text_confidence, llm_result.confidence.text_confidence)
        table_confidence = max(library_result.confidence.table_confidence, llm_result.confidence.table_confidence)
        image_confidence = max(library_result.confidence.image_confidence, llm_result.confidence.image_confidence)
        overall_confidence = (text_confidence + table_confidence + image_confidence) / 3
        
        reasons = ["Hybrid approach combining both methods"]
        
        return ConfidenceScoring(
            text_confidence=text_confidence,
            table_confidence=table_confidence,
            image_confidence=image_confidence,
            overall_confidence=overall_confidence,
            reasons=reasons
        )
    
    def _combine_text(self, library_text: str, llm_text: str) -> str:
        """Intelligently combine text from both methods"""
        if len(library_text) > len(llm_text):
            return library_text
        else:
            return llm_text
    
    def _combine_tables(self, library_tables: List, llm_tables: List) -> List:
        """Combine tables from both methods"""
        # Simple approach: use library tables if available, else LLM tables
        return library_tables if library_tables else llm_tables
    
    def _combine_images(self, library_images: List, llm_images: List) -> List:
        """Combine images from both methods"""
        # Library extraction typically better for images
        return library_images if library_images else llm_images
    
    def _create_comparison(
        self,
        library_result: SmartParseResult,
        llm_result: SmartParseResult
    ) -> Dict:
        """Create performance comparison between methods"""
        if not self.performance_tracker:
            return {}
        
        # Get the latest metrics for comparison
        library_metrics = None
        llm_metrics = None
        
        for metric in reversed(self.performance_tracker.metrics_history):
            if metric.method == "library" and library_metrics is None:
                library_metrics = metric
            elif metric.method == "llm" and llm_metrics is None:
                llm_metrics = metric
            
            if library_metrics and llm_metrics:
                break
        
        if library_metrics and llm_metrics:
            comparison = self.performance_tracker.compare_methods(library_metrics, llm_metrics)
            return {
                "winner": comparison.winner,
                "speed_improvement": comparison.speed_improvement,
                "accuracy_comparison": comparison.accuracy_comparison,
                "recommendation": comparison.recommendation
            }
        
        return {}
    
    def _get_page_count(self, pdf_path: str) -> int:
        """Get number of pages in PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except:
            return 0
    
    def _extract_text_library(self, pdf_path: str) -> str:
        """Extract text using library method"""
        with pdfplumber.open(pdf_path) as pdf:
            text_content = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
            return "\n\n".join(text_content)
    
    def _extract_tables_library(self, pdf_path: str) -> List[Dict]:
        """Extract tables using library method"""
        with pdfplumber.open(pdf_path) as pdf:
            tables = []
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table_num, table in enumerate(page_tables):
                    if table and len(table) > 1:
                        try:
                            headers = table[0]
                            data = table[1:]
                            df = pd.DataFrame(data, columns=headers)
                            tables.append({
                                "page": page_num + 1,
                                "table_number": table_num + 1,
                                "data": df.to_dict('records')
                            })
                        except Exception:
                            tables.append({
                                "page": page_num + 1,
                                "table_number": table_num + 1,
                                "raw_data": table
                            })
            return tables
    
    def _extract_images_library(self, pdf_path: str) -> List[Dict]:
        """Extract images using library method"""
        images = []
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(pdf_document, xref)
                
                if pix.n - pix.alpha < 4:
                    img_data = pix.tobytes("png")
                    encoded_img = base64.b64encode(img_data).decode('utf-8')
                    images.append({
                        "page": page_num + 1,
                        "image_number": img_index + 1,
                        "format": "png",
                        "image_base64": encoded_img
                    })
                pix = None
        
        pdf_document.close()
        return images

    def _parse_page_by_page(
        self,
        pdf_path: str,
        file_size: int,
        page_count: int,
        preferred_llm_provider: str = "openai"
    ) -> SmartParseResult:
        """Parse PDF page by page, using LLM only for blurry pages"""
        start_time = time.time()
        
        # Process each page individually
        page_results = []
        blurry_pages = []
        clear_pages = []
        
        print(f"🔍 Analyzing {page_count} pages individually...")
        
        # First pass: analyze each page with library method
        for page_num in range(page_count):
            page_result = self._process_single_page(pdf_path, page_num)
            page_results.append(page_result)
            
            # Check if page is blurry
            if self._is_page_blurry(page_result):
                blurry_pages.append(page_num)
                print(f"⚠️  Page {page_num + 1} detected as blurry (confidence: {page_result.confidence.overall_confidence:.2f})")
            else:
                clear_pages.append(page_num)
        
        print(f"✅ Clear pages: {len(clear_pages)}, Blurry pages: {len(blurry_pages)}")
        
        # Second pass: process blurry pages with LLM
        if blurry_pages and self.llm_services:
            print(f"🧠 Processing {len(blurry_pages)} blurry pages with LLM...")
            
            # Get preferred LLM service
            llm_service = self.llm_services.get(preferred_llm_provider)
            if not llm_service:
                # Fallback to any available LLM service
                llm_service = next(iter(self.llm_services.values()))
            
            for page_num in blurry_pages:
                print(f"   Processing page {page_num + 1} with {llm_service.config.provider.value}...")
                llm_result = self._process_single_page_with_llm(pdf_path, page_num, llm_service)
                
                # Replace the blurry page result with LLM result
                page_results[page_num] = llm_result
        
        # Combine all page results
        final_result = self._combine_page_results(page_results)
        final_result.processing_time = time.time() - start_time
        final_result.method_used = "page_by_page"
        final_result.provider_used = preferred_llm_provider if blurry_pages else None
        final_result.fallback_triggered = len(blurry_pages) > 0
        
        print(f"🎯 Final result: {len(clear_pages)} clear pages + {len(blurry_pages)} LLM-processed pages")
        
        return final_result
    
    def _process_single_page(self, pdf_path: str, page_num: int) -> SmartParseResult:
        """Process a single page using library method"""
        start_time = time.time()
        
        try:
            # Extract text from single page
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text() or ""
                    tables = page.extract_tables() or []
                else:
                    text = ""
                    tables = []
            
            # Extract images from single page
            images = self._extract_images_from_page(pdf_path, page_num)
            
            # Calculate confidence for this page
            confidence = self._calculate_page_confidence(text, tables, images)
            
            return SmartParseResult(
                text=text,
                tables=tables,
                images=images,
                method_used="library",
                provider_used=None,
                confidence=confidence,
                processing_time=time.time() - start_time,
                fallback_triggered=False,
                performance_comparison=None
            )
            
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {e}")
            return SmartParseResult(
                text="",
                tables=[],
                images=[],
                method_used="library",
                provider_used=None,
                confidence=ConfidenceScoring(0.0, 0.0, 0.0, 0.0, [f"Error: {e}"]),
                processing_time=time.time() - start_time,
                fallback_triggered=False,
                performance_comparison=None
            )
    
    def _process_single_page_with_llm(self, pdf_path: str, page_num: int, llm_service) -> SmartParseResult:
        """Process a single page using LLM method"""
        start_time = time.time()
        
        try:
            # Convert single page to image
            images = self._convert_single_page_to_image(pdf_path, page_num)
            
            # Parse with LLM
            llm_result = llm_service.parse_with_llm_from_images(images)
            
            # Convert to SmartParseResult format
            confidence = ConfidenceScoring(
                text_confidence=llm_result.confidence_score,
                table_confidence=llm_result.confidence_score,
                image_confidence=llm_result.confidence_score,
                overall_confidence=llm_result.confidence_score,
                reasons=[f"LLM processed page {page_num + 1}"]
            )
            
            return SmartParseResult(
                text=llm_result.text,
                tables=llm_result.tables,
                images=llm_result.images,
                method_used="llm",
                provider_used=llm_service.config.provider.value,
                confidence=confidence,
                processing_time=time.time() - start_time,
                fallback_triggered=True,
                performance_comparison=None
            )
            
        except Exception as e:
            print(f"Error processing page {page_num + 1} with LLM: {e}")
            # Fallback to library method for this page
            return self._process_single_page(pdf_path, page_num)
    
    def _is_page_blurry(self, page_result: SmartParseResult) -> bool:
        """Check if a single page has blurry text indicators"""
        # Check overall confidence
        if page_result.confidence.overall_confidence < self.confidence_threshold:
            return True
        
        # Check text quality indicators
        text = page_result.text
        if not text.strip():
            return True
        
        # Check for blurry text patterns
        return self._has_blurry_text_indicators(text)
    
    def _calculate_page_confidence(self, text: str, tables: List, images: List) -> ConfidenceScoring:
        """Calculate confidence for a single page"""
        reasons = []
        
        # Text confidence
        text_confidence = 0.8 if len(text.strip()) > 50 else 0.4
        if len(text.strip()) > 200:
            text_confidence = 0.9
        reasons.append(f"Text: {len(text)} chars")
        
        # Table confidence
        table_confidence = 0.9 if len(tables) > 0 else 0.6
        reasons.append(f"Tables: {len(tables)}")
        
        # Image confidence
        image_confidence = 0.8 if len(images) > 0 else 0.7
        reasons.append(f"Images: {len(images)}")
        
        # Overall confidence
        overall_confidence = (text_confidence + table_confidence + image_confidence) / 3
        
        return ConfidenceScoring(
            text_confidence=text_confidence,
            table_confidence=table_confidence,
            image_confidence=image_confidence,
            overall_confidence=overall_confidence,
            reasons=reasons
        )
    
    def _extract_images_from_page(self, pdf_path: str, page_num: int) -> List[Dict]:
        """Extract images from a single page"""
        images = []
        try:
            pdf_document = fitz.open(pdf_path)
            if page_num < len(pdf_document):
                page = pdf_document[page_num]
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_document, xref)
                    
                    if pix.n - pix.alpha < 4:
                        img_data = pix.tobytes("png")
                        encoded_img = base64.b64encode(img_data).decode('utf-8')
                        images.append({
                            "page": page_num + 1,
                            "image_number": img_index + 1,
                            "format": "png",
                            "image_base64": encoded_img
                        })
                    pix = None
            
            pdf_document.close()
        except Exception as e:
            print(f"Error extracting images from page {page_num + 1}: {e}")
        
        return images
    
    def _convert_single_page_to_image(self, pdf_path: str, page_num: int) -> List[str]:
        """Convert a single page to base64 image"""
        try:
            pdf_document = fitz.open(pdf_path)
            if page_num < len(pdf_document):
                page = pdf_document[page_num]
                # High resolution for better LLM processing
                mat = fitz.Matrix(3.0, 3.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                pdf_document.close()
                return [img_base64]
            pdf_document.close()
        except Exception as e:
            print(f"Error converting page {page_num + 1} to image: {e}")
        
        return []
    
    def _combine_page_results(self, page_results: List[SmartParseResult]) -> SmartParseResult:
        """Combine individual page results into final result"""
        # Combine text
        all_text = []
        for i, result in enumerate(page_results):
            if result.text.strip():
                all_text.append(f"--- Page {i + 1} ---\n{result.text}")
        
        combined_text = "\n\n".join(all_text)
        
        # Combine tables
        all_tables = []
        for result in page_results:
            all_tables.extend(result.tables)
        
        # Combine images
        all_images = []
        for result in page_results:
            all_images.extend(result.images)
        
        # Calculate overall confidence
        confidences = [result.confidence.overall_confidence for result in page_results if result.confidence.overall_confidence > 0]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Create final confidence scoring
        final_confidence = ConfidenceScoring(
            text_confidence=overall_confidence,
            table_confidence=overall_confidence,
            image_confidence=overall_confidence,
            overall_confidence=overall_confidence,
            reasons=[f"Combined {len(page_results)} pages", f"Overall confidence: {overall_confidence:.2f}"]
        )
        
        return SmartParseResult(
            text=combined_text,
            tables=all_tables,
            images=all_images,
            method_used="page_by_page",
            provider_used=None,
            confidence=final_confidence,
            processing_time=0,  # Will be set by caller
            fallback_triggered=False,
            performance_comparison=None
        )