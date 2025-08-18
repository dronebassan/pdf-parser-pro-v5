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

# Initialize Authentication System
auth_system = None
try:
    from auth_system import auth_system
    print("✅ Authentication system initialized")
except Exception as e:
    print(f"❌ Authentication system failed: {e}")
    print(f"Error details: {type(e).__name__}: {str(e)}")
    auth_system = None

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

class UserRegistration(BaseModel):
    email: str
    password: str
    plan_type: str = "student"

class UserLogin(BaseModel):
    email: str
    password: str

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not credentials or not auth_system:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide API key in Authorization header."
        )
    
    try:
        # Get customer by API key
        customer = auth_system.get_customer_by_api_key(credentials.credentials)
        if not customer:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return customer
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# Optional authentication for free tier
async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user, but allow unauthenticated access for free tier"""
    if not credentials or not auth_system:
        return None
    
    try:
        customer = auth_system.get_customer_by_api_key(credentials.credentials)
        return customer
    except:
        return None

@app.get("/", response_class=HTMLResponse)
def home():
    """Home page with PDF upload interface"""
    # Check if advanced features are available
    advanced_available = all(services_status.values())
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Parser Pro - AI Document Processing</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #2563eb;
                --primary-hover: #1d4ed8;
                --secondary-color: #6b7280;
                --success-color: #059669;
                --background: #ffffff;
                --background-secondary: #f8fafc;
                --background-tertiary: #f1f5f9;
                --text-primary: #1f2937;
                --text-secondary: #6b7280;
                --text-muted: #9ca3af;
                --border-color: #e5e7eb;
                --border-hover: #d1d5db;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
                --border-radius: 8px;
                --border-radius-lg: 12px;
                --transition: all 0.2s ease-in-out;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                line-height: 1.6;
                color: var(--text-primary);
                background: var(--background);
                min-height: 100vh;
            }}
            
            /* Navigation */
            .navbar {{
                position: sticky;
                top: 0;
                z-index: 1000;
                background: var(--background);
                border-bottom: 1px solid var(--border-color);
                padding: 1rem 0;
                box-shadow: var(--shadow-sm);
            }}
            
            .nav-container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .logo {{
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--text-primary);
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .logo i {{
                font-size: 1.5rem;
                color: var(--primary-color);
            }}
            
            .nav-links {{
                display: flex;
                gap: 2rem;
                list-style: none;
                align-items: center;
            }}
            
            .nav-links a {{
                color: var(--text-secondary);
                text-decoration: none;
                font-weight: 500;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                transition: var(--transition);
            }}
            
            .nav-links a:hover {{
                color: var(--text-primary);
                background: var(--background-secondary);
            }}
            
            .cta-button {{
                background: var(--primary-color);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: var(--border-radius);
                text-decoration: none;
                font-weight: 600;
                transition: var(--transition);
                box-shadow: var(--shadow-sm);
            }}
            
            .cta-button:hover {{
                background: var(--primary-hover);
                box-shadow: var(--shadow-md);
            }}
            
            /* Main Content */
            .main-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 2rem;
            }}
            
            .hero-section {{
                text-align: center;
                margin-bottom: 4rem;
            }}
            
            .hero-section h1 {{
                font-size: clamp(2.5rem, 5vw, 3.5rem);
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 1rem;
                line-height: 1.2;
            }}
            
            .hero-section .subtitle {{
                font-size: 1.125rem;
                color: var(--text-secondary);
                margin-bottom: 2rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.6;
            }}
            
            .features-row {{
                display: flex;
                justify-content: center;
                gap: 2rem;
                margin-bottom: 3rem;
                flex-wrap: wrap;
            }}
            
            .feature-badge {{
                background: var(--background-secondary);
                color: var(--text-secondary);
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                font-size: 0.875rem;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .feature-badge i {{
                color: var(--success-color);
            }}
            
            /* Upload Section */
            .upload-container {{
                background: var(--background);
                border: 2px solid var(--border-color);
                border-radius: var(--border-radius-lg);
                padding: 2rem;
                margin: 2rem auto;
                max-width: 800px;
                box-shadow: var(--shadow-md);
            }}
            
            .upload-area {{
                border: 2px dashed var(--border-color);
                padding: 3rem 2rem;
                text-align: center;
                border-radius: var(--border-radius);
                background: var(--background-secondary);
                transition: var(--transition);
                cursor: pointer;
            }}
            
            .upload-area:hover {{
                border-color: var(--primary-color);
                background: var(--background-tertiary);
            }}
            
            .upload-icon {{
                font-size: 3rem;
                margin-bottom: 1rem;
                color: var(--text-muted);
            }}
            
            .upload-area h3 {{
                font-size: 1.25rem;
                margin-bottom: 0.5rem;
                color: var(--text-primary);
                font-weight: 600;
            }}
            
            .upload-area p {{
                color: var(--text-secondary);
                margin-bottom: 1rem;
                font-size: 0.875rem;
            }}
            
            .btn-primary {{
                background: var(--primary-color);
                color: white;
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: var(--border-radius);
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: var(--transition);
                box-shadow: var(--shadow-sm);
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .btn-primary:hover {{
                background: var(--primary-hover);
                box-shadow: var(--shadow-md);
            }}
            
            .btn-secondary {{
                background: var(--background);
                color: var(--text-primary);
                padding: 0.75rem 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: var(--transition);
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .btn-secondary:hover {{
                background: var(--background-secondary);
                border-color: var(--border-hover);
            }}
            
            /* Loading and Results */
            .loading {{
                display: none;
                text-align: center;
                padding: 2rem;
                color: var(--text-secondary);
            }}
            
            .loading.active {{
                display: block;
            }}
            
            .spinner {{
                border: 3px solid var(--border-color);
                border-radius: 50%;
                border-top: 3px solid var(--primary-color);
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            .results {{
                background: var(--background-secondary);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                margin-top: 2rem;
                display: none;
            }}
            
            .results.active {{
                display: block;
                animation: slideIn 0.3s ease-out;
            }}
            
            @keyframes slideIn {{
                from {{
                    opacity: 0;
                    transform: translateY(10px);
                }}
                to {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            }}
            
            .results h3 {{
                color: var(--text-primary);
                margin-bottom: 1rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .results h3 i {{
                color: var(--success-color);
            }}
            
            .results-content {{
                background: var(--background);
                border: 1px solid var(--border-color);
                padding: 1rem;
                border-radius: var(--border-radius);
                color: var(--text-primary);
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 0.875rem;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
            }}
            
            /* Responsive Design */
            @media (max-width: 768px) {{
                .nav-container {{
                    padding: 0 1rem;
                }}
                
                .nav-links {{
                    display: none;
                }}
                
                .main-content {{
                    padding: 2rem 1rem;
                }}
                
                .hero-section h1 {{
                    font-size: 2rem;
                }}
                
                .features-row {{
                    flex-direction: column;
                    align-items: center;
                }}
                
                .upload-container {{
                    margin: 1rem;
                    padding: 1.5rem;
                }}
            }}
            
            /* Utility Classes */
            .text-center {{
                text-align: center;
            }}
            
            .mb-4 {{
                margin-bottom: 2rem;
            }}
            
            .hidden {{
                display: none;
            }}
            
            /* Enhanced Login Section */
            .login-container {{
                margin-top: 3rem;
                display: flex;
                justify-content: center;
                padding: 0 1rem;
            }}
            
            .login-card {{
                background: var(--background);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-lg);
                padding: 2rem;
                max-width: 400px;
                width: 100%;
                box-shadow: var(--shadow-lg);
                transition: var(--transition);
            }}
            
            .login-card:hover {{
                box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 10px 10px -5px rgb(0 0 0 / 0.04);
            }}
            
            .login-header {{
                text-align: center;
                margin-bottom: 2rem;
            }}
            
            .login-header i {{
                font-size: 3rem;
                color: var(--primary-color);
                margin-bottom: 1rem;
                display: block;
            }}
            
            .login-header h3 {{
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }}
            
            .login-header p {{
                color: var(--text-secondary);
                font-size: 0.875rem;
            }}
            
            .login-form {{
                margin-bottom: 1.5rem;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            .form-group label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: var(--text-primary);
                font-size: 0.875rem;
            }}
            
            .form-group input {{
                width: 100%;
                padding: 0.75rem 1rem;
                border: 2px solid var(--border-color);
                border-radius: var(--border-radius);
                font-size: 1rem;
                transition: var(--transition);
                background: var(--background);
            }}
            
            .form-group input:focus {{
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgb(37 99 235 / 0.1);
            }}
            
            .form-group input:hover {{
                border-color: var(--border-hover);
            }}
            
            .error-message {{
                background: #fef2f2;
                border: 1px solid #fecaca;
                color: #dc2626;
                padding: 0.75rem 1rem;
                border-radius: var(--border-radius);
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                animation: shake 0.5s ease-in-out;
            }}
            
            @keyframes shake {{
                0%, 100% {{ transform: translateX(0); }}
                25% {{ transform: translateX(-5px); }}
                75% {{ transform: translateX(5px); }}
            }}
            
            .login-btn {{
                width: 100%;
                background: var(--primary-color);
                color: white;
                padding: 0.875rem 1.5rem;
                border: none;
                border-radius: var(--border-radius);
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: var(--transition);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
            }}
            
            .login-btn:hover {{
                background: var(--primary-hover);
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }}
            
            .login-btn:active {{
                transform: translateY(0);
            }}
            
            .login-footer {{
                text-align: center;
                padding-top: 1.5rem;
                border-top: 1px solid var(--border-color);
            }}
            
            .login-footer p {{
                color: var(--text-secondary);
                font-size: 0.875rem;
                margin-bottom: 1rem;
            }}
            
            .signup-link {{
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--primary-color);
                text-decoration: none;
                font-weight: 600;
                font-size: 0.875rem;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                transition: var(--transition);
            }}
            
            .signup-link:hover {{
                background: var(--background-secondary);
                transform: translateY(-1px);
            }}
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">
                    <i class="fas fa-file-pdf"></i>
                    PDF Parser Pro
                </a>
                <ul class="nav-links">
                    <li><a href="/">Parse PDF</a></li>
                    <li><a href="/pricing">Pricing</a></li>
                    <li><a href="/docs">API Docs</a></li>
                </ul>
                <a href="/pricing" class="cta-button">Get Started</a>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Hero Section -->
            <section class="hero-section">
                <h1>AI-Powered PDF Processing</h1>
                <p class="subtitle">
                    Extract text, tables, and images from any PDF with intelligent 3-step fallback processing.
                    Fast, accurate, and cost-effective document processing for businesses.
                </p>
                
                <div class="features-row">
                    <div class="feature-badge">
                        <i class="fas fa-gift"></i>
                        10 Pages FREE
                    </div>
                    <div class="feature-badge">
                        <i class="fas fa-brain"></i>
                        Smart AI Processing
                    </div>
                    <div class="feature-badge">
                        <i class="fas fa-chart-line"></i>
                        99% Cost Savings
                    </div>
                    <div class="feature-badge">
                        <i class="fas fa-shield-alt"></i>
                        Enterprise Security
                    </div>
                </div>
            </section>

            <!-- Upload Section -->
            <section class="upload-container">
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    <div class="upload-icon">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <h3>Upload Your PDF - FREE</h3>
                    <p>Process up to 10 pages with full AI features • No registration required</p>
                    <input type="file" id="fileInput" style="display: none;" accept=".pdf" onchange="handleFileSelect(event)">
                </div>
                
                <!-- Login/Account Section -->
                <div id="account-section" style="margin-top: 2rem; text-align: center; display: none;">
                    <div style="background: var(--background-secondary); padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem;">
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Welcome back!</h4>
                        <p style="color: var(--text-secondary); font-size: 0.875rem;">You're logged in with unlimited processing</p>
                        <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1rem;">
                            <button onclick="showUsage()" class="btn-secondary" style="font-size: 0.875rem; padding: 0.5rem 1rem;">View Usage</button>
                            <button onclick="logout()" class="btn-secondary" style="font-size: 0.875rem; padding: 0.5rem 1rem;">Logout</button>
                        </div>
                    </div>
                </div>
                
                <!-- Enhanced Login Section -->
                <div id="login-section" class="login-container">
                    <div class="login-card">
                        <div class="login-header">
                            <i class="fas fa-user-circle"></i>
                            <h3>Welcome Back</h3>
                            <p>Sign in to access unlimited processing</p>
                        </div>
                        
                        <form class="login-form" onsubmit="quickLogin(event)">
                            <div class="form-group">
                                <label for="loginEmail">Email Address</label>
                                <input type="email" id="loginEmail" placeholder="Enter your email" required>
                            </div>
                            
                            <div class="form-group">
                                <label for="loginPassword">Password</label>
                                <input type="password" id="loginPassword" placeholder="Enter your password" required>
                            </div>
                            
                            <!-- Error Message Area -->
                            <div id="login-error" class="error-message" style="display: none;">
                                <i class="fas fa-exclamation-circle"></i>
                                <span id="login-error-text"></span>
                            </div>
                            
                            <button type="submit" class="login-btn">
                                <i class="fas fa-sign-in-alt"></i>
                                Sign In
                            </button>
                        </form>
                        
                        <div class="login-footer">
                            <p>Don't have an account?</p>
                            <a href="/pricing" class="signup-link">
                                <i class="fas fa-rocket"></i>
                                Get started for $6.99 CAD/month
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Processing your document with AI...</p>
                </div>
                
                <div class="results">
                    <h3><i class="fas fa-check-circle"></i> Extraction Complete</h3>
                    <div class="results-content" id="results-content"></div>
                </div>
            </section>
        </main>

        <script>
            // Check if user is logged in on page load
            window.addEventListener('load', function() {{
                const apiKey = localStorage.getItem('pdf_parser_api_key');
                const userEmail = localStorage.getItem('pdf_parser_email');
                
                if (apiKey && userEmail) {{
                    showLoggedInState();
                }}
            }});
            
            // File upload handling
            function handleFileSelect(event) {{
                const file = event.target.files[0];
                if (file && file.type === 'application/pdf') {{
                    uploadFile(file);
                }} else {{
                    alert('Please select a valid PDF file.');
                }}
            }}
            
            async function uploadFile(file) {{
                const loadingEl = document.querySelector('.loading');
                const resultsEl = document.querySelector('.results');
                const resultsContent = document.getElementById('results-content');
                
                // Show loading
                loadingEl.classList.add('active');
                resultsEl.classList.remove('active');
                
                try {{
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    // Add API key if user is logged in
                    const apiKey = localStorage.getItem('pdf_parser_api_key');
                    const headers = {{}};
                    if (apiKey) {{
                        headers['Authorization'] = `Bearer ${{apiKey}}`;
                    }}
                    
                    const response = await fetch('/parse/', {{
                        method: 'POST',
                        headers: headers,
                        body: formData
                    }});
                    
                    const result = await response.json();
                    
                    // Hide loading
                    loadingEl.classList.remove('active');
                    
                    if (result.success) {{
                        // Show results with user info
                        let displayResult = {{
                            success: result.success,
                            text: result.text,
                            pages_processed: result.pages_processed,
                            strategy_used: result.strategy_used,
                            user_info: result.user_info
                        }};
                        resultsContent.textContent = JSON.stringify(displayResult, null, 2);
                        resultsEl.classList.add('active');
                        
                        // Show upgrade prompt if free user hit limit
                        if (!result.user_info.authenticated && result.pages_processed >= 10) {{
                            showUpgradePrompt();
                        }}
                    }} else {{
                        // Handle free tier limit
                        if (result.detail && typeof result.detail === 'object') {{
                            showUpgradePrompt(result.detail);
                        }} else {{
                            alert('Error: ' + (result.detail || result.error || 'Processing failed'));
                        }}
                    }}
                }} catch (error) {{
                    loadingEl.classList.remove('active');
                    alert('Upload failed: ' + error.message);
                }}
            }}
            
            // Enhanced login functionality with error handling
            async function quickLogin(event) {{
                event.preventDefault(); // Prevent form submission
                
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPassword').value;
                const errorDiv = document.getElementById('login-error');
                const errorText = document.getElementById('login-error-text');
                const submitBtn = event.target.querySelector('button[type="submit"]');
                
                // Hide previous errors
                hideLoginError();
                
                // Basic validation
                if (!email || !password) {{
                    showLoginError('Please enter both email and password');
                    return;
                }}
                
                // Show loading state
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
                submitBtn.disabled = true;
                
                try {{
                    const response = await fetch('/auth/login', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{email: email, password: password}})
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        // Store user session
                        localStorage.setItem('pdf_parser_email', email);
                        localStorage.setItem('pdf_parser_logged_in', 'true');
                        
                        // Show success (brief)
                        submitBtn.innerHTML = '<i class="fas fa-check"></i> Success!';
                        submitBtn.style.background = 'var(--success-color)';
                        
                        // Transition to logged in state
                        setTimeout(() => {{
                            showLoggedInState();
                        }}, 1000);
                    }} else {{
                        showLoginError(result.message || 'Invalid email or password');
                    }}
                }} catch (error) {{
                    showLoginError('Connection error. Please try again.');
                    console.error('Login error:', error);
                }} finally {{
                    // Reset button after delay
                    setTimeout(() => {{
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                        submitBtn.style.background = '';
                    }}, 2000);
                }}
            }}
            
            // Show login error message
            function showLoginError(message) {{
                const errorDiv = document.getElementById('login-error');
                const errorText = document.getElementById('login-error-text');
                
                errorText.textContent = message;
                errorDiv.style.display = 'flex';
                
                // Auto-hide after 5 seconds
                setTimeout(hideLoginError, 5000);
            }}
            
            // Hide login error message
            function hideLoginError() {{
                const errorDiv = document.getElementById('login-error');
                errorDiv.style.display = 'none';
            }}
            
            // Show logged in state
            function showLoggedInState() {{
                document.getElementById('login-section').style.display = 'none';
                document.getElementById('account-section').style.display = 'block';
            }}
            
            // Logout
            function logout() {{
                localStorage.removeItem('pdf_parser_api_key');
                localStorage.removeItem('pdf_parser_email');
                document.getElementById('login-section').style.display = 'block';
                document.getElementById('account-section').style.display = 'none';
                alert('Logged out successfully');
            }}
            
            // Show usage info
            async function showUsage() {{
                const apiKey = localStorage.getItem('pdf_parser_api_key');
                if (!apiKey) return;
                
                try {{
                    const response = await fetch('/auth/me', {{
                        headers: {{'Authorization': `Bearer ${{apiKey}}`}}
                    }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        const usage = result.usage_info;
                        alert(`Usage This Month:
Pages Used: ${{usage.total_pages || 0}}
Plan: ${{result.subscription_tier}}
Total Cost: $${{usage.total_cost || 0}}`);
                    }}
                }} catch (error) {{
                    alert('Could not fetch usage info');
                }}
            }}
            
            // Show upgrade prompt
            function showUpgradePrompt(details) {{
                const message = details ? details.message : 'Upgrade for unlimited processing!';
                const upgradeUrl = details ? details.upgrade_url : '/pricing';
                
                if (confirm(message + '\\n\\nGo to pricing page?')) {{
                    window.location.href = upgradeUrl;
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
                uploadArea.style.borderColor = 'var(--primary-color)';
                uploadArea.style.background = 'var(--background-tertiary)';
            }}
            
            function unhighlight(e) {{
                uploadArea.style.borderColor = 'var(--border-color)';
                uploadArea.style.background = 'var(--background-secondary)';
            }}
            
            uploadArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {{
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > 0) {{
                    const file = files[0];
                    if (file.type === 'application/pdf') {{
                        uploadFile(file);
                    }} else {{
                        alert('Please drop a valid PDF file.');
                    }}
                }}
            }}
        </script>
    </body>
    </html>"""
    return html_content

