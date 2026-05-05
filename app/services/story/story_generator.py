import numpy as np
import json
import os
import logging
import random
import time
from typing import Dict, List, Optional
from tensorflow.keras.models import load_model
import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class StoryGenerator:
    """Enhanced GRU Story Generator with Gemini Refinement + Multi-Key Support"""

    def __init__(self, model_path: str = None, vocab_path: str = None):

        load_dotenv()

        # Environment mode
        is_production = os.getenv("PRODUCTION", "false").lower() == "true"

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    
        # Model Path
    
        default_model_path = os.path.join(base_dir, "data", "models", "best_gru_model.h5")

        self.model_path = (
            model_path
            or (os.getenv("STORY_MODEL_PATH") if is_production else None)
            or default_model_path
        )

    
        # Vocabulary Path (NO ENV NEEDED)
    
        default_vocab_path = os.path.join(base_dir, "data", "vocabulary")

        self.vocab_path = vocab_path or default_vocab_path

        if not os.path.exists(self.vocab_path):
            raise FileNotFoundError(f"Vocabulary path not found: {self.vocab_path}")

    
        # Gemini API Keys (MULTIPLE)
    
        keys_env = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY")

        if not keys_env:
            raise ValueError("No Gemini API keys found in environment")

        # Convert to list
        self.api_keys: List[str] = [k.strip() for k in keys_env.split(",")]

        self.model_name = "gemini-1.5-flash"

        self.seq_length = 120

        print("Running in:", "PRODUCTION" if is_production else "DEVELOPMENT")
        print("Model path:", self.model_path)
        print("Vocab path:", self.vocab_path)
        print(f"Loaded {len(self.api_keys)} Gemini key(s)")

        self._load_vocabulary()
        self._load_model()


    # Load Vocabulary

    def _load_vocabulary(self):
        try:
            with open(os.path.join(self.vocab_path, "char_to_idx.json"), "r") as f:
                self.char_to_idx = json.load(f)

            with open(os.path.join(self.vocab_path, "idx_to_char.json"), "r") as f:
                self.idx_to_char = {int(k): v for k, v in json.load(f).items()}

            self.vocab_size = len(self.char_to_idx)

        except Exception as e:
            logger.error(f"Vocabulary load failed: {e}")
            raise


    # Load Model

    def _load_model(self):
        try:
            self.model = load_model(self.model_path)
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            self.model = None


    # Encode Input

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


    # Clean Text

    def _clean_text(self, text):
        import re
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(.)\1{3,}', r'\1\1', text)
        return text.strip()


    # Generate Raw Story (GRU)

    def _generate_raw_story(self, mood, character, start, max_length, temperature):

        seed = f"<MOOD:{mood}> <CHAR:{character}> <START:{start}> "
        generated = seed

        for _ in range(max_length):
            encoded = self._encode(generated)
            preds = self.model.predict(encoded, verbose=0)[0]

            next_idx = self._sample(preds, temperature)
            next_char = self.idx_to_char.get(next_idx, "")

            generated += next_char

            if generated.endswith(".") and len(generated) > 200:
                break

        return self._clean_text(generated)


    # Gemini Refinement (Multi-Key Fallback)

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

        keys = self.api_keys[:]
        random.shuffle(keys)  # avoid always hitting same key

        last_error = None

        for key in keys:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(self.model_name)

                response = model.generate_content(prompt)

                if response and response.text:
                    return response.text

            except Exception as e:
                logger.warning(f"Gemini key failed: {key} -> {e}")
                last_error = e
                time.sleep(1)

        logger.error("All Gemini keys failed")
        return raw_story  # fallback


    # Main Generation Function

    def generate_story(
        self,
        mood_inputs: Dict,
        max_length: int = 400,
        temperature: float = 0.7
    ):

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


    # Model Info

    def get_model_info(self):
        return {
            "model_loaded": self.model is not None,
            "vocab_size": self.vocab_size,
            "seq_length": self.seq_length,
            "gemini_keys": len(self.api_keys)
        }