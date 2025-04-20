import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image
import numpy as np
from app import app

class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        img = Image.new('RGB', (100, 100), color='white')
        draw = Image.new('RGB', (60, 60), color='red')
        img.paste(draw, (20, 20))
        
        self.test_img_io = BytesIO()
        img.save(self.test_img_io, format='PNG')
        self.test_img_io.seek(0)
        
        self.result_img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        red_square = Image.new('RGBA', (60, 60), (255, 0, 0, 255))
        self.result_img.paste(red_square, (20, 20))
        
    @patch('app.remove')
    def test_successful_image_processing(self, mock_remove):
        mock_result = self.result_img
        mock_remove.return_value = mock_result
        
        data = {
            'file': (self.test_img_io, 'test.png')
        }
        
        with self.client as client:
            response = client.post('/', data=data, content_type='multipart/form-data', buffered=True)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/png')
            self.assertEqual(response.headers['Content-Disposition'], 
                            'attachment; filename=test.png_bg_removed.png')
            
            mock_remove.assert_called_once()
        
    @patch('app.remove')
    def test_error_handling(self, mock_remove):
        mock_remove.side_effect = Exception("Processing error")
        
        data = {
            'file': (self.test_img_io, 'test.png')
        }
        response = self.client.post('/', data=data, content_type='multipart/form-data')
        
        self.assertIn(b'Failed to process image', response.data)