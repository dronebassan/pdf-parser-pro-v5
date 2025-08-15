
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import pdfplumber
import pandas as pd
import fitz  # PyMuPDF for better image extraction
from tempfile import NamedTemporaryFile
import base64
import os
from typing import Optional, Dict, Any
import json

# Import our new services
from smart_parser import SmartParser, ParseStrategy
from performance_tracker import PerformanceTracker
from ocr_service import create_ocr_service
from llm_service import create_llm_service

app = FastAPI(
    title="PDF Parser Pro API",
    description="Advanced PDF parsing with AI fallback, OCR support, and performance optimization",
    version="2.0.0"
)

# Initialize services
smart_parser = SmartParser()
ocr_service = create_ocr_service()
performance_tracker = PerformanceTracker()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def extract_text(path: str) -> str:
    """Extract all text from PDF"""
    try:
        with pdfplumber.open(path) as pdf:
            text_content = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
            return "\n\n".join(text_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

def extract_tables(path: str) -> list:
    """Extract tables from PDF"""
    try:
        with pdfplumber.open(path) as pdf:
            tables = []
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table_num, table in enumerate(page_tables):
                    if table and len(table) > 1:  # Ensure table has header and data
                        try:
                            # Use first row as headers
                            headers = table[0]
                            data = table[1:]
                            df = pd.DataFrame(data, columns=headers)
                            tables.append({
                                "page": page_num + 1,
                                "table_number": table_num + 1,
                                "data": df.to_dict('records')
                            })
                        except Exception as e:
                            # If table processing fails, include raw data
                            tables.append({
                                "page": page_num + 1,
                                "table_number": table_num + 1,
                                "raw_data": table,
                                "error": f"Processing error: {str(e)}"
                            })
            return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting tables: {str(e)}")

def extract_images(path: str) -> list:
    """Extract images from PDF using PyMuPDF"""
    try:
        images = []
        pdf_document = fitz.open(path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(pdf_document, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting images: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main PDF parser interface"""
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api/info")
async def api_info():
    """API health check and information"""
    return {
        "message": "PDF Parser Pro API",
        "version": "2.0.0",
        "features": {
            "ai_fallback": bool(smart_parser.llm_services),
            "ocr_support": ocr_service.available,
            "performance_tracking": True,
            "smart_parsing": True,
            "page_by_page_processing": True
        },
        "endpoints": {
            "/parse/": "Extract content with smart parsing and AI fallback",
            "/parse-smart/": "Advanced parsing with strategy selection",
            "/extract-text/": "Extract only text from PDF",
            "/extract-tables/": "Extract only tables from PDF",
            "/extract-images/": "Extract only images from PDF",
            "/performance-stats/": "Get performance statistics",
            "/health-check/": "Check service health and capabilities"
        },
        "strategies": {
            "auto": "Automatically choose best strategy",
            "library_only": "Use only library methods (fastest)",
            "llm_only": "Use only AI models (most accurate)",
            "library_first": "Try library first, fallback to AI",
            "llm_first": "Try AI first, fallback to library",
            "hybrid": "Combine both methods",
            "page_by_page": "Process each page individually, use AI only for blurry pages"
        }
    }

@app.post("/parse-smart/")
async def parse_pdf_smart(
    file: UploadFile = File(...),
    strategy: str = Form("auto"),
    llm_provider: str = Form("openai"),
    extract_text_flag: bool = Form(True),
    extract_tables_flag: bool = Form(True),
    extract_images_flag: bool = Form(True)
):
    """Advanced PDF parsing with smart strategy selection and AI fallback"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if not any([extract_text_flag, extract_tables_flag, extract_images_flag]):
        raise HTTPException(status_code=400, detail="At least one extraction option must be true")

    # Validate strategy
    try:
        parse_strategy = ParseStrategy(strategy.lower())
    except ValueError:
        parse_strategy = ParseStrategy.AUTO

    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Use smart parser
        result = smart_parser.parse_pdf(
            temp_path, 
            strategy=parse_strategy,
            preferred_llm_provider=llm_provider
        )
        
        response_data = {
            "filename": file.filename,
            "parsing_method": result.method_used,
            "provider_used": result.provider_used,
            "confidence_score": result.confidence.overall_confidence,
            "processing_time": result.processing_time,
            "fallback_triggered": result.fallback_triggered
        }
        
        if extract_text_flag:
            response_data["text"] = result.text
        if extract_tables_flag:
            response_data["tables"] = result.tables
        if extract_images_flag:
            response_data["images"] = result.images
            
        if result.performance_comparison:
            response_data["performance_comparison"] = result.performance_comparison
            
    finally:
        os.unlink(temp_path)

    return JSONResponse(content=response_data)

@app.post("/parse/")
async def parse_pdf(
    file: UploadFile = File(...),
    extract_text_flag: bool = Form(True),
    extract_tables_flag: bool = Form(True),
    extract_images_flag: bool = Form(True)
):
    """Legacy endpoint - Extract content from PDF (now uses smart parsing by default)"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if not any([extract_text_flag, extract_tables_flag, extract_images_flag]):
        raise HTTPException(status_code=400, detail="At least one extraction option must be true")

    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Use smart parser with library-first strategy for backward compatibility
        result = smart_parser.parse_pdf(
            temp_path, 
            strategy=ParseStrategy.LIBRARY_FIRST
        )
        
        response_data = {
            "filename": file.filename,
            "parsing_method": result.method_used,
            "confidence_score": result.confidence.overall_confidence,
            "processing_time": result.processing_time
        }
        
        if extract_text_flag:
            response_data["text"] = result.text
        if extract_tables_flag:
            response_data["tables"] = result.tables
        if extract_images_flag:
            response_data["images"] = result.images
            
    finally:
        os.unlink(temp_path)

    return JSONResponse(content=response_data)

@app.post("/extract-text/")
async def extract_text_only(file: UploadFile = File(...)):
    """Extract only text from PDF"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        text_content = extract_text(temp_path)
    finally:
        os.unlink(temp_path)
    
    return {"filename": file.filename, "text": text_content}

@app.post("/extract-tables/")
async def extract_tables_only(file: UploadFile = File(...)):
    """Extract only tables from PDF"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        tables_content = extract_tables(temp_path)
    finally:
        os.unlink(temp_path)
    
    return {"filename": file.filename, "tables": tables_content}

@app.post("/extract-images/")
async def extract_images_only(file: UploadFile = File(...)):
    """Extract only images from PDF"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        images_content = extract_images(temp_path)
    finally:
        os.unlink(temp_path)
    
    return {"filename": file.filename, "images": images_content}

@app.get("/performance-stats/")
async def get_performance_stats(method: Optional[str] = Query(None)):
    """Get performance statistics for parsing methods"""
    if not smart_parser.performance_tracker:
        raise HTTPException(status_code=503, detail="Performance tracking not enabled")
    
    try:
        stats = {
            "general_stats": smart_parser.performance_tracker.get_performance_summary(method),
            "method_comparison": smart_parser.performance_tracker.get_method_comparison_stats(),
            "total_operations": len(smart_parser.performance_tracker.metrics_history)
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

@app.get("/health-check/")
async def health_check():
    """Comprehensive health check for all services"""
    health_status = {
        "status": "healthy",
        "services": {
            "smart_parser": True,
            "ocr_service": ocr_service.available if ocr_service else False,
            "llm_services": {
                provider: True for provider in smart_parser.llm_services.keys()
            },
            "performance_tracking": smart_parser.performance_tracker is not None
        },
        "capabilities": {
            "library_parsing": True,
            "ai_fallback": len(smart_parser.llm_services) > 0,
            "ocr_support": ocr_service.available if ocr_service else False,
            "scanned_pdf_detection": ocr_service.available if ocr_service else False,
            "performance_comparison": True,
            "smart_strategy_selection": True
        }
    }
    
    # Check if any critical services are down
    if not any(health_status["services"].values()):
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/analyze-pdf/")
async def analyze_pdf(file: UploadFile = File(...)):
    """Analyze PDF characteristics without full parsing"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Get basic PDF info
        file_size = os.path.getsize(temp_path)
        
        # Get page count and other metadata
        with pdfplumber.open(temp_path) as pdf:
            page_count = len(pdf.pages)
            
            # Sample first page for analysis
            first_page_text = ""
            if page_count > 0:
                first_page_text = pdf.pages[0].extract_text() or ""
        
        # Check if likely scanned
        is_scanned = False
        if ocr_service and ocr_service.available:
            is_scanned = ocr_service.is_scanned_pdf(temp_path)
        
        # Recommend parsing strategy
        if is_scanned:
            recommended_strategy = "llm_first"
        elif page_count > 50 or file_size > 50 * 1024 * 1024:
            recommended_strategy = "library_only"
        else:
            recommended_strategy = "auto"
        
        analysis = {
            "filename": file.filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "page_count": page_count,
            "likely_scanned": is_scanned,
            "has_extractable_text": len(first_page_text.strip()) > 50,
            "recommended_strategy": recommended_strategy,
            "estimated_processing_time": {
                "library_method": f"{max(1, page_count * 0.1):.1f} seconds",
                "llm_method": f"{max(5, page_count * 2):.1f} seconds"
            }
        }
        
    finally:
        os.unlink(temp_path)
    
    return analysis

