# Changelog

All notable changes to this skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
