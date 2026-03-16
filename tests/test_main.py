from tests.base import BaseTestCase

class TestMain(BaseTestCase):
    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
