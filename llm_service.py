import os
import base64
import json
import time
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
import anthropic
import google.generativeai as genai
from PIL import Image
import io
import fitz

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

@dataclass
class ParseResult:
    text: str
    tables: List[Dict]
    images: List[Dict]
    confidence_score: float
    processing_time: float
    method: str
    provider: Optional[str] = None

@dataclass
class LLMConfig:
    provider: LLMProvider
    api_key: str
    model: str
    max_tokens: int = 4000
    temperature: float = 0.1

class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        if self.config.provider == LLMProvider.OPENAI:
            return openai.OpenAI(api_key=self.config.api_key)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return anthropic.Anthropic(api_key=self.config.api_key)
        elif self.config.provider == LLMProvider.GEMINI:
            genai.configure(api_key=self.config.api_key)
            return genai
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def pdf_to_images(self, pdf_path: str, max_pages: int = 10) -> List[str]:
        """Convert PDF pages to base64 encoded images with enhanced quality for blurry text"""
        images = []
        pdf_document = fitz.open(pdf_path)
        
        pages_to_process = min(len(pdf_document), max_pages)
        
        for page_num in range(pages_to_process):
            page = pdf_document[page_num]
            # Render page as image with higher DPI for better text recognition
            # Increased from 2.0 to 3.0 for better quality on blurry text
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            images.append(img_base64)
        
        pdf_document.close()
        return images
    
    def parse_with_llm(self, pdf_path: str) -> ParseResult:
        """Parse PDF using LLM vision capabilities"""
        start_time = time.time()
        
        # Convert PDF to images
        images = self.pdf_to_images(pdf_path)
        
        if self.config.provider == LLMProvider.OPENAI:
            result = self._parse_with_openai(images)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            result = self._parse_with_anthropic(images)
        elif self.config.provider == LLMProvider.GEMINI:
            result = self._parse_with_gemini(images)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
        
        processing_time = time.time() - start_time
        
        return ParseResult(
            text=result.get('text', ''),
            tables=result.get('tables', []),
            images=result.get('images', []),
            confidence_score=result.get('confidence_score', 0.8),
            processing_time=processing_time,
            method="llm",
            provider=self.config.provider.value
        )
    
    def parse_with_llm_from_images(self, images: List[str]) -> ParseResult:
        """Parse from pre-converted images (for individual page processing)"""
        start_time = time.time()
        
        if self.config.provider == LLMProvider.OPENAI:
            result = self._parse_with_openai(images)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            result = self._parse_with_anthropic(images)
        elif self.config.provider == LLMProvider.GEMINI:
            result = self._parse_with_gemini(images)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
        
        processing_time = time.time() - start_time
        
        return ParseResult(
            text=result.get('text', ''),
            tables=result.get('tables', []),
            images=result.get('images', []),
            confidence_score=result.get('confidence_score', 0.8),
            processing_time=processing_time,
            method="llm",
            provider=self.config.provider.value
        )
    
    def _parse_with_openai(self, images: List[str]) -> Dict:
        """Parse using OpenAI GPT-4V"""
        system_prompt = """You are an expert PDF parser with special skills for handling blurry or low-quality text. Analyze the provided PDF page images and extract:

1. **All readable text content** - Even if text appears blurry, try your best to read it. If text is unclear, note it in the confidence score.
2. **Any tables** - Preserve the structure and relationships between data
3. **Descriptions of images/charts** - Describe what you see in any images, graphs, or charts
4. **Confidence score (0-1)** - Rate how confident you are in the extraction quality:
   - 0.9-1.0: Clear, crisp text
   - 0.7-0.8: Slightly blurry but readable
   - 0.5-0.6: Moderately blurry, some uncertainty
   - 0.3-0.4: Very blurry, significant uncertainty
   - 0.1-0.2: Extremely blurry, mostly guessing

**Special instructions for blurry text:**
- Try to read text even if it's not perfectly clear
- Use context clues to fill in unclear characters
- If you're unsure about a word, include it with a note about uncertainty
- Pay extra attention to numbers, dates, and important data

Return your response in this JSON format:
{
    "text": "extracted text content",
    "tables": [{"page": 1, "table_data": [...], "headers": [...]}],
    "images": [{"page": 1, "description": "description of image"}],
    "confidence_score": 0.95,
    "text_quality_notes": "Any notes about text clarity or readability issues"
}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please extract all content from these PDF pages:"}
                ]
            }
        ]
        
        # Add images to the message
        for i, img_base64 in enumerate(images):
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}",
                    "detail": "high"
                }
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    "text": content,
                    "tables": [],
                    "images": [],
                    "confidence_score": 0.6
                }
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return {
                "text": "",
                "tables": [],
                "images": [],
                "confidence_score": 0.0
            }
    
    def _parse_with_anthropic(self, images: List[str]) -> Dict:
        """Parse using Claude 3.5 Sonnet"""
        system_prompt = """You are an expert PDF parser with special skills for handling blurry or low-quality text. Analyze the provided PDF page images and extract:

