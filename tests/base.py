import unittest
from fastapi.testclient import TestClient
from app.main import app

class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
