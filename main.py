from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
import magic
from analyzers.metadata_analyzer import MetadataAnalyzer
from analyzers.image_analyzer import ImageAnalyzer
from analyzers.video_analyzer import VideoAnalyzer
from analyzers.audio_analyzer import AudioAnalyzer
from analyzers.url_analyzer import URLAnalyzer
from analyzers.behavioral_analyzer import BehavioralAnalyzer
from analyzers.content_classifier import ContentClassifier
from utils.aggregator import ConfidenceAggregator

app = FastAPI(title="LAVS - Layered Authenticity Verification System")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
