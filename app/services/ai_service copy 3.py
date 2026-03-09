from google import genai
import random
import hashlib
import time
from typing import Optional, Dict


class GeminiSinhalaStoryGenerator:

    def __init__(self, api_key: str):
        # Create Gemini client
        self.client = genai.Client(api_key=api_key)

        # Recommended fast model
        self.model_name = "gemini-2.0-flash"

        # Sinhala names for characters
        self.character_names = {
            "lion": "සිංහයා",
            "elephant": "අලියා",
            "hare": "හාවා",
            "bird": "කුරුල්ලා"
        }

    # -----------------------------------------
    # Story Length Mapping
    # -----------------------------------------
    def _length_instruction(self, story_length: str) -> str:

        mapping = {
            "short": "8-12 වාක්‍ය",
            "medium": "12-18 වාක්‍ය",
            "long": "18-25 වාක්‍ය"
        }

        return mapping.get(story_length, "12-18 වාක්‍ය")

    # -----------------------------------------
    # Unique Story ID
    # -----------------------------------------
    def _generate_story_id(self, mood, weather, character):

        raw = f"{mood}_{weather}_{character}_{time.time()}_{random.random()}"
        return hashlib.md5(raw.encode()).hexdigest()[:10]

    # -----------------------------------------
    # Generate Text from Gemini
    # -----------------------------------------
    def _generate_text(self, prompt: str, temperature: float, max_tokens: int):

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )

        return response.text.strip()

    # -----------------------------------------
    # Main Story Generation
    # -----------------------------------------
    def generate_story(
        self,
        mood: str,
        weather: str,
        character: str,
        starter_sentence: Optional[str],
        story_length: str = "medium",
        temperature: float = 0.7,
        max_length: Optional[int] = None
    ) -> Dict:

        char_name = self.character_names.get(character, character)
        length_text = self._length_instruction(story_length)

        random_events = [
            "අභිරහස් වස්තුවක් සොයා ගැනීම",
            "රහස් සත්වයෙකු හමුවීම",
            "ගම්මානයට අමුතු අමුත්තෙක් පැමිණීම",
            "වනාන්තරයේ රහස් ගුහාවක් සොයා ගැනීම",
            "මායා බලයක් ඇති වස්තුවක් හමුවීම",
            "මිතුරෙකු විසින් වංචා වීම",
            "අනතුරුදායක ගමනක් ආරම්භ කිරීම",
            "ගම්මානය බේරා ගැනීමට සිදුවීම"
        ]

        event = random.choice(random_events)

        prompt = f"""
ඔබ නිර්මාණශීලී සිංහල කතාකරුයෙකි.

මෙම තොරතුරු අනුව නව සහ රසවත් සිංහල කතාවක් ලියන්න.

මනෝභාවය: {mood}
කාලගුණය: {weather}
ප්‍රධාන චරිතය: {char_name}
ප්‍රධාන සිදුවීම: {event}

{"කතාව මෙයින් ආරම්භ විය යුතුය: " + starter_sentence if starter_sentence else ""}

නියමයන්:

• සරල සිංහල භාෂාව භාවිතා කරන්න  
• dialogues ඇතුළත් කරන්න  
• plot twist එකක් තිබිය යුතුය  
• අවසානයේ meaningful idea එකක් තිබිය යුතුය  

දිග: {length_text}
"""

        max_tokens = max_length if max_length else 1200

        story = self._generate_text(prompt, temperature, max_tokens)

        # Generate title
        title_prompt = f"මෙම සිංහල කතාවට කෙටි ආකර්ෂණීය සිරස්තලයක් ලියන්න:\n\n{story[:500]}"
        title = self._generate_text(title_prompt, 0.6, 50)

        # Generate moral
        moral_prompt = f"මෙම කතාවෙන් ඉගෙන ගත හැකි පාඩම එක වාක්‍යයකින් ලියන්න:\n\n{story}"
        moral = self._generate_text(moral_prompt, 0.6, 60)

        return {
            "success": True,
            "title": title,
            "story": story,
            "moral_lesson": {
                "teaching": moral
            },
            "metadata": {
                "mood": mood,
                "weather": weather,
                "character": character,
                "story_length": story_length,
                "generation_method": "Gemini AI",
                "unique_id": self._generate_story_id(mood, weather, character)
            }
        }


# Create global generator
story_generator = GeminiSinhalaStoryGenerator(
    api_key="AIzaSyBak_gq9nqKdex0tNNlf2Zig44g2ulO1OI"
)