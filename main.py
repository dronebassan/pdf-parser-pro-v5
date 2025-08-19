from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pdfplumber
import fitz  # PyMuPDF
from tempfile import NamedTemporaryFile
import os
import time
import stripe  # Re-enabled for production billing
from typing import Optional, Dict, Any
import json
from pydantic import BaseModel

# Initialize FastAPI
app = FastAPI(
    title="PDF Parser Pro API",
    description="AI-powered PDF processing with smart optimization",
    version="2.0.1-js-fixed"
)

# Add healthcheck endpoint for Railway
@app.get("/health")
async def health_check():
    """Railway healthcheck endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

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
    print("🔍 Attempting to import SmartParser...")
    from smart_parser import SmartParser
    smart_parser = SmartParser()
    print("✅ Smart Parser initialized with revolutionary 3-step fallback system")
except ImportError as ie:
    print(f"⚠️  SmartParser import failed: {ie}")
    smart_parser = None
except Exception as e:
    print(f"❌ Smart parser failed: {e}")
    smart_parser = None

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

# Initialize Stripe and Usage Tracking - SAFE IMPORT
stripe_service = None
usage_tracker = None
PlanType = None

try:
    print("🔍 Attempting to import stripe_service...")
    from stripe_service import stripe_service, PlanType
    print("✅ Stripe service imported successfully")
except ImportError as ie:
    print(f"⚠️  Stripe service import failed: {ie}")
    stripe_service = None
except Exception as e:
    print(f"❌ Stripe service initialization failed: {e}")
    stripe_service = None

try:
    print("🔍 Attempting to import usage_tracker...")
    from usage_tracker import usage_tracker
    print("✅ Usage tracker imported successfully")
except ImportError as ie:
    print(f"⚠️  Usage tracker import failed: {ie}")
    usage_tracker = None
except Exception as e:
    print(f"❌ Usage tracker initialization failed: {e}")
    usage_tracker = None

# Initialize Authentication System
auth_system = None
try:
    from auth_system import AuthSystem
    auth_system = AuthSystem(secret_key="pdf-parser-jwt-secret-2024")
    print("✅ Authentication system initialized successfully")
except Exception as e:
    print(f"❌ Authentication system failed: {e}")
    print(f"Error details: {type(e).__name__}: {str(e)}")
    # Create a complete fallback auth system
    try:
        import jwt
        import hashlib
        import secrets
        import time
        import bcrypt
        from typing import Optional
        from dataclasses import dataclass
        
        # Define subscription tiers directly
        class SubscriptionTier:
            FREE = "free"
            STUDENT = "student"
            GROWTH = "growth"
            BUSINESS = "business"
        
        @dataclass
        class Customer:
            customer_id: str
            email: str
            password_hash: str
            api_key: str
            subscription_tier: str
            created_at: int
            email_verified: bool = False
            last_ip: str = ""
            last_login: int = 0
            verification_code: str = ""
            subscription_active: bool = True
        
        class SimpleAuthSystem:
            def __init__(self, secret_key: str):
                self.secret_key = secret_key
                self.db_file = "users.json"
                self.customers = self._load_customers()
                print("✅ Using simplified authentication system with persistent storage")
            
            def _load_customers(self):
                """Load customers from JSON file with migration support"""
                try:
                    import json
                    import os
                    if os.path.exists(self.db_file):
                        with open(self.db_file, 'r') as f:
                            data = json.load(f)
                            customers = {}
                            migrated_count = 0
                            
                            for email, customer_data in data.items():
                                # MIGRATION LOGIC: Add missing fields for existing accounts
                                original_data = customer_data.copy()
                                
                                # Add new security fields with sensible defaults
                                if 'last_login' not in customer_data:
                                    customer_data['last_login'] = int(time.time())  # Set to now for existing users
                                    migrated_count += 1
                                
                                if 'subscription_active' not in customer_data:
                                    # Existing users are active (they already paid/registered)
                                    customer_data['subscription_active'] = True
                                    migrated_count += 1
                                
                                if 'email_verified' not in customer_data:
                                    # Grandfather existing accounts as verified (they already paid/registered)
                                    customer_data['email_verified'] = True
                                    migrated_count += 1
                                
                                if 'last_ip' not in customer_data:
                                    customer_data['last_ip'] = ""
                                
                                # Remove old expiration fields if they exist
                                customer_data.pop('api_key_expires_at', None)
                                customer_data.pop('session_expires_at', None)
                                
                                if 'verification_code' not in customer_data:
                                    customer_data['verification_code'] = ""
                                
                                # Create customer object
                                customers[email] = Customer(**customer_data)
                            
                            if migrated_count > 0:
                                print(f"🔄 Migrated {migrated_count} existing user accounts to new security schema")
                                # Save migrated data back to file
                                self.customers = customers
                                self._save_customers()
                            
                            print(f"📂 Loaded {len(customers)} users from {self.db_file}")
                            return customers
                except Exception as e:
                    print(f"⚠️  Could not load customers: {e}")
                    print(f"Error details: {type(e).__name__}: {str(e)}")
                return {}
            
            def _save_customers(self):
                """Save customers to JSON file"""
                try:
                    import json
                    data = {}
                    for email, customer in self.customers.items():
                        data[email] = {
                            'customer_id': customer.customer_id,
                            'email': customer.email,
                            'password_hash': customer.password_hash,
                            'api_key': customer.api_key,
                            'subscription_tier': customer.subscription_tier,
                            'created_at': customer.created_at,
                            'email_verified': customer.email_verified,
                            'last_ip': customer.last_ip,
                            'last_login': customer.last_login,
                            'verification_code': customer.verification_code,
                            'subscription_active': customer.subscription_active
                        }
                    with open(self.db_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"💾 Saved {len(self.customers)} users to {self.db_file}")
                except Exception as e:
                    print(f"❌ Could not save customers: {e}")
            
            def generate_api_key(self) -> str:
                """Generate API key (never expires - tied to subscription status)"""
                return f"pdf_parser_{secrets.token_urlsafe(32)}"
            
            def generate_verification_code(self) -> str:
                """Generate 6-digit verification code"""
                return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
            
            def hash_password(self, password: str) -> str:
                return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            def verify_password(self, password: str, hashed: str) -> bool:
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            
            def create_customer(self, email: str, password: str, subscription_tier = SubscriptionTier.FREE, ip_address: str = ""):
                if self.get_customer_by_email(email):
                    raise Exception("Email already registered")
                
                # Check for too many accounts from same IP (prevent farming)
                accounts_from_ip = sum(1 for c in self.customers.values() if c.last_ip == ip_address)
                if accounts_from_ip >= 3 and subscription_tier == SubscriptionTier.FREE:
                    raise Exception("Too many accounts created from this location. Please contact support.")
                
                customer_id = hashlib.md5(email.encode()).hexdigest()
                api_key = self.generate_api_key()
                password_hash = self.hash_password(password)
                verification_code = self.generate_verification_code()
                
                customer = Customer(
                    customer_id=customer_id,
                    email=email,
                    password_hash=password_hash,
                    api_key=api_key,
                    subscription_tier=subscription_tier,
                    created_at=int(time.time()),
                    email_verified=False,
                    last_ip=ip_address,
                    last_login=int(time.time()),
                    verification_code=verification_code,
                    subscription_active=True
                )
                
                self.customers[email] = customer
                self._save_customers()  # Save to disk
                return customer
            
            def authenticate_password(self, email: str, password: str) -> Optional[Customer]:
                customer = self.customers.get(email)
                if customer and self.verify_password(password, customer.password_hash):
                    return customer
                return None
            
            def get_customer_by_email(self, email: str) -> Optional[Customer]:
                return self.customers.get(email)
            
            def get_customer_by_api_key(self, api_key: str, ip_address: str = "") -> Optional[Customer]:
                """Get customer by API key with security checks"""
                for customer in self.customers.values():
                    if customer.api_key == api_key:
                        # Auto-renewal system: Check subscription and activity status
                        current_time = time.time()
                        
                        # Check if subscription is active
                        if hasattr(customer, 'subscription_active') and not customer.subscription_active:
                            print(f"🚫 Subscription inactive for {customer.email}")
                            return None
                        
                        # Check for inactivity (6 months = security measure)
                        if hasattr(customer, 'last_login'):
                            six_months_ago = current_time - (6 * 30 * 24 * 60 * 60)  # 6 months
                            if customer.last_login < six_months_ago:
                                print(f"🚫 Account inactive for 6+ months: {customer.email}")
                                return None
                        
                        # AUTO-RENEWAL: Update last login time (keeps account active)
                        customer.last_login = int(current_time)
                        self._save_customers()  # Save updated login time
                        
                        # Check if email verified (required for paid features)
                        if hasattr(customer, 'email_verified') and customer.subscription_tier != SubscriptionTier.FREE:
                            if not customer.email_verified:
                                print(f"🚫 Email not verified for paid user {customer.email}")
                                return None
                        
                        # IP validation for high-value accounts
                        if ip_address and hasattr(customer, 'last_ip') and customer.subscription_tier in [SubscriptionTier.GROWTH, SubscriptionTier.BUSINESS]:
                            if customer.last_ip and customer.last_ip != ip_address:
                                # Allow IP change but log it
                                print(f"⚠️  IP change detected for {customer.email}: {customer.last_ip} -> {ip_address}")
                                customer.last_ip = ip_address
                                self._save_customers()
                        
                        return customer
                return None
            
            def upgrade_customer(self, email: str, new_tier: str) -> bool:
                """Upgrade customer subscription tier with validation"""
                customer = self.get_customer_by_email(email)
                if customer:
                    # Validate tier progression (prevent downgrade exploitation)
                    tier_order = [SubscriptionTier.FREE, SubscriptionTier.STUDENT, SubscriptionTier.GROWTH, SubscriptionTier.BUSINESS]
                    current_index = tier_order.index(customer.subscription_tier) if customer.subscription_tier in tier_order else 0
                    new_index = tier_order.index(new_tier) if new_tier in tier_order else 0
                    
                    # Only allow upgrades or same tier (no downgrades without verification)
                    if new_index >= current_index or customer.email_verified:
                        customer.subscription_tier = new_tier
                        # Activate subscription for paid upgrades
                        if new_tier != SubscriptionTier.FREE:
                            customer.subscription_active = True
                            customer.last_login = int(time.time())  # Reset activity timer
                        self._save_customers()  # Save to disk
                        return True
                    else:
                        print(f"🚫 Tier downgrade blocked for unverified user: {email}")
                        return False
                return False
            
            def verify_email(self, email: str, verification_code: str) -> bool:
                """Verify email with code"""
                customer = self.get_customer_by_email(email)
                if customer and hasattr(customer, 'verification_code'):
                    if customer.verification_code == verification_code:
                        customer.email_verified = True
                        customer.verification_code = ""  # Clear code
                        self._save_customers()
                        print(f"✅ Email verified for {email}")
                        return True
                print(f"🚫 Invalid verification code for {email}")
                return False
            
            def deactivate_subscription(self, email: str) -> bool:
                """Deactivate subscription (cancellation/non-payment)"""
                customer = self.get_customer_by_email(email)
                if customer:
                    customer.subscription_active = False
                    self._save_customers()
                    print(f"📴 Subscription deactivated for {email}")
                    return True
                return False
            
            def reactivate_subscription(self, email: str) -> bool:
                """Reactivate subscription (payment received)"""
                customer = self.get_customer_by_email(email)
                if customer:
                    customer.subscription_active = True
                    customer.last_login = int(time.time())  # Reset activity
                    self._save_customers()
                    print(f"✅ Subscription reactivated for {email}")
                    return True
                return False
        
        auth_system = SimpleAuthSystem(secret_key="pdf-parser-jwt-secret-2024")
    except Exception as fallback_error:
        print(f"❌ Fallback auth system also failed: {fallback_error}")
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
async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user with IP validation"""
    if not credentials or not auth_system:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide API key in Authorization header."
        )
    
    try:
        # Get client IP for security validation
        client_ip = request.client.host
        
        # Get customer by API key with IP validation
        customer = auth_system.get_customer_by_api_key(credentials.credentials, client_ip)
        if not customer:
            raise HTTPException(status_code=401, detail="Invalid or expired API key")
        return customer
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# Simple session storage (in production, use Redis or database)
active_sessions = {}

