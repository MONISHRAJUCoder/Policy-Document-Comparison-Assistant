"""
Diff Engine - Computes structural and semantic differences between two policy documents.
Uses Python's difflib for line-level diff and custom logic for section-level analysis.
"""

import difflib
import re
from typing import List, Dict, Any


def compute_diff(legacy_text: str, modern_text: str) -> List[Dict[str, Any]]:
    """
    Compute a line-by-line diff between legacy and modern policy texts.
    Returns a list of diff chunks with type and content.
    """
    legacy_lines = legacy_text.splitlines(keepends=True)
    modern_lines = modern_text.splitlines(keepends=True)

    matcher = difflib.SequenceMatcher(None, legacy_lines, modern_lines, autojunk=False)
    opcodes = matcher.get_opcodes()

    diff_chunks = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            diff_chunks.append({
                'type': 'equal',
                'legacy_lines': legacy_lines[i1:i2],
                'modern_lines': modern_lines[j1:j2],
                'legacy_start': i1 + 1,
                'modern_start': j1 + 1,
            })
        elif tag == 'insert':
            diff_chunks.append({
                'type': 'addition',
                'legacy_lines': [],
                'modern_lines': modern_lines[j1:j2],
                'legacy_start': i1 + 1,
                'modern_start': j1 + 1,
            })
        elif tag == 'delete':
            diff_chunks.append({
                'type': 'deletion',
                'legacy_lines': legacy_lines[i1:i2],
                'modern_lines': [],
                'legacy_start': i1 + 1,
                'modern_start': j1 + 1,
            })
        elif tag == 'replace':
            diff_chunks.append({
                'type': 'modification',
                'legacy_lines': legacy_lines[i1:i2],
                'modern_lines': modern_lines[j1:j2],
                'legacy_start': i1 + 1,
                'modern_start': j1 + 1,
                'inline_diff': _compute_inline_diff(
                    ''.join(legacy_lines[i1:i2]),
                    ''.join(modern_lines[j1:j2])
                )
            })

    return diff_chunks


def _compute_inline_diff(legacy_text: str, modern_text: str) -> Dict[str, str]:
    """
    Compute word-level inline diff for modification chunks.
    Returns HTML-annotated strings showing word-level changes.
    """
    legacy_words = legacy_text.split()
    modern_words = modern_text.split()

    matcher = difflib.SequenceMatcher(None, legacy_words, modern_words)

    legacy_html = []
    modern_html = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            legacy_html.extend(legacy_words[i1:i2])
            modern_html.extend(modern_words[j1:j2])
        elif tag == 'delete':
            for word in legacy_words[i1:i2]:
                legacy_html.append(f'<mark class="del">{word}</mark>')
        elif tag == 'insert':
            for word in modern_words[j1:j2]:
                modern_html.append(f'<mark class="ins">{word}</mark>')
        elif tag == 'replace':
            for word in legacy_words[i1:i2]:
                legacy_html.append(f'<mark class="del">{word}</mark>')
            for word in modern_words[j1:j2]:
                modern_html.append(f'<mark class="ins">{word}</mark>')

    return {
        'legacy': ' '.join(legacy_html),
        'modern': ' '.join(modern_html),
    }


def _extract_sections(text: str) -> Dict[str, str]:
    """
    Extract named sections from a policy document.
    Looks for numbered or titled headings.
    """
    # Pattern: numbered sections like "1. TITLE" or "Section 1:" or all-caps headings
    section_pattern = re.compile(
        r'(?:^|\n)(\d+[\.\)]\s+[A-Z][^\n]+|[A-Z]{3,}[^\n]*|Section\s+\d+[:\s][^\n]+)',
        re.MULTILINE
    )
    matches = list(section_pattern.finditer(text))

    sections = {}
    for i, match in enumerate(matches):
        title = match.group(0).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections[title] = content

    return sections if sections else {'Full Document': text}


def structure_diff_results(diff_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Structure the raw diff chunks into a presentation-ready format.
    """
    additions = 0
    deletions = 0
    modifications = 0
    equal_lines = 0

    formatted_chunks = []

    for chunk in diff_chunks:
        if chunk['type'] == 'equal':
            equal_lines += len(chunk['legacy_lines'])
            # Include context lines (show up to 2 lines of context)
            context_text = ''.join(chunk['legacy_lines']).strip()
            if context_text:
                formatted_chunks.append({
                    'type': 'equal',
                    'text': context_text[:300] + ('...' if len(context_text) > 300 else ''),
                    'truncated': len(context_text) > 300,
                })
        elif chunk['type'] == 'addition':
            added_text = ''.join(chunk['modern_lines']).strip()
            if added_text:
                additions += len(chunk['modern_lines'])
                formatted_chunks.append({
                    'type': 'addition',
                    'text': added_text,
                    'line_count': len(chunk['modern_lines']),
                    'modern_start': chunk['modern_start'],
                })
        elif chunk['type'] == 'deletion':
            deleted_text = ''.join(chunk['legacy_lines']).strip()
            if deleted_text:
                deletions += len(chunk['legacy_lines'])
                formatted_chunks.append({
                    'type': 'deletion',
                    'text': deleted_text,
                    'line_count': len(chunk['legacy_lines']),
                    'legacy_start': chunk['legacy_start'],
                })
        elif chunk['type'] == 'modification':
            legacy_text = ''.join(chunk['legacy_lines']).strip()
            modern_text = ''.join(chunk['modern_lines']).strip()
            if legacy_text or modern_text:
                modifications += 1
                formatted_chunks.append({
                    'type': 'modification',
                    'legacy_text': legacy_text,
                    'modern_text': modern_text,
                    'inline_diff': chunk.get('inline_diff', {}),
                    'legacy_start': chunk['legacy_start'],
                    'modern_start': chunk['modern_start'],
                })

    # Calculate similarity ratio
    legacy_total = additions + deletions + modifications + equal_lines
    similarity = round((equal_lines / max(legacy_total, 1)) * 100, 1)

    return {
        'chunks': formatted_chunks,
        'stats': {
            'additions': additions,
            'deletions': deletions,
            'modifications': modifications,
            'equal_lines': equal_lines,
            'similarity_percent': similarity,
            'change_percent': round(100 - similarity, 1),
        }
    }
