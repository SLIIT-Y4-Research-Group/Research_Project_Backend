from typing import Dict, Any, List

def build_observations_report(
    emotion: Dict[str, Any],
    color: Dict[str, Any],
    stroke: Dict[str, Any],
    spatial: Dict[str, Any],
    objects: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """
    This is NOT a medical diagnosis.
    It's an observations-based summary with heuristic flags.
    """
    observations: List[str] = []
    flags: List[str] = []
    recommendations: List[str] = []

    # Emotion model result (your 4-class)
    e_label = emotion.get("label")
    e_conf = float(emotion.get("confidence", 0.0))
    observations.append(f"Emotion model output: {e_label} (confidence {e_conf:.2f}).")

    # Color
    colored_ratio = float(color.get("colored_ratio", 0.0))
    tags = color.get("tags", [])
    observations.append(f"Color usage: colored_ratio={colored_ratio:.2f}, tags={tags}.")

    if "mostly_blank" in tags or colored_ratio < 0.03:
        flags.append("Low color/ink usage (drawing may be very light or minimal).")

    if "dark_tones" in tags:
        observations.append("Overall brightness is low (darker tones present).")

    # Stroke
    edge_density = float(stroke.get("edge_density", 0.0))
    ink_ratio = float(stroke.get("ink_ratio", 0.0))
    thickness = float(stroke.get("thickness_proxy", 0.0))

    observations.append(
        f"Stroke metrics: edge_density={edge_density:.3f}, ink_ratio={ink_ratio:.3f}, thickness_proxy={thickness:.3f}."
    )

    if ink_ratio < 0.02:
        flags.append("Very low ink coverage (possible avoidance, incomplete drawing, or faint medium).")
    if thickness > 0.02:
        observations.append("Heavier/denser stroke appearance (thicker line proxy elevated).")

    # Spatial
    if not spatial.get("has_foreground", False):
        flags.append("No clear foreground detected (blank or extremely faint).")
    else:
        cov = float(spatial.get("coverage", 0.0))
        center = spatial.get("center_offset", {"dx": 0.0, "dy": 0.0})
        q = spatial.get("quadrant_ink", {})

        observations.append(f"Spatial coverage={cov:.2f}, center_offset dx={center['dx']:.2f}, dy={center['dy']:.2f}.")
        observations.append(f"Ink distribution quadrants (tl,tr,bl,br)={q}.")

        if cov < 0.08:
            flags.append("Small occupied area (drawing uses limited page space).")
        elif cov > 0.65:
            observations.append("Large occupied area (expansive page usage).")

        # top-heavy example
        tl = float(q.get("tl", 0.0))
        tr = float(q.get("tr", 0.0))
        bl = float(q.get("bl", 0.0))
        br = float(q.get("br", 0.0))
        if (tl + tr) > (bl + br) * 1.5 and (tl + tr) > 0.02:
            observations.append("Content is more concentrated in the upper half of the page.")

    # Objects
    if objects is None:
        observations.append("Object detection was not run.")
    else:
        observations.append(f"Detected objects count: {objects.get('count', 0)}.")
        # Add top labels summary
        dets = objects.get("detections", [])[:10]
        labels = [d.get("label") for d in dets]
        if labels:
            observations.append(f"Example detected labels: {labels}.")

    # Recommendations (safe + useful)
    recommendations.append("Use this result as a screening/observation aid, not a clinical diagnosis.")
    recommendations.append("If repeated flags appear across multiple drawings/weeks, consider a professional review with context (age, prompt, environment).")
    recommendations.append("Compare with the child's baseline drawings rather than single-image conclusions.")

    # Summary sentence
    summary = " | ".join(flags) if flags else "No strong heuristic flags; drawing appears within expected variation."

    return {
        "summary": summary,
        "observations": observations,
        "flags": flags,
        "recommendations": recommendations,
        "confidence_note": (
            "Heuristic interpretation is sensitive to scan quality, lighting, prompt type, and age. "
            "Prefer trends over time (multiple drawings) for higher reliability."
        )
    }