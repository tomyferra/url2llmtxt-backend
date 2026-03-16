import sys
import asyncio

# Playwright on Windows requires ProactorEventLoop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import convert
from app.services.storage import StorageService
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="URL2LLM.txt Converter API")

# Custom exception handler for Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if not errors:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid request body"}
        )
    
    error = errors[0]
    # Pydantic 2 error messages often start with "Value error, "
    msg = error.get("msg", "Validation error")
    if msg.startswith("Value error, "):
        detail = msg.replace("Value error, ", "")
    else:
        type = error.get("type", "")
        field = ".".join(str(loc) for loc in error.get("loc", []))
        
        if "missing" in type:
            detail = f"Missing required field: {field.split('.')[-1]}"
        elif "url" in type:
            detail = f"Invalid URL provided"
        elif "type" in type:
             detail = f"Invalid input type"
        else:
            detail = f"Validation Error: {msg}"
         
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": detail}
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(convert.router, tags=["Conversion"])

@app.get("/")
def root():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