# Rate limiting storage (user_id -> list of timestamps)
user_upload_history = {}

# AI usage tracking (user_id -> count this month)
monthly_ai_usage = {}

# Optional authentication for free tier
async def get_current_user_optional(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user, but allow unauthenticated access for free tier"""
    if not auth_system:
        return None
    
    # Check for session-based auth first (for web UI)
    session_token = request.cookies.get("session_token")
    if session_token and session_token in active_sessions:
        email = active_sessions[session_token]
        customer = auth_system.get_customer_by_email(email)
        if customer:
            return customer
    
    # Fallback to API key auth (for API usage)
    if credentials:
        try:
            client_ip = request.client.host
            customer = auth_system.get_customer_by_api_key(credentials.credentials, client_ip)
            return customer
        except:
            pass
    
    return None

@app.get("/", response_class=HTMLResponse)
def home():
    """Home page with PDF upload interface"""
    # Check if advanced features are available
    advanced_available = all(services_status.values())
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Parser Pro - AI Document Processing</title>
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
                padding: 1.5rem 0;
                box-shadow: var(--shadow-sm);
            }
            
            .nav-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: grid;
                grid-template-columns: 1fr 2fr 1fr;
                align-items: center;
                min-height: 60px;
                gap: 2rem;
            }
            
            .logo {
                font-size: 1.75rem;
                font-weight: 700;
                color: var(--text-primary);
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .logo i {
                font-size: 1.75rem;
                color: var(--primary-color);
            }
            
            .nav-links {
                display: flex;
                gap: 2.5rem;
                list-style: none;
                align-items: center;
                justify-content: center;
            }
            
            .nav-links a {
                color: var(--text-secondary);
                text-decoration: none;
                font-weight: 500;
                font-size: 1.05rem;
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                transition: var(--transition);
            }
            
            .nav-links a:hover {
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
            
            .hero-section {
                text-align: center;
                margin-bottom: 4rem;
            }
            
            .hero-section h1 {
                font-size: clamp(2.5rem, 5vw, 3.5rem);
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            .hero-section .subtitle {
                font-size: 1.125rem;
                color: var(--text-secondary);
                margin-bottom: 2rem;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.6;
            }
            
            .features-row {
                display: flex;
                justify-content: center;
                gap: 2rem;
                margin-bottom: 3rem;
                flex-wrap: wrap;
            }
            
            .feature-badge {
                background: var(--background-secondary);
                color: var(--text-secondary);
                padding: 0.5rem 1rem;
                border-radius: var(--border-radius);
                font-size: 0.875rem;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .feature-badge i {
                color: var(--success-color);
            }
            
            /* Upload Section */
            .upload-container {
                background: var(--background);
                border: 2px solid var(--border-color);
                border-radius: var(--border-radius-lg);
                padding: 2rem;
                margin: 2rem auto;
                max-width: 800px;
                box-shadow: var(--shadow-md);
            }
            
            .upload-area {
                border: 2px dashed var(--border-color);
                padding: 3rem 2rem;
                text-align: center;
                border-radius: var(--border-radius);
                background: var(--background-secondary);
                transition: var(--transition);
                cursor: pointer;
            }
            
            .upload-area:hover {
                border-color: var(--primary-color);
                background: var(--background-tertiary);
            }
            
            .upload-icon {
                font-size: 3rem;
                margin-bottom: 1rem;
                color: var(--text-muted);
            }
            
            .upload-area h3 {
                font-size: 1.25rem;
                margin-bottom: 0.5rem;
                color: var(--text-primary);
                font-weight: 600;
            }
            
            .upload-area p {
                color: var(--text-secondary);
                margin-bottom: 1rem;
                font-size: 0.875rem;
            }
            
            .btn-primary {
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
            }
            
            .btn-primary:hover {
                background: var(--primary-hover);
                box-shadow: var(--shadow-md);
            }
            
            .btn-secondary {
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
            }
            
            .btn-secondary:hover {
                background: var(--background-secondary);
                border-color: var(--border-hover);
            }
            
            /* Loading and Results */
            .loading {
                display: none;
                text-align: center;
                padding: 2rem;
                color: var(--text-secondary);
            }
            
            .loading.active {
                display: block;
            }
            
            .spinner {
                border: 3px solid var(--border-color);
                border-radius: 50%;
                border-top: 3px solid var(--primary-color);
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .results {
                background: var(--background-secondary);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                margin-top: 2rem;
                display: none;
            }
            
            .results.active {
                display: block;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .results h3 {
                color: var(--text-primary);
                margin-bottom: 1rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .results h3 i {
                color: var(--success-color);
            }
            
            .results-content {
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
            }
            
            /* Responsive Design */
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
                
                .hero-section h1 {
                    font-size: 2rem;
                }
                
                .features-row {
                    flex-direction: column;
                    align-items: center;
                }
                
                .upload-container {
                    margin: 1rem;
                    padding: 1.5rem;
                }
            }
            
            /* Utility Classes */
            .text-center {
                text-align: center;
            }
            
            .mb-4 {
                margin-bottom: 2rem;
            }
            
            .hidden {
                display: none;
            }
            
            /* Enhanced Login Section */
            .login-container {
                margin-top: 3rem;
                display: flex;
                justify-content: center;
                padding: 0 1rem;
            }
            
            .login-card {
                background: var(--background);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius-lg);
                padding: 2rem;
                max-width: 400px;
                width: 100%;
                box-shadow: var(--shadow-lg);
                transition: var(--transition);
            }
            
            .login-card:hover {
                box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 10px 10px -5px rgb(0 0 0 / 0.04);
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .login-header i {
                font-size: 3rem;
                color: var(--primary-color);
                margin-bottom: 1rem;
                display: block;
            }
            
            .login-header h3 {
                font-size: 1.75rem;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }
            
            .login-header p {
                color: var(--text-secondary);
                font-size: 0.875rem;
            }
            
            .login-form {
                margin-bottom: 1.5rem;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: var(--text-primary);
                font-size: 0.875rem;
            }
            
            .form-group input {
                width: 100%;
                padding: 0.75rem 1rem;
                border: 2px solid var(--border-color);
                border-radius: var(--border-radius);
                font-size: 1rem;
                transition: var(--transition);
                background: var(--background);
            }
            
            .form-group input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgb(37 99 235 / 0.1);
            }
            
            .form-group input:hover {
                border-color: var(--border-hover);
            }
            
            .error-message {
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
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            /* Toast Notification Styles */
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border-radius: 8px;
                padding: 1rem 1.25rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                border-left: 4px solid var(--primary-color);
                z-index: 10000;
                max-width: 400px;
                transform: translateX(400px);
                transition: transform 0.3s ease-in-out;
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }
            
            .toast.show {
                transform: translateX(0);
            }
            
            .toast.error {
                border-left-color: #dc2626;
                background: #fef2f2;
            }
            
            .toast.success {
                border-left-color: #16a34a;
                background: #f0fdf4;
            }
            
            .toast.warning {
                border-left-color: #ea580c;
                background: #fff7ed;
            }
            
            .toast-content {
                flex: 1;
            }
            
            .toast-title {
                font-weight: 600;
                font-size: 0.875rem;
                margin-bottom: 0.25rem;
            }
            
            .toast-message {
                font-size: 0.8rem;
                color: #6b7280;
                line-height: 1.4;
            }
            
            .toast-close {
                background: none;
                border: none;
                font-size: 1.25rem;
                cursor: pointer;
                color: #9ca3af;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .toast-close:hover {
                color: #6b7280;
            }
            
            /* Loading states */
            .btn-loading {
                opacity: 0.7;
                cursor: not-allowed;
                position: relative;
            }
            
            .btn-loading .btn-text {
                opacity: 0;
            }
            
            .btn-loading::after {
                content: '';
                position: absolute;
                width: 16px;
                height: 16px;
                border: 2px solid transparent;
                border-top: 2px solid currentColor;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }
            
            @keyframes spin {
                0% { transform: translate(-50%, -50%) rotate(0deg); }
                100% { transform: translate(-50%, -50%) rotate(360deg); }
            }
            
            /* Upload progress */
            .upload-progress {
                margin-top: 1rem;
                padding: 1rem;
                background: #f8fafc;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e2e8f0;
                border-radius: 4px;
                overflow: hidden;
                margin: 0.5rem 0;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--primary-color), #60a5fa);
                border-radius: 4px;
                transition: width 0.3s ease;
                position: relative;
            }
            
            .progress-fill::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                animation: shimmer 2s infinite;
            }
            
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            .progress-text {
                font-size: 0.875rem;
                color: #64748b;
                text-align: center;
                margin-top: 0.5rem;
            }
            
            .login-btn {
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
                position: relative;
            }
            
            .login-btn:hover {
                background: var(--primary-hover);
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }
            
            .login-btn:active {
                transform: translateY(0);
            }
            
            .login-footer {
                text-align: center;
                padding-top: 1.5rem;
                border-top: 1px solid var(--border-color);
            }
            
            .login-footer p {
                color: var(--text-secondary);
                font-size: 0.875rem;
                margin-bottom: 1rem;
            }
            
            .signup-link {
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
            }
            
            .signup-link:hover {
                background: var(--background-secondary);
                transform: translateY(-1px);
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
                    <li><a href="/pricing">Pricing</a></li>
                    <li><a href="/docs">Integration Guide</a></li>
                </ul>
                
                <!-- Auth and Usage Section -->
                <div style="display: flex; justify-content: flex-end; align-items: center; gap: 1rem;">
                    <!-- Usage Tracker - Only shown when logged in -->
                    <div id="usage-tracker" style="display: none; background: #667eea; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.875rem; font-weight: 500;">
                        <i class="fas fa-chart-line"></i>
                        <span id="usage-text">Loading...</span>
                    </div>
                    
                    <!-- Auth buttons -->
                    <div class="auth-section" style="display: flex; align-items: center; gap: 0.5rem;">
                        <a href="/pricing" class="cta-button" id="get-started-btn">Get Started</a>
                        <button onclick="logout()" class="btn-secondary" id="logout-btn" style="display: none; background: #6b7280; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.875rem; cursor: pointer;">Logout</button>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Fair Usage Notice -->
        <div style="background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); border-bottom: 1px solid #d1d5db; padding: 0.75rem 0; text-align: center;">
            <div style="max-width: 1200px; margin: 0 auto; padding: 0 2rem;">
                <div style="font-size: 0.875rem; color: #374151; font-weight: 500;">
                    <i class="fas fa-info-circle" style="color: #667eea; margin-right: 0.5rem;"></i>
                    <strong>Fair Usage:</strong> 1 page credit = ~2,000 characters of content processed. This ensures accurate billing based on actual document complexity.
                </div>
            </div>
        </div>

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
                    <p>Try up to 3 uploads per hour • Create free account for 15 uploads per hour + AI features</p>
                    <input type="file" id="fileInput" style="display: none;" accept=".pdf" onchange="handleFileSelect(event)">
                </div>
                
                <!-- Login/Account Section -->
                <div id="account-section" style="margin-top: 2rem; text-align: center; display: none;">
                    <div style="background: var(--background-secondary); padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem;">
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">Welcome back!</h4>
                        <p style="color: var(--text-secondary); font-size: 0.875rem;">You're logged in with unlimited processing</p>
                        <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1rem;">
                            <a href="/dashboard" class="btn-secondary" style="font-size: 0.875rem; padding: 0.5rem 1rem; text-decoration: none; display: inline-block;">📊 Dashboard</a>
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
                                <span class="btn-text">
                                    <i class="fas fa-sign-in-alt"></i>
                                    Sign In
                                </span>
                            </button>
                        </form>
                        
                        <div class="login-footer">
                            <p>Don't have an account?</p>
                            <a href="/pricing" class="signup-link">
                                <i class="fas fa-rocket"></i>
                                Get started for $4.99 CAD/month
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Processing your document with AI...</p>
                    <div class="upload-progress" id="upload-progress" style="display: none;">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
                        </div>
                        <div class="progress-text" id="progress-text">Uploading document...</div>
                    </div>
                </div>
                
                <div class="results">
                    <h3><i class="fas fa-check-circle"></i> Extraction Complete</h3>
                    <div class="results-content" id="results-content"></div>
                </div>
            </section>
        </main>

        <script>
            // Check if user is logged in on page load
            window.addEventListener('load', async function() {
                try {
                    const response = await fetch('/auth/me', {
                        credentials: 'include'
                    });
                    if (response.ok) {
                        const result = await response.json();
                        if (result.success) {
                            showLoggedInState();
                        }
                    }
                } catch (error) {
                    console.log('User not logged in');
                }
            });
            
            // File upload handling
            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (file && file.type === 'application/pdf') {
                    uploadFile(file);
                } else {
                    alert('Please select a valid PDF file.');
                }
            }
            
            async function uploadFile(file) {
                const loadingEl = document.querySelector('.loading');
                const resultsEl = document.querySelector('.results');
                const resultsContent = document.getElementById('results-content');
                
                // Show loading
                loadingEl.classList.add('active');
                resultsEl.classList.remove('active');
                
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    // Add API key if user is logged in
                    const apiKey = localStorage.getItem('pdf_parser_api_key');
                    const headers = {};
                    if (apiKey) {
                        headers['Authorization'] = `Bearer ${apiKey}`;
                    }
                    
                    const response = await fetch('/parse/', {
                        method: 'POST',
                        headers: headers,
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    // Hide loading
                    loadingEl.classList.remove('active');
                    
                    if (result.success) {
                        // Update usage tracker after successful processing
                        updateUsageTracker();
                        // Show success message first
                        if (result.success_message) {
                            const successDiv = document.createElement('div');
                            successDiv.style.cssText = `
                                background: #d4edda;
                                color: #155724;
                                border: 1px solid #c3e6cb;
                                border-radius: 8px;
                                padding: 16px 20px;
                                margin: 20px 0;
                                font-size: 16px;
                                font-weight: 500;
                                text-align: center;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            `;
                            successDiv.textContent = result.success_message;
                            
                            // Insert success message before results
                            const resultsContainer = document.querySelector('.results-container') || resultsEl.parentNode;
                            resultsContainer.insertBefore(successDiv, resultsEl);
                            
                            // Auto-scroll to success message, then scroll down a bit more
                            setTimeout(() => {
                                successDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                setTimeout(() => {
                                    window.scrollBy({ top: 200, behavior: 'smooth' });
                                }, 1000);
                            }, 100);
                        }
                        
                        // Display clean, user-friendly content
                        resultsContent.innerHTML = '';
                        
                        // Add text content
                        if (result.text && result.text.trim()) {
                            const textSection = document.createElement('div');
                            textSection.style.cssText = `
                                background: white;
                                border: 1px solid #e0e0e0;
                                border-radius: 8px;
                                padding: 20px;
                                margin-bottom: 20px;
                                line-height: 1.6;
                                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                white-space: pre-wrap;
                                word-wrap: break-word;
                            `;
                            
                            const textHeaderContainer = document.createElement('div');
                            textHeaderContainer.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;';
                            
                            const textHeader = document.createElement('h3');
                            textHeader.textContent = '📄 Extracted Text';
                            textHeader.style.cssText = 'margin: 0; color: #333; font-size: 18px;';
                            
                            const copyButton = document.createElement('button');
                            copyButton.textContent = '📋 Copy Text';
                            copyButton.style.cssText = `
                                background: #007bff;
                                color: white;
                                border: none;
                                border-radius: 6px;
                                padding: 8px 16px;
                                cursor: pointer;
                                font-size: 14px;
                                font-weight: 500;
                                transition: background-color 0.2s;
                            `;
                            
                            copyButton.onmouseover = () => copyButton.style.background = '#0056b3';
                            copyButton.onmouseout = () => copyButton.style.background = '#007bff';
                            
                            copyButton.onclick = async () => {
                                try {
                                    await navigator.clipboard.writeText(result.text.trim());
                                    copyButton.textContent = '✅ Copied!';
                                    copyButton.style.background = '#28a745';
                                    setTimeout(() => {
                                        copyButton.textContent = '📋 Copy Text';
                                        copyButton.style.background = '#007bff';
                                    }, 2000);
                                } catch (err) {
                                    // Fallback for older browsers
                                    const textArea = document.createElement('textarea');
                                    textArea.value = result.text.trim();
                                    document.body.appendChild(textArea);
                                    textArea.select();
                                    document.execCommand('copy');
                                    document.body.removeChild(textArea);
                                    
                                    copyButton.textContent = '✅ Copied!';
                                    copyButton.style.background = '#28a745';
                                    setTimeout(() => {
                                        copyButton.textContent = '📋 Copy Text';
                                        copyButton.style.background = '#007bff';
                                    }, 2000);
                                }
                            };
                            
                            textHeaderContainer.appendChild(textHeader);
                            textHeaderContainer.appendChild(copyButton);
                            
                            const textContent = document.createElement('div');
                            textContent.textContent = result.text.trim();
                            textContent.style.cssText = 'color: #444; font-size: 14px;';
                            
                            textSection.appendChild(textHeaderContainer);
                            textSection.appendChild(textContent);
                            resultsContent.appendChild(textSection);
                        }
                        
                        // Add tables if present
                        if (result.tables && result.tables.length > 0) {
                            const tablesSection = document.createElement('div');
                            tablesSection.style.cssText = `
                                background: white;
                                border: 1px solid #e0e0e0;
                                border-radius: 8px;
                                padding: 20px;
                                margin-bottom: 20px;
                            `;
                            
                            const tablesHeader = document.createElement('h3');
                            tablesHeader.textContent = `📊 Tables (${result.tables.length})`;
                            tablesHeader.style.cssText = 'margin: 0 0 15px 0; color: #333; font-size: 18px;';
                            tablesSection.appendChild(tablesHeader);
                            
                            result.tables.forEach((table, index) => {
                                const tableDiv = document.createElement('div');
                                tableDiv.style.cssText = 'margin-bottom: 20px; overflow-x: auto;';
                                
                                const tableTitle = document.createElement('h4');
                                tableTitle.textContent = `Table ${index + 1}`;
                                tableTitle.style.cssText = 'margin: 0 0 10px 0; color: #555;';
                                
                                const tableContent = document.createElement('pre');
                                tableContent.textContent = JSON.stringify(table, null, 2);
                                tableContent.style.cssText = `
                                    background: #f8f9fa;
                                    padding: 15px;
                                    border-radius: 4px;
                                    font-size: 12px;
                                    overflow-x: auto;
                                `;
                                
                                tableDiv.appendChild(tableTitle);
                                tableDiv.appendChild(tableContent);
                                tablesSection.appendChild(tableDiv);
                            });
                            
                            resultsContent.appendChild(tablesSection);
                        }
                        
                        // Add images if present
                        if (result.images && result.images.length > 0) {
                            const imagesSection = document.createElement('div');
                            imagesSection.style.cssText = `
                                background: white;
                                border: 1px solid #e0e0e0;
                                border-radius: 8px;
                                padding: 20px;
                                margin-bottom: 20px;
                            `;
                            
                            const imagesHeader = document.createElement('h3');
                            imagesHeader.textContent = `🖼️ Images (${result.images.length})`;
                            imagesHeader.style.cssText = 'margin: 0 0 15px 0; color: #333; font-size: 18px;';
                            imagesSection.appendChild(imagesHeader);
                            
                            result.images.forEach((image, index) => {
                                const imageDiv = document.createElement('div');
                                imageDiv.textContent = `Image ${index + 1}: ${image.description || 'Extracted image'}`;
                                imageDiv.style.cssText = 'margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;';
                                imagesSection.appendChild(imageDiv);
                            });
                            
                            resultsContent.appendChild(imagesSection);
                        }
                        
                        resultsEl.classList.add('active');
                        
                        // Show upgrade prompt if free user hit limit
                        if (!result.user_info.authenticated && result.pages_processed >= 10) {
                            showUpgradePrompt();
                        }
                    } else {
                        // Handle free tier limit
                        if (result.detail && typeof result.detail === 'object') {
                            showUpgradePrompt(result.detail);
                        } else {
                            alert('Error: ' + (result.detail || result.error || 'Processing failed'));
                        }
                    }
                } catch (error) {
                    loadingEl.classList.remove('active');
                    alert('Upload failed: ' + error.message);
                }
            }
            
            // Enhanced login functionality with error handling
            async function quickLogin(event) {
                event.preventDefault(); // Prevent form submission
                
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPassword').value;
                const errorDiv = document.getElementById('login-error');
                const errorText = document.getElementById('login-error-text');
                const submitBtn = event.target.querySelector('button[type="submit"]');
                
                // Hide previous errors
                hideLoginError();
                
                // Basic validation
                if (!email || !password) {
                    showLoginError('Please enter both email and password');
                    return;
                }
                
                // Show loading state
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
                submitBtn.disabled = true;
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({email: email, password: password})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        // Store user session info
                        localStorage.setItem('pdf_parser_email', email);
                        localStorage.setItem('pdf_parser_logged_in', 'true');
                        if (result.api_key) {
                            localStorage.setItem('pdf_parser_api_key', result.api_key);
                        }
                        if (result.subscription_tier) {
                            localStorage.setItem('pdf_parser_subscription_tier', result.subscription_tier);
                        }
                        
                        // Show success
                        submitBtn.classList.remove('btn-loading');
                        submitBtn.innerHTML = '<span class="btn-text"><i class="fas fa-check"></i> Success!</span>';
                        submitBtn.style.background = '#16a34a';
                        
                        showToast('Welcome Back!', 'You have been logged in successfully.', 'success');
                        
                        // Transition to logged in state
                        setTimeout(() => {
                            showLoggedInState();
                        }, 1000);
                    } else {
                        submitBtn.classList.remove('btn-loading');
                        submitBtn.disabled = false;
                        
                        if (result.message && result.message.includes('verification')) {
                            showToast('Email Verification Required', 'Please check your email and complete verification before logging in.', 'warning');
                        } else {
                            showToast('Login Failed', result.message || 'Invalid email or password. Please double-check and try again.', 'error');
                        }
                        showLoginError(result.message || 'Invalid email or password');
                    }
                } catch (error) {
                    submitBtn.classList.remove('btn-loading');
                    submitBtn.disabled = false;
                    showToast('Connection Error', 'Unable to connect. Please check your internet connection and try again.', 'error');
                    showLoginError('Connection error. Please try again.');
                    console.error('Login error:', error);
                } finally {
                    // Always reset button after delay if still loading or showing success
                    setTimeout(() => {
                        if (submitBtn.disabled || submitBtn.innerHTML.includes('Success') || submitBtn.innerHTML.includes('Signing')) {
                            submitBtn.innerHTML = '<span class="btn-text"><i class="fas fa-sign-in-alt"></i> Sign In</span>';
                            submitBtn.disabled = false;
                            submitBtn.style.background = '';
                            submitBtn.classList.remove('btn-loading');
                        }
                    }, 3000);
                }
            }
            
            // Show login error message
            function showLoginError(message) {
                const errorDiv = document.getElementById('login-error');
                const errorText = document.getElementById('login-error-text');
                
                errorText.textContent = message;
                errorDiv.style.display = 'flex';
                
                // Auto-hide after 5 seconds
                setTimeout(hideLoginError, 5000);
            }
            
            // Hide login error message
            function hideLoginError() {
                const errorDiv = document.getElementById('login-error');
                errorDiv.style.display = 'none';
            }
            
            // Show logged in state
            function showLoggedInState() {
                document.getElementById('login-section').style.display = 'none';
                document.getElementById('account-section').style.display = 'block';
                
                // Show usage tracker in navbar
                document.getElementById('usage-tracker').style.display = 'block';
                document.getElementById('get-started-btn').style.display = 'none';
                document.getElementById('logout-btn').style.display = 'inline-block';
                
                // Load and display usage information
                updateUsageTracker();
            }
            
            // Logout
            function logout() {
                // Clear all stored session data
                localStorage.removeItem('pdf_parser_api_key');
                localStorage.removeItem('pdf_parser_email');
                localStorage.removeItem('pdf_parser_logged_in');
                localStorage.removeItem('pdf_parser_subscription_tier');
                localStorage.removeItem('pdf_parser_customer_id');
                
                // Update UI to logged out state
                document.getElementById('login-section').style.display = 'block';
                document.getElementById('account-section').style.display = 'none';
                
                // Hide usage tracker and show get started button
                document.getElementById('usage-tracker').style.display = 'none';
                document.getElementById('get-started-btn').style.display = 'inline-block';
                document.getElementById('logout-btn').style.display = 'none';
                
                showToast('Logged Out', 'You have been logged out successfully.', 'info');
            }
            
            // Show usage info
            async function showUsage() {
                try {
                    const response = await fetch('/auth/me', {
                        credentials: 'include'  // Include cookies for session auth
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        const usage = result.usage_info;
                        alert(`Usage This Month:
Pages Used: ${usage.total_pages || 0}
Plan: ${result.subscription_tier}
Total Cost: $${usage.total_cost || 0}`);
                    }
                } catch (error) {
                    alert('Could not fetch usage info');
                }
            }
            
            // Update usage tracker in navbar
            async function updateUsageTracker() {
                try {
                    const response = await fetch('/auth/me', {
                        credentials: 'include'  // Include cookies for session auth
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        const usage = result.usage_info;
                        const tier = result.subscription_tier.toLowerCase();
                        
                        // Calculate remaining pages based on subscription tier
                        const planLimits = {
                            'student': 500,
                            'growth': 2500,
                            'business': 10000,
                            'free': 10
                        };
                        
                        const maxPages = planLimits[tier] || 10;
                        const usedPages = usage.total_pages || 0;
                        const remainingPages = Math.max(0, maxPages - usedPages);
                        
                        // Update the usage tracker display
                        const usageText = document.getElementById('usage-text');
                        const tracker = document.getElementById('usage-tracker');
                        
                        if (remainingPages <= 0) {
                            usageText.textContent = `${tier.toUpperCase()}: 0 pages left`;
                            tracker.style.background = '#dc2626'; // Red for no pages left
                        } else if (remainingPages < maxPages * 0.2) {
                            usageText.textContent = `${tier.toUpperCase()}: ${remainingPages} pages left`;
                            tracker.style.background = '#f59e0b'; // Orange for low pages
                        } else {
                            usageText.textContent = `${tier.toUpperCase()}: ${remainingPages} pages left`;
                            tracker.style.background = '#667eea'; // Blue for good
                        }
                    }
                } catch (error) {
                    console.error('Could not fetch usage info:', error);
                    document.getElementById('usage-text').textContent = 'Usage unavailable';
                }
            }
            
            // Show upgrade prompt
            function showUpgradePrompt(details) {
                const message = details ? details.message : 'Upgrade for unlimited processing!';
                const upgradeUrl = details ? details.upgrade_url : '/pricing';
                
                if (confirm(message + '\\n\\nGo to pricing page?')) {
                    window.location.href = upgradeUrl;
                }
            }
            
            // Debug function to check Stripe status
            async function debugStripeStatus() {
                try {
                    const response = await fetch('/stripe-status/');
                    const data = await response.json();
                    alert('🔍 Stripe Debug Info:\\n\\n' + JSON.stringify(data, null, 2));
                } catch (error) {
                    alert('❌ Debug Error: ' + error.message);
                }
            }
            
            // Drag and drop functionality
            const uploadArea = document.querySelector('.upload-area');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight(e) {
                uploadArea.style.borderColor = 'var(--primary-color)';
                uploadArea.style.background = 'var(--background-tertiary)';
            }
            
            function unhighlight(e) {
                uploadArea.style.borderColor = 'var(--border-color)';
                uploadArea.style.background = 'var(--background-secondary)';
            }
            
            uploadArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > 0) {
                    const file = files[0];
                    if (file.type === 'application/pdf') {
                        uploadFile(file);
                    } else {
                        alert('Please drop a valid PDF file.');
                    }
                }
            }
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
                padding: 1.5rem 0;
                box-shadow: var(--shadow-sm);
            }
            
            .nav-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                display: grid;
                grid-template-columns: 1fr 2fr 1fr;
                align-items: center;
                min-height: 60px;
                gap: 2rem;
            }
            
            .logo {
                font-size: 1.75rem;
                font-weight: 700;
                color: var(--text-primary);
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .logo i {
                font-size: 1.75rem;
                color: var(--primary-color);
            }
            
            .nav-links {
                display: flex;
                gap: 2.5rem;
                list-style: none;
                align-items: center;
                justify-content: center;
            }
            
            .nav-links a {
                color: var(--text-secondary);
                text-decoration: none;
                font-weight: 500;
                font-size: 1.05rem;
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
                grid-template-columns: repeat(4, 1fr);
                gap: 1.5rem;
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
                font-size: 1.75rem;
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
                overflow: hidden;
                transition: var(--transition);
            }
            
            .faq-item:hover {
                border-color: var(--primary-color);
            }
            
            .faq-question {
                font-weight: 600;
                color: var(--text-primary);
                padding: 1.5rem;
                margin: 0;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: var(--background);
                transition: var(--transition);
                user-select: none;
            }
            
            .faq-question:hover {
                background: var(--background-secondary);
            }
            
            .faq-question::after {
                content: '+';
                font-size: 1.5rem;
                font-weight: 300;
                color: var(--primary-color);
                transition: transform 0.3s ease;
            }
            
            .faq-question.active::after {
                transform: rotate(45deg);
            }
            
            .faq-answer {
                color: var(--text-secondary);
                line-height: 1.6;
                padding: 0;
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease, padding 0.3s ease;
            }
            
            .faq-answer.active {
                max-height: 200px;
                padding: 0 1.5rem 1.5rem;
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
                    grid-template-columns: repeat(2, 1fr);
                    gap: 1rem;
                }
                
                @media (max-width: 640px) {
                    .pricing-grid {
                        grid-template-columns: 1fr;
                    }
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
                    <li><a href="/docs">Integration Guide</a></li>
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
                    <div class="plan-name">Free</div>
                    <div class="plan-price">
                        <span class="currency">$</span>0
                        <span class="period">/forever</span>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-top: 0.25rem;">No credit card required</div>
                    <div class="plan-description">Try our basic PDF processing</div>
                    <ul class="plan-features">
                        <li><i class="fas fa-check"></i> 3 uploads per hour (anonymous) or 15 uploads per hour + 10 pages/month (account)</li>
                        <li><i class="fas fa-check"></i> Library-based parsing</li>
                        <li><i class="fas fa-check"></i> OCR for scanned PDFs</li>
                        <li><i class="fas fa-times" style="color: var(--text-muted);"></i> <span style="color: var(--text-muted);">AI processing (upgrade required)</span></li>
                    </ul>
                    <a href="/auth/register?plan=free" class="plan-button secondary">Create Free Account</a>
                </div>
                
                <div class="pricing-card">
                    <div class="plan-name">Student</div>
                    <div class="plan-price">
                        <span class="currency">$</span>4.99
                        <span class="period">/month CAD</span>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-top: 0.25rem;">Plus applicable taxes</div>
                    <div class="plan-description">Perfect for students and light usage</div>
                    <ul class="plan-features">
                        <li><i class="fas fa-check"></i> 500 pages/month</li>
                        <li><i class="fas fa-check"></i> 🤖 AI-powered processing</li>
                        <li><i class="fas fa-check"></i> 25 AI documents/month</li>
                        <li><i class="fas fa-check"></i> All advanced features</li>
                        <li><i class="fas fa-check"></i> Email support</li>
                    </ul>
                    <button type="button" onclick="createCheckout('student', this)" class="plan-button secondary">Get Started</button>
                </div>

                <div class="pricing-card popular">
                    <div class="plan-name">Growth</div>
                    <div class="plan-price">
                        <span class="currency">$</span>19.99
                        <span class="period">/month CAD</span>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-align: center; margin-top: 0.25rem;">Plus applicable taxes</div>
                    <div class="plan-description">Great for growing businesses</div>
                    <ul class="plan-features">
                        <li><i class="fas fa-check"></i> 2,500 pages/month</li>
                        <li><i class="fas fa-check"></i> 🤖 AI-powered processing</li>
                        <li><i class="fas fa-check"></i> 100 AI documents/month</li>
                        <li><i class="fas fa-check"></i> Priority processing</li>
                        <li><i class="fas fa-check"></i> Advanced analytics</li>
                        <li><i class="fas fa-check"></i> Chat support</li>
                        <li><i class="fas fa-check"></i> API access</li>
                    </ul>
                    <button type="button" onclick="createCheckout('growth', this)" class="plan-button">Get Started</button>
                </div>

                <div class="pricing-card">
                    <div class="plan-name">Business</div>
                    <div class="plan-price">
                        <span class="currency">$</span>49.99
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
                    <button type="button" onclick="createCheckout('business', this)" class="plan-button">Get Started</button>
                </div>
            </section>

            <!-- FAQ Section -->
            <section class="faq-section">
                <div class="faq-header">
                    <h2>Frequently Asked Questions</h2>
                </div>
                <div class="faq-grid">
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">How do I get started?</div>
                        <div class="faq-answer">Try 3 uploads per hour without account, or create free account for 15 uploads per hour + 10 pages/month tracked usage. For AI features and higher limits, choose a paid plan. Email verification required for paid subscriptions.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">Why are there upload limits per hour?</div>
                        <div class="faq-answer">Upload limits prevent server overload and ensure fair access for all users. They also protect against abuse while keeping our service fast and reliable. Higher limits are available with paid plans.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">How does the billing work?</div>
                        <div class="faq-answer">We use character-based billing: every 2,000 characters = 1 page. Overage fees apply if you exceed your monthly limit. Student: $0.01/page, Growth/Business: $0.008/page.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">What's the difference between free and paid plans?</div>
                        <div class="faq-answer">Anonymous users: 3 uploads per hour basic processing. Free accounts: 15 uploads per hour + 10 pages/month tracked. Paid plans: AI-powered processing with Google Gemini 2.5 Flash for complex layouts, tables, and superior accuracy.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">Do I need to manage API keys manually?</div>
                        <div class="faq-answer">No! API keys auto-renew based on your subscription status. They automatically extend when you're a paying customer and expire when subscriptions end.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">What file formats do you support?</div>
                        <div class="faq-answer">We support PDF files with advanced OCR for scanned documents, intelligent text extraction, and AI-powered structure recognition for complex layouts.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">Is my data secure?</div>
                        <div class="faq-answer">Yes! We have zero data retention - documents are processed and immediately deleted. Plus IP validation, session security, email verification, and comprehensive abuse protection.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">What are the upload limits?</div>
                        <div class="faq-answer">File size limit: 50MB. Rate limits vary by plan: Free accounts (15 uploads per hour), Student (40 uploads per hour), Growth (120 uploads per hour), Business (300 uploads per hour). Anonymous users: 3 uploads per hour.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">Can I cancel anytime?</div>
                        <div class="faq-answer">Yes! Go to your Account Dashboard (after logging in) and click "Manage Subscription" to cancel through Stripe. You keep access until your current billing period ends, then automatically switch to free tier (15 uploads per hour + 10 pages/month).</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">I can't log in after purchasing. What's wrong?</div>
                        <div class="faq-answer">Make sure you're using the same email address for both account creation AND payment. Check your email for verification code if using a paid plan.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">How does the AI processing work?</div>
                        <div class="faq-answer">We use Google Gemini 2.5 Flash for intelligent document understanding. It analyzes layout, extracts tables, handles complex formatting, and provides superior accuracy over basic OCR.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">What happens to my account if payment fails?</div>
                        <div class="faq-answer">Stripe automatically retries failed payments. If ultimately unsuccessful, your account switches to free tier (15 uploads per hour + 10 pages/month) until payment is resolved.</div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question" onclick="toggleFaq(this)">Do you have an API?</div>
                        <div class="faq-answer">Yes! Growth and Business plans include full API access with auto-renewing keys. Perfect for integrating PDF processing into your applications.</div>
                    </div>
                </div>
            </section>
        </main>
        
        <script>
            // Debug: Check if script is loading
            console.log('🔥 PRICING: Script loaded successfully!');
            
            // Test function first - simpler implementation
            function testButton(planType) {
                console.log('🔥 TEST: Button clicked for plan:', planType);
                alert('✅ SUCCESS! Button is working for plan: ' + planType);
                
                // Test fetch to ensure network connectivity
                fetch('/test-button/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({plan: planType, test: true, timestamp: new Date().toISOString()})
                })
                .then(function(response) { return response.json(); })
                .then(function(result) {
                    console.log('🔥 TEST: Server response:', result);
                    alert('✅ Server Response: ' + JSON.stringify(result, null, 2));
                })
                .catch(function(error) {
                    console.error('🔥 TEST: Error:', error);
                    alert('❌ Network Error: ' + error.message);
                });
            }
            
            // Stripe Checkout Integration - Fixed version
            // Fixed JavaScript syntax - removed double curly braces
            function createCheckout(planType, buttonElement) {
                try {
                    console.log('🔥 CHECKOUT: Function called with planType:', planType);
                    
                    // Show loading state on button
                    var button = buttonElement;
                    if (button) {
                        var originalText = button.textContent;
                        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                        button.disabled = true;
                    }
                    
                    console.log('🔥 CHECKOUT: Redirecting to protected subscription route');
                    
                    // Add small delay to show loading state
                    setTimeout(function() {
                        // Redirect to protected route - it will handle authentication check
                        // If user is not logged in, they'll be redirected to register with plan pre-selected
                        // If user is logged in, they'll be redirected to Stripe Payment Link
                        console.log('🔥 CHECKOUT: Actually redirecting now to /subscribe/' + planType);
                        window.location.href = '/subscribe/' + planType;
                    }, 100);
                    
                } catch (error) {
                    console.error('❌ CHECKOUT ERROR:', error);
                    alert('Error: ' + error.message);
                }
            }
            
            // Initialize when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {
                console.log('🔥 PRICING: DOM loaded, page ready');
                
                // Test that all functions are available
                if (typeof testButton === 'function') {
                    console.log('✅ testButton function available');
                } else {
                    console.error('❌ testButton function missing');
                }
                
                if (typeof createCheckout === 'function') {
                    console.log('✅ createCheckout function available');
                } else {
                    console.error('❌ createCheckout function missing');
                }
            });
            
            // Global error handler for debugging
            window.addEventListener('error', function(event) {
                console.error('🔥 GLOBAL ERROR:', event.error);
                console.error('🔥 ERROR DETAILS:', {
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno
                });
            });
            
            // FAQ Collapse functionality
            function toggleFaq(questionElement) {
                const answer = questionElement.nextElementSibling;
                const isActive = questionElement.classList.contains('active');
                
                // Close all other FAQs
                document.querySelectorAll('.faq-question').forEach(q => {
                    q.classList.remove('active');
                    q.nextElementSibling.classList.remove('active');
                });
                
                // Toggle current FAQ
                if (!isActive) {
                    questionElement.classList.add('active');
                    answer.classList.add('active');
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.get("/auth/register")
async def register_page(plan: str = "student"):
    """Registration page with password collection"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create Account - PDF Parser</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }}
            
            .auth-container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 3rem;
                width: 100%;
                max-width: 400px;
            }}
            
            .logo {{
                text-align: center;
                margin-bottom: 2rem;
                font-size: 2rem;
                font-weight: 700;
                color: #667eea;
            }}
            
            .plan-badge {{
                background: #667eea;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.875rem;
                text-align: center;
                margin-bottom: 2rem;
                font-weight: 500;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: #374151;
            }}
            
            input {{
                width: 100%;
                padding: 0.75rem 1rem;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 1rem;
                transition: border-color 0.2s;
            }}
            
            input:focus {{
                outline: none;
                border-color: #667eea;
            }}
            
            .btn-primary {{
                width: 100%;
                background: #667eea;
                color: white;
                border: none;
                padding: 0.875rem 1rem;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: background-color 0.2s;
                margin-bottom: 1rem;
            }}
            
            .btn-primary:hover {{
                background: #5a67d8;
            }}
            
            .btn-primary:disabled {{
                background: #9ca3af;
                cursor: not-allowed;
            }}
            
            .login-link {{
                text-align: center;
                color: #6b7280;
                font-size: 0.875rem;
            }}
            
            .login-link a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
            }}
            
            .error {{
                background: #fee2e2;
                color: #dc2626;
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                font-size: 0.875rem;
            }}
            
            .success {{
                background: #dcfce7;
                color: #16a34a;
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                font-size: 0.875rem;
            }}
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo">
                <i class="fas fa-file-pdf"></i> PDF Parser
            </div>
            
            <div class="plan-badge">
                Creating account for {plan.title()} Plan
            </div>
            
            <div id="message"></div>
            
            <form id="registerForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required minlength="6">
                </div>
                
                <div class="form-group">
                    <label for="confirmPassword">Confirm Password</label>
                    <input type="password" id="confirmPassword" name="confirmPassword" required minlength="6">
                </div>
                
                <button type="submit" class="btn-primary" id="submitBtn">
                    Create Account & Continue to Payment
                </button>
            </form>
            
            <div class="login-link">
                Already have an account? <a href="/auth/login?plan={plan}">Sign in</a>
            </div>
        </div>
        
        <script>
            document.getElementById('registerForm').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                const messageDiv = document.getElementById('message');
                const submitBtn = document.getElementById('submitBtn');
                
                // Clear previous messages
                messageDiv.innerHTML = '';
                
                // Validate passwords match
                if (password !== confirmPassword) {{
                    messageDiv.innerHTML = '<div class="error">Passwords do not match</div>';
                    return;
                }}
                
                // Validate password length
                if (password.length < 6) {{
                    messageDiv.innerHTML = '<div class="error">Password must be at least 6 characters</div>';
                    return;
                }}
                
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
                
                try {{
                    const response = await fetch('/auth/register', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            email: email,
                            password: password,
                            plan_type: '{plan}'
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        if (data.verification_required) {{
                            messageDiv.innerHTML = '<div class="success">Account created! Please check your email for a 6-digit verification code, then proceed to payment.</div>';
                        }} else {{
                            messageDiv.innerHTML = '<div class="success">Account created successfully! Redirecting to payment...</div>';
                        }}
                        
                        // Store user info in localStorage for session management
                        if (data.customer_id) {{
                            localStorage.setItem('pdf_parser_customer_id', data.customer_id);
                            localStorage.setItem('pdf_parser_email', data.email);
                            localStorage.setItem('pdf_parser_subscription_tier', data.subscription_tier);
                        }}
                        
                        // Store login info and redirect appropriately
                        setTimeout(() => {{
                            if ('{plan}' === 'free') {{
                                window.location.href = '/?welcome=true';
                            }} else {{
                                window.location.href = '/subscribe/{plan}';
                            }}
                        }}, 1500);
                    }} else {{
                        throw new Error(data.error || 'Registration failed');
                    }}
                }} catch (error) {{
                    messageDiv.innerHTML = `<div class="error">${{error.message}}</div>`;
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Create Account & Continue to Payment';
                }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/auth/register")
async def register_user(registration: UserRegistration, request: Request):
    """Register a new user with email verification"""
    if not auth_system:
        print("❌ Registration failed: auth_system is None")
        raise HTTPException(status_code=503, detail="Authentication service unavailable - server restarting")
    
    print(f"🔄 Registration attempt for: {registration.email}")
    try:
        # Check if user already exists
        existing_customer = auth_system.get_customer_by_email(registration.email)
        if existing_customer:
            return {
                "success": False,
                "error": "User already exists. Please log in instead.",
                "existing_user": True
            }
        
        # Map plan type to subscription tier
        tier_map = {
            "student": "student",
            "growth": "growth", 
            "business": "business"
        }
        
        subscription_tier = tier_map.get(registration.plan_type.lower(), "free")
        client_ip = request.client.host
        
        # Create customer with password and IP tracking
        customer = auth_system.create_customer(
            email=registration.email,
            password=registration.password,
            subscription_tier=subscription_tier,
            ip_address=client_ip
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
        
        # Create session token for immediate login
        import secrets
        session_token = secrets.token_urlsafe(32)
        active_sessions[session_token] = customer.email
        
        from fastapi.responses import JSONResponse
        response_data = {
            "success": True,
            "customer_id": customer.customer_id,
            "email": customer.email,
            "subscription_tier": customer.subscription_tier,
            "verification_required": subscription_tier != "free",
            "verification_code": customer.verification_code if hasattr(customer, 'verification_code') else None,
            "message": "Account created successfully! Check your email for verification code." if subscription_tier != "free" else "Account created successfully! You can now login."
        }
        
        response = JSONResponse(content=response_data)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=86400 * 7,  # 7 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.get("/auth/login")
async def login_page(plan: str = "student"):
    """Login page for existing users"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sign In - PDF Parser</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }}
            
            .auth-container {{
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 3rem;
                width: 100%;
                max-width: 400px;
            }}
            
            .logo {{
                text-align: center;
                margin-bottom: 2rem;
                font-size: 2rem;
                font-weight: 700;
                color: #667eea;
            }}
            
            .plan-badge {{
                background: #667eea;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.875rem;
                text-align: center;
                margin-bottom: 2rem;
                font-weight: 500;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: #374151;
            }}
            
            input {{
                width: 100%;
                padding: 0.75rem 1rem;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 1rem;
                transition: border-color 0.2s;
            }}
            
            input:focus {{
                outline: none;
                border-color: #667eea;
            }}
            
            .btn-primary {{
                width: 100%;
                background: #667eea;
                color: white;
                border: none;
                padding: 0.875rem 1rem;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: background-color 0.2s;
                margin-bottom: 1rem;
            }}
            
            .btn-primary:hover {{
                background: #5a67d8;
            }}
            
            .btn-primary:disabled {{
                background: #9ca3af;
                cursor: not-allowed;
            }}
            
            .register-link {{
                text-align: center;
                color: #6b7280;
                font-size: 0.875rem;
            }}
            
            .register-link a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
            }}
            
            .error {{
                background: #fee2e2;
                color: #dc2626;
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                font-size: 0.875rem;
            }}
            
            .success {{
                background: #dcfce7;
                color: #16a34a;
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 1rem;
                font-size: 0.875rem;
            }}
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo">
                <i class="fas fa-file-pdf"></i> PDF Parser
            </div>
            
            <div class="plan-badge">
                Sign in to subscribe to {plan.title()} Plan
            </div>
            
            <div id="message"></div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email Address</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="btn-primary" id="submitBtn">
                    Sign In & Continue to Payment
                </button>
            </form>
            
            <div class="register-link">
                Don't have an account? <a href="/auth/register?plan={plan}">Create one</a>
            </div>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {{
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const messageDiv = document.getElementById('message');
                const submitBtn = document.getElementById('submitBtn');
                
                // Clear previous messages
                messageDiv.innerHTML = '';
                
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
                
                try {{
                    const response = await fetch('/auth/login', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            email: email,
                            password: password
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        messageDiv.innerHTML = '<div class="success">Sign in successful! Redirecting to payment...</div>';
                        
                        // Store user info in localStorage for session management
                        if (data.customer_id) {{
                            localStorage.setItem('pdf_parser_customer_id', data.customer_id);
                            localStorage.setItem('pdf_parser_email', data.email);
                            localStorage.setItem('pdf_parser_subscription_tier', data.subscription_tier);
                        }}
                        
                        // Redirect appropriately
                        setTimeout(() => {{
                            if ('{plan}' === 'free') {{
                                window.location.href = '/?welcome=true';
                            }} else {{
                                window.location.href = '/subscribe/{plan}';
                            }}
                        }}, 1500);
                    }} else {{
                        throw new Error(data.detail || 'Login failed');
                    }}
                }} catch (error) {{
                    let errorMessage = error.message;
                    if (error.message.includes('Invalid email or password')) {{
                        errorMessage = 'Invalid email or password. If you purchased a subscription, make sure to use the same email address you used for payment.';
                    }}
                    messageDiv.innerHTML = `<div class="error">${{errorMessage}}</div>`;
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Sign In & Continue to Payment';
                }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/auth/login")
async def login_user(login: UserLogin):
    """Verify user credentials and return user info"""
    if not auth_system:
        print("❌ Login failed: auth_system is None")
        raise HTTPException(status_code=503, detail="Authentication service unavailable - server restarting")
    
    print(f"🔄 Login attempt for: {login.email}")
    try:
        # Verify email and password
        customer = auth_system.authenticate_password(login.email, login.password)
        if not customer:
            raise HTTPException(
                status_code=401, 
                detail="Invalid email or password. If you purchased a subscription, make sure to use the same email address you used for payment."
            )
        
        # Get usage info if available
        usage_info = {}
        if usage_tracker:
            usage_info = usage_tracker.get_monthly_usage(customer.customer_id)
        
        # Create session token
        import secrets
        session_token = secrets.token_urlsafe(32)
        active_sessions[session_token] = customer.email
        
        from fastapi.responses import JSONResponse
        response_data = {
            "success": True,
            "customer_id": customer.customer_id,
            "email": customer.email,
            "api_key": customer.api_key,
            "subscription_tier": customer.subscription_tier,
            "usage_info": usage_info,
            "message": "Login successful"
        }
        
        response = JSONResponse(content=response_data)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=86400 * 7,  # 7 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/me")
async def get_current_user_info(request: Request, current_user = Depends(get_current_user_optional)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get usage info
    usage_info = {"total_pages": 0, "total_cost": 0}
    if usage_tracker:
        try:
            usage_info = usage_tracker.get_monthly_usage(current_user.customer_id)
        except:
            pass
    
    return {
        "success": True,
        "customer_id": current_user.customer_id,
        "email": current_user.email,
        "subscription_tier": current_user.subscription_tier,
        "api_key": current_user.api_key,
        "usage_info": usage_info
    }

@app.get("/health-check/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.1-js-fixed",
        "services": {
            "smart_parser": smart_parser is not None,
            "ocr_service": ocr_service is not None,
            "llm_service": llm_service is not None,
            "performance_tracker": performance_tracker is not None,
            "stripe_service": stripe_service is not None,
            "auth_system": auth_system is not None
        },
        "environment": os.getenv("ENVIRONMENT", "development"),
        "stripe_configured": os.getenv("STRIPE_SECRET_KEY") is not None
    }

@app.post("/test-button/")
async def test_button(request: dict):
    """Simple test endpoint to debug button clicks"""
    print(f"🔥 Test button clicked: {request}")
    return {"success": True, "message": "Button click received!", "data": request}

@app.get("/env-debug/")
async def env_debug():
    """Debug Railway environment variables"""
    return {
        "all_env_vars": list(os.environ.keys()),
        "stripe_vars": {k: v[:10] + "..." if v and len(v) > 10 else v for k, v in os.environ.items() if 'STRIPE' in k.upper()},
        "stripe_secret_key_raw": os.getenv("STRIPE_SECRET_KEY", "NOT_SET"),
        "stripe_secret_key_exists": "STRIPE_SECRET_KEY" in os.environ,
        "stripe_secret_key_length": len(os.getenv("STRIPE_SECRET_KEY", "")),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "railway_env": os.getenv("RAILWAY_ENVIRONMENT", "unknown")
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
    
    # 1. FILE SIZE PROTECTION - Prevent server overload
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
    content_size = len(content)
    if content_size > MAX_FILE_SIZE:
        size_mb = content_size / (1024 * 1024)
        raise HTTPException(
            status_code=413, 
            detail=f"File too large ({size_mb:.1f}MB). Maximum size is 50MB. Please split large documents or use a smaller file."
        )
    
    # 2. RATE LIMITING PROTECTION - Prevent spam and server overload
    import time as time_module
    current_time = time_module.time()
    
    # IP-based anti-farming protection
    client_ip = request.client.host
    ip_key = f"ip_{client_ip}"
    
    # Check total uploads from this IP across all accounts
    if ip_key not in user_upload_history:
        user_upload_history[ip_key] = []
    
    # Clean old IP entries
    user_upload_history[ip_key] = [
        timestamp for timestamp in user_upload_history[ip_key]
        if current_time - timestamp < 3600  # 1 hour
    ]
    
    # Anti-farming: Max 50 uploads per hour per IP (prevents account creation spam)
    if len(user_upload_history[ip_key]) >= 50:
        raise HTTPException(
            status_code=429, 
            detail="Too many uploads from this location. This prevents abuse. Please try again later or contact support."
        )
    
    # Different limits for different user types
    if current_user:
        user_key = f"user_{current_user.customer_id}"
        subscription_tier = current_user.subscription_tier
        
        # Check if email verified for paid plans
        if hasattr(current_user, 'email_verified') and subscription_tier != "free":
            if not current_user.email_verified:
                raise HTTPException(
                    status_code=403,
                    detail="Email verification required for paid features. Please check your email for verification code."
                )
        
        # Tiered limits that encourage upgrades while staying profitable
        if subscription_tier == "student":
            max_uploads_per_hour = 40    # $4.99 plan - good for personal use
        elif subscription_tier == "growth": 
            max_uploads_per_hour = 120   # $19.99 plan - good for small business
        elif subscription_tier == "business":
            max_uploads_per_hour = 300   # $49.99 plan - enterprise level
        else:
            max_uploads_per_hour = 15    # Free accounts with login - taste of premium
    else:
        # Anonymous users: strict limits to encourage signup
        user_key = f"anon_{client_ip}"
        max_uploads_per_hour = 3     # Very limited - must create account
    
    # Clean old entries (older than 1 hour)
    if user_key in user_upload_history:
        user_upload_history[user_key] = [
            timestamp for timestamp in user_upload_history[user_key]
            if current_time - timestamp < 3600  # 1 hour = 3600 seconds
        ]
    else:
        user_upload_history[user_key] = []
    
    # Check rate limit
    if len(user_upload_history[user_key]) >= max_uploads_per_hour:
        time_until_reset = 3600 - (current_time - user_upload_history[user_key][0])
        minutes_left = int(time_until_reset / 60)
        
        if current_user:
            detail = f"Rate limit exceeded: {max_uploads_per_hour} uploads per hour. Try again in {minutes_left} minutes, or upgrade for higher limits."
        else:
            detail = f"Rate limit exceeded: {max_uploads_per_hour} uploads per hour. Create a free account for higher limits, or try again in {minutes_left} minutes."
            
        raise HTTPException(status_code=429, detail=detail)
    
    # Record this upload for both user and IP tracking
    user_upload_history[user_key].append(current_time)
    user_upload_history[ip_key].append(current_time)
    
    # Determine user info and limits
    user_id = None
    subscription_tier = "free"
    if current_user:
        user_id = current_user.customer_id
        subscription_tier = current_user.subscription_tier
    
    try:
        # Save uploaded file
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Calculate "pages" based PURELY on character count for accurate billing
        try:
            doc = fitz.open(tmp_path)
            actual_pdf_pages = len(doc)
            
            # Extract all text to measure actual content
            total_text = ""
            for page_num in range(actual_pdf_pages):
                page = doc[page_num]
                total_text += page.get_text()
            
            doc.close()
            
            # PURE CHARACTER-BASED BILLING
            # 1 "page" = exactly 2000 characters of content
            CHARS_PER_PAGE = 2000
            char_count = len(total_text.strip())
            
            # 4. CHARACTER LIMIT PROTECTION - Prevent massive documents
            MAX_CHAR_COUNT = 200000  # ~100 pages worth of content (200k chars)
            if char_count > MAX_CHAR_COUNT:
                estimated_pages = char_count // CHARS_PER_PAGE
                max_pages = MAX_CHAR_COUNT // CHARS_PER_PAGE
                raise HTTPException(
                    status_code=413, 
                    detail=f"Document too large: {estimated_pages} pages of content (max {max_pages} pages). Please split this document or use a smaller file."
                )
            
            if char_count == 0:
                # No extractable text (pure images/scanned docs)
                pages_processed = actual_pdf_pages  # Fall back to physical pages
                print(f"📊 Image/Scanned document: {actual_pdf_pages} physical pages → {pages_processed} billing pages")
            else:
                # Pure character-based billing - extremely accurate
                pages_processed = max(1, (char_count + CHARS_PER_PAGE - 1) // CHARS_PER_PAGE)  # Ceiling division
                
                print(f"📊 Character-based billing: {char_count} chars ÷ {CHARS_PER_PAGE} = {pages_processed} billing pages")
                print(f"    (Physical PDF pages: {actual_pdf_pages})")
        except Exception as e:
            print(f"⚠️  Page calculation failed: {e}")
            pages_processed = 1  # Safe fallback
        
        # Check usage limits and permissions with overage billing
        if current_user and usage_tracker:
            # Authenticated user - check their limits and handle overages
            usage_check = usage_tracker.check_user_limits(user_id, pages_processed)
            
            # If over limit, calculate overage charges
            if not usage_check.get("success", True):
                overage_pages = usage_check.get("overage_pages", 0)
                overage_cost = usage_check.get("overage_cost", 0)
                
                if overage_pages > 0 and current_user.subscription_tier != "free":
                    # Process overage billing for paid users
                    try:
                        if stripe_service:
                            # Create overage invoice
                            print(f"💰 Creating overage invoice: ${overage_cost:.2f} for {overage_pages} pages")
                            
                            # Record overage for future billing
                            usage_tracker.record_overage_usage(
                                user_id=user_id,
                                overage_pages=overage_pages,
                                overage_cost=overage_cost
                            )
                            
                            # Allow processing to continue
                            print(f"✅ Overage approved: Processing {pages_processed} pages")
                        else:
                            print(f"⚠️  Stripe not available for overage billing")
                            # Still allow processing for paid users
                    except Exception as e:
                        print(f"⚠️  Overage billing failed: {e}")
                        # Still allow processing for paid users
                else:
                    # Free users hit hard limit
                    raise HTTPException(
                        status_code=429,
                        detail=f"Monthly limit exceeded. Upgrade to continue processing or wait for next billing cycle."
                    )
        elif not current_user:
            # Unauthenticated user - free tier with generous limits to drive conversions
            if pages_processed > 10:  # Free tier: max 10 pages per request
                raise HTTPException(
                    status_code=401,
                    detail={
                        "error": "Free tier limited to 10 pages per document",
                        "message": "Want more pages + AI processing? Upgrade to Student plan for just $4.99/month!",
                        "upgrade_url": "/pricing",
                        "register_url": "/auth/register",
                        "pages_processed": pages_processed,
                        "pages_limit": 10
                    }
                )
            # Give free users FULL AI features to showcase quality
            # This creates the "wow factor" that drives conversions
        
        result = None
        
        # Run memory cleanup to prevent memory attacks
        cleanup_memory_usage()
        
        # PAID-ONLY AI STRATEGY: Protect costs by restricting AI to paying customers
        if not current_user or current_user.subscription_tier == "free":
            # FREE USERS: Library-only parsing (no AI costs)
            strategy = "library_only"
            print(f"🆓 Free tier: Using library-only parsing (no AI costs)")
        else:
            # PAID USERS: Full AI features available
            print(f"💎 Paid user ({current_user.subscription_tier}): AI features enabled")
        
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
                
                parse_strategy = strategy_map.get(strategy, ParseStrategy.LIBRARY_ONLY)  # Default to safe option
                
                # 3. AI COST PROTECTION - PAID USERS ONLY
                if current_user and current_user.subscription_tier != "free":
                    subscription_tier = current_user.subscription_tier
                    
                    # Clean old AI usage (reset monthly)
                    import datetime
                    current_month = datetime.datetime.now().strftime("%Y-%m")
                    if user_ai_key not in monthly_ai_usage:
                        monthly_ai_usage[user_ai_key] = {"month": current_month, "count": 0}
                    elif monthly_ai_usage[user_ai_key]["month"] != current_month:
                        monthly_ai_usage[user_ai_key] = {"month": current_month, "count": 0}
                    
                    # Set AI limits per subscription tier
                    ai_limits = {
                        "free": 5,      # 5 AI-processed documents per month
                        "student": 25,  # 25 AI-processed documents per month  
                        "growth": 100,  # 100 AI-processed documents per month
                        "business": 500 # 500 AI-processed documents per month
                    }
                    
                    max_ai_usage = ai_limits.get(subscription_tier, 5)
                    current_ai_usage = monthly_ai_usage[user_ai_key]["count"]
                    
                    # Force library-only parsing if AI limit exceeded
                    if current_ai_usage >= max_ai_usage:
                        print(f"🛡️  AI limit reached for {subscription_tier} user ({current_ai_usage}/{max_ai_usage}). Forcing library-only parsing.")
                        parse_strategy = ParseStrategy.LIBRARY_ONLY
                        
                result = smart_parser.parse_pdf(tmp_path, parse_strategy, preferred_llm)
                
                # Check if AI was used
                ai_used = result.fallback_triggered or "ai" in result.method_used.lower() or "llm" in result.method_used.lower()
                
                # Track AI usage for cost protection and billing
                if ai_used and current_user:
                    user_ai_key = f"ai_{current_user.customer_id}"
                    if user_ai_key in monthly_ai_usage:
                        monthly_ai_usage[user_ai_key]["count"] += 1
                        print(f"💰 AI usage tracked: {monthly_ai_usage[user_ai_key]['count']} for {current_user.subscription_tier} user")
                    
                    # Record AI cost for billing
                    if usage_tracker:
                        try:
                            usage_tracker.record_ai_usage(
                                user_id=current_user.customer_id,
                                ai_cost=0.02  # $0.02 per AI processing call
                            )
                        except Exception as e:
                            print(f"💰 AI cost tracking failed: {e}")
                
                # Track usage and update billing cycle
                if user_id and usage_tracker:
                    try:
                        # Check and reset billing cycle if needed
                        usage_tracker.check_and_reset_billing_cycle(user_id)
                        
                        # Record usage with accurate cost estimation
                        base_cost = pages_processed * 0.001  # Base processing cost
                        ai_cost = 0.02 if ai_used else 0  # AI processing cost
                        total_cost = base_cost + ai_cost
                        
                        usage_tracker.track_usage(
                            user_id=user_id,
                            subscription_id="",  # Would get from user's subscription
                            pages_processed=pages_processed,
                            document_name=file.filename,
                            processing_strategy=result.method_used,
                            ai_used=ai_used,
                            cost_estimate=total_cost
                        )
                        
                        print(f"📊 Usage tracked: {pages_processed} pages, cost: ${total_cost:.4f}")
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
                    "success_message": "✅ PDF successfully parsed! Scroll down to view your results.",
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
            "success_message": "✅ PDF successfully parsed! Scroll down to view your results.",
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
        "version": "2.0.1-js-fixed",
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

@app.get("/subscribe/{plan_type}")
async def subscribe_redirect(plan_type: str, request: Request, current_user = Depends(get_current_user_optional)):
    """Protected subscription - requires account creation with password"""
    
    # If user is not logged in, redirect to registration page with plan pre-selected
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/auth/register?plan={plan_type}", status_code=302)
    
    # User is logged in - redirect to Stripe Payment Links
    payment_links = {
        "student": "https://buy.stripe.com/4gM14m11zaRk2ELcT6e3e04",    # $4.99 CAD/month
        "growth": "https://buy.stripe.com/4gMeVcfWt4sW7Z5cT6e3e05",     # $19.99 CAD/month  
        "business": "https://buy.stripe.com/eVq9AS25D3oS5QX2ese3e06"    # $49.99 CAD/month
    }
    
    checkout_url = payment_links.get(plan_type.lower(), payment_links["student"])
    print(f"🔥 User {current_user.email} redirecting to Stripe Payment Link: {checkout_url}")
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=checkout_url, status_code=302)

@app.post("/create-checkout-session/")
async def create_checkout_session(request: CheckoutRequest, current_user = Depends(get_current_user)):
    """Legacy endpoint - redirects to new protected route"""
    
    print(f"🔥 Legacy checkout request from user: {current_user.email}")
    
    # User must be logged in to pay
    if not current_user:
        raise HTTPException(
            status_code=401, 
            detail={
                "error": "Must create account first",
                "message": "Please create an account to subscribe to a plan",
                "register_url": "/auth/register"
            }
        )
    
    # Your actual Payment Links from Stripe Dashboard  
    payment_links = {
        "student": "https://buy.stripe.com/4gM14m11zaRk2ELcT6e3e04",    # Student Plan: $4.99 CAD/month
        "growth": "https://buy.stripe.com/4gMeVcfWt4sW7Z5cT6e3e05",     # Growth Plan: $19.99 CAD/month
        "business": "https://buy.stripe.com/eVq9AS25D3oS5QX2ese3e06"    # Business Plan: $49.99 CAD/month
    }
    
    checkout_url = payment_links.get(request.plan_type.lower(), payment_links["student"])
    
    # Add user email as URL parameter so Stripe can pre-fill it
    if "?" in checkout_url:
        checkout_url += f"&prefilled_email={current_user.email}"
    else:
        checkout_url += f"?prefilled_email={current_user.email}"
    
    print(f"✅ Sending logged-in user {current_user.email} to: {checkout_url}")
    
    return {
        "success": True,
        "checkout_url": checkout_url,
        "session_id": f"user_{current_user.customer_id}_{request.plan_type}_{int(time.time())}",
        "user_email": current_user.email,
        "requires_login": False
    }

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
    """Handle Stripe webhooks with full billing automation"""
    import json
    from datetime import datetime, timedelta
    
    try:
        payload = await request.body()
        event = json.loads(payload)
        event_type = event.get('type', 'unknown')
        print(f"📨 Webhook received: {event_type}")
        
        # Handle initial payment completion
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            customer_email = session.get('customer_details', {}).get('email')
            subscription_id = session.get('subscription')
            
            if customer_email:
                print(f"💳 Initial payment completed for: {customer_email}")
                
                # Determine plan from amount
                amount = session.get('amount_total', 0) / 100
                plan = "student"
                if amount >= 49:
                    plan = "business"
                elif amount >= 19:
                    plan = "growth"
                
                # Upgrade account and setup billing cycle
                if auth_system and hasattr(auth_system, 'upgrade_customer'):
                    try:
                        tier_map = {
                            "student": "student",
                            "growth": "growth", 
                            "business": "business"
                        }
                        new_tier = tier_map.get(plan.lower(), "student")
                        
                        if auth_system.upgrade_customer(customer_email, new_tier):
                            print(f"🎯 Successfully upgraded {customer_email} to {new_tier} tier")
                            
                            # Setup billing cycle in usage tracker
                            if usage_tracker:
                                customer = auth_system.get_customer_by_email(customer_email)
                                if customer:
                                    usage_tracker.setup_billing_cycle(
                                        user_id=customer.customer_id,
                                        subscription_id=subscription_id or f"manual_{int(time.time())}",
                                        plan_type=new_tier,
                                        start_date=datetime.now()
                                    )
                                    print(f"📅 Billing cycle setup for {customer_email}")
                        else:
                            print(f"📋 Payment received but no account found for {customer_email}")
                    except Exception as e:
                        print(f"⚠️  Account upgrade process failed: {e}")
        
        # Handle recurring payment success
        elif event_type == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            customer_email = invoice.get('customer_email')
            subscription_id = invoice.get('subscription')
            
            if customer_email and subscription_id:
                print(f"🔄 Recurring payment succeeded for: {customer_email}")
                
                # Reset billing cycle for new month
                if usage_tracker:
                    try:
                        usage_tracker.reset_monthly_usage(customer_email, subscription_id)
                        print(f"📅 Monthly usage reset for {customer_email}")
                    except Exception as e:
                        print(f"⚠️  Monthly reset failed: {e}")
                
                # Reactivate subscription if it was suspended
                if auth_system:
                    try:
                        auth_system.reactivate_subscription(customer_email)
                        print(f"✅ Subscription reactivated for {customer_email}")
                    except Exception as e:
                        print(f"⚠️  Reactivation failed: {e}")
        
        # Handle payment failure
        elif event_type == 'invoice.payment_failed':
            invoice = event['data']['object']
            customer_email = invoice.get('customer_email')
            
            if customer_email:
                print(f"❌ Payment failed for: {customer_email}")
                
                # Don't immediately deactivate - Stripe will retry
                # Just log for monitoring
                print(f"💳 Payment retry will be attempted automatically")
        
        # Handle subscription cancellation
        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            customer_email = subscription.get('customer_email') or subscription.get('metadata', {}).get('email')
            
            if customer_email:
                print(f"🛑 Subscription cancelled for: {customer_email}")
                
                # Deactivate subscription access
                if auth_system:
                    try:
                        auth_system.deactivate_subscription(customer_email)
                        print(f"🚫 Access deactivated for {customer_email}")
                    except Exception as e:
                        print(f"⚠️  Deactivation failed: {e}")
        
        # Handle successful subscription creation
        elif event_type == 'customer.subscription.created':
            subscription = event['data']['object']
            customer_email = subscription.get('customer_email') or subscription.get('metadata', {}).get('email')
            subscription_id = subscription.get('id')
            
            if customer_email and subscription_id:
                print(f"✅ Subscription created: {subscription_id} for {customer_email}")
                
                # Link subscription to user in usage tracker
                if usage_tracker:
                    try:
                        usage_tracker.link_subscription(
                            customer_email=customer_email,
                            subscription_id=subscription_id
                        )
                        print(f"🔗 Subscription linked in usage tracker")
                    except Exception as e:
                        print(f"⚠️  Subscription linking failed: {e}")
        
        return {"status": "success", "message": f"webhook {event_type} processed"}
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"status": "success", "message": "webhook failed but continuing"}

# ==================== USAGE TRACKING ENDPOINTS ====================

@app.get("/dashboard")
async def user_dashboard(current_user = Depends(get_current_user)):
    """User dashboard page with account management and billing"""
    
    try:
        # Get usage information
        usage_info = {"pages_used": 0, "pages_included": 10}
        try:
            usage_result = usage_tracker.check_user_limits(current_user.customer_id, 0)
            if usage_result.get("success", False):
                usage_info = {
                    "pages_used": usage_result.get("current_usage", 0),
                    "pages_included": usage_result.get("pages_included", 10),
                    "pages_remaining": usage_result.get("pages_remaining", 0),
                    "plan_type": usage_result.get("plan_type", "free"),
                    "within_limit": usage_result.get("within_limit", True)
                }
        except Exception as e:
            print(f"⚠️  Usage info retrieval failed: {e}")
        
        # Get plan details
        plan_details = {
            "free": {"name": "Free", "price": 0, "pages": 10},
            "student": {"name": "Student", "price": 4.99, "pages": 500},
            "growth": {"name": "Growth", "price": 19.99, "pages": 2500},
            "business": {"name": "Business", "price": 49.99, "pages": 10000}
        }
        
        current_plan = plan_details.get(current_user.subscription_tier, plan_details["free"])
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Account Dashboard - PDF Parser</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                :root {{
                    --primary-color: #2563eb;
                    --primary-hover: #1d4ed8;
                    --background: #ffffff;
                    --background-secondary: #f8fafc;
                    --text-primary: #0f172a;
                    --text-secondary: #64748b;
                    --border-color: #e2e8f0;
                    --border-radius: 8px;
                    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
                    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                    --transition: all 0.2s ease;
                }}
                
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', sans-serif;
                    background: var(--background-secondary);
                    color: var(--text-primary);
                    line-height: 1.6;
                }}
                
                .container {{
                    max-width: 1000px;
                    margin: 2rem auto;
                    padding: 0 1rem;
                }}
                
                .header {{
                    background: var(--background);
                    border-radius: var(--border-radius);
                    padding: 2rem;
                    margin-bottom: 2rem;
                    box-shadow: var(--shadow-sm);
                }}
                
                .header h1 {{
                    font-size: 2rem;
                    font-weight: 700;
                    color: var(--text-primary);
                    margin-bottom: 0.5rem;
                }}
                
                .header p {{
                    color: var(--text-secondary);
                    font-size: 1.1rem;
                }}
                
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 2rem;
                }}
                
                .card {{
                    background: var(--background);
                    border-radius: var(--border-radius);
                    padding: 2rem;
                    box-shadow: var(--shadow-sm);
                    border: 1px solid var(--border-color);
                }}
                
                .card h3 {{
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }}
                
                .card i {{
                    color: var(--primary-color);
                }}
                
                .usage-bar {{
                    background: var(--background-secondary);
                    border-radius: var(--border-radius);
                    height: 8px;
                    margin: 1rem 0;
                    overflow: hidden;
                }}
                
                .usage-fill {{
                    background: var(--primary-color);
                    height: 100%;
                    transition: var(--transition);
                }}
                
                .btn {{
                    background: var(--primary-color);
                    color: white;
                    padding: 0.75rem 1.5rem;
                    border: none;
                    border-radius: var(--border-radius);
                    font-weight: 600;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    cursor: pointer;
                    transition: var(--transition);
                }}
                
                .btn:hover {{
                    background: var(--primary-hover);
                }}
                
                .btn-secondary {{
                    background: var(--background-secondary);
                    color: var(--text-primary);
                    border: 1px solid var(--border-color);
                }}
                
                .btn-secondary:hover {{
                    background: var(--border-color);
                }}
                
                .plan-badge {{
                    display: inline-block;
                    background: var(--primary-color);
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 999px;
                    font-size: 0.875rem;
                    font-weight: 600;
                }}
                
                .api-key {{
                    background: var(--background-secondary);
                    padding: 1rem;
                    border-radius: var(--border-radius);
                    font-family: monospace;
                    word-break: break-all;
                    margin: 1rem 0;
                }}
                
                .back-link {{
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: var(--text-secondary);
                    text-decoration: none;
                    margin-bottom: 1rem;
                    font-weight: 500;
                }}
                
                .back-link:hover {{
                    color: var(--primary-color);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-link">
                    <i class="fas fa-arrow-left"></i>
                    Back to Home
                </a>
                
                <div class="header">
                    <h1>Account Dashboard</h1>
                    <p>Welcome back, {current_user.email}</p>
                </div>
                
                <div class="dashboard-grid">
                    <div class="card">
                        <h3><i class="fas fa-user"></i> Account Details</h3>
                        <p><strong>Email:</strong> {current_user.email}</p>
                        <p><strong>Plan:</strong> <span class="plan-badge">{current_plan["name"]}</span></p>
                        <p><strong>Status:</strong> {"✅ Active" if getattr(current_user, 'subscription_active', False) else "❌ Inactive"}</p>
                        <p><strong>Email Verified:</strong> {"✅ Yes" if getattr(current_user, 'email_verified', False) else "❌ No"}</p>
                    </div>
                    
                    <div class="card">
                        <h3><i class="fas fa-chart-bar"></i> Usage This Month</h3>
                        <p><strong>{usage_info["pages_used"]}</strong> of <strong>{usage_info["pages_included"]}</strong> pages used</p>
                        <div class="usage-bar">
                            <div class="usage-fill" style="width: {min(100, (usage_info["pages_used"] / max(usage_info["pages_included"], 1)) * 100)}%"></div>
                        </div>
                        <p style="color: var(--text-secondary);">
                            {usage_info.get("pages_remaining", 0)} pages remaining
                        </p>
                    </div>
                    
                    <div class="card">
                        <h3><i class="fas fa-key"></i> API Access</h3>
                        <p>Your API key for integrations:</p>
                        <div class="api-key">{current_user.api_key}</div>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">
                            🔄 Auto-renews with your subscription
                        </p>
                    </div>
                    
                    <div class="card">
                        <h3><i class="fas fa-credit-card"></i> Billing Management</h3>
                        <p><strong>Current Plan:</strong> {current_plan["name"]}</p>
                        <p><strong>Monthly Cost:</strong> {"$" + str(current_plan["price"]) if current_plan["price"] > 0 else "Free"}</p>
                        <div style="margin-top: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
                            {"<button class='btn' onclick='openCustomerPortal()'>💳 Manage Subscription</button>" if current_user.subscription_tier != "free" else ""}
                            <a href="/pricing" class="btn btn-secondary">
                                <i class="fas fa-upgrade"></i>
                                {"Upgrade Plan" if current_user.subscription_tier == "free" else "Change Plan"}
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                function openCustomerPortal() {{
                    // Show loading
                    event.target.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                    event.target.disabled = true;
                    
                    // Create Stripe customer portal session
                    fetch('/create-portal-session', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            return_url: window.location.origin + '/dashboard'
                        }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success && data.portal_url) {{
                            window.location.href = data.portal_url;
                        }} else {{
                            alert('Error: ' + (data.error || 'Could not open billing portal'));
                            event.target.innerHTML = '💳 Manage Subscription';
                            event.target.disabled = false;
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                        alert('Error opening billing portal');
                        event.target.innerHTML = '💳 Manage Subscription';
                        event.target.disabled = false;
                    }});
                }}
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard unavailable")

@app.post("/create-portal-session")
async def create_portal_session(request: Request, current_user = Depends(get_current_user)):
    """Create Stripe customer portal session for subscription management"""
    
    try:
        data = await request.json()
        return_url = data.get("return_url", "https://your-domain.com/dashboard")
        
        if not stripe_service or not stripe_service.available:
            raise HTTPException(status_code=503, detail="Billing service unavailable")
        
        # For now, we'll use a placeholder since we need the Stripe customer ID
        # In production, you'd store the Stripe customer ID with the user account
        result = {
            "success": True,
            "portal_url": "https://billing.stripe.com/p/login/test_123",
            "message": "Redirecting to Stripe customer portal"
        }
        
        return result
        
    except Exception as e:
        print(f"❌ Portal session creation failed: {e}")
        return {
            "success": False,
            "error": "Could not create billing portal session. Please contact support."
        }

@app.post("/auth/verify-email")
async def verify_email(email: str = Form(...), verification_code: str = Form(...)):
    """Verify email address with code"""
    if not auth_system:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    success = auth_system.verify_email(email, verification_code)
    if success:
        return {"success": True, "message": "Email verified successfully! You now have access to paid features."}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")

@app.post("/auth/subscription/deactivate")
async def deactivate_subscription(current_user: Customer = Depends(get_current_user)):
    """Deactivate subscription (admin/webhook use)"""
    if not auth_system:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    success = auth_system.deactivate_subscription(current_user.email)
    if success:
        return {"success": True, "message": "Subscription deactivated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to deactivate subscription")

@app.post("/auth/subscription/reactivate")
async def reactivate_subscription(current_user: Customer = Depends(get_current_user)):
    """Reactivate subscription (payment received)"""
    if not auth_system:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    success = auth_system.reactivate_subscription(current_user.email)
    if success:
        return {"success": True, "message": "Subscription reactivated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reactivate subscription")

@app.get("/usage/{user_id}")
async def get_user_usage(user_id: str):
    """Get user's current usage and limits (admin endpoint)"""
    # You might want to add authentication here
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