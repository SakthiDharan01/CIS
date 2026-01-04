# Layered Authenticity Verification System (LAVS)

FastAPI-based multi-modal verifier that detects AI-generated or manipulated content across images, videos, audio recordings, and website URLs using layered evidence instead of a single classifier.

## Features

- **Content Type Classifier:** MIME + signature detection to route files/URLs to the right pipeline.
- **Origin & Metadata Forensics:** Timestamps, camera/tool fingerprints, compression hints; video codec/FPS; audio sample rate; URL WHOIS age.
- **Pattern Integrity Engines:**
  - Image: micro-region variance, edge/border consistency, symmetry, pixel co-occurrence (GLCM).
  - Video: temporal variance, luminance variance, resolution jumps, micro-motion proxy.
  - Audio: pitch stability, pause randomness, spectral flatness/flux, RMS spike proxy for breaths.
  - Web: SSL/redirects, DOM repetition, sentence-length uniformity, keyword over-optimization.
- **Behavioral Deviation:** Flags over-consistency across layers and low entropy signals.
- **Adaptive Aggregation:** Content-type-aware weighting with a human-readable verdict (Real / Suspicious / Likely Fake).

## Setup

1) **Install dependencies**
```bash
pip install -r requirements.txt
```

2) **Run the dev server**
```bash
uvicorn main:app --reload
```
Or use the VS Code Task: **Run LAVS**.

3) **Open UI**
Visit `http://127.0.0.1:8000`.

## Project Structure

- `main.py` — FastAPI app, routing, and layer orchestration.
- `analyzers/`
  - `content_classifier.py` — MIME/file-signature and URL classifier.
  - `metadata_analyzer.py` — Origin/forensic checks (EXIF, codec/FPS/SR, WHOIS).
  - `image_analyzer.py` — Pattern integrity for images.
  - `video_analyzer.py` — Temporal/motion integrity for video.
  - `audio_analyzer.py` — Speech/microsignal integrity.
  - `url_analyzer.py` — Web structure and trust signals.
  - `behavioral_analyzer.py` — Over-consistency/low-entropy detection.
- `utils/aggregator.py` — Adaptive confidence aggregation and verdict.
- `templates/` — HTML templates.
- `static/` — CSS and assets.
