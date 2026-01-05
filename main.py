from fastapi import FastAPI, Request, File, UploadFile, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tempfile
from analyzers.metadata_analyzer import MetadataAnalyzer
from analyzers.image_analyzer import ImageAnalyzer
from analyzers.video_analyzer import VideoAnalyzer
from analyzers.audio_analyzer import AudioAnalyzer
from analyzers.url_analyzer import URLAnalyzer
from analyzers.behavioral_analyzer import BehavioralAnalyzer
from analyzers.content_classifier import ContentClassifier
from utils.aggregator import ConfidenceAggregator

app = FastAPI(title="LAVS - Layered Authenticity Verification System")

# CORS for frontend (localhost dev + common deployment origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        "https://cis-3f7h.onrender.com",
        "https://cis-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Analyzers
metadata_analyzer = MetadataAnalyzer()
image_analyzer = ImageAnalyzer()
video_analyzer = VideoAnalyzer()
audio_analyzer = AudioAnalyzer()
url_analyzer = URLAnalyzer()
behavioral_analyzer = BehavioralAnalyzer()
content_classifier = ContentClassifier()
aggregator = ConfidenceAggregator()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    file: UploadFile = File(None),
    url: str = Form(None)
):
    results = []
    file_path = None
    content_type = None
    classification = None

    try:
        # Handle URL Input
        if url:
            classification = content_classifier.classify_url(url)
            content_type = classification.get("content_type")

            # Origin / metadata for URL
            meta_res = metadata_analyzer.analyze(url, 'url')
            results.append(meta_res)

            # Content Analysis for URL
            url_res = url_analyzer.analyze(url)
            results.append(url_res)
            
        # Handle File Upload
        elif file and file.filename:
            # Save file
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Identify MIME type via classifier
            classification = content_classifier.classify_file(file_path)
            raw_mime = classification.get("raw_mime") or ""
            content_type = classification.get("content_type") or ""
            
            # 1. Metadata Analysis
            meta_res = metadata_analyzer.analyze(file_path, raw_mime or content_type)
            results.append(meta_res)
            
            # 2. Content Analysis
            if content_type == 'image':
                img_res = image_analyzer.analyze(file_path)
                results.append(img_res)
            elif content_type == 'video':
                vid_res = video_analyzer.analyze(file_path)
                results.append(vid_res)
            elif content_type == 'audio':
                aud_res = audio_analyzer.analyze(file_path)
                results.append(aud_res)
            else:
                # Clean up and return error
                if os.path.exists(file_path):
                    os.remove(file_path)
                return templates.TemplateResponse("index.html", {
                    "request": request, 
                    "error": f"Unsupported content type: {content_type}",
                    "classification": classification
                })

        else:
            return templates.TemplateResponse("index.html", {
                "request": request, 
                "error": "No input provided"
            })

        # 3. Behavioral Analysis
        beh_res = behavioral_analyzer.analyze(results)
        results.append(beh_res)

        # 4. Aggregation
        final_verdict = aggregator.aggregate(results, content_type)
        final_verdict["classification"] = classification

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": f"An error occurred: {str(e)}"
        })
    finally:
        # Clean up uploaded file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    return templates.TemplateResponse("result.html", {
        "request": request, 
        "verdict": final_verdict
    })


@app.post("/verify")
async def verify(
    file: UploadFile = File(None),
    url: str = Form(None),
    payload: dict = Body(None)
):
    results = []
    file_path = None
    content_type = None
    classification = None

    try:
        if not url and payload:
            url = payload.get("url")

        # URL path
        if url:
            classification = content_classifier.classify_url(url)
            content_type = classification.get("content_type")
            meta_res = metadata_analyzer.analyze(url, 'url')
            results.append(meta_res)
            url_res = url_analyzer.analyze(url)
            results.append(url_res)

        elif file and file.filename:
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, dir=UPLOAD_FOLDER, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                file_path = tmp.name

            classification = content_classifier.classify_file(file_path)
            raw_mime = classification.get("raw_mime") or ""
            content_type = classification.get("content_type") or ""

            meta_res = metadata_analyzer.analyze(file_path, raw_mime or content_type)
            results.append(meta_res)

            if content_type == 'image':
                results.append(image_analyzer.analyze(file_path))
            elif content_type == 'video':
                results.append(video_analyzer.analyze(file_path))
            elif content_type == 'audio':
                results.append(audio_analyzer.analyze(file_path))
            else:
                return JSONResponse({"error": f"Unsupported content type: {content_type}"}, status_code=400)
        else:
            return JSONResponse({"error": "No input provided. Upload a file or send {\"url\": \"https://...\"}."}, status_code=400)

        beh_res = behavioral_analyzer.analyze(results)
        results.append(beh_res)

        final_verdict = aggregator.aggregate(results, content_type)
        final_verdict["classification"] = classification

        explanation_signals = final_verdict.get("top_signals") or []
        explanation = "; ".join(explanation_signals[:2]) if explanation_signals else ""
        if not explanation and final_verdict.get("layer_breakdown"):
            last_layer = final_verdict["layer_breakdown"][-1]
            details = last_layer.get("details", []) if isinstance(last_layer, dict) else []
            explanation = details[0] if details else ""

        return JSONResponse({
            "verdict": final_verdict.get("verdict"),
            "confidence": final_verdict.get("final_score"),
            "explanation": explanation or "Risk assessment generated from metadata, AI-pattern, and behavioral cues.",
            "breakdown": final_verdict
        })

    except Exception as e:
        return JSONResponse({"error": f"Verification error: {str(e)}"}, status_code=500)
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
