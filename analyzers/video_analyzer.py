import cv2
import numpy as np


class VideoAnalyzer:
    def analyze(self, file_path):
        details = []
        score = 100

        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                return {"layer": "Content-Specific AI Pattern Integrity (Video)", "score": 0, "details": ["Failed to open video"]}

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            details.append(f"Frames: {frame_count}, FPS: {fps:.2f}, Resolution: {width}x{height}")

            prev_frame = None
            diffs = []
            luminance = []
            resolution_changes = 0

            sample_rate = max(1, frame_count // 40)  # ~40 samples

            last_size = (width, height)
            for i in range(0, frame_count, sample_rate):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    break

                h, w = frame.shape[:2]
                if (w, h) != last_size:
                    resolution_changes += 1
                last_size = (w, h)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                luminance.append(np.mean(gray))

                if prev_frame is not None:
                    diff = np.mean(np.abs(gray - prev_frame))
                    diffs.append(diff)
                prev_frame = gray

            cap.release()

            if diffs:
                avg_diff = np.mean(diffs)
                std_diff = np.std(diffs)
                details.append(f"Frame diff avg/std: {avg_diff:.2f}/{std_diff:.2f}")
                if std_diff < 1.0:
                    score -= 15
                    details.append("Low temporal variance (motion too uniform).")
                if avg_diff < 2.0:
                    score -= 10
                    details.append("Very stable consecutive frames (possible frame freezing or synthesis).")

            if luminance:
                lum_std = np.std(luminance)
                details.append(f"Luminance std across frames: {lum_std:.2f}")
                if lum_std < 3:
                    score -= 10
                    details.append("Luminance barely changes across time (synthetic lighting).")

            if resolution_changes > 0:
                score -= 10
                details.append("Detected resolution jumps between sampled frames (possible splice).")

            # Blink / micro-motion proxy: edge energy variance
            if prev_frame is not None:
                edge_energy = []
                prev_gray = None
                cap = cv2.VideoCapture(file_path)
                for i in range(0, min(frame_count, 120), max(1, frame_count // 60)):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ok, frame = cap.read()
                    if not ok:
                        break
                    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(g, 50, 150)
                    edge_energy.append(np.mean(edges))
                    if prev_gray is not None:
                        delta = np.mean(np.abs(g - prev_gray))
                        if delta < 1.0:
                            score -= 3
                            details.append("Consecutive sampled frames nearly identical (low micro-motion).")
                    prev_gray = g
                cap.release()
                if edge_energy:
                    ee_std = np.std(edge_energy)
                    if ee_std < 2.0:
                        score -= 5
                        details.append("Edge energy too consistent (possible temporal smoothing).")

        except Exception as e:
            details.append(f"Error in video analysis: {str(e)}")
            score -= 10

        return {
            "layer": "Content-Specific AI Pattern Integrity (Video)",
            "score": max(0, score),
            "details": details
        }
