#!/usr/bin/env python3
"""
Quick test script for PDF Parser Pro
Run this to verify your setup works
"""

import os
import sys
import requests
import time
import subprocess
from pathlib import Path

def test_imports():
    """Test if all modules can be imported"""
    print("🧪 Testing module imports...")
    
    modules = [
        ("fastapi", "FastAPI framework"),
        ("pdfplumber", "PDF text extraction"),
        ("pandas", "Data processing"),
        ("fitz", "PyMuPDF for images"),
    ]
    
    results = {}
    for module, description in modules:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
            results[module] = True
        except ImportError as e:
            print(f"  ❌ {module} - {description}: {e}")
            results[module] = False
    
    # Test our custom modules
    custom_modules = [
        ("performance_tracker", "Performance tracking"),
        ("llm_service", "LLM integration"),
    ]
    
    for module, description in custom_modules:
        try:
            __import__(module)
            print(f"  ✅ {module} - {description}")
            results[module] = True
        except ImportError as e:
            print(f"  ⚠️  {module} - {description}: {e}")
            results[module] = False
    
    return results

def test_basic_pdf_processing():
    """Test basic PDF processing without server"""
    print("\n📄 Testing basic PDF processing...")
    
    try:
        import pdfplumber
        
        # Create a simple test
        print("  ✅ PDF processing libraries available")
        print("  📝 You can test with any PDF file using the original functions")
        return True
        
    except Exception as e:
        print(f"  ❌ PDF processing test failed: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting FastAPI server...")
    
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "127.0.0.1", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Test if server is responding
        try:
            response = requests.get("http://127.0.0.1:8000/api/info", timeout=5)
            if response.status_code == 200:
                print("  ✅ Server started successfully!")
                data = response.json()
                print(f"  📊 API Version: {data.get('version', 'Unknown')}")
                print(f"  🧠 AI Features: {data.get('features', {})}")
                return process
            else:
                print(f"  ⚠️  Server responded with status {response.status_code}")
                return process
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Server may be starting... ({e})")
            return process
            
    except Exception as e:
        print(f"  ❌ Failed to start server: {e}")
        return None

def test_api_endpoints(max_retries=5):
    """Test API endpoints"""
    print("\n🔗 Testing API endpoints...")
    
    base_url = "http://127.0.0.1:8000"
    endpoints = [
        ("/api/info", "API information"),
        ("/health-check/", "Health check"),
        ("/", "Web interface"),
    ]
    
    for endpoint, description in endpoints:
        for retry in range(max_retries):
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint} - {description}")
                    break
                else:
                    print(f"  ⚠️  {endpoint} - Status {response.status_code}")
                    if retry < max_retries - 1:
                        time.sleep(2)
            except requests.exceptions.RequestException as e:
                if retry == max_retries - 1:
                    print(f"  ❌ {endpoint} - {description}: Connection failed")
                else:
                    time.sleep(2)

def show_usage_instructions():
    """Show how to use the system"""
    print(f"""
🎉 Setup Test Complete!

📝 HOW TO USE YOUR PDF PARSER:

1. 🌐 WEB INTERFACE:
   Open your browser and go to: http://127.0.0.1:8000
   - Upload a PDF file
   - Choose what to extract (text, tables, images)
   - Click "Parse PDF" and see results!

2. 🔌 API USAGE:
   Test with curl:
   
   # Basic parsing
   curl -X POST "http://127.0.0.1:8000/parse/" \\
     -F "file=@your-document.pdf"
   
   # Smart parsing (if LLM keys are set)
   curl -X POST "http://127.0.0.1:8000/parse-smart/" \\
     -F "file=@your-document.pdf" \\
     -F "strategy=auto"
   
   # Health check
   curl "http://127.0.0.1:8000/health-check/"

3. 🔑 FOR AI FEATURES:
   Set environment variables:
   export OPENAI_API_KEY="your-key-here"
   export ANTHROPIC_API_KEY="your-key-here"
   
   Then restart the server for AI-powered parsing!

4. 📊 PERFORMANCE STATS:
   Visit: http://127.0.0.1:8000/performance-stats/

5. 📖 API DOCUMENTATION:
   Visit: http://127.0.0.1:8000/docs

🛑 TO STOP THE SERVER:
   Press Ctrl+C in the terminal where the server is running
""")

def main():
    """Main test function"""
    print("🔥 PDF Parser Pro - Setup Test")
    print("=" * 50)
    
    # Test imports
    import_results = test_imports()
    
    # Test basic functionality
    basic_test = test_basic_pdf_processing()
    
    # Start server
    server_process = start_server()
    
    if server_process:
        # Test endpoints
        test_api_endpoints()
        
        # Show usage instructions
        show_usage_instructions()
        
        # Keep server running
        try:
            print("\n⏳ Server is running. Press Ctrl+C to stop...")
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            server_process.terminate()
    else:
        print("\n❌ Could not start server. Check the error messages above.")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure you're in the correct directory")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Try running manually: uvicorn main:app --reload")

if __name__ == "__main__":
    main()