class ConfidenceAggregator:
    def aggregate(self, results, content_type=None):
        """
        Combines evidence from multiple layers to compute a final verdict.
        Adaptive weighting based on content type and available evidence.
        """
        # Base weights by content type
        base_weights = {
            "image": {
                "Origin & Metadata Consistency": 0.25,
                "Content-Specific AI Pattern Integrity (Image)": 0.45,
                "Behavioral Deviation Analysis": 0.30,
            },
            "video": {
                "Origin & Metadata Consistency": 0.20,
                "Content-Specific AI Pattern Integrity (Video)": 0.50,
                "Behavioral Deviation Analysis": 0.30,
            },
            "audio": {
                "Origin & Metadata Consistency": 0.20,
                "Content-Specific AI Pattern Integrity (Audio)": 0.50,
                "Behavioral Deviation Analysis": 0.30,
            },
            "url": {
                "Origin & Metadata Consistency": 0.25,
                "Content-Specific AI Pattern Integrity (URL)": 0.45,
                "Behavioral Deviation Analysis": 0.30,
            },
            "default": {
                "Origin & Metadata Consistency": 0.25,
                "Behavioral Deviation Analysis": 0.25,
            }
        }

        weights = base_weights.get(content_type, base_weights["default"])

        weighted_sum = 0
        total_weight = 0

        for res in results:
            layer = res.get("layer")
            score = res.get("score", 0)
            weight = weights.get(layer, 0.1)  # fall-back weight
            weighted_sum += score * weight
            total_weight += weight

        final_score = (weighted_sum / total_weight) if total_weight else 0

        # Verdict mapping
        if final_score >= 70:
            verdict = "Real"
            risk_level = "Low"
        elif final_score >= 40:
            verdict = "Suspicious"
            risk_level = "Medium"
        else:
            verdict = "Likely Fake"
            risk_level = "High"

        return {
            "final_score": round(final_score, 2),
            "verdict": verdict,
            "risk_level": risk_level,
            "layer_breakdown": results
        }
