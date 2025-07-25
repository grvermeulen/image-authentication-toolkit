
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
<html>
<head>
<title>Image Authenticity Toolkit</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
.container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
.upload-section { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
.upload-form input[type="file"] { margin-right: 10px; padding: 5px; }
.upload-form input[type="submit"] { background: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
.upload-form input[type="submit"]:hover { background: #0056b3; }
.error { color: #dc3545; font-weight: bold; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
.results-container { display: flex; gap: 30px; margin-top: 20px; }
.image-section { flex: 1; }
.analysis-section { flex: 1; background: #f8f9fa; padding: 20px; border-radius: 5px; }
.result-badge { display: inline-block; padding: 5px 10px; border-radius: 15px; font-weight: bold; margin: 5px 0; }
.authentic { background: #d4edda; color: #155724; }
.manipulated { background: #f8d7da; color: #721c24; }
.unknown { background: #d1ecf1; color: #0c5460; }
.confidence-bar { width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }
.confidence-fill { height: 100%; transition: width 0.3s ease; }
.confidence-high { background: linear-gradient(90deg, #28a745, #20c997); }
.confidence-medium { background: linear-gradient(90deg, #ffc107, #fd7e14); }
.confidence-low { background: linear-gradient(90deg, #dc3545, #e83e8c); }
.metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }
.metric-card { background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }
.metric-label { font-size: 12px; color: #666; text-transform: uppercase; }
.metric-value { font-size: 18px; font-weight: bold; color: #333; }
.export-section { margin-top: 20px; padding-top: 15px; border-top: 1px solid #dee2e6; }
.export-btn { background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; text-decoration: none; display: inline-block; }
.export-btn:hover { background: #218838; }
</style>
</head>
<body>
<div class="container">
<h1>🔍 Image Authenticity Toolkit</h1>
<div class="upload-section">
  <h3>Upload Image for Analysis</h3>
  {% if error %}
    <div class="error">Error: {{ error }}</div>
  {% endif %}
  <form method=post enctype=multipart/form-data class="upload-form">
    <input type=file name=file accept="image/*">
    <input type=submit value="Analyze Image">
  </form>
</div>

{% if filename %}
<div class="results-container">
  <div class="image-section">
    <h2>📊 Analysis Results: {{ filename }}</h2>
    <div style="text-align: center;">
      <h4>Original Image</h4>
      <img src="{{ url_for('serve_ela_image', filename=filename) }}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 20px;">
      <h4>ELA Analysis</h4>
      <img src="{{ url_for('serve_ela_image', filename='ela_' + filename) }}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;">
      <p style="font-size: 12px; color: #666; margin-top: 10px;">
        ELA (Error Level Analysis) highlights areas with different compression levels, which may indicate manipulation.
      </p>
    </div>
  </div>
  
  <div class="analysis-section">
    <h3>🎯 Authentication Report</h3>
    
    <div class="result-badge {{ ela_report.result.lower() }}">
      {{ ela_report.result.upper() }}
    </div>
    
    <div style="margin: 15px 0;">
      <strong>Confidence Level: {{ ela_report.certainty }}%</strong>
      <div class="confidence-bar">
        <div class="confidence-fill {% if ela_report.certainty >= 70 %}confidence-high{% elif ela_report.certainty >= 40 %}confidence-medium{% else %}confidence-low{% endif %}" 
             style="width: {{ ela_report.certainty }}%;"></div>
      </div>
    </div>
    
    <p><strong>Analysis:</strong> {{ ela_report.description }}</p>
    
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">ELA Mean Value</div>
        <div class="metric-value">{{ "%.2f"|format(ela_report.ela_mean) }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">ELA Std Deviation</div>
        <div class="metric-value">{{ "%.2f"|format(ela_report.ela_std) }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Image Dimensions</div>
        <div class="metric-value">{{ ela_report.dimensions }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">File Size</div>
        <div class="metric-value">{{ ela_report.file_size }}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">High Variance Pixels</div>
        <div class="metric-value">{{ "%.1f"|format(ela_report.high_variance_percent) }}%</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Edge Density</div>
        <div class="metric-value">{{ "%.2f"|format(ela_report.edge_density) }}</div>
      </div>
    </div>
    
    <div style="margin-top: 20px; padding: 15px; background: white; border-radius: 5px;">
      <h4>📋 Technical Details</h4>
      <ul style="margin: 0; padding-left: 20px;">
        <li><strong>Algorithm:</strong> Error Level Analysis (ELA)</li>
        <li><strong>Threshold:</strong> Mean pixel value > 15 indicates potential manipulation</li>
        <li><strong>Analysis Method:</strong> Statistical analysis of compression artifacts</li>
        <li><strong>Confidence Factors:</strong> Mean value, standard deviation, edge detection</li>
      </ul>
    </div>
    
    <div class="export-section">
      <h4>📥 Export Results</h4>
      <a href="#" onclick="downloadReport()" class="export-btn">Download JSON Report</a>
      <a href="#" onclick="downloadSummary()" class="export-btn">Download Summary</a>
    </div>
  </div>
</div>

<script>
function downloadReport() {
  const report = {
    filename: "{{ filename }}",
    result: "{{ ela_report.result }}",
    certainty: {{ ela_report.certainty }},
    description: "{{ ela_report.description }}",
    metrics: {
      ela_mean: {{ ela_report.ela_mean }},
      ela_std: {{ ela_report.ela_std }},
      dimensions: "{{ ela_report.dimensions }}",
      file_size: "{{ ela_report.file_size }}",
      high_variance_percent: {{ ela_report.high_variance_percent }},
      edge_density: {{ ela_report.edge_density }}
    },
    timestamp: new Date().toISOString()
  };
  
  const blob = new Blob([JSON.stringify(report, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'image_analysis_report_{{ filename }}.json';
  a.click();
  URL.revokeObjectURL(url);
}

function downloadSummary() {
  const summary = `Image Authentication Report
========================
File: {{ filename }}
Result: {{ ela_report.result }}
Confidence: {{ ela_report.certainty }}%
Analysis: {{ ela_report.description }}

Technical Metrics:
- ELA Mean Value: {{ "%.2f"|format(ela_report.ela_mean) }}
- ELA Standard Deviation: {{ "%.2f"|format(ela_report.ela_std) }}
- Image Dimensions: {{ ela_report.dimensions }}
- File Size: {{ ela_report.file_size }}
- High Variance Pixels: {{ "%.1f"|format(ela_report.high_variance_percent) }}%
- Edge Density: {{ "%.2f"|format(ela_report.edge_density) }}

Generated: ${new Date().toLocaleString()}
`;
  
  const blob = new Blob([summary], {type: 'text/plain'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'image_analysis_summary_{{ filename }}.txt';
  a.click();
  URL.revokeObjectURL(url);
}
</script>
{% endif %}
</div>
</body>
</html>
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
    ela_report = {"description": "No analysis performed yet.", "result": "Unknown", "certainty": 0, 
                 "ela_mean": 0, "ela_std": 0, "dimensions": "Unknown", "file_size": "Unknown",
                 "high_variance_percent": 0, "edge_density": 0}
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
        # Enhanced ELA report analysis
        ela_path = os.path.join(app.config['UPLOAD_FOLDER'], f'ela_{filename}')
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        ela_report = {"description": "No ELA image found.", "result": "Unknown", "certainty": 0, 
                     "ela_mean": 0, "ela_std": 0, "dimensions": "Unknown", "file_size": "Unknown",
                     "high_variance_percent": 0, "edge_density": 0}
        
        if os.path.exists(ela_path) and os.path.exists(original_path):
            try:
                ela_img = Image.open(ela_path).convert('L')
                ela_arr = np.array(ela_img)
                mean_val = ela_arr.mean()
                std_val = ela_arr.std()
                
                orig_img = Image.open(original_path)
                file_size = os.path.getsize(original_path)
                file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                
                high_variance_threshold = mean_val + std_val
                high_variance_pixels = np.sum(ela_arr > high_variance_threshold)
                high_variance_percent = (high_variance_pixels / ela_arr.size) * 100
                
                edges = np.abs(np.diff(ela_arr, axis=0)).sum() + np.abs(np.diff(ela_arr, axis=1)).sum()
                edge_density = edges / ela_arr.size
                
                base_confidence = 50
                mean_factor = min(40, (mean_val / 255) * 100)
                std_factor = min(20, (std_val / 50) * 20)
                variance_factor = min(20, high_variance_percent * 2)
                edge_factor = min(10, edge_density / 10)
                
                if mean_val > 15:
                    result = "Manipulated"
                    certainty = min(100, int(base_confidence + mean_factor + std_factor + variance_factor))
                    description = f"Analysis indicates potential manipulation. ELA shows bright areas (mean: {mean_val:.1f}) suggesting inconsistent compression levels. High variance regions ({high_variance_percent:.1f}%) and edge artifacts support this assessment."
                else:
                    result = "Authentic"
                    certainty = max(30, int(100 - mean_factor - (std_factor/2) - (variance_factor/2)))
                    description = f"Analysis suggests the image is likely authentic. ELA shows mostly uniform compression (mean: {mean_val:.1f}) with low variance regions ({high_variance_percent:.1f}%), indicating consistent processing throughout the image."
                
                ela_report = {
                    "description": description,
                    "result": result,
                    "certainty": certainty,
                    "ela_mean": mean_val,
                    "ela_std": std_val,
                    "dimensions": f"{orig_img.width} × {orig_img.height}",
                    "file_size": file_size_str,
                    "high_variance_percent": high_variance_percent,
                    "edge_density": edge_density
                }
                
            except Exception as e:
                ela_report = {
                    "description": f"Error analyzing ELA image: {e}", 
                    "result": "Unknown", 
                    "certainty": 0,
                    "ela_mean": 0, 
                    "ela_std": 0, 
                    "dimensions": "Unknown", 
                    "file_size": "Unknown",
                    "high_variance_percent": 0, 
                    "edge_density": 0
                }
    return render_template_string(HTML, filename=filename, error=error, ela_report=ela_report)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
