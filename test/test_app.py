import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image
from app import app, allowed_file

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    def test_allowed_file(self):
        self.assertTrue(allowed_file('image.jpg'))
        self.assertTrue(allowed_file('photo.jpeg'))
        self.assertTrue(allowed_file('picture.png'))
        self.assertFalse(allowed_file('document.pdf'))
        self.assertFalse(allowed_file('script.js'))
        
    def test_upload_no_file(self):
        response = self.client.post('/')
        self.assertIn(b'No file part', response.data)
        
    def test_upload_empty_filename(self):
        data = {
            'file': (BytesIO(b''), '')
        }
        response = self.client.post('/', data=data, content_type='multipart/form-data')
        self.assertIn(b'No selected file', response.data)
        
    def test_upload_invalid_extension(self):
        data = {
            'file': (BytesIO(b'test data'), 'test.txt')
        }
        response = self.client.post('/', data=data, content_type='multipart/form-data')
        self.assertIn(b'Invalid file extension', response.data)