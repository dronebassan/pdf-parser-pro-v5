#!/usr/bin/env python3
"""
Test Gemini integration
"""

import os
import base64
from llm_service import create_llm_service

def test_gemini_integration():
    """Test if Gemini integration is working"""
    print("🧪 Testing Gemini Integration")
    print("=" * 40)
    
    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        print("   Set it with: export GEMINI_API_KEY='your-key-here'")
        print("   Get your key from: https://aistudio.google.com/app/apikey")
        return False
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:8]}...{api_key[-4:]}")
    
    # Test service creation
    try:
        service = create_llm_service("gemini")
        if service:
            print("✅ Gemini service created successfully")
            print(f"   Model: {service.config.model}")
            return True
        else:
            print("❌ Failed to create Gemini service")
            return False
    except Exception as e:
        print(f"❌ Error creating Gemini service: {e}")
        return False

if __name__ == "__main__":
    test_gemini_integration()
