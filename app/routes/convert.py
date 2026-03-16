from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, validator
from typing import Any
from app.services.scraper import ScraperService
from app.services.text_converter import TextConverterService
from app.services.storage import StorageService
import logging
from datetime import datetime
import asyncio
import re

router = APIRouter()
logger = logging.getLogger(__name__)

class ConvertRequest(BaseModel):
    url: Any

    @validator('url')
    def validate_url(cls, v):
        if v is None:
            raise ValueError("URL cannot be null")
        if not isinstance(v, str):
            raise ValueError("Invalid input type")
        if not v.strip():
            raise ValueError("URL cannot be empty")
        
        # Simple URL validation or use HttpUrl internally
        if not (v.startswith('http://') or v.startswith('https://')):
             # Match the test expectation "Invalid URL provided: {url}"
             raise ValueError(f"Invalid URL provided: {v}")
        return v

class ConvertResponse(BaseModel):
    download_url: str
    content: str
    filename: str

@router.post("/convert", response_model=ConvertResponse)
async def convert_url_to_txt(request: ConvertRequest):
    try:
        url_str = str(request.url)
        logger.info(f"Processing URL: {url_str}")
        
        # 1. Fetch HTML
        html_content = await ScraperService.fetch_html(url_str)
        # 2. Extract Text
        content_data = TextConverterService.ai_enhancer_text(html_content, url_str)

        if not content_data:
            raise HTTPException(status_code=400, detail="No readable text found on the page.")
            
        title = content_data['title']
        # Sanitize title: replace spaces/dashes/special chars with hyphens, keep alphanumerics
        try:
            safe_title = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to sanitize title: {str(e)}")
        datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # 3. Generate Filename
        filename = f"{safe_title}-{datetime_now}-llm.txt"
        # 4. Upload to Storage
        storage_service = StorageService()
        download_url = await storage_service.upload_text_file(content_data['text'], filename)
        
        return ConvertResponse(
            download_url=download_url,
            content=content_data['text'],
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
