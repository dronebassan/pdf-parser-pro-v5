"""
Business version of the PDF Parser API with authentication and billing
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
import time

# Import business modules
from auth_system import get_current_customer, Customer, auth_system, SubscriptionTier
from api_key_manager import api_key_manager
from smart_parser import SmartParser, ParseStrategy
from llm_service import LLMService, LLMConfig, LLMProvider

app = FastAPI(
    title="PDF Parser Pro - Business API",
    description="AI-powered PDF parsing with smart fallback and usage-based billing",
    version="2.0.0-business"
)

# CORS for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for demo/dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

# Business-aware smart parser
class BusinessSmartParser(SmartParser):
    def __init__(self):
        super().__init__()
        self.api_key_manager = api_key_manager
    
    def get_llm_service_for_customer(self, customer: Customer, provider: str = "openai") -> Optional[LLMService]:
        """Get LLM service using customer's allocated API keys"""
        try:
            # Get appropriate API key for this customer
            api_key = self.api_key_manager.get_api_key_for_customer(
                customer.customer_id, 
                provider
            )
            
            if not api_key:
                return None
            
            # Create LLM service with customer's allocated key
            if provider == "openai":
                config = LLMConfig(
                    provider=LLMProvider.OPENAI,
                    api_key=api_key,
                    model="gpt-4-vision-preview"
                )
            elif provider == "anthropic":
                config = LLMConfig(
                    provider=LLMProvider.ANTHROPIC,
                    api_key=api_key,
                    model="claude-3-5-sonnet-20241022"
                )
            else:
                return None
            
            return LLMService(config)
            
        except Exception as e:
            raise HTTPException(status_code=402, detail=f"Usage quota exceeded: {str(e)}")
    
    def parse_pdf_for_customer(
        self, 
        pdf_path: str, 
        customer: Customer,
        strategy: ParseStrategy = ParseStrategy.AUTO,
        preferred_provider: str = "openai"
    ):
        """Parse PDF with customer-specific billing"""
        
        start_time = time.time()
        file_size = os.path.getsize(pdf_path)
        
        # Get page count for billing
        with open(pdf_path, 'rb') as f:
            import fitz
            doc = fitz.open(stream=f.read(), filetype="pdf")
            page_count = len(doc)
            doc.close()
        
        # Parse using appropriate strategy
        if strategy == ParseStrategy.LIBRARY_ONLY:
            result = self._parse_with_library(pdf_path, file_size, page_count)
            provider_used = None
        elif strategy == ParseStrategy.LLM_ONLY:
            llm_service = self.get_llm_service_for_customer(customer, preferred_provider)
            if not llm_service:
                raise HTTPException(status_code=402, detail="LLM service not available for your subscription")
            result = self._parse_with_llm_service(pdf_path, file_size, page_count, llm_service)
            provider_used = preferred_provider
        else:
            # Smart parsing with fallback
            result = self._parse_smart_for_customer(pdf_path, file_size, page_count, customer, preferred_provider)
            provider_used = getattr(result, 'provider_used', None)
        
        # Record usage for billing (only if LLM was used)
        if provider_used and result.method_used in ['llm', 'hybrid']:
            api_key_manager.record_usage(
                customer.customer_id,
                page_count,
                provider_used
            )
        
        return result
    
    def _parse_smart_for_customer(self, pdf_path: str, file_size: int, page_count: int, 
                                customer: Customer, preferred_provider: str):
        """Smart parsing with customer-specific LLM access"""
        
        # Try library first
        library_result = self._parse_with_library(pdf_path, file_size, page_count)
        
        # Check if LLM fallback is needed and available
        if self._should_fallback_to_llm(library_result):
            llm_service = self.get_llm_service_for_customer(customer, preferred_provider)
            
            if llm_service:
                llm_result = self._parse_with_llm_service(pdf_path, file_size, page_count, llm_service)
                
                # Return better result
                if llm_result.confidence.overall_confidence > library_result.confidence.overall_confidence:
                    llm_result.fallback_triggered = True
                    llm_result.provider_used = preferred_provider
                    return llm_result
        
        return library_result
    
    def _parse_with_llm_service(self, pdf_path: str, file_size: int, page_count: int, llm_service: LLMService):
        """Parse using specific LLM service"""
        result = llm_service.parse_with_llm(pdf_path)
        
        # Convert to SmartParseResult format
        from smart_parser import SmartParseResult, ConfidenceScoring
        
        confidence = ConfidenceScoring(
            text_confidence=result.confidence_score,
            table_confidence=result.confidence_score,
            image_confidence=result.confidence_score,
            overall_confidence=result.confidence_score,
            reasons=[f"LLM confidence: {result.confidence_score}"]
        )
        
        return SmartParseResult(
            text=result.text,
            tables=result.tables,
            images=result.images,
            method_used="llm",
            provider_used=result.provider,
            confidence=confidence,
            processing_time=result.processing_time,
            fallback_triggered=False,
            performance_comparison=None
        )

# Initialize business parser
business_parser = BusinessSmartParser()

