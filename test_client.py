#!/usr/bin/env python3
"""
Simple test client for the PDF Parser API
"""
import requests
import json

# API base URL (adjust if running on different host/port)
BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print("✅ API Health Check:")
        print(json.dumps(response.json(), indent=2))
        return True
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Start it with: uvicorn main:app --reload")
        return False

def test_parse_pdf(pdf_path):
    """Test PDF parsing with all options"""
    try:
        with open(pdf_path, 'rb') as file:
            files = {'file': file}
            data = {
                'extract_text_flag': True,
                'extract_tables_flag': True,
                'extract_images_flag': True
            }
            
            response = requests.post(f"{BASE_URL}/parse/", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully parsed {pdf_path}")
                print(f"📄 Text length: {len(result.get('text', ''))}")
                print(f"📊 Tables found: {len(result.get('tables', []))}")
                print(f"🖼️  Images found: {len(result.get('images', []))}")
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
    except FileNotFoundError:
        print(f"❌ File not found: {pdf_path}")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_extract_text_only(pdf_path):
    """Test text-only extraction"""
    try:
        with open(pdf_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(f"{BASE_URL}/extract-text/", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Text extraction successful")
                print(f"📄 Text preview: {result['text'][:200]}...")
                return result
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    print("🧪 Testing PDF Parser API")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        exit(1)
    
    print("\n" + "=" * 50)
    
    # Ask user for PDF file path
    pdf_path = input("Enter path to a PDF file to test (or press Enter to skip): ").strip()
    
    if pdf_path:
        print(f"\n🔍 Testing with file: {pdf_path}")
        print("-" * 30)
        
        # Test full parsing
        print("\n1. Testing full parsing...")
        test_parse_pdf(pdf_path)
        
        # Test text-only extraction
        print("\n2. Testing text-only extraction...")
        test_extract_text_only(pdf_path)
    else:
        print("\n⏭️  Skipping file tests")
    
    print("\n" + "=" * 50)
    print("🎉 Testing complete!")
    print("\nTo use the API:")
    print("1. Start the server: uvicorn main:app --reload")
    print("2. Visit http://localhost:8000/docs for interactive API documentation")
    print("3. Use curl or any HTTP client to send PDF files to the endpoints")
