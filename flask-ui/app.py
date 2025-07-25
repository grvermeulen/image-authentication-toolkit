
from flask import Flask, render_template_string, request, send_from_directory
import requests
import os
import shutil
from werkzeug.utils import secure_filename
from urllib.parse import unquote
from PIL import Image
import numpy as np

app = Flask(__name__)
UPLOAD_FOLDER = './images'
STATIC_FOLDER = './static'
os.makedirs(STATIC_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

HTML = '''
<!doctype html>
<title>Image Authenticity Toolkit</title>
<h1>Upload Image for Analysis</h1>
{% if error %}
  <div style="color: red; font-weight: bold;">Error: {{ error }}</div>
{% endif %}
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
{% if filename %}
  <div style="display: flex; align-items: flex-start; gap: 40px;">
    <div>
      <h2>Results for: {{ filename }}</h2>
      <img src="{{ url_for('serve_ela_image', filename='ela_' + filename) }}" height="300"><br>
    </div>
    <div style="max-width: 400px;">
      <h3>ELA Report</h3>
      <p>{{ ela_report.description }}</p>
      <b>Result:</b> {{ ela_report.result }}<br>
      <b>Certainty:</b> {{ ela_report.certainty }}%
    </div>
  </div>
{% endif %}
'''

@app.route('/ela_images/<path:filename>')
def serve_ela_image(filename):
    from urllib.parse import unquote
    import os
    decoded = unquote(filename)
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], decoded)
    print(f"[DEBUG] Requested: {filename}", flush=True)
    print(f"[DEBUG] Decoded: {decoded}", flush=True)
    print(f"[DEBUG] Full path: {full_path}", flush=True)
    print(f"[DEBUG] Exists: {os.path.exists(full_path)}", flush=True)
    return send_from_directory(app.config['UPLOAD_FOLDER'], decoded)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    filename = None
    error = None
    if request.method == 'POST':
        f = request.files['file']
        base_filename = os.path.basename(f.filename)
        safe_filename = secure_filename(base_filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        try:
            f.save(filepath)
            print(f"[INFO] Saved uploaded file to {filepath}", flush=True)
        except Exception as e:
            error = f"Failed to save uploaded file: {e}"
            print(f"[ERROR] {error}", flush=True)
            return render_template_string(HTML, filename=None, error=error)
        try:
            # Send the file to foto-forensics with the sanitized filename as a parameter
            response = requests.post('http://foto-forensics:5000/upload', files={'file': open(filepath, 'rb')}, data={'filename': safe_filename})
            print(f"[INFO] Sent file to foto-forensics, response status: {response.status_code}", flush=True)
        except Exception as e:
            error = f"Failed to send file to foto-forensics: {e}"
            print(f"[ERROR] {error}", flush=True)
            return render_template_string(HTML, filename=None, error=error)
        filename = safe_filename
        # ELA report analysis
        ela_path = os.path.join(app.config['UPLOAD_FOLDER'], f'ela_{filename}')
        ela_report = {"description": "No ELA image found.", "result": "Unknown", "certainty": 0}
        if os.path.exists(ela_path):
            try:
                ela_img = Image.open(ela_path).convert('L')
                ela_arr = np.array(ela_img)
                mean_val = ela_arr.mean()
                # Heuristic: mean > 15 = manipulated, else authentic
                if mean_val > 15:
                    ela_report = {
                        "description": "Bright areas in the ELA image suggest possible manipulation or inconsistent compression.",
                        "result": "Manipulated",
                        "certainty": min(100, int((mean_val/255)*100 + 50))
                    }
                else:
                    ela_report = {
                        "description": "The ELA image is mostly dark, indicating uniform compression and no obvious signs of manipulation.",
                        "result": "Authentic",
                        "certainty": max(0, 100 - int((mean_val/255)*100 + 10))
                    }
            except Exception as e:
                ela_report = {"description": f"Error analyzing ELA image: {e}", "result": "Unknown", "certainty": 0}
    return render_template_string(HTML, filename=filename, error=error, ela_report=ela_report)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
