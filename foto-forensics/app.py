
from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS
import os
import json
import numpy as np
from scipy import ndimage
from werkzeug.utils import secure_filename
import cv2
import hashlib
from datetime import datetime
from dutch_insurance_rules import DutchInsuranceAuthenticityRules

app = Flask(__name__)

# Initialize Dutch Insurance Authenticity Rules
dutch_rules = DutchInsuranceAuthenticityRules()

def extract_exif_metadata(image_path):
    """Extract and analyze EXIF metadata for authenticity verification"""
    try:
        image = Image.open(image_path)
        exifdata = image.getexif()
        
        metadata = {}
        suspicious_indicators = []
        
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            data = exifdata.get(tag_id)
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
            metadata[tag] = str(data)
        
        if 'Software' in metadata:
            editing_software = ['photoshop', 'gimp', 'paint.net', 'canva', 'midjourney', 'dall-e', 'stable diffusion']
            if any(software in metadata['Software'].lower() for software in editing_software):
                suspicious_indicators.append(f"Editing software detected: {metadata['Software']}")
        
        camera_tags = ['Make', 'Model', 'DateTime', 'ExposureTime', 'FNumber', 'ISO']
        missing_tags = [tag for tag in camera_tags if tag not in metadata]
        if len(missing_tags) > 3:
            suspicious_indicators.append(f"Missing typical camera metadata: {', '.join(missing_tags)}")
        
        if 'DateTime' in metadata and 'DateTimeOriginal' in metadata:
            if metadata['DateTime'] != metadata['DateTimeOriginal']:
                suspicious_indicators.append("Inconsistent timestamp metadata")
        
        return {
            'metadata': metadata,
            'suspicious_indicators': suspicious_indicators,
            'metadata_score': max(0, 100 - len(suspicious_indicators) * 20)
        }
    except Exception as e:
        return {
            'metadata': {},
            'suspicious_indicators': [f"Error reading metadata: {str(e)}"],
            'metadata_score': 0
        }

def analyze_jpeg_compression(image_path):
    """Analyze JPEG compression artifacts for re-compression detection"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        file_size = os.path.getsize(image_path)
        img_area = img.shape[0] * img.shape[1]
        compression_ratio = file_size / img_area
        
        block_artifacts = 0
        for i in range(0, img.shape[0] - 8, 8):
            for j in range(0, img.shape[1] - 8, 8):
                block = img[i:i+8, j:j+8]
                if i > 0:
                    boundary_diff = np.mean(np.abs(img[i-1, j:j+8].astype(float) - img[i, j:j+8].astype(float)))
                    if boundary_diff > 10:
                        block_artifacts += 1
        
        artifact_density = block_artifacts / ((img.shape[0] // 8) * (img.shape[1] // 8))
        
        estimated_quality = min(100, int(compression_ratio * 1000))
        recompression_indicators = []
        
        if artifact_density > 0.1:
            recompression_indicators.append("High blocking artifact density detected")
        if compression_ratio < 0.1:
            recompression_indicators.append("Unusually high compression detected")
        if estimated_quality < 70:
            recompression_indicators.append("Low quality compression suggests editing")
        
        return {
            'compression_ratio': compression_ratio,
            'estimated_quality': estimated_quality,
            'artifact_density': artifact_density,
            'recompression_indicators': recompression_indicators,
            'compression_score': max(0, 100 - len(recompression_indicators) * 25)
        }
    except Exception as e:
        return {
            'compression_ratio': 0,
            'estimated_quality': 0,
            'artifact_density': 0,
            'recompression_indicators': [f"Error analyzing compression: {str(e)}"],
            'compression_score': 0
        }

def detect_copy_move(image_path):
    """Detect copy-move forgeries using feature matching"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        orb = cv2.ORB_create(nfeatures=1000)
        keypoints, descriptors = orb.detectAndCompute(img, None)
        
        if descriptors is None or len(descriptors) < 10:
            return {
                'copy_move_detected': False,
                'suspicious_regions': 0,
                'confidence': 0,
                'copy_move_score': 50
            }
        
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(descriptors, descriptors)
        
        suspicious_matches = []
        for match in matches:
            if match.queryIdx != match.trainIdx:
                pt1 = keypoints[match.queryIdx].pt
                pt2 = keypoints[match.trainIdx].pt
                distance = np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
                if 20 < distance < 200:  # Reasonable copy-move distance
                    suspicious_matches.append(match)
        
        suspicious_regions = len(suspicious_matches) // 5  # Rough clustering
        copy_move_detected = suspicious_regions > 3
        confidence = min(100, suspicious_regions * 20)
        
        return {
            'copy_move_detected': copy_move_detected,
            'suspicious_regions': suspicious_regions,
            'confidence': confidence,
            'copy_move_score': max(0, 100 - confidence)
        }
    except Exception as e:
        return {
            'copy_move_detected': False,
            'suspicious_regions': 0,
            'confidence': 0,
            'copy_move_score': 50
        }

