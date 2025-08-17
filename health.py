#!/usr/bin/env python3
"""
Simple health check script for Railway deployment
"""

import os
import sys
import requests

def check_health():
    """Check if the service is healthy"""
    try:
        # Try to import core modules
        import fastapi
        import uvicorn
        import pdfplumber
        import fitz
        print("✅ Core dependencies available")
        
        # Check if Gemini API key is available
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            print("✅ GEMINI_API_KEY configured")
        else:
            print("⚠️  GEMINI_API_KEY not configured")
        
        # Check environment
        env = os.getenv("ENVIRONMENT", "development")
        print(f"✅ Environment: {env}")
        
        # Check port
        port = os.getenv("PORT", "8000")
        print(f"✅ Port: {port}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        print("\n🚀 Service ready for deployment!")
        sys.exit(0)
    else:
        print("\n❌ Service not ready")
        sys.exit(1)