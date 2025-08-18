#!/usr/bin/env python3
import os
import sys
import time

# MINIMAL SERVER - NO IMPORTS THAT CAN FAIL
try:
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI(title="PDF Parser Pro")
    
    @app.get("/")
    def root():
        return {"status": "online", "service": "PDF Parser Pro"}
    
    @app.get("/health")
    def health():
        return {"status": "healthy", "time": time.time()}
    
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    sys.exit(1)