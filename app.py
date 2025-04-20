from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from rembg import remove
from io import BytesIO
from PIL import Image
import os

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1014 * 1024 # 10MB Limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# UPLOAD_FOLDER = 'uploads'
# OUTPUT_FOLDER = 'outputs'

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)
# if not os.path.exists(OUTPUT_FOLDER):
#     os.makedirs(OUTPUT_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error='No file part')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file')

        if not allowed_file(file.filename):
            return render_template('index.html', error='Invalid file extension')

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
                download_name = f"{secure_filename(file.filename)}_bg_removed.png"
            )

        except Exception as e:
            app.logger.error(f"Error processing image: {e}")
            return render_template('index.html', error='Failed to process image')
    
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)