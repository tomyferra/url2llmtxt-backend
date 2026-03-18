# Backend - URL to TXT Converter

Minimal FastAPI backend that scrapes webpages and converts them to text files stored in Supabase.

## Setup

```bash
git clone https://github.com/tomyferra/url2llmtxt-backend.git
cd url2llmtxt-backend
python -m venv venv && venv\Scripts\activate  # Windows
python -m venv venv && source venv/bin/activate  # MacOS
pip install -r requirements.txt
playwright install chromium               # Install Playwright browser binaries
python -m uvicorn app.main:app --reload                  # Dev server on :8000
```

Run tests:
```bash
cd url2llmtxt-backend
pytest tests/                         # All tests
pytest tests/test_convert.py          # Single file
pytest tests/test_convert.py::TestConvertEndpoint::test_successful_conversion  # Single test
```
