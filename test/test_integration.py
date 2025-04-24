import pytest
from io import BytesIO
import json
from unittest.mock import patch, MagicMock
from PIL import Image

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    # Set MAX_FILE_SIZE to a small value for testing limits
    app.config['MAX_FILE_SIZE'] = 100 # 100 bytes
    with app.test_client() as client:
        yield client

def create_dummy_image(file_format='PNG') -> BytesIO:
    """Creates a dummy image in memory."""
    img = Image.new('RGB', (60, 30), color = 'red')
    buffer = BytesIO()
    img.save(buffer, format=file_format)
    buffer.seek(0)
    return buffer

# --- Integration Tests ---

def test_get_index(client):
    """Test GET request to the index page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Remove Background" in response.data

# --- POST Request Tests (Simulating Browser/AJAX) ---

@patch('app.remove')
@patch('app.Image.open')
def test_post_valid_image_ajax(mock_image_open, mock_rembg_remove, client):
    """Test successful POST with a valid image (AJAX)."""
    # --- Mocking Setup ---
    mock_input_img = MagicMock(spec=Image.Image)
    mock_image_open.return_value = mock_input_img
    mock_output_img = MagicMock(spec=Image.Image)
    mock_rembg_remove.return_value = mock_output_img
    
    def mock_save(buffer, format):
        buffer.write(b"processed_png_data")
    mock_output_img.save.side_effect = mock_save
    # --- /Mocking Setup ---

    image_data = create_dummy_image('PNG')
    data = {'file': (image_data, 'test.png')}

    response = client.post('/', data=data, content_type='multipart/form-data',
                           headers={'X-Requested-With': 'XMLHttpRequest'}) # AJAX header

    assert response.status_code == 200
    assert response.mimetype == 'image/png'
    assert response.headers['Content-Disposition'] == 'attachment; filename=test.png_rmbg.png'
    assert response.data == b"processed_png_data"
    mock_image_open.assert_called_once()
    mock_rembg_remove.assert_called_once_with(mock_input_img)
    mock_output_img.save.assert_called_once()


def test_post_no_file_ajax(client):
    """Test POST request with no file part (AJAX)."""
    response = client.post('/', data={}, content_type='multipart/form-data',
                           headers={'X-Requested-With': 'XMLHttpRequest'})
    assert response.status_code == 400
    assert response.mimetype == 'application/json'
    assert json.loads(response.data) == {'error': 'No file part'}

def test_post_no_file_non_ajax(client):
    """Test POST request with no file part (Non-AJAX)."""
    response = client.post('/', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.mimetype == 'text/html'
    assert b"No file part" in response.data # Error message in HTML

def test_post_empty_filename_ajax(client):
    """Test POST request with an empty filename (AJAX)."""
    data = {'file': (BytesIO(b""), '')}
    response = client.post('/', data=data, content_type='multipart/form-data',
                           headers={'X-Requested-With': 'XMLHttpRequest'})
    assert response.status_code == 400
    assert response.mimetype == 'application/json'
    assert json.loads(response.data) == {'error': 'No selected file'}

def test_post_empty_filename_non_ajax(client):
    """Test POST request with an empty filename (Non-AJAX)."""
    data = {'file': (BytesIO(b""), '')}
    response = client.post('/', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.mimetype == 'text/html'
    assert b"No selected file" in response.data

def test_post_invalid_extension_ajax(client):
    """Test POST request with invalid file extension (AJAX)."""
    data = {'file': (BytesIO(b"some data"), 'test.txt')}
    response = client.post('/', data=data, content_type='multipart/form-data',
                           headers={'X-Requested-With': 'XMLHttpRequest'})
    assert response.status_code == 400
    assert response.mimetype == 'application/json'
    assert json.loads(response.data) == {'error': 'Invalid file extension'}

def test_post_invalid_extension_non_ajax(client):
    """Test POST request with invalid file extension (Non-AJAX)."""
    data = {'file': (BytesIO(b"some data"), 'test.txt')}
    response = client.post('/', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.mimetype == 'text/html'
    assert b"Invalid file extension" in response.data

@patch('app.remove', side_effect=Exception("Processing Failed"))
@patch('app.Image.open')
def test_post_processing_error_ajax(mock_image_open, mock_rembg_remove, client):
    """Test POST request resulting in a processing error (AJAX)."""
    # --- Mocking Setup ---
    mock_input_img = MagicMock(spec=Image.Image)
    mock_image_open.return_value = mock_input_img
    # --- /Mocking Setup ---

    image_data = create_dummy_image('PNG')
    data = {'file': (image_data, 'error.png')}
    response = client.post('/', data=data, content_type='multipart/form-data',
                           headers={'X-Requested-With': 'XMLHttpRequest'})

    assert response.status_code == 500
    assert response.mimetype == 'application/json'
    assert json.loads(response.data) == {'error': 'Failed to process image'}
    mock_image_open.assert_called_once()
    mock_rembg_remove.assert_called_once_with(mock_input_img)


@patch('app.remove', side_effect=Exception("Processing Failed"))
@patch('app.Image.open')
def test_post_processing_error_non_ajax(mock_image_open, mock_rembg_remove, client):
    """Test POST request resulting in a processing error (Non-AJAX)."""
    
    mock_input_img = MagicMock(spec=Image.Image)
    mock_image_open.return_value = mock_input_img

    image_data = create_dummy_image('PNG')
    data = {'file': (image_data, 'error.png')}
    response = client.post('/', data=data, content_type='multipart/form-data')

    assert response.status_code == 500
    assert response.mimetype == 'text/html'
    assert b"Failed to process image" in response.data # Error message in HTML
    mock_image_open.assert_called_once()
    mock_rembg_remove.assert_called_once_with(mock_input_img)
