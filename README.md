# PolicyLens — AI-Powered Policy Document Comparator

> **Hackathon Project**: An AI tool that compares legacy vs modernized policy documents, highlights differences, and explains regulatory impact — powered by Claude AI.

---

## Features

- **Document Comparison** — Upload PDF, DOCX, or TXT files (or paste text directly)
- **Visual Diff View** — Side-by-side diff with word-level highlighting for additions, deletions, and modifications
- **AI Regulatory Analysis** — Claude AI identifies compliance frameworks (GDPR, CCPA, HIPAA, SOX, etc.)
- **Risk Scoring** — Before/after risk scores with eliminated risks and new obligations
- **Implementation Roadmap** — Prioritized action items (Immediate / Short-term / Long-term)
- **Modernization Score** — Overall compliance improvement percentage

---

## Project Structure

```
policy_comparator/
├── app.py                        # Flask application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── utils/
│   ├── document_parser.py        # PDF/DOCX/TXT text extraction
│   ├── diff_engine.py            # Structural diff computation
│   └── regulatory_analyzer.py   # Claude AI regulatory analysis
├── templates/
│   └── index.html                # Main UI template
├── static/
│   ├── css/style.css             # Styles
│   └── js/app.js                 # Frontend logic
└── uploads/                      # Temporary file storage (auto-created)
```

---

## Quick Start

### 1. Prerequisites
- Python 3.9+
- An Anthropic API key (get one at https://console.anthropic.com)

### 2. Install dependencies

```bash
cd policy_comparator
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Or set the environment variable directly:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Run the application

```bash
python app.py
```

Open your browser to: **http://localhost:5000**

---

## Usage

1. **Paste or upload** your legacy policy document (left panel)
2. **Paste or upload** your modernized policy document (right panel)
3. Click **Analyze & Compare** (takes 15–30 seconds)
4. Explore the results across 4 tabs:
   - **Diff View** — Line-by-line changes with color coding
   - **Regulatory Impact** — Framework-by-framework analysis
   - **Risk Analysis** — Before/after risk scores
   - **Recommendations** — Prioritized action items

### Try the Demo
Click **"Load Sample GDPR Migration"** to instantly load a legacy privacy policy vs a GDPR/CCPA-compliant modernized version.

---

## How It Works

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Document Input │───▶│   Diff Engine    │───▶│   Claude AI         │
│  (PDF/DOCX/TXT) │    │  (difflib-based) │    │  Regulatory Analyst │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌──────────────┐      ┌──────────────────────┐
                       │  Structured  │      │  Compliance Report:  │
                       │  Diff Data   │      │  - Framework status  │
                       │  (additions, │      │  - Risk scores       │
                       │  deletions,  │      │  - Key changes       │
                       │  mods)       │      │  - Recommendations   │
                       └──────────────┘      └──────────────────────┘
```

### Components

**`utils/document_parser.py`**
- Extracts text from PDF (PyMuPDF), DOCX (python-docx), and TXT files
- Handles multiple text encodings

**`utils/diff_engine.py`**
- Uses Python's `difflib.SequenceMatcher` for line-level comparison
- Computes word-level inline diffs for modified sections
- Returns structured diff with stats (additions, deletions, modifications, similarity %)

**`utils/regulatory_analyzer.py`**
- Sends document excerpts + diff summary to Claude claude-sonnet-4-6
- Receives structured JSON with compliance frameworks, risk scores, and recommendations
- Handles JSON parsing and fallbacks

---

## Supported File Formats

| Format | Support | Library Required |
|--------|---------|-----------------|
| `.txt` | ✅ Built-in | None |
| `.pdf` | ✅ Optional | `pymupdf` or `pdfplumber` |
| `.docx`| ✅ Optional | `python-docx` |

Text can also be pasted directly without file upload.

---

## Compliance Frameworks Analyzed

PolicyLens automatically detects and analyzes:
- **GDPR** — EU General Data Protection Regulation
- **CCPA** — California Consumer Privacy Act
- **HIPAA** — Health Insurance Portability and Accountability Act
- **SOX** — Sarbanes-Oxley Act
- **ISO 27001** — Information Security Management
- **PCI-DSS** — Payment Card Industry Data Security Standard
- Any other frameworks detected in the document context

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Anthropic API key |
| `FLASK_ENV` | No | `development` or `production` |
| `FLASK_SECRET_KEY` | No | Flask session secret (auto-generated if not set) |

---

## Troubleshooting

**"AI API error"** → Check your `ANTHROPIC_API_KEY` is set correctly.

**"Could not decode text file"** → Try converting your file to UTF-8 encoding.

**PDF parsing fails** → Install PyMuPDF: `pip install pymupdf`

**DOCX parsing fails** → Install python-docx: `pip install python-docx`

**Port already in use** → Change the port in `app.py`: `app.run(port=5001)`

---

## Tech Stack

- **Backend**: Python 3, Flask
- **AI**: Anthropic Claude claude-sonnet-4-6 API
- **Diff Engine**: Python `difflib` (SequenceMatcher)
- **PDF Parsing**: PyMuPDF / pdfplumber
- **DOCX Parsing**: python-docx
- **Frontend**: Vanilla HTML/CSS/JS (no build step required)

---

Built for the AI Hackathon · Powered by Claude AI
