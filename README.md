# Backend - URL to TXT Converter

Minimal FastAPI backend that scrapes webpages and converts them to text files stored in Supabase.

## Setup

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env` and fill in your Supabase credentials.

4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Deployment on Vercel

1. Install Vercel CLI.
2. Run `vercel` in the `backend/` directory.
3. Configure the environment variables on the Vercel dashboard.
