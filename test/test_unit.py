import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image
import json

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, allowed_file, handle_error

# --- Unit Tests for Helper Functions ---

def test_allowed_file_valid():
    """Test allowed_file with valid extensions."""
    assert allowed_file("image.png") == True
    assert allowed_file("photo.jpg") == True
    assert allowed_file("picture.jpeg") == True
    assert allowed_file("document.JPEG") == True # Case-insensitivity check

def test_allowed_file_invalid():
    """Test allowed_file with invalid extensions."""
    assert allowed_file("archive.zip") == False
    assert allowed_file("script.py") == False
    assert allowed_file("image") == False # No extension
    assert allowed_file(".png") == False # No filename

def test_handle_error_non_ajax():
    """Test handle_error for non-AJAX requests."""
    with app.test_request_context('/'):
        rendered_html, status_code = handle_error("Test Error", 400)
        assert status_code == 400
        
        assert b"Test Error" in rendered_html.encode('utf-8')

def test_handle_error_ajax():
    """Test handle_error for AJAX requests."""
    with app.test_request_context('/', headers={'X-Requested-With': 'XMLHttpRequest'}):
        response, status_code = handle_error("AJAX Error", 400)
        assert status_code == 400
        assert response.mimetype == 'application/json'
        error_data = json.loads(response.data)
        assert error_data == {'error': 'AJAX Error'}

# --- Unit Tests for Route Logic (with mocking) ---

@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('app.remove')
@patch('app.Image.open')
def test_upload_success_mocked(mock_image_open, mock_rembg_remove, client):
    """Test successful upload with mocked image processing (AJAX)."""
    mock_img = MagicMock(spec=Image.Image)
    mock_image_open.return_value = mock_img
    mock_output_img = MagicMock(spec=Image.Image)
    mock_rembg_remove.return_value = mock_output_img
    saved_output = BytesIO()
    mock_output_img.save.side_effect = lambda buffer, format: buffer.write(b"fake_png_data")

    data = {'file': (BytesIO(b"fake_image_data"), 'test.png')}
    response = client.post('/', data=data, content_type='multipart/form-data',
                           headers={'X-Requested-With': 'XMLHttpRequest'})

    assert response.status_code == 200
    assert response.mimetype == 'image/png'
    
    expected_disposition = 'attachment; filename=test.png_rmbg.png'
    assert response.headers['Content-Disposition'] == expected_disposition
    assert response.data == b"fake_png_data"
    mock_image_open.assert_called_once()
    mock_rembg_remove.assert_called_once_with(mock_img)
    mock_output_img.save.assert_called_once()


@patch('app.remove', side_effect=Exception("Processing Failed"))
@patch('app.Image.open')
def test_upload_processing_error_mocked(mock_image_open, mock_rembg_remove, client):
    """Test image processing failure (AJAX)."""
    mock_img = MagicMock(spec=Image.Image)
    mock_image_open.return_value = mock_img

    data = {'file': (BytesIO(b"fake_image_data"), 'test.png')}
    response = client.post('/', data=data, content_type='multipart/form-data',
                           headers={'X-Requested-With': 'XMLHttpRequest'})

    assert response.status_code == 500
    assert response.mimetype == 'application/json'
    error_data = json.loads(response.data)
    assert error_data == {'error': 'Failed to process image'}
    mock_image_open.assert_called_once()
    mock_rembg_remove.assert_called_once_with(mock_img)
