import json
from typing import List
from google import genai

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_API_KEY_2,
    GEMINI_MODEL,
)

_clients: List[genai.Client] = []

if GEMINI_API_KEY:
    _clients.append(genai.Client(api_key=GEMINI_API_KEY))
if GEMINI_API_KEY_2:
    _clients.append(genai.Client(api_key=GEMINI_API_KEY_2))


def _call_gemini(prompt: str) -> str:
    for client in _clients:
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()
        except Exception:
            continue
    raise RuntimeError("Gemini failed for all API keys")


def generate_full_sinhala_report(llm_review: dict) -> str:
    """
    Convert the full English LLM analysis into a rich, human-readable Sinhala report.
    Written for non-technical parents — zero technical jargon.
    """

    prompt = f"""
ඔබ දරු මනෝවිද්‍යා හා චිත්‍ර ශිල්ප ක්ෂේත්‍රයේ අත්දැකීම් සහිත ලිංගිකත්ව ශ්‍රේෂ්ඨ විශේෂඥයෙකි. 
ඔබේ කාර්යය නම් ළමා චිත්‍ර විශ්ලේෂණ ලිපියක් සිංහලෙන් දෙමාපියන්ට තේරෙන ආකාරයෙන් ලිවීමයි.

IMPORTANT RULES:
- Write ONLY in natural, warm Sinhala — as if explaining to a parent face to face
- NO technical terms at all (no "foreground ratio", "edge density", "spatial coordinates" etc.)
- NO JSON, NO code, NO English words except proper nouns
- Write in flowing paragraphs — not bullet lists everywhere
- Be warm, empathetic, and reassuring
- Reference actual things visible in the drawing (objects, colors, figures)
- This is NOT a medical diagnosis — make that clear gently
- Length: comprehensive but readable (400-600 Sinhala words)

STRUCTURE TO FOLLOW:

🔍 **හඳුනාගත් දේවල්**
(Describe what objects/figures are in the drawing, in plain Sinhala. 
What did the child draw? Where are they? How do they look?
Example: "චිත්‍රයේ මැද ළමයෙකු ඉඳගෙන ඉන්නා දර්ශනයක් ඇත. ඔහුගේ මුහුණේ ..."
Do NOT say "detected objects array" or list labels mechanically.)

😊 **දරුවාගේ හැඟීම්**
(What emotions does the drawing show? Use warm language.
Explain the FINAL EMOTION and why — in simple terms.
Example: "මෙම චිත්‍රය දෙස බලන විට, දරුවා යම් ආකාරයක ...")

🎨 **වර්ණ සහ ඒවායේ අර්ථය**
(What colors were used? What might they mean emotionally?
Avoid percentages or ratios — just describe naturally.
Example: "දරුවා ප්‍රධාන වශයෙන් නිල් සහ රතු ...")

📍 **චිත්‍රයේ සැකැස්ම**
(How are things arranged? Are figures close together or far apart?
Is there empty space? Are figures large or small?
Again — no technical jargon.
Example: "චිත්‍රයේ ඇති සියලු රූප ...")

🌱 **දරුවාගේ වයසට ගැළපෙනවාද?**
(Is this drawing normal for the child's age? Reassure or note concerns warmly.)

💬 **දෙමාපියන් සදහා මඟ පෙන්වීම**
(What should the parent do next? What gentle questions can they ask?
Is there anything to watch out for?
Be warm and practical — not alarming.)

🧾 **සමස්ත හැඟීම් තත්ත්වය**
(One or two warm sentences summarizing the child's overall emotional state.
End on a caring, hopeful note.)

---
ENGLISH ANALYSIS TO CONVERT:
{json.dumps(llm_review, ensure_ascii=False, indent=2)}
---

Write the complete Sinhala report now. Remember: warm, clear, no jargon, no JSON, for parents.
"""

    try:
        return _call_gemini(prompt)
    except Exception:
        # Graceful fallback: return basic Sinhala from the English description
        desc = llm_review.get("description", "")
        emotion = llm_review.get("final_emotion", "")
        condition = llm_review.get("emotional_condition", "")

        fallback_parts = []
        if emotion:
            label_si = "සතුටු" if emotion.lower() == "happy" else "දුකසිත"
            fallback_parts.append(f"මෙම චිත්‍රය {label_si} හැඟීමක් පෙන්නුම් කරයි.")
        if condition:
            fallback_parts.append(condition)
        if desc:
            fallback_parts.append(desc)

        if fallback_parts:
            return "\n\n".join(fallback_parts)

        return "චිත්‍ර විශ්ලේෂණ වාර්තාව ජනනය කිරීමට නොහැකි විය. කරුණාකර දරුවා සමඟ සෘජුවම කතා කරන්න."