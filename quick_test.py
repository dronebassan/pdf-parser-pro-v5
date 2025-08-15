#!/usr/bin/env python3
"""
Super simple test - just start the server
"""

import subprocess
import sys
import time

def main():
    print("🚀 Starting PDF Parser Pro...")
    print("=" * 40)
    
    try:
        # Start the server
        print("Starting server at http://localhost:8000")
        print("Press Ctrl+C to stop\n")
        
        # Run uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n🔧 Try installing dependencies:")
        print("pip install fastapi uvicorn pdfplumber pymupdf pandas")

if __name__ == "__main__":
    main()