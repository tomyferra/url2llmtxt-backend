from tests.base import BaseTestCase
from fastapi.exceptions import RequestValidationError

class TestMain(BaseTestCase):
    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_raise_custom_exception(self):
        response = self.client.post("/convert", json={"url": "invalid-url"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid URL provided",response.json()["detail"])
