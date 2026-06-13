"""
Policy Document Comparator - Main Flask Application
Compares legacy vs modernized policy documents, highlights differences,
and explains regulatory impact using AI.
"""

import os
import json
import traceback
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from utils.document_parser import extract_text
from utils.diff_engine import compute_diff, structure_diff_results
from utils.regulatory_analyzer import analyze_regulatory_impact, OLLAMA_URL, OLLAMA_MODEL

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = 'uploads'

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Check if Ollama is reachable and the model is available."""
    status = {"flask": "ok", "ollama": "unknown", "model": OLLAMA_MODEL}
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            status["ollama"] = "running"
            status["available_models"] = models
            status["model_ready"] = any(OLLAMA_MODEL in m for m in models)
            if not status["model_ready"]:
                status["fix"] = f"Run: ollama pull {OLLAMA_MODEL}"
        else:
            status["ollama"] = f"error: HTTP {r.status_code}"
    except requests.exceptions.ConnectionError:
        status["ollama"] = "not running"
        status["fix"] = "Run: ollama serve"
    except Exception as e:
        status["ollama"] = f"error: {str(e)}"
    return jsonify(status)


@app.route('/compare', methods=['POST'])
def compare_documents():
    """Main endpoint to compare two policy documents."""
    try:
        legacy_text = ""
        modern_text = ""

        # Handle file uploads or direct text input
        if 'legacy_file' in request.files and request.files['legacy_file'].filename:
            file = request.files['legacy_file']
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"legacy_{filename}")
                file.save(filepath)
                legacy_text = extract_text(filepath)
            else:
                return jsonify({'error': 'Legacy file must be PDF, DOCX, or TXT.'}), 400
        else:
            legacy_text = request.form.get('legacy_text', '').strip()

        if 'modern_file' in request.files and request.files['modern_file'].filename:
            file = request.files['modern_file']
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"modern_{filename}")
                file.save(filepath)
                modern_text = extract_text(filepath)
            else:
                return jsonify({'error': 'Modern file must be PDF, DOCX, or TXT.'}), 400
        else:
            modern_text = request.form.get('modern_text', '').strip()

        if not legacy_text:
            return jsonify({'error': 'Legacy policy document is empty or could not be read.'}), 400
        if not modern_text:
            return jsonify({'error': 'Modernized policy document is empty or could not be read.'}), 400

        # Compute structural diff
        diff_results = compute_diff(legacy_text, modern_text)
        structured = structure_diff_results(diff_results)

        # AI-powered regulatory impact analysis
        regulatory_analysis = analyze_regulatory_impact(legacy_text, modern_text, structured)

        return jsonify({
            'success': True,
            'diff': structured,
            'regulatory_analysis': regulatory_analysis,
            'stats': {
                'legacy_words': len(legacy_text.split()),
                'modern_words': len(modern_text.split()),
                'additions': structured['stats']['additions'],
                'deletions': structured['stats']['deletions'],
                'modifications': structured['stats']['modifications'],
            }
        })

    except Exception as e:
        # Print full traceback to Flask console for debugging
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/sample', methods=['GET'])
def get_sample():
    """Return sample policy texts for demo purposes."""
    legacy = """DATA PRIVACY POLICY - Version 1.0 (Legacy)
Effective Date: January 1, 2010

1. DATA COLLECTION
The company collects personal information including name, address, phone number, and email address from users who register on our platform. Data may also be collected through cookies and tracking technologies without explicit user consent.

2. DATA STORAGE
All collected data is stored on internal servers located within company premises. Backup procedures are conducted monthly. Data retention period is indefinite unless user requests deletion.

3. DATA SHARING
User data may be shared with third-party partners for marketing purposes. The company is not responsible for how third parties handle shared data. Users cannot opt out of data sharing.

4. USER RIGHTS
Users may request to view their stored data by submitting a written request via postal mail. Processing time is 60 business days. The company reserves the right to deny requests at its discretion.

5. SECURITY MEASURES
Basic password protection and firewall systems are in place. The company will notify users of data breaches within 90 days of discovery.

6. COOKIES
The company uses cookies to track user behavior. Continued use of the platform implies consent to cookie usage."""

    modern = """DATA PRIVACY POLICY - Version 3.0 (GDPR/CCPA Compliant)
Effective Date: January 1, 2024

1. DATA COLLECTION
We collect only the minimum necessary personal data required to provide our services, including name, email address, and usage data. All data collection is based on explicit, informed consent obtained through clear opt-in mechanisms. Users are informed of data collection purposes prior to collection.

2. DATA STORAGE
All data is encrypted at rest and in transit using AES-256 encryption. Data is stored in ISO 27001-certified data centers. Automated backup procedures occur every 24 hours. Data retention follows a strict policy: active account data retained for 3 years, with automatic deletion thereafter unless renewed consent is obtained.

3. DATA SHARING
User data is never sold to third parties. Data may be shared only with service providers under strict Data Processing Agreements (DPAs). Users must provide explicit consent for any third-party data sharing. Users can withdraw consent at any time through their account settings.

4. USER RIGHTS
Users have the following rights under GDPR/CCPA:
- Right to Access: Request a copy of your data within 30 days
- Right to Rectification: Correct inaccurate data immediately
- Right to Erasure: Request complete deletion within 72 hours
- Right to Portability: Export data in machine-readable format
- Right to Object: Opt out of any processing activity

5. SECURITY MEASURES
We implement multi-layered security including end-to-end encryption, multi-factor authentication, regular penetration testing, and 24/7 security monitoring. In the event of a data breach, affected users will be notified within 72 hours as required by GDPR Article 33.

6. COOKIES
We use only strictly necessary cookies by default. All non-essential cookies require explicit user consent through our cookie consent manager. Users can manage cookie preferences at any time through our Privacy Dashboard."""

    return jsonify({'legacy': legacy, 'modern': modern})


if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    print(f"\n{'='*50}")
    print(f"  PolicyLens starting...")
    print(f"  Ollama model: {OLLAMA_MODEL}")
    print(f"  Health check: http://localhost:5000/health")
    print(f"{'='*50}\n")
    app.run(debug=True, port=5000)
