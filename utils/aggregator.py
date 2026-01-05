from typing import Dict, List, Optional


class ConfidenceAggregator:
    """
    Confidence / Risk Aggregation Engine

    - Converts per-layer scores (0-100 where higher = cleaner) into risk scores (0-100 where higher = riskier)
    - Applies adaptive weights by content type with default 0.2/0.6/0.2 (metadata / AI model / behavioral)
    - Maps final risk to verdict bands: 0–30 Real, 31–60 Suspicious, 61–100 Likely Fake
    """

    metadata_layers = {"Origin & Metadata Consistency"}
    ai_layers_map: Dict[str, set] = {
        "image": {"Content-Specific AI Pattern Integrity (Image)"},
        "video": {"Content-Specific AI Pattern Integrity (Video)"},
        "audio": {"Content-Specific AI Pattern Integrity (Audio)"},
        "url": {"Content-Specific AI Pattern Integrity (URL)"},
    }
    behavioral_layers = {"Behavioral Deviation Analysis"}

    def _avg_risk(self, results: List[dict], layer_names: set) -> Optional[float]:
        risks = [max(0, min(100, 100 - r.get("score", 0))) for r in results if r.get("layer") in layer_names]
        if not risks:
            return None
        return sum(risks) / len(risks)

    def _component_weights(self, content_type: Optional[str]):
        base = {"metadata": 0.2, "ai": 0.6, "behavioral": 0.2}
        # Slight emphasis tweaks per modality
        if content_type == "url":
            return {"metadata": 0.3, "ai": 0.5, "behavioral": 0.2}
        if content_type == "audio":
            return {"metadata": 0.2, "ai": 0.55, "behavioral": 0.25}
        return base

    def _verdict(self, risk_score: float):
        if risk_score <= 30:
            return "Real", "Low"
        if risk_score <= 60:
            return "Suspicious", "Medium"
        return "Likely Fake", "High"

    def aggregate(self, results: List[dict], content_type: Optional[str] = None):
        ai_layers = self.ai_layers_map.get(content_type or "", set())

        metadata_risk = self._avg_risk(results, self.metadata_layers)
        ai_risk = self._avg_risk(results, ai_layers) if ai_layers else None
        behavioral_risk = self._avg_risk(results, self.behavioral_layers)

        weights = self._component_weights(content_type)

        def safe(score, fallback=50):
            return fallback if score is None else score

        final_score = (
            safe(metadata_risk) * weights["metadata"] +
            safe(ai_risk) * weights["ai"] +
            safe(behavioral_risk) * weights["behavioral"]
        ) / sum(weights.values())

        verdict, risk_level = self._verdict(final_score)

        # Identify top contributing signals (highest risk layers first)
        layer_risks = []
        for res in results:
            risk = max(0, min(100, 100 - res.get("score", 0)))
            detail = res.get("details", [""])
            layer_risks.append({
                "layer": res.get("layer"),
                "risk": risk,
                "detail": detail[0] if detail else "",
            })
        top_signals = [f"{lr['layer']}: {lr['detail']}".strip() for lr in sorted(layer_risks, key=lambda x: x["risk"], reverse=True)[:3] if lr.get("layer")]

        return {
            "final_score": round(final_score, 2),
            "verdict": verdict,
            "risk_level": risk_level,
            "layer_breakdown": results,
            "component_scores": {
                "metadata_risk": metadata_risk,
                "ai_risk": ai_risk,
                "behavioral_risk": behavioral_risk,
            },
            "top_signals": top_signals,
        }
