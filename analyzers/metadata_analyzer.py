import os
import datetime
import exifread
import mimetypes
import cv2
import librosa
import whois
from urllib.parse import urlparse

class MetadataAnalyzer:
    def analyze(self, file_path, content_type):
        """
        Analyzes metadata for consistency.
        Returns a dictionary with 'score' (0-100) and 'details' (list of strings).
        """
        details = []
        score = 100  # Start with high confidence, deduct for anomalies

        try:
            # Basic File Stats
            file_stats = os.stat(file_path)
            creation_time = datetime.datetime.fromtimestamp(file_stats.st_ctime)
            modification_time = datetime.datetime.fromtimestamp(file_stats.st_mtime)
            
            details.append(f"Creation Time: {creation_time}")
            details.append(f"Modification Time: {modification_time}")

            if modification_time < creation_time:
                score -= 20
                details.append("Suspicious: Modification time is before creation time.")

            # Image Metadata (EXIF) and compression hints
            if content_type.startswith('image'):
                with open(file_path, 'rb') as f:
                    tags = exifread.process_file(f)
                    if not tags:
                        score -= 25
                        details.append("No EXIF metadata found (common in AI-generated images).")
                    else:
                        software = str(tags.get('Image Software', ''))
                        camera_make = str(tags.get('Image Make', ''))
                        lens_model = str(tags.get('EXIF LensModel', ''))
                        if software:
                            details.append(f"Software: {software}")
                        if camera_make:
                            details.append(f"Camera: {camera_make}")
                        if lens_model:
                            details.append(f"Lens: {lens_model}")

                        if 'Adobe' in software or 'GIMP' in software:
                            score -= 10
                            details.append(f"Edited with software: {software}")
                        if 'DALL-E' in software or 'Midjourney' in software:
                            score -= 80
                            details.append("Metadata explicitly indicates AI generation.")
                        if not camera_make:
                            score -= 10
                            details.append("Missing camera fingerprint (could be synthetic).")

                # Compression lineage proxy: compare file size vs resolution
                try:
                    img = cv2.imread(file_path)
                    if img is not None:
                        h, w = img.shape[:2]
                        size_kb = os.path.getsize(file_path) / 1024
                        pixels = h * w
                        size_per_mp = size_kb / max(1, pixels / 1_000_000)
                        details.append(f"Size per megapixel: {size_per_mp:.1f} KB/MP")
                        if size_per_mp < 80:  # highly compressed
                            score -= 10
                            details.append("High compression ratio detected (possible re-encoding).")
                except Exception:
                    pass

            # Video metadata: codec, fps, resolution consistency
            elif content_type.startswith('video'):
                cap = cv2.VideoCapture(file_path)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS) or 0
                    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0
                    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0
                    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                    codec = ''.join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
                    details.append(f"Codec: {codec}, FPS: {fps:.2f}, Resolution: {int(w)}x{int(h)}")
                    if fps and (fps < 15 or fps > 90):
                        score -= 10
                        details.append("Unusual frame rate for typical capture devices.")
                    if w and h and (w < 320 or h < 240):
                        score -= 5
                        details.append("Very low resolution video (possible downscale/re-encode).")
                else:
                    score -= 10
                    details.append("Could not read video metadata.")
                cap.release()

            # Audio metadata: sample rate and codec consistency
            elif content_type.startswith('audio'):
                try:
                    y, sr = librosa.load(file_path, sr=None, mono=True)
                    details.append(f"Sample Rate: {sr} Hz")
                    if sr not in [16000, 22050, 44100, 48000]:
                        score -= 10
                        details.append("Non-standard sample rate (possible resampling).")
                except Exception as e:
                    score -= 5
                    details.append(f"Audio metadata read issue: {str(e)}")

            # URL metadata: domain age and registration
            elif content_type == 'url':
                try:
                    parsed = urlparse(file_path)
                    domain = parsed.netloc
                    w = whois.whois(domain)
                    creation_date = w.creation_date
                    expiration_date = w.expiration_date
                    details.append(f"Domain: {domain}")
                    details.append(f"WHOIS creation: {creation_date}")
                    if creation_date:
                        age_days = (datetime.datetime.utcnow() - creation_date).days if isinstance(creation_date, datetime.datetime) else 0
                        details.append(f"Domain age (days): {age_days}")
                        if age_days < 180:
                            score -= 20
                            details.append("Very young domain (higher risk).")
                    if expiration_date:
                        details.append(f"WHOIS expiration: {expiration_date}")
                except Exception as e:
                    score -= 5
                    details.append(f"WHOIS lookup failed: {str(e)}")

        except Exception as e:
            details.append(f"Error analyzing metadata: {str(e)}")
            score -= 10

        return {
            "layer": "Origin & Metadata Consistency",
            "score": max(0, score),
            "details": details
        }