1. **All readable text content** - Even if text appears blurry, try your best to read it. If text is unclear, note it in the confidence score.
2. **Any tables** - Preserve the structure and relationships between data
3. **Descriptions of images/charts** - Describe what you see in any images, graphs, or charts
4. **Confidence score (0-1)** - Rate how confident you are in the extraction quality:
   - 0.9-1.0: Clear, crisp text
   - 0.7-0.8: Slightly blurry but readable
   - 0.5-0.6: Moderately blurry, some uncertainty
   - 0.3-0.4: Very blurry, significant uncertainty
   - 0.1-0.2: Extremely blurry, mostly guessing

**Special instructions for blurry text:**
- Try to read text even if it's not perfectly clear
- Use context clues to fill in unclear characters
- If you're unsure about a word, include it with a note about uncertainty
- Pay extra attention to numbers, dates, and important data

Return your response in this JSON format:
{
    "text": "extracted text content",
    "tables": [{"page": 1, "table_data": [...], "headers": [...]}],
    "images": [{"page": 1, "description": "description of image"}],
    "confidence_score": 0.95,
    "text_quality_notes": "Any notes about text clarity or readability issues"
}
"""
        
        content = [{"type": "text", "text": "Please extract all content from these PDF pages:"}]
        
        # Add images to content
        for img_base64 in images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })
        
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": content}]
            )
            
            content_text = response.content[0].text
            
            # Try to parse JSON response
            try:
                return json.loads(content_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    "text": content_text,
                    "tables": [],
                    "images": [],
                    "confidence_score": 0.6
                }
                
        except Exception as e:
            print(f"Anthropic API error: {e}")
            return {
                "text": "",
                "tables": [],
                "images": [],
                "confidence_score": 0.0
            }

    def _parse_with_gemini(self, images: List[str]) -> Dict:
        """Parse using Gemini 2.5 Flash"""
        system_prompt = """You are an expert PDF parser with special skills for handling blurry or low-quality text. Analyze the provided PDF page images and extract:

1. **All readable text content** - Even if text appears blurry, try your best to read it. If text is unclear, note it in the confidence score.
2. **Any tables** - Preserve the structure and relationships between data
3. **Descriptions of images/charts** - Describe what you see in any images, graphs, or charts
4. **Confidence score (0-1)** - Rate how confident you are in the extraction quality:
   - 0.9-1.0: Clear, crisp text
   - 0.7-0.8: Slightly blurry but readable
   - 0.5-0.6: Moderately blurry, some uncertainty
   - 0.3-0.4: Very blurry, significant uncertainty
   - 0.1-0.2: Extremely blurry, mostly guessing

**Special instructions for blurry text:**
- Try to read text even if it's not perfectly clear
- Use context clues to fill in unclear characters
- If you're unsure about a word, include it with a note about uncertainty
- Pay extra attention to numbers, dates, and important data

Return your response in this JSON format:
{
    "text": "extracted text content",
    "tables": [{"page": 1, "table_data": [...], "headers": [...]}],
    "images": [{"page": 1, "description": "description of image"}],
    "confidence_score": 0.95,
    "text_quality_notes": "Any notes about text clarity or readability issues"
}
"""
        
        try:
            # Create the model
            model = genai.GenerativeModel(self.config.model)
            
            # Prepare the content - start with text
            content_parts = [f"{system_prompt}\n\nPlease extract all content from these PDF pages:"]
            
            # Add images to content
            for i, img_base64 in enumerate(images):
                # Convert base64 to bytes for Gemini
                img_bytes = base64.b64decode(img_base64)
                content_parts.append({
                    "mime_type": "image/png",
                    "data": img_bytes
                })
            
            # Generate content
            response = model.generate_content(
                content_parts,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
            )
            
            content_text = response.text
            
            # Try to parse JSON response
            try:
                return json.loads(content_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    "text": content_text,
                    "tables": [],
                    "images": [],
                    "confidence_score": 0.6
                }
                
        except Exception as e:
            print(f"Gemini API error: {e}")
            return {
                "text": "",
                "tables": [],
                "images": [],
                "confidence_score": 0.0
            }

def create_llm_service(provider: str = "openai") -> Optional[LLMService]:
    """Factory function to create LLM service based on environment variables"""
    if provider.lower() == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables")
            return None
        
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key=api_key,
            model="gpt-4-vision-preview"
        )
    elif provider.lower() == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not found in environment variables")
            return None
        
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            api_key=api_key,
            model="claude-3-5-sonnet-20241022"
        )
    elif provider.lower() == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
            return None
        
        config = LLMConfig(
            provider=LLMProvider.GEMINI,
            api_key=api_key,
            model="gemini-2.0-flash-exp"
        )
    else:
        print(f"Unsupported provider: {provider}")
        return None
    
    return LLMService(config)