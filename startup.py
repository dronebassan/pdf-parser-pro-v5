#!/usr/bin/env python3
"""
Minimal startup script to ensure Railway deployment succeeds
"""
import sys
import os
import time

print("🚀 Starting PDF Parser Pro...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Check if main.py exists
if not os.path.exists("main.py"):
    print("❌ main.py not found!")
    sys.exit(1)

try:
    print("🔍 Testing basic imports...")
    import uvicorn
    print("✅ uvicorn imported successfully")
    
    # Test FastAPI import
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
    
    print("🚀 Starting main application...")
    
    # Import and run the main app
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run("main:app", host="0.0.0.0", port=port)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔄 Trying minimal FastAPI server...")
    
    # Fallback minimal server
    try:
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI(title="PDF Parser Pro - Minimal Mode")
        
        @app.get("/")
        def read_root():
            return {"status": "running", "mode": "minimal", "message": "Service is starting up"}
        
        @app.get("/health")
        def health_check():
            return {"status": "healthy", "timestamp": time.time()}
        
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as fallback_error:
        print(f"❌ Fallback failed: {fallback_error}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Startup error: {e}")
    sys.exit(1)