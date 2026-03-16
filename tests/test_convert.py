import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from tests.base import BaseTestCase


class TestConvert(BaseTestCase):

    @patch("app.routes.convert.StorageService")
    @patch("app.routes.convert.ScraperService")
    @patch("app.routes.convert.TextConverterService")
    def test_convert_url_success(self, mock_converter_class, mock_scraper_service, mock_storage_class):
        # StorageService is instantiated, so we mock the instance method
        mock_storage_instance = mock_storage_class.return_value
        mock_storage_instance.upload_text_file = AsyncMock(return_value="https://example.com/file.txt")
        
        # ScraperService.fetch_html is a static method called on the class
        mock_scraper_service.fetch_html = AsyncMock(return_value="<html><body><h1>Test Title</h1><p>Test Content</p></body></html>")
        
        # TextConverterService.ai_enhancer_text is a static method called on the class
        mock_converter_class.ai_enhancer_text = MagicMock(return_value={
            "title": "Test Title",
            "text": "Cleaned Test Content"
        })

        # Valid URL input
        response = self.client.post(
            "/convert",
            json={"url": "https://www.google.com"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("download_url", data)
        self.assertEqual(data["content"], "Cleaned Test Content")
        self.assertIn("llm.txt", data["filename"])

    def test_convert_invalid_url_type(self):
        # Testing input types: Non-URL string
        response = self.client.post(
            "/convert",
            json={"url": "not-a-url"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid URL provided: not-a-url")

    def test_convert_invalid_data_type(self):
        # Testing input types: Integer instead of string URL
        response = self.client.post(
            "/convert",
            json={"url": 12345}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid input type", response.json()["detail"])

    def test_convert_missing_url(self):
        # Testing input types: Missing field
        response = self.client.post(
            "/convert",
            json={}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Missing required field: url")

    def test_convert_null_url(self):
        # Testing input types: Null value
        response = self.client.post(
            "/convert",
            json={"url": None}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "URL cannot be null")

    def test_convert_empty_url(self):
        # Testing input types: Empty string
        response = self.client.post(
            "/convert",
            json={"url": ""}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "URL cannot be empty")

    @patch("app.routes.convert.StorageService")
    @patch("app.routes.convert.ScraperService")
    @patch("app.routes.convert.TextConverterService")
    def test_convert_scraper_failure(self, mock_converter_class, mock_scraper_service, mock_storage_class):
        # Mock scraper service to raise an exception
        mock_scraper_service.fetch_html = AsyncMock(side_effect=Exception("Scraper failed"))
        
        response = self.client.post(
            "/convert",
            json={"url": "https://example.com"}
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("Scraper failed", response.json()["detail"])

    @patch("app.routes.convert.StorageService")
    @patch("app.routes.convert.ScraperService")
    @patch("app.routes.convert.TextConverterService")
    def test_convert_no_text_found(self, mock_converter_class, mock_scraper_service, mock_storage_class):
        # Mock text converter to return no text
        mock_converter_class.ai_enhancer_text.return_value = None
        
        # Mock scraper to succeed
        mock_scraper_service.fetch_html = AsyncMock(return_value="<html></html>")

        response = self.client.post(
            "/convert",
            json={"url": "https://example.com"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "No readable text found on the page.")

    @patch("app.routes.convert.ScraperService")
    @patch("app.routes.convert.TextConverterService")
    def test_convert_sanitize_title_failure(self, mock_converter_class, mock_scraper_service):
        # Mock text converter to return None title, which triggers an exception in re.sub
        mock_converter_class.ai_enhancer_text = MagicMock(return_value={
            "title": None,
            "text": "Cleaned Test Content"
        })                
        # Mock scraper to succeed
        mock_scraper_service.fetch_html = AsyncMock(return_value="<html><body><h1>Test Title</h1><p>Test Content</p></body></html>")

        response = self.client.post(
            "/convert",
            json={"url": "https://example.com"}
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to sanitize title", response.json()["detail"])
