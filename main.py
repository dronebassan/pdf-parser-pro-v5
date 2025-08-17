from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pdfplumber
import fitz  # PyMuPDF
from tempfile import NamedTemporaryFile
import os
import time
import stripe
from typing import Optional, Dict, Any
import json
from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(
    title="PDF Parser Pro API",
    description="AI-powered PDF processing with smart optimization",
    version="2.0.0"
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass  # Static files optional

# Initialize advanced services with full feature support
smart_parser = None
performance_tracker = None
ocr_service = None
llm_service = None

try:
    from smart_parser import SmartParser
    smart_parser = SmartParser()
    print("✅ Smart Parser initialized with revolutionary 3-step fallback system")
except Exception as e:
    print(f"❌ Smart parser failed: {e}")

try:
    from performance_tracker import PerformanceTracker
    performance_tracker = PerformanceTracker()
    print("✅ Performance Tracker initialized")
except Exception as e:
    print(f"❌ Performance tracker failed: {e}")

try:
    from ocr_service import create_ocr_service
    ocr_service = create_ocr_service()
    print("✅ Advanced OCR Service initialized")
except Exception as e:
    print(f"⚠️  Advanced OCR failed, trying simple: {e}")
    try:
        from ocr_service_simple import create_simple_ocr_service
        ocr_service = create_simple_ocr_service()
        print("✅ Simple OCR Service initialized")
    except Exception as e2:
        print(f"❌ All OCR services failed: {e2}")

try:
    from llm_service import create_llm_service
    llm_service = create_llm_service("gemini")  # Gemini only
    print("✅ Gemini AI Service initialized (Google Gemini 2.5 Flash)")
except Exception as e:
    print(f"❌ Gemini AI service failed: {e}")

# Service status summary
services_status = {
    "smart_parser": smart_parser is not None,
    "performance_tracker": performance_tracker is not None,
    "ocr_service": ocr_service is not None,
    "llm_service": llm_service is not None
}

print(f"\n🚀 PDF Parser Pro - Service Status:")
for service, status in services_status.items():
    status_icon = "✅" if status else "❌"
    print(f"   {status_icon} {service}: {'Available' if status else 'Unavailable'}")

if all(services_status.values()):
    print("\n🎯 ALL ADVANCED FEATURES ACTIVE - Ready to beat competitors!")
elif smart_parser:
    print("\n⚡ Core features active - Revolutionary parsing ready!")
else:
    print("\n⚠️  Basic mode - Some advanced features unavailable")

# Initialize Stripe and Usage Tracking
try:
    from stripe_service import stripe_service, PlanType
    from usage_tracker import usage_tracker
    print("✅ Stripe billing service initialized")
    print("✅ Usage tracking system initialized")
except Exception as e:
    print(f"❌ Billing services failed: {e}")
    stripe_service = None
    usage_tracker = None

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models for requests
class CheckoutRequest(BaseModel):
    plan_type: str
    customer_email: str
    success_url: str = "https://your-domain.com/success"
    cancel_url: str = "https://your-domain.com/cancel"

class UsageRequest(BaseModel):
    user_id: str
    pages_processed: int

@app.get("/", response_class=HTMLResponse)
def home():
    """Home page with PDF upload interface"""
    # Check if advanced features are available
    advanced_available = all(services_status.values())
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Parser Pro - Revolutionary AI-Powered Processing</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{ 
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            .header {{ 
                text-align: center; 
                margin-bottom: 40px;
                padding: 30px 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: -20px -20px 40px -20px;
                border-radius: 20px 20px 0 0;
                color: white;
            }}
            .header h1 {{ 
                font-size: 3.5em;
                font-weight: 700;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            .header p {{ 
                font-size: 1.3em;
                margin-bottom: 20px;
                opacity: 0.9;
            }}
            .features {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
                gap: 25px; 
                margin: 40px 0;
            }}
            .feature-card {{ 
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 25px;
                border-radius: 15px;
                border: 1px solid #e9ecef;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .feature-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }}
            .feature-card:hover {{ 
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }}
            .feature-card h4 {{
                font-size: 1.3em;
                margin-bottom: 10px;
                color: #2c3e50;
                font-weight: 600;
            }}
            .upload-area {{ 
                border: 3px dashed #667eea;
                padding: 50px;
                text-align: center;
                margin: 40px 0;
                border-radius: 20px;
                background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .upload-area:hover {{
                border-color: #764ba2;
                background: linear-gradient(135deg, #f0f8ff 0%, #e1efff 100%);
                transform: translateY(-2px);
                box-shadow: 0 20px 40px rgba(102, 126, 234, 0.2);
            }}
            .upload-container {{
                position: relative;
                z-index: 2;
            }}
            .upload-icon {{
                font-size: 4em;
                margin-bottom: 20px;
                opacity: 0.8;
                animation: float 3s ease-in-out infinite;
            }}
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            .upload-area h3 {{
                font-size: 1.8em;
                margin-bottom: 10px;
                color: #2c3e50;
                font-weight: 600;
            }}
            .upload-area p {{
                font-size: 1.1em;
                color: #666;
                margin-bottom: 30px;
                opacity: 0.8;
            }}
            .upload-button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 40px;
                border-radius: 50px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                display: inline-block;
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 20px;
            }}
            .upload-button:hover {{
                transform: translateY(-3px);
                box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
            }}
            .upload-button span {{
                position: relative;
                z-index: 2;
            }}
            .upload-button-bg {{
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
                transition: left 0.3s ease;
                z-index: 1;
            }}
            .upload-button:hover .upload-button-bg {{
                left: 0;
            }}
            .file-info {{
                margin-top: 20px;
                padding: 20px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(102, 126, 234, 0.2);
            }}
            .file-info span {{
                display: block;
                font-size: 16px;
                color: #2c3e50;
                margin-bottom: 15px;
                font-weight: 500;
            }}
            .process-btn {{
                background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
                box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .process-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 12px 30px rgba(76, 175, 80, 0.4);
            }}
            .process-btn span {{
                position: relative;
                z-index: 2;
            }}
            .process-btn-bg {{
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #45a049 0%, #4caf50 100%);
                transition: left 0.3s ease;
                z-index: 1;
            }}
            .process-btn:hover .process-btn-bg {{
                left: 0;
            }}
            .btn {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 40px;
                border: none;
                border-radius: 50px;
                cursor: pointer;
                font-size: 18px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .btn:hover {{ 
                transform: translateY(-3px);
                box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
            }}
            .btn:active {{
                transform: translateY(-1px);
            }}
            .result {{ 
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 30px;
                margin: 30px 0;
                border-radius: 15px;
                border: 1px solid #e9ecef;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}
            .status-indicator {{ 
                display: inline-block; 
                width: 12px; 
                height: 12px; 
                border-radius: 50%; 
                margin-right: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);
            }}
            .status-active {{ 
                background: linear-gradient(135deg, #4caf50, #45a049);
                box-shadow: 0 0 15px rgba(76, 175, 80, 0.4);
            }}
            .status-inactive {{ 
                background: linear-gradient(135deg, #f44336, #d32f2f);
                box-shadow: 0 0 15px rgba(244, 67, 54, 0.4);
            }}
            .advanced-badge {{ 
                background: linear-gradient(135deg, #4caf50, #8bc34a);
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
            }}
            .basic-badge {{ 
                background: linear-gradient(135deg, #ff9800, #ffc107);
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 5px 15px rgba(255, 152, 0, 0.3);
            }}
            .pricing-section {{
                margin-top: 60px;
                padding: 40px 0;
            }}
            .pricing-section h2 {{
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 20px;
                color: #2c3e50;
                font-weight: 700;
            }}
            .pricing-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 30px;
                margin-top: 40px;
            }}
            .pricing-card {{
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                padding: 35px 25px;
                border-radius: 20px;
                border: 2px solid #e9ecef;
                text-align: center;
                position: relative;
                transition: all 0.3s ease;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            }}
            .pricing-card:hover {{
                transform: translateY(-10px);
                box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            }}
            .pricing-card.featured {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: 3px solid #667eea;
                transform: scale(1.05);
                box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
            }}
            .pricing-card.featured:hover {{
                transform: scale(1.05) translateY(-10px);
            }}
            .pricing-card .price {{
                font-size: 3em;
                font-weight: 700;
                margin: 20px 0;
                color: #2c3e50;
            }}
            .pricing-card.featured .price {{
                color: white;
            }}
            .pricing-card ul {{
                list-style: none;
                padding: 0;
                margin: 25px 0;
                text-align: left;
            }}
            .pricing-card li {{
                padding: 8px 0;
                font-size: 16px;
                color: #555;
            }}
            .pricing-card.featured li {{
                color: rgba(255,255,255,0.9);
            }}
            .pricing-card button {{
                width: 100%;
                margin-top: 20px;
                padding: 15px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 15px;
                transition: all 0.3s ease;
            }}
            .plan-badge {{
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                display: inline-block;
                margin-bottom: 15px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-size: 14px;
            }}
            .advantages {{
                text-align: center;
                margin-top: 40px;
                padding: 30px;
                background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
                border-radius: 20px;
                border: 1px solid #e1bee7;
            }}
            .advantages h3 {{
                font-size: 1.8em;
                margin-bottom: 25px;
                color: #2c3e50;
            }}
            .advantages-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .advantages-grid div {{
                font-size: 16px;
                font-weight: 500;
                padding: 15px;
                background: rgba(255,255,255,0.7);
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }}
            @media (max-width: 768px) {{
                .container {{ margin: 10px; padding: 15px; }}
                .header h1 {{ font-size: 2.5em; }}
                .controls {{ grid-template-columns: 1fr; }}
                .pricing-grid {{ grid-template-columns: 1fr; }}
                .pricing-card.featured {{ transform: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 PDF Parser Pro</h1>
                <p>Revolutionary 3-Step Fallback System with 99% Cost Optimization</p>
                <div>
                    {'<span class="advanced-badge">ALL ADVANCED FEATURES ACTIVE</span>' if advanced_available else '<span class="basic-badge">BASIC MODE ACTIVE</span>'}
                </div>
            </div>
            
            
            <div class="upload-area">
                <div class="upload-container">
                    <div class="upload-icon">📄</div>
                    <h3>Drop your PDF here or click to browse</h3>
                    <p>Revolutionary AI will extract every detail with 99% accuracy</p>
                    <input type="file" id="pdfFile" accept=".pdf" style="display: none;">
                    <div class="upload-button" onclick="document.getElementById('pdfFile').click()">
                        <span>Choose PDF File</span>
                        <div class="upload-button-bg"></div>
                    </div>
                    <div class="file-info" id="fileInfo" style="display: none;">
                        <span id="fileName"></span>
                        <button class="process-btn" onclick="uploadFile()">
                            <span>🚀 Process with AI</span>
                            <div class="process-btn-bg"></div>
                        </button>
                    </div>
                </div>
            </div>
            
            <div id="result" class="result" style="display:none;">
                <h3>Results:</h3>
                <div id="output"></div>
            </div>
            
            <!-- Pricing Section -->
            <div class="pricing-section" style="margin-top: 50px;">
                <h2 style="text-align: center; margin-bottom: 30px;">💎 Choose Your Plan</h2>
                <div class="pricing-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                    
                    <div class="pricing-card">
                        <div class="plan-badge" style="background: linear-gradient(135deg, #2196f3, #1976d2);">🎓 Student</div>
                        <div class="price">$4.99<span style="font-size: 0.4em; color: #666;">/month</span></div>
                        <ul>
                            <li>✅ 500 pages/month</li>
                            <li>✅ Revolutionary AI processing</li>
                            <li>✅ All advanced features</li>
                            <li>✅ Email support</li>
                        </ul>
                        <button class="btn" onclick="subscribe('student')">Choose Student</button>
                    </div>
                    
                    <div class="pricing-card featured">
                        <div class="plan-badge" style="background: white; color: #667eea; font-weight: 700;">📈 MOST POPULAR</div>
                        <div class="price">$19.99<span style="font-size: 0.4em; color: rgba(255,255,255,0.8);">/month</span></div>
                        <ul>
                            <li>✅ 2,500 pages/month</li>
                            <li>✅ Priority processing</li>
                            <li>✅ Advanced analytics</li>
                            <li>✅ Chat support</li>
                            <li>✅ API access</li>
                        </ul>
                        <button onclick="subscribe('growth')" style="background: white; color: #667eea; padding: 15px; border: none; border-radius: 15px; cursor: pointer; font-size: 16px; font-weight: 600; width: 100%; transition: all 0.3s ease;">Choose Growth</button>
                    </div>
                    
                    <div class="pricing-card">
                        <div class="plan-badge" style="background: linear-gradient(135deg, #ff9800, #f57c00);">🏢 Business</div>
                        <div class="price">$79.99<span style="font-size: 0.4em; color: #666;">/month</span></div>
                        <ul>
                            <li>✅ 10,000 pages/month</li>
                            <li>✅ Faster processing queues</li>
                            <li>✅ Performance dashboard</li>
                            <li>✅ Phone + chat support</li>
                            <li>✅ Full API access</li>
                            <li>✅ Custom integrations</li>
                        </ul>
                        <button class="btn" onclick="subscribe('business')">Choose Business</button>
                    </div>
                    
                    <div class="pricing-card">
                        <div class="plan-badge" style="background: linear-gradient(135deg, #9c27b0, #7b1fa2);">🏗️ Enterprise</div>
                        <div class="price">$299.99<span style="font-size: 0.4em; color: #666;">/month</span></div>
                        <ul>
                            <li>✅ 50,000 pages/month</li>
                            <li>✅ Dedicated processing</li>
                            <li>✅ White-label options</li>
                            <li>✅ 24/7 priority support</li>
                            <li>✅ Custom deployment</li>
                            <li>✅ SLA guarantees</li>
                        </ul>
                        <button class="btn" onclick="subscribe('enterprise')">Choose Enterprise</button>
                    </div>
                </div>
                
                <div class="advantages">
                    <h3>💡 Why Choose PDF Parser Pro?</h3>
                    <div class="advantages-grid">
                        <div>🚀 <strong>99% Cost Savings</strong><br>vs Adobe & Google</div>
                        <div>⚡ <strong>3-Step Fallback</strong><br>Never fails to extract</div>
                        <div>🧠 <strong>Gemini 2.5 Flash</strong><br>Latest Google AI</div>
                        <div>📊 <strong>Page-by-Page</strong><br>Revolutionary processing</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Handle file selection
            document.getElementById('pdfFile').addEventListener('change', handleFileSelection);
            
            function handleFileSelection(e) {{
                const file = e.target.files[0];
                displayFileInfo(file);
            }}
            
            function displayFileInfo(file) {{
                const fileInfo = document.getElementById('fileInfo');
                const fileName = document.getElementById('fileName');
                
                if (file) {{
                    fileName.textContent = `📄 ${{file.name}} (${{(file.size / 1024 / 1024).toFixed(2)}} MB)`;
                    fileInfo.style.display = 'block';
                }} else {{
                    fileInfo.style.display = 'none';
                }}
            }}
            
            // Drag and drop functionality
            const uploadArea = document.querySelector('.upload-area');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {{
                uploadArea.addEventListener(eventName, preventDefaults, false);
            }});
            
            function preventDefaults(e) {{
                e.preventDefault();
                e.stopPropagation();
            }}
            
            ['dragenter', 'dragover'].forEach(eventName => {{
                uploadArea.addEventListener(eventName, highlight, false);
            }});
            
            ['dragleave', 'drop'].forEach(eventName => {{
                uploadArea.addEventListener(eventName, unhighlight, false);
            }});
            
            function highlight(e) {{
                uploadArea.style.background = 'linear-gradient(135deg, #e8f4fd 0%, #d4f1f4 100%)';
                uploadArea.style.borderColor = '#4caf50';
            }}
            
            function unhighlight(e) {{
                uploadArea.style.background = 'linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%)';
                uploadArea.style.borderColor = '#667eea';
            }}
            
            uploadArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {{
                const dt = e.dataTransfer;
                const files = dt.files;
                const file = files[0];
                
                if (file && file.type === 'application/pdf') {{
                    document.getElementById('pdfFile').files = files;
                    displayFileInfo(file);
                }} else {{
                    alert('Please drop a PDF file');
                }}
            }}
            
            async function uploadFile() {{
                const fileInput = document.getElementById('pdfFile');
                const file = fileInput.files[0];
                
                if (!file) {{
                    alert('Please select a PDF file');
                    return;
                }}

                const formData = new FormData();
                formData.append('file', file);
                formData.append('strategy', 'auto');
                formData.append('preferred_llm', 'gemini');

                try {{
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('output').innerHTML = '🚀 Processing with revolutionary AI...';
                    
                    const response = await fetch('/parse/', {{
                        method: 'POST',
                        body: formData
                    }});

                    const result = await response.json();
                    
                    if (result.success) {{
                        let outputHtml = '';
                        
                        // Advanced result display
                        if (result.metadata && result.metadata.advanced_features) {{
                            outputHtml += '<div style="background: linear-gradient(45deg, #4caf50, #8bc34a); color: white; padding: 10px; border-radius: 5px; margin-bottom: 15px;"><strong>✅ Advanced Processing Complete!</strong></div>';
                        }}
                        
                        outputHtml += '<h4>📄 Extracted Text (' + (result.text ? result.text.length : 0) + ' characters):</h4>';
                        outputHtml += '<pre style="max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 5px;">' + (result.text || 'No text found') + '</pre>';
                        
                        if (result.tables && result.tables.length > 0) {{
                            outputHtml += '<h4>📊 Tables Found: ' + result.tables.length + '</h4>';
                        }}
                        
                        if (result.images && result.images.length > 0) {{
                            outputHtml += '<h4>🖼️ Images Found: ' + result.images.length + '</h4>';
                        }}
                        
                        outputHtml += '<h4>⚙️ Processing Details:</h4>';
                        outputHtml += '<div style="background: #e3f2fd; padding: 15px; border-radius: 5px;">';
                        outputHtml += '<p><strong>Strategy Used:</strong> ' + result.strategy_used + '</p>';
                        outputHtml += '<p><strong>Processing Time:</strong> ' + result.processing_time.toFixed(2) + 's</p>';
                        outputHtml += '<p><strong>Confidence Score:</strong> ' + (result.confidence * 100).toFixed(1) + '%</p>';
                        
                        if (result.provider_used) {{
                            outputHtml += '<p><strong>LLM Provider:</strong> ' + result.provider_used + '</p>';
                        }}
                        
                        if (result.fallback_triggered) {{
                            outputHtml += '<p style="color: #ff9800;"><strong>⚡ Fallback Triggered:</strong> Advanced AI processing used</p>';
                        }}
                        
                        if (result.metadata) {{
                            outputHtml += '<p><strong>File Size:</strong> ' + (result.metadata.file_size / 1024).toFixed(1) + ' KB</p>';
                        }}
                        
                        outputHtml += '</div>';
                        
                        document.getElementById('output').innerHTML = outputHtml;
                    }} else {{
                        document.getElementById('output').innerHTML = 
                            '<div style="background: #f44336; color: white; padding: 10px; border-radius: 5px;"><strong>❌ Error:</strong> ' + (result.error || result.detail) + '</div>';
                    }}
                }} catch (error) {{
                    document.getElementById('output').innerHTML = 
                        '<div style="background: #f44336; color: white; padding: 10px; border-radius: 5px;"><strong>❌ Network Error:</strong> ' + error.message + '</div>';
                }}
            }}
            
            async function subscribe(plan) {{
                const email = prompt('Enter your email address:');
                if (!email) return;
                
                try {{
                    const response = await fetch('/create-checkout-session/', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            plan_type: plan,
                            customer_email: email,
                            success_url: window.location.origin + '/success',
                            cancel_url: window.location.origin + '/cancel'
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        window.location.href = data.checkout_url;
                    }} else {{
                        alert('Error creating checkout session: ' + data.error);
                    }}
                    
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/health-check/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "smart_parser": smart_parser is not None,
            "ocr_service": ocr_service is not None,
            "llm_service": llm_service is not None,
            "performance_tracker": performance_tracker is not None
        },
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.post("/parse/")
async def parse_pdf_advanced(
    file: UploadFile = File(...),
    strategy: str = "auto",
    preferred_llm: str = "gemini",
    user_id: Optional[str] = None
):
    """Revolutionary PDF parsing with 3-step fallback system and 99% cost optimization"""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    start_time = time.time()
    pages_processed = 0
    ai_used = False
    
    try:
        # Save uploaded file
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Get page count for usage tracking
        try:
            doc = fitz.open(tmp_path)
            pages_processed = len(doc)
            doc.close()
        except:
            pages_processed = 1  # Fallback
        
        # Check usage limits if user is provided
        if user_id and usage_tracker:
            usage_check = usage_tracker.check_user_limits(user_id, pages_processed)
            if not usage_check.get("success", True):
                raise HTTPException(status_code=429, detail=usage_check.get("error", "Usage limit check failed"))
        
        result = None
        
        # Use revolutionary smart parser if available
        if smart_parser:
            try:
                print(f"🧠 Using Smart Parser with strategy: {strategy}")
                from smart_parser import ParseStrategy
                
                # Map string to enum
                strategy_map = {
                    "auto": ParseStrategy.AUTO,
                    "library_only": ParseStrategy.LIBRARY_ONLY,
                    "ai_fallback": ParseStrategy.LLM_FIRST,
                    "page_by_page": ParseStrategy.PAGE_BY_PAGE,
                    "smart_detection": ParseStrategy.AUTO,
                    "hybrid": ParseStrategy.HYBRID
                }
                
                parse_strategy = strategy_map.get(strategy, ParseStrategy.AUTO)
                result = smart_parser.parse_pdf(tmp_path, parse_strategy, preferred_llm)
                
                # Check if AI was used
                ai_used = result.fallback_triggered or "ai" in result.method_used.lower() or "llm" in result.method_used.lower()
                
                # Track usage for billing
                if user_id and usage_tracker:
                    try:
                        usage_tracker.track_usage(
                            user_id=user_id,
                            subscription_id="",  # Would get from user's subscription
                            pages_processed=pages_processed,
                            document_name=file.filename,
                            processing_strategy=result.method_used,
                            ai_used=ai_used,
                            cost_estimate=pages_processed * (0.001 if ai_used else 0.0001)
                        )
                    except Exception as e:
                        print(f"Usage tracking failed: {e}")
                
                # Convert SmartParseResult to API response
                processing_time = time.time() - start_time
                
                return {
                    "success": True,
                    "text": result.text,
                    "tables": result.tables,
                    "images": result.images,
                    "strategy_used": result.method_used,
                    "provider_used": result.provider_used,
                    "confidence": result.confidence.overall_confidence,
                    "processing_time": processing_time,
                    "fallback_triggered": result.fallback_triggered,
                    "performance_data": result.performance_comparison,
                    "pages_processed": pages_processed,
                    "ai_used": ai_used,
                    "metadata": {
                        "file_size": os.path.getsize(tmp_path),
                        "strategy_requested": strategy,
                        "advanced_features": True,
                        "usage_tracked": user_id is not None
                    }
                }
                
            except Exception as e:
                print(f"⚠️  Smart parser failed: {e}")
                # Fall through to basic parsing
        
        # Fallback to basic parsing
        print("📚 Using basic library parsing as fallback")
        text = ""
        tables = []
        
        try:
            with pdfplumber.open(tmp_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"Page {page_num + 1}:\n{page_text}\n\n"
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        
        except Exception as e:
            # Final fallback to PyMuPDF
            try:
                doc = fitz.open(tmp_path)
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text:
                        text += f"Page {page_num + 1}:\n{page_text}\n\n"
                doc.close()
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"All parsing methods failed: {str(e2)}")
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "text": text.strip(),
            "tables": tables,
            "images": [],
            "strategy_used": "library_basic_fallback",
            "provider_used": None,
            "confidence": 0.8,
            "processing_time": processing_time,
            "fallback_triggered": True,
            "performance_data": None,
            "metadata": {
                "file_size": os.path.getsize(tmp_path),
                "strategy_requested": strategy,
                "advanced_features": False,
                "note": "Advanced features unavailable - using basic fallback"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        # Clean up
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass

@app.get("/api/info")
def api_info():
    """API information endpoint"""
    return {
        "name": "PDF Parser Pro",
        "version": "2.0.0",
        "description": "AI-powered PDF processing API",
        "features": {
            "basic_parsing": True,
            "smart_parsing": smart_parser is not None,
            "ai_fallback": llm_service is not None,
            "ocr_support": ocr_service is not None,
            "billing_system": stripe_service is not None,
            "usage_tracking": usage_tracker is not None
        },
        "endpoints": [
            "/",
            "/health-check/",
            "/parse/",
            "/api/info",
            "/pricing",
            "/create-checkout-session/",
            "/customer-portal/",
            "/stripe-webhook/",
            "/usage/",
            "/docs"
        ]
    }

# ==================== STRIPE BILLING ENDPOINTS ====================

@app.get("/pricing")
def get_pricing():
    """Get pricing plans information"""
    if not stripe_service:
        raise HTTPException(status_code=503, detail="Billing service unavailable")
    
    plans_info = {}
    for plan_type, plan in stripe_service.plans.items():
        plans_info[plan_type.value] = {
            "name": plan.name,
            "price_monthly": plan.price_monthly,
            "pages_included": plan.pages_included,
            "overage_rate": plan.overage_rate,
            "features": plan.features
        }
    
    return {
        "success": True,
        "plans": plans_info,
        "currency": "USD"
    }

@app.post("/create-checkout-session/")
async def create_checkout_session(request: CheckoutRequest):
    """Create Stripe checkout session for subscription"""
    if not stripe_service:
        raise HTTPException(status_code=503, detail="Billing service unavailable")
    
    try:
        # Validate plan type
        plan_type = PlanType(request.plan_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    
    result = stripe_service.create_checkout_session(
        plan_type=plan_type,
        customer_email=request.customer_email,
        success_url=request.success_url,
        cancel_url=request.cancel_url
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/customer-portal/")
async def customer_portal(customer_id: str, return_url: str = "https://your-domain.com"):
    """Create customer portal session for managing subscription"""
    if not stripe_service:
        raise HTTPException(status_code=503, detail="Billing service unavailable")
    
    result = stripe_service.create_customer_portal_session(customer_id, return_url)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@app.post("/stripe-webhook/")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    if not stripe_service:
        raise HTTPException(status_code=503, detail="Billing service unavailable")
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    result = stripe_service.handle_webhook_event(event)
    
    if not result["success"]:
        print(f"Webhook handling error: {result['error']}")
    
    return {"status": "success"}

# ==================== USAGE TRACKING ENDPOINTS ====================

@app.get("/usage/{user_id}")
async def get_user_usage(user_id: str):
    """Get user's current usage and limits"""
    if not usage_tracker:
        raise HTTPException(status_code=503, detail="Usage tracking unavailable")
    
    try:
        usage_info = usage_tracker.check_user_limits(user_id, 0)
        monthly_usage = usage_tracker.get_monthly_usage(user_id)
        analytics = usage_tracker.get_analytics(user_id)
        
        return {
            "success": True,
            "usage_info": usage_info,
            "monthly_summary": monthly_usage,
            "analytics": analytics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/usage/track/")
async def track_usage_endpoint(request: UsageRequest):
    """Track usage for billing (internal endpoint)"""
    if not usage_tracker:
        raise HTTPException(status_code=503, detail="Usage tracking unavailable")
    
    # This would typically be called internally, not by users
    # You might want to add authentication here
    
    result = usage_tracker.track_usage(
        user_id=request.user_id,
        subscription_id="", # You'd get this from user's subscription
        pages_processed=request.pages_processed
    )
    
    return result

@app.get("/usage/{user_id}/history")
async def get_usage_history(user_id: str, days: int = 30):
    """Get user's usage history"""
    if not usage_tracker:
        raise HTTPException(status_code=503, detail="Usage tracking unavailable")
    
    try:
        history = usage_tracker.get_usage_history(user_id, days)
        return {
            "success": True,
            "history": history,
            "days": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)