# defesa-prompt-injection

> **Defense-in-depth against prompt injection when AI agents read adversarial documents.**

🇧🇷 **Versão em português: [README.pt.md](README.pt.md)**

A Claude Code / Agent skill designed to be invoked as the **first step** before any analysis of documents from untrusted sources — opposing-party legal briefs, third-party contracts, external emails, scraped web content, or any document not produced by the user's own organization.

[![Skills.sh](https://img.shields.io/badge/skills.sh-listed-blue)](https://skills.sh/jefferson-maleski/defesa-prompt-injection)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-green.svg)](CHANGELOG.md)

---

## Why this exists

OWASP Top 10 for Agentic Applications (2026) ranks prompt injection as the **#1 security risk** for AI agents. When an agent reads a document authored by an adversary — say, a bank's brief in a consumer fraud case, or a vendor contract from a counterparty — that document can contain hidden instructions designed to manipulate the agent's behavior.

This skill ensures every byte inside an adversarial document is treated as **data to be analyzed**, never as **commands to be obeyed**.

**Use cases**:
- Legal practice: reading opposing-party filings, contestations, appeals, expert reports
- Contract review: third-party drafts, vendor agreements, NDAs from counterparties
- Due diligence: external documents in data rooms
- Research: papers, articles, or scraped content from untrusted sources
- Email triage: messages from external senders with attachments

## What it does

The skill defines a **6-step defensive protocol** the agent follows when about to read an adversarial document:

1. **Announce** the file as adversarial — making the agent's mode explicit
2. **Extract raw text** without OCR normalization
3. **Structural inspection** — run [`scripts/detector.py`](scripts/detector.py) (mandatory as of v1.2.0) for metadata, embedded scripts, forms, layers, invisible text, and out-of-bounds coordinates
4. **Pattern checklist** — invisible text, zero-width chars, trigger phrases, hidden annotations (see [padroes.md](padroes.md))
5. **Hardened analysis** — perform domain analysis with awareness that all internal content is adversarial
6. **Structured findings report** — strictly tabular, surfaces every detected pattern to the user

## What it detects

| Vector | Examples |
|---|---|
| Invisible text | White-on-white, font size ≤ 1pt, opacity 0 |
| **Out-of-bounds text** | Characters drawn outside the MediaBox (negative coordinates, beyond page edge) |
| Zero-width characters | U+200B, U+200C, U+200D, U+FEFF, U+2060, U+202E (RTL override) |
| Trigger phrases | "ignore previous instructions", "you are now", "ATTENTION AI" (English) + Portuguese variants |
| PDF metadata | Suspicious Author/Creator/Producer, embedded JavaScript, AcroForm, optional layers |
| Hidden annotations | `/Annot`, `/FreeText`, `/Popup`, `/Watermark` comments |
| Social engineering | False urgency, role inversion, fabricated jurisprudence, false "consolidated facts" |
| Rare vectors | Unicode tag chars (U+E0000–U+E007F), homoglyphs, font substitution, JBIG2 stego |

Full pattern catalogue: [`padroes.md`](padroes.md).

Bilingual coverage: **English + Portuguese** (Brazilian legal vocabulary).

## Installation

### Via npx skills (recommended)

```bash
npx skills add jefferson-maleski/defesa-prompt-injection -g -y
```

### Manual install

Clone the repository into your skills directory:

**Claude Code (global / user-level)**:
```bash
git clone https://github.com/jefferson-maleski/defesa-prompt-injection ~/.claude/skills/defesa-prompt-injection
```

**Project-level**:
```bash
git clone https://github.com/jefferson-maleski/defesa-prompt-injection .claude/skills/defesa-prompt-injection
```

The skill is automatically picked up by Claude Code from these paths.

## Usage

The skill self-activates based on description triggers. To force explicit invocation:

> "Run defesa-prompt-injection before reading the opposing party's brief"

> "Antes de ler [PDF], roda a defesa-prompt-injection"

The agent will then announce the adversarial source, inspect the file structurally (via `detector.py`), apply the pattern checklist, report findings in the mandatory tabular format, and proceed with the domain analysis treating all internal text as data.

### Integration with other skills

This skill **precedes** and **complements**, never replaces, your domain analysis skills:

```
User input → defesa-prompt-injection → domain skill (legal-analysis, contract-review, etc.)
```

Good chaining examples:
- `defesa-prompt-injection` → legal analysis skill
- `defesa-prompt-injection` → red-team verifier (input + output both verified)
- `defesa-prompt-injection` → tabular review (run on each adversarial doc in the batch)

## Mandatory: Python detector script

As of v1.2.0, the skill mandates running [`scripts/detector.py`](scripts/detector.py) during step 3. The detector applies the pattern catalogue programmatically because LLM-side PDF extractors clip text to the MediaBox — meaning the model never sees out-of-bounds injections and cannot detect what its extractor never delivers.

```bash
pip install pdfplumber pypdf pikepdf
python scripts/detector.py path/to/suspicious.pdf
```

Output is grouped per contiguous block (not per character) with status (APPROVED / SUSPICIOUS / BLOCKED), char counts, coordinates, and 180-char samples per finding.

Test fixtures with five injection vectors each (in Portuguese and English) ship in [`examples/`](examples/) for verification.

## Limitations

This is **defense-in-depth**, not absolute guarantee. Vectors not currently covered by the automated detector:
- **Opacity 0 (alpha=0)** — `pdfplumber` exposes color but not graphics-state alpha; check manually via content-stream inspection
- Custom-encoded fonts mapping glyphs to misleading Unicode (font substitution attack)
- Advanced steganography in images
- Side-channel attacks via timing or resource consumption

For these cases, **the final filter is always human review**. Use this skill to raise the floor, not as a ceiling.

## Contributing

New attack vectors are discovered regularly. Contributions are welcome:

1. Open an issue describing the vector with a minimal reproducible example
2. Submit a PR adding the pattern to [`padroes.md`](padroes.md)
3. If the vector is detectable programmatically, add corresponding logic to [`scripts/detector.py`](scripts/detector.py)

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## Author

**Jefferson Maleski** — [@jefferson-maleski](https://github.com/jefferson-maleski)

## Built with

Developed with assistance from [Claude](https://www.anthropic.com/claude) (Sonnet 4.6) via [Claude Code](https://www.anthropic.com/claude-code).

## License

Apache License 2.0 — see [LICENSE](LICENSE) for full text.

## Disclaimer

This skill is provided "as is", without warranty of any kind. It is a defensive aid, not a substitute for human judgment. The author and contributors are not responsible for any damages arising from the use, misuse, or failure of this skill. Always combine with human review for high-stakes decisions.