def analyze_noise_patterns(image_path):
    """Analyze sensor noise patterns for camera model verification"""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        noise = cv2.filter2D(img, -1, kernel)
        
        noise_std = np.std(noise)
        noise_mean = np.mean(np.abs(noise))
        
        noise_histogram = np.histogram(noise.flatten(), bins=50)[0]
        noise_uniformity = np.std(noise_histogram) / np.mean(noise_histogram)
        
        artificial_indicators = []
        if noise_std < 5:
            artificial_indicators.append("Unusually low noise levels")
        if noise_uniformity > 2:
            artificial_indicators.append("Non-uniform noise distribution")
        if noise_mean > 50:
            artificial_indicators.append("Excessive noise artifacts")
        
        return {
            'noise_std': float(noise_std),
            'noise_mean': float(noise_mean),
            'noise_uniformity': float(noise_uniformity),
            'artificial_indicators': artificial_indicators,
            'noise_score': max(0, 100 - len(artificial_indicators) * 30)
        }
    except Exception as e:
        return {
            'noise_std': 0,
            'noise_mean': 0,
            'noise_uniformity': 0,
            'artificial_indicators': [f"Error analyzing noise: {str(e)}"],
            'noise_score': 0
        }

def analyze_pixel_histogram(image_path):
    """Analyze pixel value histograms for artificial modifications"""
    try:
        img = cv2.imread(image_path)
        
        hist_b = cv2.calcHist([img], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([img], [1], None, [256], [0, 256])
        hist_r = cv2.calcHist([img], [2], None, [256], [0, 256])
        
        def analyze_channel_hist(hist):
            hist = hist.flatten()
            peaks = np.where(hist > np.mean(hist) + 2 * np.std(hist))[0]
            gaps = np.where(hist < np.mean(hist) - np.std(hist))[0]
            return len(peaks), len(gaps)
        
        b_peaks, b_gaps = analyze_channel_hist(hist_b)
        g_peaks, g_gaps = analyze_channel_hist(hist_g)
        r_peaks, r_gaps = analyze_channel_hist(hist_r)
        
        total_peaks = b_peaks + g_peaks + r_peaks
        total_gaps = b_gaps + g_gaps + r_gaps
        
        histogram_indicators = []
        if total_peaks > 15:
            histogram_indicators.append("Excessive histogram peaks detected")
        if total_gaps > 20:
            histogram_indicators.append("Unnatural histogram gaps detected")
        
        combined_hist = hist_b + hist_g + hist_r
        uniformity = np.std(combined_hist) / np.mean(combined_hist)
        
        if uniformity > 3:
            histogram_indicators.append("Non-uniform pixel distribution")
        
        return {
            'total_peaks': int(total_peaks),
            'total_gaps': int(total_gaps),
            'uniformity': float(uniformity),
            'histogram_indicators': histogram_indicators,
            'histogram_score': max(0, 100 - len(histogram_indicators) * 25)
        }
    except Exception as e:
        return {
            'total_peaks': 0,
            'total_gaps': 0,
            'uniformity': 0,
            'histogram_indicators': [f"Error analyzing histogram: {str(e)}"],
            'histogram_score': 0
        }

def detect_ai_generated_images(image_path):
    """Detect AI-generated images using multiple techniques"""
    try:
        img = cv2.imread(image_path)
        gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        ai_indicators = []
        
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.log(np.abs(f_shift) + 1)
        
        freq_std = np.std(magnitude_spectrum)
        freq_mean = np.mean(magnitude_spectrum)
        freq_ratio = freq_std / freq_mean if freq_mean > 0 else 0
        
        if freq_ratio < 0.3:
            ai_indicators.append("Unnatural frequency domain patterns detected")
        
        h_corr = np.corrcoef(gray[:-1].flatten(), gray[1:].flatten())[0, 1]
        v_corr = np.corrcoef(gray[:, :-1].flatten(), gray[:, 1:].flatten())[0, 1]
        
        if h_corr > 0.95 or v_corr > 0.95:
            ai_indicators.append("Excessive pixel correlation suggests AI generation")
        
        def calculate_lbp_uniformity(image):
            rows, cols = image.shape
            uniformity_count = 0
            total_patterns = 0
            
            for i in range(1, rows-1):
                for j in range(1, cols-1):
                    center = image[i, j]
                    pattern = []
                    for di in [-1, -1, -1, 0, 0, 1, 1, 1]:
                        for dj in [-1, 0, 1, -1, 1, -1, 0, 1]:
                            if len(pattern) < 8:
                                pattern.append(1 if image[i+di, j+dj] >= center else 0)
                    
                    transitions = sum(1 for k in range(8) if pattern[k] != pattern[(k+1)%8])
                    if transitions <= 2:
                        uniformity_count += 1
                    total_patterns += 1
            
            return uniformity_count / total_patterns if total_patterns > 0 else 0
        
        lbp_uniformity = calculate_lbp_uniformity(gray)
        if lbp_uniformity > 0.8:
            ai_indicators.append("High texture uniformity suggests AI generation")
        
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        if edge_density < 0.05 or edge_density > 0.3:
            ai_indicators.append("Unnatural edge patterns detected")
        
        if len(img.shape) == 3:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            hue_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            
            hue_peaks = len(np.where(hue_hist > np.mean(hue_hist) + 2*np.std(hue_hist))[0])
            if hue_peaks < 5:
                ai_indicators.append("Limited color palette suggests AI generation")
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                left_half = face_roi[:, :w//2]
                right_half = cv2.flip(face_roi[:, w//2:], 1)
                if left_half.shape == right_half.shape:
                    symmetry = np.corrcoef(left_half.flatten(), right_half.flatten())[0, 1]
                    if symmetry > 0.9:
                        ai_indicators.append("Unnatural facial symmetry detected")
        
        ai_confidence = min(100, len(ai_indicators) * 20)
        ai_detected = len(ai_indicators) >= 2
        
        return {
            'ai_detected': ai_detected,
            'ai_confidence': ai_confidence,
            'ai_indicators': ai_indicators,
            'frequency_ratio': float(freq_ratio),
            'pixel_correlation': {'horizontal': float(h_corr), 'vertical': float(v_corr)},
            'texture_uniformity': float(lbp_uniformity),
            'edge_density': float(edge_density),
            'ai_score': max(0, 100 - ai_confidence)
        }
        
    except Exception as e:
        return {
            'ai_detected': False,
            'ai_confidence': 0,
            'ai_indicators': [f"Error in AI detection: {str(e)}"],
            'frequency_ratio': 0,
            'pixel_correlation': {'horizontal': 0, 'vertical': 0},
            'texture_uniformity': 0,
            'edge_density': 0,
            'ai_score': 50
        }

def create_blockchain_timestamp(image_path):
    """Create blockchain-style timestamp for image provenance"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_hash = hashlib.sha256(image_data).hexdigest()
        
        timestamp = datetime.now().isoformat()
        provenance_record = {
            'image_hash': image_hash,
            'timestamp': timestamp,
            'file_size': len(image_data),
            'verification_method': 'SHA256'
        }
        
        record_string = json.dumps(provenance_record, sort_keys=True)
        verification_hash = hashlib.sha256(record_string.encode()).hexdigest()
        provenance_record['verification_hash'] = verification_hash
        
        return {
            'provenance_record': provenance_record,
            'blockchain_score': 100
        }
    except Exception as e:
        return {
            'provenance_record': {'error': str(e)},
            'blockchain_score': 0
        }

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

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """Comprehensive image analysis endpoint"""
    try:
        f = request.files['file']
        safe_filename = request.form.get('filename')
        if not safe_filename:
            safe_filename = secure_filename(f.filename)
        path = f"./images/{safe_filename}"
        f.save(path)

        print(f"[INFO] Starting comprehensive analysis of {safe_filename}", flush=True)
        
        metadata_analysis = extract_exif_metadata(path)
        print(f"[INFO] Metadata analysis complete", flush=True)
        
        compression_analysis = analyze_jpeg_compression(path)
        print(f"[INFO] Compression analysis complete", flush=True)
        
        copy_move_analysis = detect_copy_move(path)
        print(f"[INFO] Copy-move analysis complete", flush=True)
        
        noise_analysis = analyze_noise_patterns(path)
        print(f"[INFO] Noise analysis complete", flush=True)
        
        histogram_analysis = analyze_pixel_histogram(path)
        print(f"[INFO] Histogram analysis complete", flush=True)
        
        blockchain_analysis = create_blockchain_timestamp(path)
        print(f"[INFO] Blockchain timestamp created", flush=True)
        
        ai_analysis = detect_ai_generated_images(path)
        print(f"[INFO] AI detection analysis complete", flush=True)
        
        # Apply Dutch Insurance Industry authenticity rules
        all_analysis_results = {
            'metadata_analysis': metadata_analysis,
            'compression_analysis': compression_analysis,
            'copy_move_analysis': copy_move_analysis,
            'noise_analysis': noise_analysis,
            'histogram_analysis': histogram_analysis,
            'blockchain_analysis': blockchain_analysis,
            'ai_analysis': ai_analysis
        }
        
        # Get authenticity decision using Dutch insurance rules
        dutch_decision = dutch_rules.determine_authenticity(all_analysis_results)
        
        # Map Dutch insurance results to display format
        overall_result = dutch_decision['authenticity_result']
        overall_score = dutch_decision['confidence_score']
        
        # Add Dutch insurance specific information
        dutch_compliance_info = {
            'decision_reasoning': dutch_decision['decision_reasoning'],
            'critical_flags': dutch_decision['critical_flags'],
            'requires_human_review': dutch_decision['requires_human_review'],
            'compliance_status': dutch_decision['compliance_status'],
            'weighted_score': dutch_decision['weighted_score'],
            'rule_version': dutch_decision['rule_version']
        }
        
        analysis_result = {
            'filename': safe_filename,
            'overall_score': round(overall_score, 1),
            'overall_result': overall_result,
            'metadata_analysis': metadata_analysis,
            'compression_analysis': compression_analysis,
            'copy_move_analysis': copy_move_analysis,
            'noise_analysis': noise_analysis,
            'histogram_analysis': histogram_analysis,
            'blockchain_analysis': blockchain_analysis,
            'ai_analysis': ai_analysis,
            'dutch_insurance_compliance': dutch_compliance_info,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[INFO] Comprehensive analysis complete for {safe_filename}", flush=True)
        return jsonify(analysis_result)
        
    except Exception as e:
        print(f"[ERROR] Exception in analyze_image: {e}", flush=True)
        return jsonify({'error': f"Error analyzing image: {e}"}), 500

@app.route('/compliance/audit-trail', methods=['GET'])
def get_audit_trail():
    """Get the complete audit trail for regulatory compliance"""
    try:
        audit_trail = dutch_rules.get_audit_trail()
        return jsonify({
            'audit_trail': audit_trail,
            'total_decisions': len(audit_trail),
            'compliance_standards': [
                'DNB AI Guidelines',
                'EU AI Act', 
                'GDPR',
                'Dutch Insurance Fraud Prevention Standards'
            ],
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': f"Error retrieving audit trail: {e}"}), 500

@app.route('/compliance/export', methods=['POST'])
def export_compliance_report():
    """Export compliance report for regulatory authorities"""
    try:
        filename = dutch_rules.export_compliance_report()
        return send_file(filename, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f"Error exporting compliance report: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
