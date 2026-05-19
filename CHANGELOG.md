# Changelog

All notable changes to this skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] — 2026-05-19

### Changed
- `detector.py`: char-level findings are now **grouped into contiguous blocks** — output went from 978 findings (one per char) to 6 findings (one per injection block) for the canonical test case `fabula_infantil.pdf`. Each block shows `char_count`, `first_bbox`, and a `sample` of the first 180 chars
- `detector.py`: UTF-8 stdout/stderr forced on Windows (was breaking accented characters as `�` under cp1252)
- `SKILL.md` step 3: running `detector.py` is now **MANDATORY**, not just recommended. The detector's grouped findings are the source of truth for the structural section of the final report. Models must not synthesize structural findings from their own reading of the extracted text

### Added
- `SKILL.md`: explicit section "Known detector gaps" — documents that opacity-0 (`ca=0` in graphics state), custom-encoded font substitution, and steganographic image content are NOT yet covered by the automated detector and must be checked manually when adversarial sophistication is suspected

### Motivation
- Real-world test with `fabula_infantil.pdf` confirmed that the LLM-side document extractor (Read tool / anthropic-skills:pdf) clips to MediaBox, so the model never sees out-of-bounds injections and cannot detect them. Mandating `detector.py` closes this gap regardless of which extractor the LLM uses.

## [1.1.0] — 2026-05-19

### Added
- New detection check `check_out_of_bounds_text` in `detector.py`: flags characters whose bbox falls outside the page's MediaBox (always critical severity)
- Section 1.b in `padroes.md` documenting the out-of-bounds vector explicitly, with rationale and pdfplumber detection snippet
- Explicit mention of MediaBox/CropBox inspection in step 3 of `SKILL.md`
- Reference to running `scripts/detector.py` programmatically as the preferred structural-inspection tool

### Changed
- Step 6 of `SKILL.md` (structured findings report) is now strictly mandatory with a fixed-format table — free-form prose summaries no longer accepted. Empty table = explicit "no patterns detected" inside the table, not omission.

### Motivation
- Real-world test (fabula_infantil.pdf) showed that one of 5 injection vectors (text at coordinates x=-800, y=-300) was not listed in the spontaneous analysis report, even though it was successfully neutralized. Two failure modes possible: extractor clipped to MediaBox (defense by accident), or model omitted from prose report. The mandatory table format and explicit out-of-bounds check close both gaps.

## [1.0.0] — 2026-05-17

### Added
- Initial release of `defesa-prompt-injection` skill
- 6-step defensive reading protocol (announce, extract, inspect, checklist, analyze, report)
- Pattern catalogue (`padroes.md`) covering:
  - Invisible text (color, size, opacity, position)
  - Zero-width and invisible Unicode characters
  - Trigger phrases in English and Portuguese (Brazilian legal vocabulary)
  - PDF metadata red flags
  - Hidden annotations and comments
  - Social engineering patterns
  - Rare vectors (homoglyphs, font substitution, JBIG2)
- Optional Python detector script (`scripts/detector.py`)
- Documented example of usage in Brazilian litigation practice (`examples/`)
- Apache 2.0 license
