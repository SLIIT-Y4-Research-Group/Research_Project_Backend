import numpy as np
import json
import os
import logging
from typing import Dict
from tensorflow.keras.models import load_model
import google.generativeai as genai

logger = logging.getLogger(__name__)

from dotenv import load_dotenv


class StoryGenerator:
    """Enhanced GRU Story Generator with Gemini Refinement"""

    def __init__(self, model_path: str = None, vocab_path: str = None):

        load_dotenv()  # Load .env

        # Convert string to boolean
        is_production = os.getenv("PRODUCTION", "false").lower() == "true"

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Select paths based on environment
        if is_production:
            self.model_path = model_path or os.getenv("STORY_MODEL_PATH")
            self.vocab_path = vocab_path or os.getenv("STORY_VOCAB_PATH")
        else:
            self.model_path = model_path or os.getenv("STORY_MODEL_PATH") or os.path.join(
                base_dir, "data", "models", "best_gru_model.h5"
            )
            self.vocab_path = vocab_path or os.getenv("STORY_VOCAB_PATH") or os.path.join(
                base_dir, "data", "vocabulary"
            )

        self.seq_length = 120

        # Gemini setup 
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.gemini = genai.GenerativeModel("gemini-1.5-flash")

        print("Running in:", "PRODUCTION" if is_production else "DEVELOPMENT")
        print("Model path:", self.model_path)

        self._load_vocabulary()
        self._load_model()

    
    # Load vocabulary
    
    def _load_vocabulary(self):
        try:
            with open(os.path.join(self.vocab_path, "char_to_idx.json"), "r") as f:
                self.char_to_idx = json.load(f)

            with open(os.path.join(self.vocab_path, "idx_to_char.json"), "r") as f:
                self.idx_to_char = {int(k): v for k, v in json.load(f).items()}

            self.vocab_size = len(self.char_to_idx)

        except Exception as e:
            logger.error(f"Vocabulary load failed: {e}")

    
    # Load model
    
    def _load_model(self):
        try:
            self.model = load_model(self.model_path)
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            self.model = None

    
    # Encode input
    
    def _encode(self, text):
        seq = [self.char_to_idx.get(c, 0) for c in text]

        if len(seq) < self.seq_length:
            seq = [0] * (self.seq_length - len(seq)) + seq
        else:
            seq = seq[-self.seq_length:]

        return np.array([seq])

    
    # Sampling
    
    def _sample(self, preds, temperature=0.7):
        preds = np.log(preds + 1e-8) / temperature
        preds = np.exp(preds) / np.sum(np.exp(preds))
        return np.random.choice(len(preds), p=preds)

    
    # Clean raw GRU output
    
    def _clean_text(self, text):
        import re

        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(.)\1{3,}', r'\1\1', text)

        return text.strip()

    
    # Generate raw GRU story
    
    def _generate_raw_story(self, mood, character, start, max_length, temperature):

        seed = f"<MOOD:{mood}> <CHAR:{character}> <START:{start}> "

        generated = seed

        for _ in range(max_length):
            encoded = self._encode(generated)

            preds = self.model.predict(encoded, verbose=0)[0]

            next_idx = self._sample(preds, temperature)
            next_char = self.idx_to_char.get(next_idx, "")

            generated += next_char

            # simple stop condition
            if generated.endswith(".") and len(generated) > 200:
                break

        return self._clean_text(generated)

    
    # Gemini refinement
    
    def _refine_with_gemini(self, raw_story, mood):

        prompt = f"""
Rewrite the following story to make it:
- Easy to read for children aged 12–14
- Emotionally engaging and relatable
- Clear and well-structured
- Keep the same meaning but improve grammar and flow
- Add a gentle positive or meaningful ending

Story:
{raw_story}
"""

        try:
            response = self.gemini.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini failed: {e}")
            return raw_story

    
    # Main generation function
    
    def generate_story(self, mood_inputs: Dict,
                       max_length: int = 400,
                       temperature: float = 0.7):

        if self.model is None:
            return "Model not loaded."

        mood = mood_inputs.get("mood", "happy")
        character = mood_inputs.get("character", "rabbit")
        start = mood_inputs.get("start", "Once upon a time")

        # 1. Generate raw GRU story
        raw_story = self._generate_raw_story(
            mood, character, start, max_length, temperature
        )

        # 2. Refine with Gemini
        final_story = self._refine_with_gemini(raw_story, mood)

        return final_story

    
    def get_model_info(self):
        return {
            "model_loaded": self.model is not None,
            "vocab_size": self.vocab_size,
            "seq_length": self.seq_length
        }