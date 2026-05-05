import os
import random
import time
import hashlib
from typing import Dict, Optional
import logging
from app.core.story.config import settings

from google import genai
from google.genai import types  # For config

logger = logging.getLogger(__name__)


class EnhancedSinhalaStoryGenerator:

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"  # Reliable current model
        self.load_moral_lessons()

    def load_moral_lessons(self):
        self.moral_lessons = {
            "happy": {
                "lesson": "සතුට බෙදා ගැනීමෙන් එය වැඩි වේ",
                "teaching": "සත්‍ය සතුට ලැබෙන්නේ අන් අයට උපකාර කිරීමෙන්ය"
            },
            "sad": {
                "lesson": "දුක ජීවිතයේ ගුරුවරයෙකි",
                "teaching": "දුක් අත්දැකීම් අපව ශක්තිමත් කරයි"
            },
            "calm": {
                "lesson": "සන්සුන් මනසකට සියල්ල පැහැදිලි වේ",
                "teaching": "සාමය ජීවිතයේ වටිනාම සම්පතකි"
            },
            "angry": {
                "lesson": "කෝපය පාලනය කිරීම මහත් ගුණයකි",
                "teaching": "කෝපය පාලනය කල හැකි අය ශක්තිමත්ය"
            },
            "hopeful": {
                "lesson": "බලාපොරොත්තුව අඳුරු කාලයේ ආලෝකයකි",
                "teaching": "බලාපොරොත්තුව ජීවිතය ඉදිරියට ගෙන යයි"
            }
        }

    def get_model_info(self) -> Dict[str, str]:
        return {
            "model_name": self.model_name,
            "type": "Gemini API",
            "language": "Sinhala",
            "provider": "Google Generative AI"
        }

    def generate_story(
        self,
        mood: str,
        weather: str,
        character: str,
        starter_sentence: Optional[str] = None,
        story_length: str = "medium",
        temperature: float = 1.0
    ) -> Dict:

        start_time = time.time()

        try:
            story_text = self._generate_with_gemini(
                mood, weather, character, starter_sentence, story_length, temperature
            )

            moral = self._extract_moral(mood)
            title = self._generate_title(mood, character)
            generation_time = time.time() - start_time

            return {
                "success": True,
                "story_type": "enhanced",
                "title": title,
                "story": story_text,
                "moral_lesson": moral,
                "metadata": {
                    "mood": mood,
                    "weather": weather,
                    "character": character,
                    "story_length": story_length,
                    "words": len(story_text.split()),
                    "generation_time": round(generation_time, 2),
                    "generator": "Gemini AI",
                    "unique_id": self._generate_story_id(mood, weather, character)
                }
            }

        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return {
                "success": False,
                "story": "කථාව නිර්මාණය කිරීමේදී දෝෂයක් ඇති විය."
            }

    def _generate_with_gemini(
        self,
        mood, weather, character,
        starter_sentence, story_length,
        temperature
    ) -> str:

        length_map = {
            "short": "3 to 4 short paragraphs",
            "medium": "5 to 6 paragraphs",
            "long": "7 to 9 paragraphs"
        }
        length_instruction = length_map.get(story_length, "5 to 6 paragraphs")

        prompt = f"""
ඔබ ශ්‍රී ලාංකීය ගම්මාන වල කතා කියන කථාකාරයෙකි.

කරුණාකර වයස අවුරුදු 12–14 අතර දරුවන්ට පහසුවෙන් කියවිය හැකි
සරල සිංහලෙන් ජනප්‍රවාද ශෛලියේ කතාවක් ලියන්න.

කථාවේ විස්තර:
- මනෝභාවය: {mood}
- කාලගුණය: {weather}
- ප්‍රධාන චරිතය: {character}

අවශ්‍යතා:

1. සරල සහ පැහැදිලි සිංහල වචන භාවිතා කරන්න
2. කෙටි වාක්‍ය භාවිතා කරන්න
3. දරුවන්ට තේරෙන ලෙස කතාව ලියන්න
4. ගම්මාන කතා කියන ආකාරයේ ජනප්‍රවාද හැඟීම තබාගන්න
5. අවස්ථා විස්තර කරන්න (ගස්, ගඟ, වනය, ගම්මාන)
6. අවසානයේ සදාචාර පාඩමක් තිබිය යුතුය
7. සංවාද (dialogue) ටිකක් ඇතුළත් කරන්න

කථාවේ දිග:
{length_instruction}

ආරම්භ වාක්‍යය:
{starter_sentence if starter_sentence else "ඉතා කලකට පෙර, ගම්මානයක් අසල..."}
"""

        # Generate text using the correct SDK call
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=5000
            )
        )

        return response.text.strip()

    def _extract_moral(self, mood):
        moral = self.moral_lessons.get(mood, self.moral_lessons["happy"])
        return {"lesson": moral["lesson"], "teaching": moral["teaching"]}

    def _generate_title(self, mood, character):
        mood_words = {
            "happy": "සතුටුමත්",
            "sad": "දුක්ඛිත",
            "calm": "සන්සුන්",
            "angry": "ක්‍රෝධයේ",
            "hopeful": "බලාපොරොත්තු සහිත"
        }
        titles = ["ගමන", "කථාව", "සංචාරය", "අභියෝගය", "පාඩම"]
        return f"{character}ගේ {mood_words.get(mood, '')} {random.choice(titles)}"

    def _generate_story_id(self, mood, weather, character):
        raw = f"{mood}_{weather}_{character}_{time.time()}_{random.random()}"
        return hashlib.md5(raw.encode()).hexdigest()[:10]


story_generator = EnhancedSinhalaStoryGenerator(
    api_key=settings.GEMINI_API_KEYS[0]
)