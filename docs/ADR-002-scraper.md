# ADR-002: Playwright Scraper Design Choice

## Status
Accepted 2025-08-11

## Context
We needed a robust scraping mechanism capable of rendering JavaScript-heavy pages while respecting site policies.

## Decision
We chose **Playwright** over simpler HTTP parsers because:
1. Full JS rendering, critical for modern sites.
2. Headless Chromium offers stability and speed.
3. Easy proxy & headless toggling via env vars.
4. Active community and future-proofing.

Robots.txt compliance is implemented via Python `robotparser`. Exponential back-off protects sites.

## Consequences
* Slightly larger container image (Chromium).
* More complex CI setup (needs Playwright install) but acceptable.
