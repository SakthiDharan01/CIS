import cv2
import numpy as np


class ImageAnalyzer:
    def _glcm_co_occurrence(self, gray):
        # Quantize to 32 levels to keep it light
        q = (gray / 8).astype(np.uint8)
        glcm = np.zeros((32, 32), dtype=np.float64)
        # Horizontal adjacency
        glcm_idx1 = q[:, :-1].flatten()
        glcm_idx2 = q[:, 1:].flatten()
        for a, b in zip(glcm_idx1, glcm_idx2):
            glcm[a, b] += 1
        glcm = glcm / (glcm.sum() + 1e-8)
        contrast = np.sum([(i - j) ** 2 * glcm[i, j] for i in range(32) for j in range(32)])
        homogeneity = np.sum([glcm[i, j] / (1 + abs(i - j)) for i in range(32) for j in range(32)])
        entropy = -np.sum(glcm * np.log2(glcm + 1e-9))
        return contrast, homogeneity, entropy

    def analyze(self, file_path):
        details = []
        score = 100

        try:
            img = cv2.imread(file_path)
            if img is None:
                return {"layer": "Content-Specific AI Pattern Integrity (Image)", "score": 0, "details": ["Failed to load image"]}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 1) Noise / texture smoothness
            noise_sigma = np.std(gray)
            details.append(f"Noise Level (sigma): {noise_sigma:.2f}")
            if noise_sigma < 5:
                score -= 20
                details.append("Unnaturally smooth texture (possible AI over-smoothing).")

            # 2) Regional coherence (micro-regions variance)
            h, w = gray.shape
            grid = 4
            region_vars = []
            for i in range(grid):
                for j in range(grid):
                    r0, r1 = int(i * h / grid), int((i + 1) * h / grid)
                    c0, c1 = int(j * w / grid), int((j + 1) * w / grid)
                    region = gray[r0:r1, c0:c1]
                    region_vars.append(np.var(region))
            var_std = np.std(region_vars)
            details.append(f"Region variance std: {var_std:.2f}")
            if var_std < 50:
                score -= 10
                details.append("Micro-regions too uniform (cross-region coherence overly smooth).")

            # 3) Boundary consistency (edge energy on borders vs center)
            edges = cv2.Canny(gray, 50, 150)
            border_band = 10
            border_edges = np.mean(np.concatenate([
                edges[:border_band, :], edges[-border_band:, :], edges[:, :border_band], edges[:, -border_band:]
            ]))
            center_edges = np.mean(edges[border_band:-border_band, border_band:-border_band]) if h > 2*border_band and w > 2*border_band else 0
            details.append(f"Edge energy border/center: {border_edges:.2f}/{center_edges:.2f}")
            if border_edges < center_edges * 0.4:
                score -= 10
                details.append("Weak boundary details compared to center (possible compositing).")

            # 4) Symmetry heuristic (horizontal flip similarity)
            flipped = cv2.flip(gray, 1)
            symmetry_score = np.mean(np.abs(gray - flipped))
            details.append(f"Symmetry difference (L1): {symmetry_score:.2f}")
            if symmetry_score < 5:
                score -= 10
                details.append("Overly symmetric content (possible AI patterning).")

            # 5) Co-occurrence statistics (pixel relationships)
            contrast, homogeneity, entropy = self._glcm_co_occurrence(gray)
            details.append(f"GLCM contrast: {contrast:.2f}, homogeneity: {homogeneity:.2f}, entropy: {entropy:.2f}")
            if homogeneity > 0.45:
                score -= 10
                details.append("High homogeneity in pixel co-occurrence (textures too regular).")
            if entropy < 4.0:
                score -= 10
                details.append("Low entropy in pixel relationships (possible synthetic texture).")

        except Exception as e:
            details.append(f"Error in image analysis: {str(e)}")
            score -= 10

        return {
            "layer": "Content-Specific AI Pattern Integrity (Image)",
            "score": max(0, score),
            "details": details
        }
