# Contributing

Thank you for your interest. This skill is most valuable when its pattern catalogue stays current with newly published attack vectors.

## How to contribute

### Report a new vector

If you discover a prompt injection pattern not yet covered:

1. Open a GitHub issue titled `[new vector] <short description>`
2. Include:
   - A minimal reproducible example (sample PDF or text fragment, sanitized of any sensitive data)
   - Reference to the source (paper, blog post, real-world incident — anonymized)
   - Suggested detection approach (regex, heuristic, structural check)

### Submit a pattern PR

1. Fork the repo
2. Add the pattern to the appropriate section in [`skills/defesa-prompt-injection/padroes.md`](skills/defesa-prompt-injection/padroes.md)
3. If the vector can be detected programmatically, extend [`skills/defesa-prompt-injection/scripts/detector.py`](skills/defesa-prompt-injection/scripts/detector.py) with corresponding logic and a docstring referencing the issue
4. Update [`CHANGELOG.md`](CHANGELOG.md) under the `## [Unreleased]` section
5. Open a PR with a clear title and reference the issue

### What we don't accept

- Patterns from undisclosed/unverified sources (we need reproducibility)
- Vectors that require offensive infrastructure to test (this is a defensive skill — keep it that way)
- Sensitive real-world content (anonymize all examples)

## Code style

- Python: PEP 8, no external dependencies beyond `pdfplumber`, `pypdf`, `pikepdf`
- Markdown: ATX-style headings, sentence-case for section titles
- Bilingual content: when adding trigger phrases, add to both English and Portuguese sections if applicable

## Review process

PRs are reviewed manually. We prioritize:
1. Correctness — does the pattern actually appear in attack scenarios?
2. Specificity — does the detection have low false-positive rate?
3. Documentation — is the pattern clearly explained?

## Security disclosure

If you find a vulnerability **in this skill itself** (not a new attack vector to cover), do not open a public issue. Email the maintainer directly via the GitHub profile contact.
