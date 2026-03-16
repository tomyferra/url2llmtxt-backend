import os
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        if self.url and not self.url.endswith('/'):
            self.url += '/'
        self.key = os.getenv("SUPABASE_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "generated-files")
        if not self.url or not self.key:
            logger.error("Supabase URL or Key not found in environment variables.")
            raise Exception("Storage configuration missing.")
            
        self.supabase: Client = create_client(self.url, self.key)

    async def upload_text_file(self, file_content: str, filename: str) -> str:
        """
        Uploads a text file to Supabase Storage and returns the public URL.
        """
        try:
            # Upload the file
            # Convert string content to bytes
            file_bytes = file_content.encode('utf-8')
            
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=filename,
                file=file_bytes,
                file_options={"content-type": "text/plain", "x-upsert": "true"}
            )
            logger.info(f"Supabase upload response: {response}")
            if response.get("error"):
                logger.error(f"Supabase upload error: {response['error']}")
                raise Exception(f"Supabase upload failed: {response['error']['message']}")
            
            # Get the public URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(filename)
            return public_url
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {e}")
            raise Exception(f"Failed to upload file to storage: {str(e)}")

