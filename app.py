from flask import Flask, render_template, request, jsonify, send_file, Response
import os
import sys
import threading
import io
import time
import json
import webbrowser
from threading import Timer
from werkzeug.utils import secure_filename
from src.core.image_stripper import ImageStripper
from src.core.psd_cleaner import PSDCleaner
from src.utils.logger import logger
from src.utils.file_validator import validate_upload
from src.analysis.ela_analyzer import ELAAnalyzer
from src.analysis.metadata_inspector import MetadataInspector

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# A thread-safe list to hold live console logs
log_buffer = []

# Custom stream to redirect print statements to the web UI buffer
class WebLogStream:
    def write(self, text):
        if text.strip():
            log_buffer.append(f"{time.strftime('%H:%M:%S')} - {text.strip()}")
        # Also print to actual console for debugging
        sys.__stdout__.write(text)
    
    def flush(self):
        sys.__stdout__.flush()

# Redirect stdout
sys.stdout = WebLogStream()
sys.stderr = WebLogStream()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream_logs')
def stream_logs():
    def generate():
        last_index = 0
        while True:
            if last_index < len(log_buffer):
                # Send all new logs
                new_logs = log_buffer[last_index:]
                last_index = len(log_buffer)
                for log in new_logs:
                    yield f"data: {log}\n\n"
            time.sleep(0.5)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/process', methods=['POST'])
def process_file():
    global log_buffer
    log_buffer.clear() # Clear previous logs on new run
    
    logger.info("[*] Receiving request from Web UI...")
    
    if 'target_file' not in request.files:
        logger.error("[-] Error: No target file provided.")
        return jsonify({'error': 'No target file provided'}), 400
        
    target_file = request.files['target_file']
    valid, err_msg = validate_upload(target_file)
    if not valid:
        logger.error(err_msg)
        return jsonify({'error': err_msg}), 400
        
    mode = request.form.get('mode', 'deep_wash')
    
    # Secure and Save Target
    target_filename = secure_filename(target_file.filename)
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], target_filename)
    target_file.save(target_path)
    
    donor_path = None
    if mode == 'clone_identity':
        if 'donor_file' not in request.files:
            logger.error("[-] Error: Identity Cloning requires a Donor Image.")
            return jsonify({'error': 'Donor file missing'}), 400
            
        donor_file = request.files['donor_file']
        d_valid, d_err = validate_upload(donor_file)
        if not d_valid:
            logger.error(d_err)
            return jsonify({'error': d_err}), 400
            
        donor_filename = secure_filename(donor_file.filename)
        donor_path = os.path.join(app.config['UPLOAD_FOLDER'], donor_filename)
        donor_file.save(donor_path)

    ext = target_filename.lower().split('.')[-1]
    
    # Determine Output Name
    output_filename = f"secure_{target_filename}"
    if ext == 'psd':
        output_filename = output_filename.replace('.psd', '.png')
    
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    
    # Process the file
    try:
        if ext == 'psd':
            if mode == 'clone_identity':
                logger.error("[-] Error: Cannot Clone Identity directly to raw PSDs. Convert to JPG first.")
                return jsonify({'error': 'PSD does not support direct Donors'}), 400
                
            logger.info("[*] Web UI: Initiating PSD Flattening & Sterilization...")
            cleaner = PSDCleaner(target_path)
            result = cleaner.create_clean_psd(output_path)
        else:
            stripper = ImageStripper(target_path)
            if mode == 'clone_identity':
                logger.info("[*] Web UI: Initiating Tier-1 Identity Cloning...")
                result = stripper.clone_identity(donor_path, output_path)
            else:
                logger.info("[*] Web UI: Initiating Deep Wash Protection...")
                result = stripper.deep_wash(output_path)
                
        if result:
            logger.info(f"[+] Anti-Forensics operation completed successfully: {output_filename}")
            return jsonify({
                'success': True, 
                'download_url': f'/download/{output_filename}',
                'message': 'Protection Applied Successfully'
            })
        else:
            logger.error("[-] Operation failed during processing.")
            return jsonify({'error': 'Processing failed internally'}), 500
            
    except Exception as e:
        logger.info(f"[-] Critical Server Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_file():
    global log_buffer
    log_buffer.clear()
    logger.info("[*] Receiving Analysis Request...")
    
    if 'target_file' not in request.files:
        logger.error("[-] Error: No target file provided.")
        return jsonify({'error': 'No file provided'}), 400
        
    target_file = request.files['target_file']
    valid, err_msg = validate_upload(target_file)
    if not valid:
        logger.error(err_msg)
        return jsonify({'error': err_msg}), 400
        
    target_filename = secure_filename(target_file.filename)
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], target_filename)
    target_file.save(target_path)
    
    # Generate Output Paths
    name, _ = os.path.splitext(target_filename)
    ela_filename = f"{name}_ela.png"
    ela_path = os.path.join(app.config['OUTPUT_FOLDER'], ela_filename)
    
    # Run Forensic Engines
    ela_result = ELAAnalyzer.generate_ela(target_path, ela_path)
    meta_results = MetadataInspector.inspect(target_path)
    
    if meta_results:
        logger.info("[+] Analysis successfully completed.")
        return jsonify({
            'success': True,
            'ela_url': f'/download/{ela_filename}' if ela_result else None,
            'metadata': meta_results
        })
    else:
        logger.error("[-] Analysis failed.")
        return jsonify({'error': 'Analysis engines failed.'}), 500

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    print("[*] Photoshop Anti-Forensics Local Web Server starting...")
    print("[*] Access the GUI at: http://127.0.0.1:5000")
    # Auto-launch the web browser exactly 1.5 seconds after the server boots
    Timer(1.5, open_browser).start()
    app.run(debug=False, host='127.0.0.1', port=5000)
