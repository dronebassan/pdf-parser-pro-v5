#!/usr/bin/env python3
import os
import sys
import time

print("🚀 Starting PDF Parser Pro - FULL VERSION")

# Try to start the full main app first
try:
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🎯 Starting FULL APP on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
    
except Exception as e:
    print(f"⚠️  Full app failed: {e}")
    print("🔄 Starting minimal fallback...")
    
    # Minimal fallback
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title="PDF Parser Pro - Fallback")
    
    @app.get("/")
    def root():
        return {"status": "fallback_mode", "message": "Main app failed to start"}
    
    @app.get("/health")
    def health():
        return {"status": "healthy", "time": time.time()}
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")