from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from app.services.scraper import ScraperService
from app.services.text_converter import TextConverterService
from app.services.storage import StorageService
import logging
from datetime import datetime
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

class ConvertRequest(BaseModel):
    url: HttpUrl

class ConvertResponse(BaseModel):
    download_url: str
    content: str

@router.post("/convert", response_model=ConvertResponse)
async def convert_url_to_txt(request: ConvertRequest):
    loop = asyncio.get_running_loop()
    logger.info(f"Current event loop type: {type(loop).__name__}")
    logger.info(request)
    try:
        url_str = str(request.url)
        logger.info(f"Processing URL: {url_str}")
        
        # 1. Fetch HTML
        html_content = await ScraperService.fetch_html(url_str)
        logger.info(f"HTML Content: {html_content}")
        # 2. Extract Text
        #content_data = TextConverterService.ai_enhancer_text(html_content)
        content_data = TextConverterService.extract_text(html_content)

        if not content_data:
            raise HTTPException(status_code=400, detail="No readable text found on the page.")
            
        title=content_data['title']
        datetime_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # 3. Generate Filename
        filename = f"{title}-{datetime_now}-llm.txt"
        # 4. Upload to Storage
        storage_service = StorageService()
        download_url = await storage_service.upload_text_file(content_data['text'], filename)
        
        return ConvertResponse(
            download_url=download_url,
            content=content_data['text']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