@app.get("/pricing", response_class=HTMLResponse)
def pricing_page():
    """Pricing page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pricing - PDF Parser Pro</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-color: #2563eb;
                --primary-hover: #1d4ed8;
                --secondary-color: #6b7280;
                --success-color: #059669;
                --background: #ffffff;
                --background-secondary: #f8fafc;
                --background-tertiary: #f1f5f9;
                --text-primary: #1f2937;
                --text-secondary: #6b7280;
                --text-muted: #9ca3af;
                --border-color: #e5e7eb;
                --border-hover: #d1d5db;
                --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
                --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
                --border-radius: 8px;
                --border-radius-lg: 12px;
                --transition: all 0.2s ease-in-out;
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                line-height: 1.6;
                color: var(--text-primary);
                background: var(--background);
                min-height: 100vh;
            }
            
            /* Navigation */
            .navbar {
                position: sticky;
                top: 0;
                z-index: 1000;
                background: var(--background);
                border-bottom: 1px solid var(--border-color);
                padding: 1rem 0;
                box-shadow: var(--shadow-sm);
            }
            
            .nav-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--text-primary);
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .logo i {
                font-size: 1.5rem;
                color: var(--primary-color);
            }
            
            .nav-links {
                display: flex;
                gap: 2rem;
                list-style: none;
                align-items: center;
            }
            
            .nav-links a {
                color: var(--text-secondary);
                text-decoration: none;
                font-weight: 500;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                transition: var(--transition);
            }
            
            .nav-links a:hover, .nav-links a.active {
                color: var(--text-primary);
                background: var(--background-secondary);
            }
            
            .cta-button {
                background: var(--primary-color);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: var(--border-radius);
                text-decoration: none;
                font-weight: 600;
                transition: var(--transition);
                box-shadow: var(--shadow-sm);
            }
            
            .cta-button:hover {
                background: var(--primary-hover);
                box-shadow: var(--shadow-md);
            }
            
            /* Main Content */
            .main-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 3rem 2rem;
            }
            
            .pricing-header {
                text-align: center;
                margin-bottom: 4rem;
            }
            
            .pricing-header h1 {
                font-size: clamp(2.5rem, 5vw, 3.5rem);
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            .pricing-header .subtitle {
                font-size: 1.125rem;
                color: var(--text-secondary);
                margin-bottom: 2rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.6;
            }
            
            .pricing-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 2rem;
                margin-bottom: 3rem;
            }
            
            .pricing-card {
                background: var(--background);
                border: 2px solid var(--border-color);
                border-radius: var(--border-radius-lg);
                padding: 2rem;
                position: relative;
                transition: var(--transition);
            }
            
            .pricing-card:hover {
                border-color: var(--primary-color);
                box-shadow: var(--shadow-lg);
            }
            
            .pricing-card.popular {
                border-color: var(--primary-color);
                box-shadow: var(--shadow-md);
            }
            
            .pricing-card.popular::before {
                content: 'Most Popular';
                position: absolute;
                top: -1rem;
                left: 50%;
                transform: translateX(-50%);
                background: var(--primary-color);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                font-size: 0.875rem;
                font-weight: 600;
            }
            
            .plan-name {
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }
            
            .plan-price {
                font-size: 3rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }
            
            .plan-price .currency {
                font-size: 1.5rem;
                vertical-align: top;
            }
            
            .plan-price .period {
                font-size: 1rem;
                font-weight: 400;
                color: var(--text-secondary);
            }
            
            .plan-description {
                color: var(--text-secondary);
                margin-bottom: 2rem;
                font-size: 0.875rem;
            }
            
            .plan-features {
                list-style: none;
                margin-bottom: 2rem;
            }
            
            .plan-features li {
                padding: 0.5rem 0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-secondary);
            }
            
            .plan-features li i {
                color: var(--success-color);
                width: 1rem;
            }
            
            .plan-button {
                width: 100%;
                background: var(--primary-color);
                color: white;
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: var(--border-radius);
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: var(--transition);
                text-decoration: none;
                display: block;
                text-align: center;
            }
            
            .plan-button:hover {
                background: var(--primary-hover);
            }
            
            .plan-button.secondary {
                background: var(--background);
                color: var(--text-primary);
                border: 2px solid var(--border-color);
            }
            
            .plan-button.secondary:hover {
                background: var(--background-secondary);
                border-color: var(--border-hover);
            }
            
            /* FAQ Section */
            .faq-section {
                margin-top: 4rem;
                background: var(--background-secondary);
                padding: 3rem;
                border-radius: var(--border-radius-lg);
            }
            
            .faq-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .faq-header h2 {
                font-size: 2rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }
            
            .faq-grid {
                display: grid;
                gap: 1.5rem;
                max-width: 800px;
                margin: 0 auto;
            }
            
            .faq-item {
                background: var(--background);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
            }
            
            .faq-question {
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }
            
            .faq-answer {
                color: var(--text-secondary);
                line-height: 1.6;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .nav-container {
                    padding: 0 1rem;
                }
                
                .nav-links {
                    display: none;
                }
                
                .main-content {
                    padding: 2rem 1rem;
                }
                
                .pricing-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar">
            <div class="nav-container">
                <a href="/" class="logo">
                    <i class="fas fa-file-pdf"></i>
                    PDF Parser Pro
                </a>
                <ul class="nav-links">
                    <li><a href="/">Parse PDF</a></li>
                    <li><a href="/pricing" class="active">Pricing</a></li>
                    <li><a href="/docs">API Docs</a></li>
                </ul>
                <a href="/" class="cta-button">Try Now</a>
            </div>
        </nav>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Pricing Header -->
            <section class="pricing-header">
                <h1>Simple, Transparent Pricing</h1>
                <p class="subtitle">
                    Choose the plan that fits your document processing needs. 
                    Pay only for what you use with our intelligent processing system.
                </p>
            </section>

            <!-- Pricing Grid -->
            <section class="pricing-grid">
                <div class="pricing-card">
                    <div class="plan-name">Student</div>
                    <div class="plan-price">
                        <span class="currency">$</span>6.99
                        <span class="period">/month CAD</span>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-top: 0.25rem;">Plus applicable taxes</div>
                    <div class="plan-description">Perfect for students and light usage</div>
                    <ul class="plan-features">
                        <li><i class="fas fa-check"></i> 500 pages/month</li>
                        <li><i class="fas fa-check"></i> AI-powered processing</li>
                        <li><i class="fas fa-check"></i> All advanced features</li>
                        <li><i class="fas fa-check"></i> Email support</li>
                    </ul>
                    <button onclick="createCheckout('student')" class="plan-button secondary">Get Started</button>
                </div>

                <div class="pricing-card popular">
                    <div class="plan-name">Growth</div>
                    <div class="plan-price">
                        <span class="currency">$</span>26.99
                        <span class="period">/month CAD</span>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-top: 0.25rem;">Plus applicable taxes</div>
                    <div class="plan-description">Great for growing businesses</div>
                    <ul class="plan-features">
                        <li><i class="fas fa-check"></i> 2,500 pages/month</li>
                        <li><i class="fas fa-check"></i> Priority processing</li>
                        <li><i class="fas fa-check"></i> Advanced analytics</li>
                        <li><i class="fas fa-check"></i> Chat support</li>
                        <li><i class="fas fa-check"></i> API access</li>
                    </ul>
                    <button onclick="createCheckout('growth')" class="plan-button">Get Started</button>
                </div>

                <div class="pricing-card">
                    <div class="plan-name">Business</div>
                    <div class="plan-price">
                        <span class="currency">$</span>109.99
                        <span class="period">/month CAD</span>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-top: 0.25rem;">Plus applicable taxes</div>
                    <div class="plan-description">For established businesses with high volume</div>
                    <ul class="plan-features">
                        <li><i class="fas fa-check"></i> 10,000 pages/month</li>
                        <li><i class="fas fa-check"></i> Faster processing queues</li>
                        <li><i class="fas fa-check"></i> Performance dashboard</li>
                        <li><i class="fas fa-check"></i> Phone + chat support</li>
                        <li><i class="fas fa-check"></i> Full API access</li>
                        <li><i class="fas fa-check"></i> Custom integrations</li>
                    </ul>
                    <button onclick="createCheckout('business')" class="plan-button">Get Started</button>
                </div>
            </section>

            <!-- FAQ Section -->
            <section class="faq-section">
                <div class="faq-header">
                    <h2>Frequently Asked Questions</h2>
                </div>
                <div class="faq-grid">
                    <div class="faq-item">
                        <div class="faq-question">How does the 3-step fallback system work?</div>
                        <div class="faq-answer">We start with fast library-based processing. If that doesn't meet quality standards, we fall back to AI processing. As a final step, we use advanced OCR for the most challenging documents.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">What happens if I exceed my monthly page limit?</div>
                        <div class="faq-answer">You'll be charged a small overage fee per additional page. Student: $0.01/page, Growth/Business: $0.008/page, Enterprise: $0.006/page.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">Do you store my documents?</div>
                        <div class="faq-answer">No, we have a zero data retention policy. Your documents are processed and immediately deleted from our servers for maximum security.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">Can I cancel anytime?</div>
                        <div class="faq-answer">Yes, you can cancel your subscription at any time. You'll continue to have access until the end of your current billing period.</div>
                    </div>
                </div>
            </section>
        </main>
        
        <script>
            // Stripe Checkout Integration
            async function createCheckout(planType) {{
                const button = event.target;
                const originalText = button.textContent;
                
                // Show loading state
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                button.disabled = true;
                
                try {{
                    const response = await fetch('/create-checkout-session/', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            plan_type: planType,
                            customer_email: '', // Will be collected by Stripe
                            success_url: window.location.origin + '/success?session_id={{CHECKOUT_SESSION_ID}}',
                            cancel_url: window.location.origin + '/pricing'
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        // Redirect to Stripe checkout
                        window.location.href = data.checkout_url;
                    }} else {{
                        alert('Error creating checkout session: ' + (data.error || 'Please try again'));
                        console.error('Checkout error:', data);
                    }}
                }} catch (error) {{
                    alert('Connection error. Please try again.');
                    console.error('Network error:', error);
                }} finally {{
                    // Reset button
                    button.innerHTML = originalText;
                    button.disabled = false;
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/auth/register")
async def register_user(registration: UserRegistration):
    """Register a new user"""
    if not auth_system:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        # Check if user already exists
        existing_customer = auth_system.get_customer_by_email(registration.email)
        if existing_customer:
            return {
                "success": False,
                "error": "User already exists",
                "api_key": existing_customer.api_key
            }
        
        # Map plan type to subscription tier
        from api_key_manager import SubscriptionTier
        tier_map = {
            "student": SubscriptionTier.STUDENT,
            "growth": SubscriptionTier.GROWTH,
            "business": SubscriptionTier.BUSINESS
        }
        
        subscription_tier = tier_map.get(registration.plan_type.lower(), SubscriptionTier.FREE)
        
        # Create customer with password
        customer = auth_system.create_customer(
            email=registration.email,
            password=registration.password,
            subscription_tier=subscription_tier
        )
        
        # Initialize usage tracking for the customer
        if usage_tracker:
            # Get plan details for usage limits
            from datetime import datetime, timedelta
            plan_details = {
                "student": {"pages": 500, "rate": 0.01},
                "growth": {"pages": 2500, "rate": 0.008},
                "business": {"pages": 10000, "rate": 0.008}
            }
            
            plan = plan_details.get(registration.plan_type.lower(), {"pages": 100, "rate": 0.02})
            
            # Set billing cycle (monthly)
            cycle_start = datetime.now()
            cycle_end = cycle_start + timedelta(days=30)
            
            usage_tracker.update_user_limits(
                user_id=customer.customer_id,
                subscription_id="",  # Will be set when Stripe subscription is created
                plan_type=registration.plan_type.lower(),
                pages_included=plan["pages"],
                overage_rate=plan["rate"],
                billing_cycle_start=cycle_start,
                billing_cycle_end=cycle_end
            )
        
        return {
            "success": True,
            "customer_id": customer.customer_id,
            "email": customer.email,
            "subscription_tier": customer.subscription_tier.value,
            "message": "Account created successfully! You can now login with your email and password."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login")
async def login_user(login: UserLogin):
    """Verify user credentials and return user info"""
    if not auth_system:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        # Verify email and password
        customer = auth_system.authenticate_password(login.email, login.password)
        if not customer:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Get usage info if available
        usage_info = {}
        if usage_tracker:
            usage_info = usage_tracker.get_monthly_usage(customer.customer_id)
        
        return {
            "success": True,
            "customer_id": customer.customer_id,
            "email": customer.email,
            "subscription_tier": customer.subscription_tier.value,
            "usage_info": usage_info,
            "message": "Login successful"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    
    # Get usage info
    usage_info = {}
    if usage_tracker:
        usage_info = usage_tracker.get_monthly_usage(current_user.customer_id)
    
    return {
        "success": True,
        "customer_id": current_user.customer_id,
        "email": current_user.email,
        "subscription_tier": current_user.subscription_tier.value,
        "api_key": current_user.api_key,
        "usage_info": usage_info
    }

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
    current_user = Depends(get_current_user_optional)
):
    """Revolutionary PDF parsing with 3-step fallback system and 99% cost optimization"""
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    start_time = time.time()
    pages_processed = 0
    ai_used = False
    
    # Determine user info and limits
    user_id = None
    subscription_tier = "free"
    if current_user:
        user_id = current_user.customer_id
        subscription_tier = current_user.subscription_tier.value
    
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
        
        # Check usage limits and permissions
        if current_user and usage_tracker:
            # Authenticated user - check their limits
            usage_check = usage_tracker.check_user_limits(user_id, pages_processed)
            if not usage_check.get("success", True):
                raise HTTPException(
                    status_code=429, 
                    detail=f"Usage limit exceeded. {usage_check.get('error', 'Please upgrade your plan or wait for next billing cycle.')}"
                )
        elif not current_user:
            # Unauthenticated user - free tier with generous limits to drive conversions
            if pages_processed > 10:  # Free tier: max 10 pages per request
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "Free tier limited to 10 pages per document",
                        "message": "Loved the results? Get 500 more pages for just $4.99/month!",
                        "upgrade_url": "/pricing",
                        "register_url": "/auth/register",
                        "pages_processed": pages_processed,
                        "pages_limit": 10
                    }
                )
            # Give free users FULL AI features to showcase quality
            # This creates the "wow factor" that drives conversions
        
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
                elif not current_user:
                    # Track free tier usage (for analytics)
                    print(f"Free tier usage: {pages_processed} pages processed")
                
                # Convert SmartParseResult to API response
                processing_time = time.time() - start_time
                
                # Get updated usage info
                usage_info = {}
                if current_user and usage_tracker:
                    usage_info = usage_tracker.get_monthly_usage(user_id)
                
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
                    "user_info": {
                        "authenticated": current_user is not None,
                        "subscription_tier": subscription_tier,
                        "user_id": user_id,
                        "usage_info": usage_info
                    },
                    "metadata": {
                        "file_size": os.path.getsize(tmp_path),
                        "strategy_requested": strategy,
                        "advanced_features": current_user is not None,
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
            "/pricing", 
            "/health-check/",
            "/parse/",
            "/api/info",
            "/auth/register",
            "/auth/login", 
            "/auth/me",
            "/create-checkout-session/",
            "/customer-portal/",
            "/stripe-webhook/",
            "/usage/{user_id}",
            "/usage/{user_id}/history",
            "/usage/track/",
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