# Public endpoints (no auth required)
@app.post("/signup")
async def signup(email: str = Form(...), tier: str = Form("free")):
    """Sign up for API access"""
    try:
        subscription_tier = SubscriptionTier(tier.lower())
        customer = auth_system.create_customer(email, subscription_tier)
        
        return {
            "message": "Account created successfully",
            "api_key": customer.api_key,
            "subscription_tier": customer.subscription_tier.value,
            "usage_quota": api_key_manager.customer_pricing[subscription_tier]['quota']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/pricing")
async def get_pricing():
    """Get pricing information"""
    return {
        "plans": {
            "free": {
                "quota": 10,
                "price_per_month": 0,
                "price_per_page": 0,
                "features": ["Library parsing", "Basic support"]
            },
            "basic": {
                "quota": 500,
                "price_per_month": 29,
                "price_per_page": 0.05,
                "features": ["AI fallback", "Priority support", "Analytics"]
            },
            "premium": {
                "quota": 5000,
                "price_per_month": 99,
                "price_per_page": 0.04,
                "features": ["Premium AI models", "Faster processing", "Custom integrations"]
            },
            "enterprise": {
                "quota": "unlimited",
                "price_per_month": "custom",
                "price_per_page": 0.03,
                "features": ["Your own API keys", "SLA guarantee", "Dedicated support"]
            }
        }
    }

# Authenticated endpoints
@app.post("/api/parse")
async def parse_pdf_business(
    file: UploadFile = File(...),
    strategy: str = Form("auto"),
    llm_provider: str = Form("openai"),
    extract_text: bool = Form(True),
    extract_tables: bool = Form(True),
    extract_images: bool = Form(True),
    customer: Customer = Depends(get_current_customer)
):
    """Business PDF parsing with authentication and billing"""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")
    
    # Validate strategy
    try:
        parse_strategy = ParseStrategy(strategy.lower())
    except ValueError:
        parse_strategy = ParseStrategy.AUTO
    
    # Save uploaded file
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name
    
    try:
        # Parse with customer billing
        result = business_parser.parse_pdf_for_customer(
            temp_path,
            customer,
            parse_strategy,
            llm_provider
        )
        
        # Build response
        response_data = {
            "filename": file.filename,
            "customer_id": customer.customer_id,
            "parsing_method": result.method_used,
            "provider_used": result.provider_used,
            "confidence_score": result.confidence.overall_confidence,
            "processing_time": result.processing_time,
            "fallback_triggered": result.fallback_triggered
        }
        
        if extract_text:
            response_data["text"] = result.text
        if extract_tables:
            response_data["tables"] = result.tables
        if extract_images:
            response_data["images"] = result.images
        
        return response_data
        
    finally:
        os.unlink(temp_path)

@app.get("/api/usage")
async def get_usage_stats(customer: Customer = Depends(get_current_customer)):
    """Get customer usage statistics"""
    return api_key_manager.get_usage_stats(customer.customer_id)

@app.get("/api/account")
async def get_account_info(customer: Customer = Depends(get_current_customer)):
    """Get customer account information"""
    usage_stats = api_key_manager.get_usage_stats(customer.customer_id)
    
    return {
        "customer_id": customer.customer_id,
        "email": customer.email,
        "subscription_tier": customer.subscription_tier.value,
        "api_key": customer.api_key,
        "created_at": customer.created_at,
        "usage": usage_stats
    }

@app.post("/api/upgrade")
async def upgrade_subscription(
    new_tier: str = Form(...),
    customer: Customer = Depends(get_current_customer)
):
    """Upgrade customer subscription"""
    try:
        subscription_tier = SubscriptionTier(new_tier.lower())
        auth_system.upgrade_customer(customer.api_key, subscription_tier)
        
        return {
            "message": f"Upgraded to {subscription_tier.value}",
            "new_tier": subscription_tier.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Demo dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Business dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Parser Pro - Business API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .section { margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            code { background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }
            .pricing { display: flex; gap: 20px; }
            .plan { flex: 1; padding: 20px; border: 1px solid #ddd; border-radius: 5px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 PDF Parser Pro - Business API</h1>
            
            <div class="section">
                <h2>🚀 Get Started</h2>
                <p>1. Sign up for an API key: <code>POST /signup</code></p>
                <p>2. Parse PDFs: <code>POST /api/parse</code> with header <code>X-API-Key: your-key</code></p>
                <p>3. Check usage: <code>GET /api/usage</code></p>
            </div>
            
            <div class="section">
                <h2>💳 Pricing Plans</h2>
                <div class="pricing">
                    <div class="plan">
                        <h3>Free</h3>
                        <p>10 pages/month</p>
                        <p>Library parsing only</p>
                        <p><strong>$0/month</strong></p>
                    </div>
                    <div class="plan">
                        <h3>Basic</h3>
                        <p>500 pages/month</p>
                        <p>AI fallback included</p>
                        <p><strong>$29/month</strong></p>
                    </div>
                    <div class="plan">
                        <h3>Premium</h3>
                        <p>5,000 pages/month</p>
                        <p>Premium AI models</p>
                        <p><strong>$99/month</strong></p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📖 API Documentation</h2>
                <p>Visit <a href="/docs">/docs</a> for interactive API documentation</p>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)