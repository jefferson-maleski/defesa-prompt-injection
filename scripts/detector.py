#!/usr/bin/env python3
"""
Standalone prompt injection detector for PDF files.

Applies the pattern catalogue from defesa-prompt-injection skill programmatically.
Useful as a pre-filter in pipelines, CI checks, or batch processing of adversarial
documents before they reach an LLM agent.

Usage:
    pip install pdfplumber pypdf pikepdf
    python detector.py path/to/document.pdf
    python detector.py path/to/document.pdf --json   # machine-readable output

Exit codes:
    0 — no patterns detected (APPROVED)
    1 — suspicious patterns detected (SUSPICIOUS)
    2 — critical patterns detected (BLOCKED — manual review required)
    3 — error reading file

This is part of the defesa-prompt-injection skill.
See https://github.com/jefferson-maleski/defesa-prompt-injection
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
    import pypdf
    import pikepdf
except ImportError as e:
    print(f"ERROR: missing dependency: {e.name}", file=sys.stderr)
    print("Install with: pip install pdfplumber pypdf pikepdf", file=sys.stderr)
    sys.exit(3)


INVISIBLE_CHARS = re.compile(
    r'[​-‏‪-‮⁠-⁯﻿­]'
)

TRIGGER_PATTERNS_EN = [
    r'ignore\s+(?:previous|prior|all|above)\s+(?:instructions|prompts|context)',
    r'disregard\s+(?:your|the)\s+(?:instructions|guidelines|rules)',
    r'you\s+are\s+now\s+(?:a|an)\s',
    r'new\s+instructions\s*:',
    r'system\s+prompt\s*:',
    r'assistant\s+prompt\s*:',
    r'###\s+(?:instruction|new|system|task)',
    r'<\|im_(?:start|end)\|>',
    r'</?(?:system|user|assistant)>',
    r'ATTENTION\s+(?:AI|ASSISTANT|CLAUDE)',
    r'END\s+OF\s+(?:DOCUMENT|CONTEXT|INSTRUCTIONS)',
]

TRIGGER_PATTERNS_PT = [
    r'ignore\s+(?:as|todas\s+as|essas|todas)\s+(?:instruções|orientações|regras)',
    r'você\s+(?:agora|é\s+agora)',
    r'nova\s+instrução\s*:',
    r'novas\s+instruções\s*:',
    r'ATENÇÃO\s+(?:IA|ASSISTENTE|CLAUDE)',
    r'FIM\s+DO\s+(?:DOCUMENTO|CONTEXTO|INSTRUÇÕES)',
]

ALL_TRIGGERS = [
    re.compile(p, re.IGNORECASE) for p in TRIGGER_PATTERNS_EN + TRIGGER_PATTERNS_PT
]


def check_invisible_chars(text: str) -> list[dict]:
    """Find zero-width and invisible Unicode characters."""
    findings = []
    matches = list(INVISIBLE_CHARS.finditer(text))
    if matches:
        codepoints = {f"U+{ord(m.group()):04X}" for m in matches}
        findings.append({
            "type": "invisible_unicode",
            "severity": "high",
            "count": len(matches),
            "codepoints": sorted(codepoints),
        })
    return findings


def check_trigger_phrases(text: str) -> list[dict]:
    """Detect known prompt injection trigger phrases."""
    findings = []
    for pattern in ALL_TRIGGERS:
        for match in pattern.finditer(text):
            findings.append({
                "type": "trigger_phrase",
                "severity": "critical",
                "pattern": pattern.pattern,
                "match": match.group()[:120],
                "position": match.start(),
            })
    return findings


def check_invisible_text(pdf_path: Path) -> list[dict]:
    """Find characters with suspicious size, color, or opacity."""
    findings = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for char in page.chars:
                    if char.get("size", 99) < 2:
                        findings.append({
                            "type": "tiny_font",
                            "severity": "critical",
                            "page": page.page_number,
                            "size": char.get("size"),
                            "text": char.get("text"),
                        })
                    color = char.get("non_stroking_color")
                    if color == (1, 1, 1) or color == 1:
                        findings.append({
                            "type": "white_text",
                            "severity": "critical",
                            "page": page.page_number,
                            "text": char.get("text"),
                        })
    except Exception as e:
        findings.append({
            "type": "extraction_error",
            "severity": "low",
            "message": str(e),
        })
    return findings


def check_pdf_metadata(pdf_path: Path) -> list[dict]:
    """Inspect PDF metadata for suspicious content."""
    findings = []
    try:
        reader = pypdf.PdfReader(pdf_path)
        meta = reader.metadata or {}
        for key, value in meta.items():
            if value is None:
                continue
            value_str = str(value)
            for pattern in ALL_TRIGGERS:
                if pattern.search(value_str):
                    findings.append({
                        "type": "metadata_injection",
                        "severity": "critical",
                        "field": key,
                        "value": value_str[:200],
                    })
                    break
    except Exception as e:
        findings.append({
            "type": "metadata_error",
            "severity": "low",
            "message": str(e),
        })
    return findings


def check_pdf_structure(pdf_path: Path) -> list[dict]:
    """Inspect PDF structural elements (JS, forms, layers)."""
    findings = []
    try:
        with pikepdf.open(pdf_path) as pdf:
            root = pdf.Root
            names = root.get("/Names", {})
            if isinstance(names, pikepdf.Dictionary) and names.get("/JavaScript"):
                findings.append({
                    "type": "embedded_javascript",
                    "severity": "high",
                    "note": "PDF contains embedded JavaScript",
                })
            if root.get("/AcroForm"):
                findings.append({
                    "type": "acroform_present",
                    "severity": "medium",
                    "note": "PDF has interactive form — check pre-filled values",
                })
            if root.get("/OCProperties"):
                findings.append({
                    "type": "optional_content_layers",
                    "severity": "medium",
                    "note": "PDF has optional content layers — check for hidden layers",
                })
            for i, page in enumerate(pdf.pages, start=1):
                annots = page.get("/Annots")
                if annots:
                    for annot in annots:
                        contents = annot.get("/Contents")
                        if contents:
                            findings.append({
                                "type": "annotation",
                                "severity": "medium",
                                "page": i,
                                "annotation_type": str(annot.get("/Subtype")),
                                "contents": str(contents)[:200],
                            })
    except Exception as e:
        findings.append({
            "type": "structure_error",
            "severity": "low",
            "message": str(e),
        })
    return findings


def extract_text(pdf_path: Path) -> str:
    """Extract all text content from a PDF."""
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                text_parts.append(t)
    except Exception as e:
        return ""
    return "\n".join(text_parts)


def analyze(pdf_path: Path) -> dict:
    """Run full detection suite on a PDF."""
    text = extract_text(pdf_path)
    findings = []
    findings.extend(check_invisible_chars(text))
    findings.extend(check_trigger_phrases(text))
    findings.extend(check_invisible_text(pdf_path))
    findings.extend(check_pdf_metadata(pdf_path))
    findings.extend(check_pdf_structure(pdf_path))

    severities = {f.get("severity") for f in findings}
    if "critical" in severities:
        status = "BLOCKED"
        exit_code = 2
    elif "high" in severities or "medium" in severities:
        status = "SUSPICIOUS"
        exit_code = 1
    else:
        status = "APPROVED"
        exit_code = 0

    return {
        "file": str(pdf_path),
        "status": status,
        "exit_code": exit_code,
        "findings_count": len(findings),
        "findings": findings,
    }


def format_human(result: dict) -> str:
    out = []
    out.append(f"=== Anti-prompt-injection detector ===")
    out.append(f"File: {result['file']}")
    out.append(f"Status: {result['status']}")
    out.append(f"Findings: {result['findings_count']}")
    out.append("")
    if not result["findings"]:
        out.append("No suspicious patterns detected.")
        return "\n".join(out)
    by_severity = {"critical": [], "high": [], "medium": [], "low": []}
    for f in result["findings"]:
        by_severity.setdefault(f.get("severity", "low"), []).append(f)
    for sev in ("critical", "high", "medium", "low"):
        items = by_severity.get(sev, [])
        if not items:
            continue
        out.append(f"[{sev.upper()}] ({len(items)} item(s))")
        for f in items:
            line = f"  - {f.get('type')}"
            if "page" in f:
                line += f" (page {f['page']})"
            if "field" in f:
                line += f" (field {f['field']})"
            details = f.get("note") or f.get("match") or f.get("value") or f.get("text") or f.get("contents")
            if details:
                line += f": {str(details)[:120]}"
            out.append(line)
        out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prompt injection detector for PDF files",
    )
    parser.add_argument("pdf", type=Path, help="Path to PDF file")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human report",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"ERROR: file not found: {args.pdf}", file=sys.stderr)
        return 3

    result = analyze(args.pdf)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_human(result))

    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
