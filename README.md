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
- **Adaptive Aggregation:** Risk-weighted 0.2/0.6/0.2 (metadata / AI-pattern / behavioral) with verdict bands: 0–30 Real, 31–60 Suspicious, 61–100 Likely Fake.

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

## API (JSON)

### POST `/verify`

Send either a file (multipart) or a URL (JSON or form field):

**File upload**
```bash
curl -X POST \
  -F "file=@sample.jpg" \
  http://127.0.0.1:8000/verify
```

**URL body (JSON)**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}' \
  http://127.0.0.1:8000/verify
```

**Response**
```json
{
  "verdict": "Likely Fake",
  "confidence": 68.5,
  "explanation": "Origin & Metadata Consistency: Very young domain (higher risk).",
  "breakdown": {
    "final_score": 68.5,
    "risk_level": "High",
    "top_signals": ["…"],
    "layer_breakdown": [{"layer": "Origin & Metadata Consistency", "score": 35, "details": ["…"]}]
  }
}
```

`confidence` here is the aggregated risk score (0–100). Lower is safer.

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
