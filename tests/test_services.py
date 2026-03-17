import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.text_converter import TextConverterService
from app.services.scraper import ScraperService
from app.services.storage import StorageService




class TestTextConverterService(unittest.TestCase):
    def test_extract_text_basic(self):
        html = "<html><head><title>Test Title</title></head><body><h1>Main Heading</h1><p>Some content.</p></body></html>"
        result = TextConverterService.extract_text(html)
        self.assertEqual(result["title"], "Test Title")
        self.assertIn("Main Heading", result["text"])
        self.assertIn("Some content.", result["text"])

    def test_extract_text_sanitization(self):
        # Test title sanitization for filenames
        html = "<html><head><title>Test/Title:With?Chars</title></head><body><p>Content</p></body></html>"
        result = TextConverterService.extract_text(html)
        self.assertNotIn("/", result["title"])
        self.assertNotIn(":", result["title"])
        self.assertNotIn("?", result["title"])

    def test_extract_text_links(self):
        html = '<html><body><p>Check this <a href="https://example.com/info">more info</a>.</p></body></html>'
        result = TextConverterService.extract_text(html, base_url="https://example.com")
        
        self.assertIn("more info (Link: https://example.com/info)", result["text"])
        self.assertIn("BaseURL: https://example.com", result["text"])

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_ai_enhancer_text(self, mock_configure, mock_model_class):
        # Configure mock
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Mocked AI Content"
        mock_model_class.return_value = mock_model

        html = "<html><head><title>Test Title</title></head><body><p>Content</p></body></html>"
        result = TextConverterService.ai_enhancer_text(html)
        self.assertEqual(result["title"], "Test Title")
        self.assertEqual(result["text"], "Mocked AI Content")

class TestScraperService(unittest.IsolatedAsyncioTestCase):
    @patch("app.services.scraper.ScraperService._fetch_html_in_thread")
    async def test_fetch_html(self, mock_fetch_html_in_thread):
        mock_fetch_html_in_thread.return_value = "<html><body><h1>Test Title</h1><p>Test Content</p></body></html>"
        url = "https://example.com"
        html = await ScraperService.fetch_html(url)
        self.assertIn("Test Title", html)
        self.assertNotIn("example", html)

    @patch("app.services.scraper.asyncio")
    @patch("app.services.scraper.ScraperService._fetch_html_impl")
    def test_fetch_html_in_thread_win32(self, mock_fetch_html_impl, mock_asyncio):

        mock_loop = MagicMock()
        mock_asyncio.ProactorEventLoop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = "<html><body><h1>Test Title</h1><p>Test Content</p></body></html>"
        mock_loop.close.return_value = True

        mock_fetch_html_impl.return_value = "mock_coroutine"
        url = "https://example.com"
        html = ScraperService._fetch_html_in_thread(url)
        self.assertTrue(html)

    @patch("app.services.scraper.asyncio")
    @patch("app.services.scraper.sys")
    @patch("app.services.scraper.ScraperService._fetch_html_impl")
    def test_fetch_html_in_thread_not_win32(self, mock_fetch_html_impl, mock_asyncio, mock_sys):

        mock_sys.platform = "not-win32"
        mock_loop = MagicMock()
        mock_asyncio.new_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = "<html><body><h1>Test Title</h1><p>Test Content</p></body></html>"
        mock_loop.close.return_value = True

        mock_fetch_html_impl.return_value = "mock_coroutine"
        url = "https://example.com"
        html = ScraperService._fetch_html_in_thread(url)
        self.assertTrue(html)

    @patch("app.services.scraper.asyncio.sleep")
    @patch("app.services.scraper.async_playwright")
    async def test_fetch_html_impl(self, mock_playwright, mock_sleep):
        # Mock the async context manager
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p
        
        # Mock the browser
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        
        # Mock the context
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        
        # Mock the page
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_page.content.return_value = "<html><body><h1>Test Title</h1><p>Test Content</p></body></html>"
        
        url = "https://example.com"
        html = await ScraperService._fetch_html_impl(url)
        self.assertIn("Test Title", html)
        self.assertTrue(mock_page.goto.called)
        self.assertTrue(mock_browser.close.called)


def getenv_side_effect(key, default=None):
    values = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "SUPABASE_BUCKET": "test-bucket",
    }
    return values.get(key, default)

class TestStorageService(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.env_patcher = patch.dict("os.environ", {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key",
            "SUPABASE_BUCKET": "test-bucket",
        }, clear=True)
        self.env_patcher.start()
        self.client_patcher = patch("app.services.storage.create_client")
        self.mock_create_client = self.client_patcher.start()
        self.mock_supabase = MagicMock()
        self.mock_create_client.return_value = self.mock_supabase
        self.service = StorageService()

    def tearDown(self):
        self.env_patcher.stop()
        self.client_patcher.stop()

    def test_init_no_url(self):
        with patch.dict("os.environ", {
            "SUPABASE_URL": "",
            "SUPABASE_KEY": "test-key",
            "SUPABASE_BUCKET": "test-bucket",
        }, clear=True):
            with self.assertRaises(Exception) as context:
                StorageService()
        self.assertEqual(str(context.exception), "Storage configuration missing.")

    def test_init_no_key(self):
        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "",
            "SUPABASE_BUCKET": "test-bucket",
        }, clear=True):
            with self.assertRaises(Exception) as context:
                StorageService()
        self.assertEqual(str(context.exception), "Storage configuration missing.")

    def test_init_success(self):
        self.assertEqual(self.service.url, "https://test.supabase.co/")
        self.assertEqual(self.service.key, "test-key")
        self.assertEqual(self.service.bucket_name, "test-bucket")
        self.assertEqual(self.service.supabase, self.mock_supabase)

    async def test_upload_text_file_success(self):
        mock_bucket = MagicMock()
        mock_bucket.get_public_url.return_value = "https://public-url/file.txt"

        self.mock_supabase.storage.from_.return_value = mock_bucket

        result = await self.service.upload_text_file(
            "hello world",
            "file.txt"
        )

        mock_bucket.upload.assert_called_once_with(
            path="file.txt",
            file=b"hello world",
            file_options={"content-type": "text/plain", "x-upsert": "true"},
        )

        mock_bucket.get_public_url.assert_called_once_with("file.txt")

        self.assertEqual(result, "https://public-url/file.txt")

    async def test_upload_text_file_failure(self):
        mock_bucket = MagicMock()
        mock_bucket.upload.side_effect = Exception("upload error")

        self.mock_supabase.storage.from_.return_value = mock_bucket

        with self.assertRaises(Exception) as context:
            await self.service.upload_text_file("hello", "file.txt")

        self.assertIn("Failed to upload file to storage", str(context.exception))