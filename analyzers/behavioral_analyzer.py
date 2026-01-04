class BehavioralAnalyzer:
    def analyze(self, previous_results):
        """
        Analyzes the results from other layers to detect behavioral deviations.
        AI content often lacks the 'imperfections' of human content.
        """
        details = []
        score = 100

        # Check for "too consistent" patterns in textual details
        for res in previous_results:
            if "details" in res:
                for detail in res["details"]:
                    key_phrases = ["unnaturally smooth", "too uniform", "stable", "regular", "consistent"]
                    if any(k in detail.lower() for k in key_phrases):
                        score -= 10
                        details.append(f"Behavioral flag: {detail}")

        # Score variance across layers (human content varies; AI often uniform)
        layer_scores = [r.get("score", 0) for r in previous_results if isinstance(r.get("score", None), (int, float))]
        if layer_scores:
            import numpy as np
            variance = float(np.var(layer_scores))
            details.append(f"Inter-layer score variance: {variance:.2f}")
            if variance < 50:  # low spread
                score -= 10
                details.append("Evidence layers are unusually consistent (behavioral uniformity).")

        # Penalize if many layers show low entropy / homogeneity flags
        consistency_flags = [d for r in previous_results for d in r.get("details", []) if "homogeneity" in d.lower() or "entropy" in d.lower()]
        if len(consistency_flags) >= 2:
            score -= 10
            details.append("Multiple layers report homogeneity/low entropy (over-regularized content).")

        if score == 100:
            details.append("No significant behavioral deviations detected.")

        return {
            "layer": "Behavioral Deviation Analysis",
            "score": max(0, score),
            "details": details
        }
