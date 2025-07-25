
from flask import Flask, request, send_file
from PIL import Image, ImageChops, ImageEnhance
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        f = request.files['file']
        # Use sanitized filename from POST data if provided, else sanitize the uploaded filename
        safe_filename = request.form.get('filename')
        if not safe_filename:
            from werkzeug.utils import secure_filename
            safe_filename = secure_filename(f.filename)
        path = f"./images/{safe_filename}"
        f.save(path)

        from PIL import Image, ImageChops, ImageEnhance
        im = Image.open(path).convert('RGB')
        im.save('temp.jpg', quality=95)
        temp = Image.open('temp.jpg')

        diff = ImageChops.difference(im, temp)
        diff = ImageEnhance.Brightness(diff).enhance(10)
        ela_path = f"./images/ela_{safe_filename}"
        diff.save(ela_path)

        print(f"[INFO] ELA image saved to {ela_path}", flush=True)
        return send_file(ela_path, mimetype='image/jpeg')
    except Exception as e:
        print(f"[ERROR] Exception in upload_image: {e}", flush=True)
        return f"Error processing image: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
