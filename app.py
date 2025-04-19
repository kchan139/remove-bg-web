from flask import Flask, render_template, request, send_file
from rembg import remove
from PIL import Image
import io
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

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
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            try:
                output_buffer = io.BytesIO()
                input_image = Image.open(filename)
                output_image = remove(input_image)
                output_image.save(output_buffer, format="PNG")
                output_buffer.seek(0)
                os.remove(filename)
                return send_file(
                    output_buffer,
                    mimetype='image/png',
                    as_attachment=True,
                    download_name='removed_background.png'
                )
            except Exception as e:
                os.remove(filename)
                return render_template('index.html', error=f'Error processing image: {e}')
        else:
            return render_template('index.html', error='Allowed file types are png, jpg, jpeg')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)