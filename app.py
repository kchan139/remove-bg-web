from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from rembg import remove
from io import BytesIO
from PIL import Image
from typing import Tuple
import os

app = Flask(__name__)
app.config['MAX_FILE_SIZE'] = 10 * 1024 * 1024 # 10MB Limit
ALLOWED_EXTENSION = {'png', 'jpg', 'jpeg'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[0] != '' and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION


def handle_error(message: str, status_code: int):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': message}), status_code
    else:
        return render_template('index.html', error=message), status_code
    

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return handle_error('No file part', 400)

        file = request.files['file']
        if file.filename == '':
            return handle_error('No selected file', 400)
        
        if not allowed_file(file.filename):
            return handle_error('Invalid file extension', 400)
        
        try:
            input_image = Image.open(file.stream)
            output_buffer = BytesIO()
            output_image = remove(input_image)
            output_image.save(output_buffer, format='PNG')
            output_buffer.seek(0)

            return send_file(
                output_buffer,
                mimetype = 'image/png',
                as_attachment = True,
                download_name = f"{secure_filename(file.filename)}_rmbg.png"
            )

        except Exception as e:
            app.logger.error(f"Error processing image: {e}")
            return handle_error('Failed to process image', 500)
    
    return render_template('index.html')



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)