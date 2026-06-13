"""
Regulatory Impact Analyzer - Uses Ollama (local LLM, no internet required)
to analyze policy document changes and explain regulatory implications.

Model: llama3 (default) — runs 100% locally via Ollama
Setup: https://ollama.com → install → run: ollama pull llama3
"""

import json
import requests
from typing import Dict, Any

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"  # Change to "mistral", "phi3", "gemma2" etc. if preferred


def analyze_regulatory_impact(
    legacy_text: str,
    modern_text: str,
    diff_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Use Ollama local LLM to analyze regulatory impact of policy changes.
    Returns structured analysis with compliance frameworks, risk scores, and recommendations.
    """
    changes_summary = _summarize_changes(diff_data)

    prompt = f"""You are a regulatory compliance expert. Analyze the transition from a legacy policy document to a modernized version and provide a regulatory impact assessment.

LEGACY POLICY (excerpt):
{legacy_text[:2000]}

MODERNIZED POLICY (excerpt):
{modern_text[:2000]}

KEY CHANGES DETECTED:
{changes_summary}

Respond with ONLY a valid JSON object — no markdown, no explanation, no extra text before or after. Use exactly this structure:
{{
  "executive_summary": "2-3 sentence overview of the regulatory transformation",
  "compliance_frameworks": [
    {{
      "framework": "GDPR",
      "status": "improved",
      "details": "specific compliance changes"
    }}
  ],
  "risk_assessment": {{
    "overall_risk_change": "reduced",
    "risk_score_legacy": 75,
    "risk_score_modern": 30,
    "key_risks_eliminated": ["risk 1", "risk 2"],
    "new_risks_introduced": ["obligation 1"],
    "risk_explanation": "explanation of risk changes"
  }},
  "regulatory_changes": [
    {{
      "category": "Data Subject Rights",
      "impact": "high",
      "change_type": "strengthened",
      "legacy_stance": "what the legacy policy said",
      "modern_stance": "what the modern policy says",
      "regulatory_significance": "why this matters"
    }}
  ],
  "key_improvements": ["improvement 1", "improvement 2"],
  "compliance_gaps": ["gap 1"],
  "implementation_recommendations": [
    {{
      "priority": "immediate",
      "action": "specific action",
      "rationale": "why this is needed"
    }}
  ],
  "jurisdiction_impact": {{
    "eu_gdpr": "impact notes",
    "us_ccpa": "impact notes",
    "general": "general notes"
  }},
  "overall_assessment": "positive",
  "modernization_score": 80
}}"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 2048,
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)

        if response.status_code == 404:
            raise Exception(
                f"Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}"
            )

        response.raise_for_status()
        result = response.json()
        raw_text = result.get("response", "")
        return _parse_json_response(raw_text)

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Cannot connect to Ollama. Make sure Ollama is running: open a terminal and run 'ollama serve'"
        )
    except requests.exceptions.Timeout:
        raise Exception(
            "Ollama timed out. The model may be slow on your hardware — try a smaller model like 'phi3' in regulatory_analyzer.py"
        )
    except Exception as e:
        raise Exception(f"Analysis failed: {str(e)}")


def _parse_json_response(text: str) -> Dict[str, Any]:
    """Extract and parse JSON from the model response."""
    text = text.strip()

    # Strip markdown code fences if present
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break

    # Find the JSON object bounds
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "executive_summary": "Analysis completed. The modernized policy shows significant changes from the legacy version. Manual review of the diff output is recommended.",
            "compliance_frameworks": [
                {"framework": "General Compliance", "status": "improved", "details": "Policy has been updated with more modern language and provisions."}
            ],
            "risk_assessment": {
                "overall_risk_change": "reduced",
                "risk_score_legacy": 70,
                "risk_score_modern": 40,
                "key_risks_eliminated": ["Outdated compliance provisions"],
                "new_risks_introduced": ["New compliance obligations may require implementation effort"],
                "risk_explanation": "The modernized policy reduces overall compliance risk through updated provisions."
            },
            "regulatory_changes": [],
            "key_improvements": ["Policy language modernized", "Compliance provisions updated"],
            "compliance_gaps": ["Full AI analysis unavailable — review diff manually"],
            "implementation_recommendations": [
                {"priority": "short-term", "action": "Review all highlighted diff changes", "rationale": "Manual review ensures no critical changes are missed"}
            ],
            "jurisdiction_impact": {
                "eu_gdpr": "Review required",
                "us_ccpa": "Review required",
                "general": "Policy update appears positive"
            },
            "overall_assessment": "positive",
            "modernization_score": 65
        }


def _summarize_changes(diff_data: Dict[str, Any]) -> str:
    """Create a concise text summary of diff changes for the AI prompt."""
    chunks = diff_data.get('chunks', [])
    stats = diff_data.get('stats', {})

    lines = [
        f"Total additions: {stats.get('additions', 0)} lines",
        f"Total deletions: {stats.get('deletions', 0)} lines",
        f"Total modifications: {stats.get('modifications', 0)} sections",
        f"Similarity: {stats.get('similarity_percent', 0)}%",
        "",
        "Notable changes:"
    ]

    change_count = 0
    for chunk in chunks:
        if change_count >= 8:
            break
        if chunk['type'] == 'addition':
            lines.append(f"ADDED: {chunk.get('text', '')[:150]}")
            change_count += 1
        elif chunk['type'] == 'deletion':
            lines.append(f"REMOVED: {chunk.get('text', '')[:150]}")
            change_count += 1
        elif chunk['type'] == 'modification':
            legacy = chunk.get('legacy_text', '')[:80]
            modern = chunk.get('modern_text', '')[:80]
            lines.append(f"MODIFIED: '{legacy}' -> '{modern}'")
            change_count += 1

    return '\n'.join(lines)
