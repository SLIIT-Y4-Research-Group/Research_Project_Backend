import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Embedding, GRU, Dense, Dropout, LSTM
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
import pickle
from typing import Dict, List, Optional
import logging
from pathlib import Path
import time
import random
import os
import re

logger = logging.getLogger(__name__)

class GRUStoryGenerator:
    def __init__(self, model_path: str = "models/best_gru_model.h5"):
        self.model = None
        self.tokenizer = None
        self.max_sequence_length = 50
        self.vocab_size = 15000
        self.story_patterns = {}
        
        self.load_or_create_model(model_path)
        self.load_or_create_tokenizer()
        self.load_story_patterns()
        
    def load_or_create_model(self, model_path: str):
        """Load existing model or create a new one"""
        try:
            if Path(model_path).exists():
                self.model = load_model(model_path, compile=False)
                logger.info(f"Loaded existing model from {model_path}")
            else:
                logger.warning(f"Model not found at {model_path}. Creating enhanced model...")
                self._create_enhanced_model()
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                self.model.save(model_path)
                logger.info(f"Created and saved enhanced model to {model_path}")
                
        except Exception as e:
            logger.error(f"Error loading/creating model: {e}")
            self._create_enhanced_model()
    
    def _create_enhanced_model(self):
        """Create an enhanced model with better generation capabilities"""
        model = Sequential([
            Embedding(self.vocab_size, 256, input_length=self.max_sequence_length),
            GRU(512, return_sequences=True, dropout=0.2, recurrent_dropout=0.2),
            GRU(256, dropout=0.2, recurrent_dropout=0.2),
            Dense(512, activation='relu'),
            Dropout(0.3),
            Dense(256, activation='relu'),
            Dense(self.vocab_size, activation='softmax')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        logger.info("Created enhanced GRU model for story generation")
    
    def load_or_create_tokenizer(self):
        """Load or create comprehensive Sinhala tokenizer"""
        tokenizer_path = "models/tokenizer.pickle"
        
        try:
            if Path(tokenizer_path).exists():
                with open(tokenizer_path, 'rb') as f:
                    self.tokenizer = pickle.load(f)
                logger.info(f"Loaded tokenizer with {len(self.tokenizer.word_index)} words")
            else:
                self._create_extensive_tokenizer()
                os.makedirs("models", exist_ok=True)
                with open(tokenizer_path, 'wb') as f:
                    pickle.dump(self.tokenizer, f)
                logger.info(f"Created extensive tokenizer with {len(self.tokenizer.word_index)} words")
                
        except Exception as e:
            logger.error(f"Error with tokenizer: {e}")
            self._create_extensive_tokenizer()
    
    def _create_extensive_tokenizer(self):
        """Create extensive Sinhala vocabulary for diverse story generation"""
        # Read from a Sinhala text file if available
        sinhala_texts = []
        
        # Add comprehensive story elements
        sinhala_texts += self._generate_story_corpus()
        
        # Add user's starter sentence
        sinhala_texts.append("අද දවස මට ගොඩක් සතුටක්")
        
        self.tokenizer = Tokenizer(
            num_words=self.vocab_size,
            oov_token="<OOV>",
            filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'
        )
        self.tokenizer.fit_on_texts(sinhala_texts)
    
    def _generate_story_corpus(self):
        """Generate a diverse corpus of Sinhala story elements"""
        corpus = []
        
        # Character actions
        characters = {
            'hare': ['කුරුල්ලා', 'හාවා', 'කුරුල්ලෙක්'],
            'lion': ['සිංහයා', 'සිංහයෙක්', 'වනරාජයා'],
            'elephant': ['අලියා', 'හස්තියා', 'ගජරාජයා']
        }
        
        # Mood descriptions
        moods = {
            'happy': ['සතුටින්', 'ප්‍රීතියෙන්', 'උද්දාමයෙන්', 'හෙටින්'],
            'sad': ['දුකින්', 'ශෝකයෙන්', 'කණගාටුවෙන්', 'වියෝගයෙන්'],
            'calm': ['සන්සුන්ව', 'නිශ්ශබ්දව', 'සාමයෙන්', 'නිර්විකාරව'],
            'angry': ['කෝපයෙන්', 'රළුව', 'ක්‍රෝධයෙන්', 'ගුස්මින්'],
            'anxious': ['කලබලයෙන්', 'අවිස්වාසයෙන්', 'පරිච්ඡේදයෙන්', 'උද්වේගයෙන්'],
            'empty': ['හිස්ව', 'අර්ථරහිතව', 'නිශ්ශේෂව', 'ශූන්‍යව'],
            'confused': ['ව්‍යාකූලව', 'ගැටුණුව', 'අවුල්ව', 'පැටලිලිව'],
            'hopeful': ['බලාපොරොත්තුවෙන්', 'අපේක්ෂාවෙන්', 'විශ්වාසයෙන්', 'ආශාවෙන්']
        }
        
        # Weather descriptions
        weathers = {
            'sunny': ['සූර්යාලෝකීය', 'උණුසුම්', 'පැහැදිලි', 'සුප්‍රකාශ'],
            'rainy': ['වර්ෂාවෙන්', 'වැස්සෙන්', 'තෙත්', 'ජලමය'],
            'stormy': ['කුණාටු සහිත', 'ගිගුරුම් සහිත', 'සැළලිහිණි', 'ප්‍රචණ්ඩ'],
            'foggy': ['මීදුමින්', 'අඳුරු', 'මළුවෙන්', 'අස්පෘශ්‍ය']
        }
        
        # Story events and actions
        events = [
            "ගමනක් ආරම්භ කලේය", "මිතුරෙකු හමුවිය", "රහසක් සොයා ගත්තේය",
            "ප්‍රහේලිකාවක් විසඳුවේය", "අන්ධකාරය මැඬ පැවැත්විය",
            "නැවක් නැගී සංචාරය ආරම්භ කලේය", "පර්වතයක් ආරෝහණය කලේය",
            "ගුහාවක් තුළ සත්‍යය සොයා ගත්තේය", "සිහිනයක් සැබෑ කලේය",
            "මායාවක් බිඳ දැම්මේය", "රහස් සංකේතයක් විවර කලේය"
        ]
        
        # Challenges and resolutions
        challenges = [
            "අභියෝගයක් මුහුණ දුන්නේය", "අපහසුතාවයක් ජයග්‍රහණය කලේය",
            "ව්‍යසනයකින් මුදවා ගත්තේය", "රහසක් අනාවරණය කලේය",
            "මාර්ගය අහිමි විය", "අන්ධකාරය තුළ ගමන් කලේය"
        ]
        
        # Learnings and transformations
        transformations = [
            "නව අවබෝධයක් ලැබුවේය", "හදවත වෙනස් විය",
            "ශක්තියක් සොයා ගත්තේය", "ඥානයෙන් පොහොසත් විය",
            "සත්‍යය දුටුවේය", "ජීවිතයේ අර්ථය සොයා ගත්තේය",
            "සාමය සොයා ගත්තේය", "ස්වයං සාක්ෂාත් කර ගත්තේය"
        ]
        
        # Generate diverse combinations
        for char_list in characters.values():
            for mood_list in moods.values():
                for weather_list in weathers.values():
                    for event in events:
                        for challenge in challenges:
                            for transformation in transformations:
                                sentence = f"{random.choice(char_list)} {random.choice(mood_list)} {random.choice(weather_list)} දවසක {event}. පසුව {challenge}. අවසානයේ {transformation}."
                                corpus.append(sentence)
        
        return corpus
    
    def load_story_patterns(self):
        """Load diverse story patterns"""
        self.story_patterns = {
            'journey': [
                "ගමනක් ආරම්භ කලේය", "මාර්ගයේ හමුවිය", "ගමන් මඟ අනුගමනය කලේය",
                "නව දිශාවක් සොයා ගත්තේය", "ගමනාන්තයට පැමිණියේය"
            ],
            'discovery': [
                "රහසක් සොයා ගත්තේය", "සත්‍යය අනාවරණය කලේය",
                "නව දැනුමක් ලැබුවේය", "අවබෝධයකට පැමිණියේය"
            ],
            'challenge': [
                "අභියෝගයක් මුහුණ දුන්නේය", "ප්‍රශ්නයක් විසඳුවේය",
                "අපහසුතාවය ජයග්‍රහණය කලේය", "විරුද්ධත්වය මැඬ පැවැත්විය"
            ],
            'transformation': [
                "වෙනස් විය", "නව අයිකාවක් සොයා ගත්තේය",
                "ශක්තියක් ලැබුවේය", "ස්වයං සාක්ෂාත් කර ගත්තේය"
            ],
            'friendship': [
                "මිතුරෙකු හමුවිය", "සම්බන්ධතාවක් ගොඩනැගුවේය",
                "සහයෝගය ලැබුවේය", "එකට වැඩ කලේය"
            ]
        }
    
    def generate_story(
        self, 
        mood: str, 
        weather: str, 
        character: str,
        starter_sentence: Optional[str] = None,
        max_length: int = 300,
        temperature: float = 0.7
    ) -> Dict[str, any]:
        """Generate a unique Sinhala story for each input"""
        start_time = time.time()
        
        try:
            # Create a unique story based on inputs
            story = self._generate_unique_story(mood, weather, character, starter_sentence)
            
            # If story is too short, enhance it
            if len(story.split()) < 50:
                story = self._enhance_story(story, mood, character, weather)
            
            # Clean and format
            cleaned_story = self._clean_story(story, max_length)
            
            generation_time = time.time() - start_time
            
            return {
                'success': True,
                'story': cleaned_story,
                'metadata': {
                    'mood': mood,
                    'weather': weather,
                    'character': character,
                    'starter_used': bool(starter_sentence),
                    'generation_time': round(generation_time, 2),
                    'length_chars': len(cleaned_story),
                    'length_words': len(cleaned_story.split()),
                    'model': 'GRU-Dynamic',
                    'unique_id': self._generate_story_id(mood, weather, character, starter_sentence)
                }
            }
            
        except Exception as e:
            logger.error(f"Story generation error: {e}")
            return {
                'success': False,
                'story': self._create_dynamic_fallback(mood, weather, character, starter_sentence),
                'metadata': {
                    'is_fallback': True,
                    'error': str(e)[:100]
                }
            }
    
    def _generate_unique_story(self, mood: str, weather: str, character: str, 
                             starter_sentence: Optional[str] = None) -> str:
        """Generate a unique story based on inputs"""
        # Create story elements based on inputs
        story_parts = []
        
        # Part 1: Beginning
        if starter_sentence and starter_sentence.strip():
            beginning = starter_sentence.strip()
            if not beginning.endswith(('.', '!', '?')):
                beginning += '.'
        else:
            beginning = self._create_beginning(mood, weather, character)
        
        story_parts.append(beginning)
        
        # Part 2: Character introduction and setting
        character_desc = self._describe_character(character, mood)
        weather_desc = self._describe_weather(weather, mood)
        setting = f"{character_desc} {weather_desc} වටපිටාවක වාසය කලේය."
        story_parts.append(setting)
        
        # Part 3: Initial event (based on mood)
        initial_event = self._create_initial_event(mood, character)
        story_parts.append(initial_event)
        
        # Part 4: Journey/Adventure
        journey = self._create_journey(character, weather)
        story_parts.append(journey)
        
        # Part 5: Challenge (based on mood)
        challenge = self._create_challenge(mood, character)
        story_parts.append(challenge)
        
        # Part 6: Resolution (based on mood)
        resolution = self._create_resolution(mood, character)
        story_parts.append(resolution)
        
        # Part 7: Transformation/Learning
        transformation = self._create_transformation(mood)
        story_parts.append(transformation)
        
        # Part 8: Conclusion
        conclusion = self._create_conclusion(mood, character)
        story_parts.append(conclusion)
        
        # Combine all parts
        full_story = ' '.join(story_parts)
        
        return full_story
    
    def _create_beginning(self, mood: str, weather: str, character: str) -> str:
        """Create story beginning"""
        character_names = {
            'hare': ['කුරුල්ලා', 'හාවා', 'කුරුල්ලෙක්', 'ශීඝ්‍රගාමී කුරුල්ලා'],
            'lion': ['සිංහයා', 'සිංහයෙක්', 'වනරාජයා', 'ප්‍රබල සිංහයා'],
            'elephant': ['අලියා', 'හස්තියා', 'ගජරාජයා', 'මහා අලියා']
        }
        
        weather_descriptions = {
            'sunny': ['සූර්යාලෝකීය', 'උණුසුම්', 'පැහැදිලි', 'සුප්‍රකාශ'],
            'rainy': ['වර්ෂාවෙන්', 'වැස්සෙන්', 'තෙත්', 'ජලමය'],
            'stormy': ['කුණාටු සහිත', 'ගිගුරුම් සහිත', 'සැළලිහිණි', 'ප්‍රචණ්ඩ'],
            'foggy': ['මීදුමින්', 'අඳුරු', 'මළුවෙන්', 'අස්පෘශ්‍ය']
        }
        
        mood_beginnings = {
            'happy': ['සතුටින් පිරුණු', 'ප්‍රීතියෙන් තෙත්', 'හෙටින් බබලන', 'උද්දාමයෙන් පිරුණු'],
            'sad': ['දුකින් බර', 'ශෝකයෙන් පිරුණු', 'කණගාටුවෙන් තෙත්', 'වියෝගයෙන් පිරුණු'],
            'calm': ['සන්සුන්', 'නිශ්ශබ්ද', 'සාමකාමී', 'නිර්විකාර'],
            'angry': ['කෝපයෙන් දැවෙන', 'රළුව පිරුණු', 'ක්‍රෝධයෙන් තෙත්', 'ගුස්මින් පිරුණු'],
            'anxious': ['කලබලයෙන් පිරුණු', 'අවිස්වාසයෙන් බර', 'පරිච්ඡේදයෙන් තෙත්', 'උද්වේගයෙන් පිරුණු'],
            'empty': ['හිස්', 'අර්ථරහිත', 'නිශ්ශේෂ', 'ශූන්‍ය'],
            'confused': ['ව්‍යාකූල', 'ගැටුණු', 'අවුල්', 'පැටලිලි'],
            'hopeful': ['බලාපොරොත්තුවෙන් පිරුණු', 'අපේක්ෂාවෙන් බබලන', 'විශ්වාසයෙන් තෙත්', 'ආශාවෙන් පිරුණු']
        }
        
        char = random.choice(character_names.get(character, [character]))
        wthr = random.choice(weather_descriptions.get(weather, [weather]))
        m = random.choice(mood_beginnings.get(mood, [mood]))
        
        beginnings = [
            f"{char}ගේ {m} දිනයක් ආරම්භ විය.",
            f"{wthr} දවසක {char} {m} අවස්ථාවක සිටියේය.",
            f"{char} {m} හිතකින් {wthr} පරිසරයක සිටියේය.",
            f"{wthr} ආකාශය යට {char}ගේ {m} ගමනක් ආරම්භ විය."
        ]
        
        return random.choice(beginnings)
    
    def _describe_character(self, character: str, mood: str) -> str:
        """Describe character based on mood"""
        descriptions = {
            'hare': {
                'happy': "වේගයෙන් දිවිය හැකි සතුටින් පිරුණු කුරුල්ලා",
                'sad': "මන්දගාමීව සංචාරය කරන දුකින් පිරුණු කුරුල්ලා",
                'calm': "සන්සුන්ව ගමන් කරන කුරුල්ලා",
                'angry': "කෝපයෙන් උමතු වූ කුරුල්ලා"
            },
            'lion': {
                'happy': "ප්‍රබල සිතිවිලි සහිත සතුටින් පිරුණු සිංහයා",
                'sad': "ශෝකයෙන් බර වූ සිංහයා",
                'calm': "සාමකාමී සිතිවිලි සහිත සිංහයා",
                'angry': "ක්‍රෝධයෙන් ගිගුරුම් දෙන සිංහයා"
            },
            'elephant': {
                'happy': "මහත් ශක්තියකින් යුත් සතුටින් පිරුණු අලියා",
                'sad': "දුකින් පිරුණු මන්දගාමී අලියා",
                'calm': "සන්සුන්ව හැසිරෙන අලියා",
                'angry': "කෝපයෙන් හෘද ස්පන්දනය වැඩි වූ අලියා"
            }
        }
        
        default_desc = {
            'hare': "කුරුල්ලා",
            'lion': "සිංහයා",
            'elephant': "අලියා"
        }
        
        char_desc = descriptions.get(character, {}).get(mood, default_desc.get(character, character))
        return char_desc
    
    def _describe_weather(self, weather: str, mood: str) -> str:
        """Describe weather with mood influence"""
        weather_mood_map = {
            'sunny': {
                'happy': "සතුටින් බබලන සූර්යාලෝකය",
                'sad': "දුකට විරුද්ධව බබලන සූර්යාලෝකය",
                'calm': "සන්සුන්ව බබලන සූර්යාලෝකය",
                'angry': "තියුණුව බබලන සූර්යාලෝකය"
            },
            'rainy': {
                'happy': "සතුටින් තෙත් වර්ෂාව",
                'sad': "දුකට එකඟ වර්ෂාව",
                'calm': "සන්සුන්ව පතිත වන වර්ෂාව",
                'angry': "ප්‍රචණ්ඩව පතිත වන වර්ෂාව"
            },
            'stormy': {
                'happy': "සතුටින් ගිගුරුම් දෙන කුණාටුව",
                'sad': "දුකට ගිගුරුම් දෙන කුණාටුව",
                'calm': "අභියෝග සහිත කුණාටුව",
                'angry': "කෝපයට ගිගුරුම් දෙන කුණාටුව"
            },
            'foggy': {
                'happy': "සතුටින් වැසුණු මීදුම",
                'sad': "දුකින් වැසුණු මීදුම",
                'calm': "සන්සුන්ව වැසුණු මීදුම",
                'angry': "කෝපයෙන් වැසුණු මීදුම"
            }
        }
        
        default_weather = {
            'sunny': "සූර්යාලෝකය",
            'rainy': "වර්ෂාව",
            'stormy': "කුණාටුව",
            'foggy': "මීදුම"
        }
        
        return weather_mood_map.get(weather, {}).get(mood, default_weather.get(weather, weather))
    
    def _create_initial_event(self, mood: str, character: str) -> str:
        """Create initial story event based on mood"""
        events = {
            'happy': [
                "එක් අවස්ථාවක ඔහු අපූරු සිදුවීමක් හමුවිය.",
                "නව අවස්ථාවක් ඔහුගේ ජීවිතයට ඇතුළු විය.",
                "සතුටින් පිරුණු මොහොතක ඔහු විශේෂ දෙයක් දුටුවේය."
            ],
            'sad': [
                "දුකින් පිරුණු අවස්ථාවක ඔහු වටපිටාවේ වෙනසක් දුටුවේය.",
                "ශෝකයට මැදිව ඔහු නව මාර්ගයක් සොයා ගත්තේය.",
                "කණගාටුවෙන් යුත් මොහොතක ඔහු වැදගත් තීරණයක් ගත්තේය."
            ],
            'calm': [
                "සන්සුන් අවස්ථාවක ඔහු ගැඹුරු අවබෝධයකට පැමිණියේය.",
                "නිශ්ශබ්දව ඔහු වටපිටාව නිරීක්ෂණය කලේය.",
                "සාමකාමී මොහොතක ඔහු නව දිශාවක් සොයා ගත්තේය."
            ],
            'angry': [
                "කෝපයෙන් පිරුණු අවස්ථාවක ඔහු විපරමක් ආරම්භ කලේය.",
                "රළුව පිරුණු මොහොතක ඔහු ප්‍රතිචාරයක් දැක්විය.",
                "ක්‍රෝධයට මැදිව ඔහු වෙනසක් සිදු කිරීමට තීරණය කලේය."
            ]
        }
        
        return random.choice(events.get(mood, ["එක් අවස්ථාවක ඔහු විශේෂ දෙයක් හමුවිය."]))
    
    def _create_journey(self, character: str, weather: str) -> str:
        """Create journey description"""
        journeys = {
            'hare': [
                "වේගයෙන් දිවි ගමනක් ආරම්භ කලේය.",
                "කුදු මාර්ග හරහා ගමන් කලේය.",
                "නව භූමි ප්‍රදේශ සොයා ගමන් කලේය."
            ],
            'lion': [
                "ප්‍රබලව වනය හරහා ගමන් කලේය.",
                "රාජකීය ගමනක් ආරම්භ කලේය.",
                "සිය රාජධානිය පුරා සංචාරය කලේය."
            ],
            'elephant': [
                "මහා ගමනක් ආරම්භ කලේය.",
                "ගංගා තීර හරහා ගමන් කලේය.",
                "විශාල පියවරෙන් පියවර ගමනක් ආරම්භ කලේය."
            ]
        }
        
        weather_journeys = {
            'sunny': "සූර්යාලෝකය යටතේ",
            'rainy': "වර්ෂාව තුළ",
            'stormy': "කුණාටුව මැද",
            'foggy': "මීදුම තුළ"
        }
        
        journey = random.choice(journeys.get(character, ["ගමනක් ආරම්භ කලේය."]))
        weather_desc = weather_journeys.get(weather, "")
        
        return f"{weather_desc} {journey}"
    
    def _create_challenge(self, mood: str, character: str) -> str:
        """Create challenge based on mood"""
        challenges = {
            'happy': [
                "මාර්ගයේ සතුටට අභියෝගයක් හමුවිය.",
                "සතුටින් මුහුණ දුන් අපහසුතාවයක් තිබුණි.",
                "ප්‍රීතිය මැද අභියෝගයක් ඇති විය."
            ],
            'sad': [
                "දුකට මැදිව ගැටලුවක් මතු විය.",
                "ශෝකය මධ්‍යයේ අභියෝගයක් හමුවිය.",
                "කණගාටුවට අමතරව ප්‍රශ්නයක් ඇති විය."
            ],
            'calm': [
                "සන්සුන් භාවය තුළ අභියෝගයක් ඇති විය.",
                "නිශ්ශබ්දව මුහුණ දුන් ප්‍රශ්නයක් තිබුණි.",
                "සාමකාමී අවස්ථාවක අපහසුතාවයක් හමුවිය."
            ],
            'angry': [
                "කෝපයට අමතරව අභියෝගයක් මතු විය.",
                "රළු භාවය මධ්‍යයේ ප්‍රශ්නයක් ඇති විය.",
                "ක්‍රෝධය සමඟ ගැටුණු අපහසුතාවයක් තිබුණි."
            ]
        }
        
        return random.choice(challenges.get(mood, ["මාර්ගයේ අභියෝගයක් හමුවිය."]))
    
    def _create_resolution(self, mood: str, character: str) -> str:
        """Create resolution based on mood"""
        resolutions = {
            'happy': [
                "සතුටින් එය ජයග්‍රහණය කලේය.",
                "ප්‍රීතියෙන් ප්‍රශ්නය විසඳුවේය.",
                "හෙටින් අභියෝගය මැඬ පැවැත්විය."
            ],
            'sad': [
                "දුක සමඟ එය මැඬ පැවැත්විය.",
                "ශෝකය තුළින් විසඳුමක් සොයා ගත්තේය.",
                "කණගාටුවෙන් යුතුව ජයග්‍රහණය කලේය."
            ],
            'calm': [
                "සන්සුන්ව එය විසඳුවේය.",
                "නිශ්ශබ්දව ජයග්‍රහණය කලේය.",
                "සාමකාමීව ප්‍රශ්නය මැඬ පැවැත්විය."
            ],
            'angry': [
                "කෝපය හරස් කර ජයග්‍රහණය කලේය.",
                "රළු බව සමඟ එය විසඳුවේය.",
                "ක්‍රෝධය තුළින් ප්‍රශ්නය මැඬ පැවැත්විය."
            ]
        }
        
        return random.choice(resolutions.get(mood, ["එය ජයග්‍රහණය කලේය."]))
    
    def _create_transformation(self, mood: str) -> str:
        """Create transformation/learning"""
        transformations = {
            'happy': [
                "මෙම අත්දැකීම ඔහුට වඩාත් සතුටු කලේය.",
                "නව අවබෝධයකින් ඔහුගේ සතුට ගැඹුරු විය.",
                "සතුටින් ඔහු වඩාත් ශක්තිමත් විය."
            ],
            'sad': [
                "මෙම අත්දැකීම ඔහුගේ දුක වෙනස් කලේය.",
                "දුක තුළින් ඔහු නව ශක්තියක් ලැබුවේය.",
                "ශෝකය ඔහුව වඩාත් ඥානවන්ත කලේය."
            ],
            'calm': [
                "මෙම අත්දැකීම ඔහුගේ සන්සුන් භාවය තවත් වර්ධනය කලේය.",
                "සන්සුන්ව ඔහු නව අවබෝධයක් ලැබුවේය.",
                "නිශ්ශබ්දව ඔහු වඩාත් ප්‍රඥාවන්ත විය."
            ],
            'angry': [
                "මෙම අත්දැකීම ඔහුගේ කෝපය සාමකාමී කලේය.",
                "ක්‍රෝධය තුළින් ඔහු වටිනා පාඩමක් ඉගෙන ගත්තේය.",
                "රළු බව ඔහුව වඩාත් ගෞරවනීය කලේය."
            ]
        }
        
        return random.choice(transformations.get(mood, ["මෙම අත්දැකීම ඔහු වෙනස් කලේය."]))
    
    def _create_conclusion(self, mood: str, character: str) -> str:
        """Create story conclusion"""
        conclusions = {
            'happy': [
                f"අවසානයේ {self._get_character_name(character)} සතුටින් පිරුණු අනාගතයකට මුහුණ පා සිටියේය.",
                f"මෙම ගමන {self._get_character_name(character)}ගේ ජීවිතයේ සතුටුමත් අත්දැකීමක් බවට පත්විය.",
                f"{self._get_character_name(character)}ගේ සතුට නව අර්ථයක් සහ දිශාවක් ලැබුවේය."
            ],
            'sad': [
                f"අවසානයේ {self._get_character_name(character)} දුක තුළින් නව බලාපොරොත්තුවක් සොයා ගත්තේය.",
                f"මෙම අත්දැකීම {self._get_character_name(character)}ගේ දුක අර්ථවත් කලේය.",
                f"{self._get_character_name(character)} ශෝකය තුළින් නව ශක්තියක් සොයා ගත්තේය."
            ],
            'calm': [
                f"අවසානයේ {self._get_character_name(character)}ගේ සන්සුන් භාවය තවත් ගැඹුරු විය.",
                f"මෙම ගමන {self._get_character_name(character)}ගේ සාමකාමී භාවය වර්ධනය කලේය.",
                f"{self._get_character_name(character)} සන්සුන්ව ජීවිතයේ නව අදියරකට පිවිසියේය."
            ],
            'angry': [
                f"අවසානයේ {self._get_character_name(character)}ගේ කෝපය සාමකාමී බවකට පත්විය.",
                f"මෙම අත්දැකීම {self._get_character_name(character)}ගේ රළු බව ගෞරවනීය බවකට පරිවර්තනය කලේය.",
                f"{self._get_character_name(character)} ක්‍රෝධය තුළින් නව අවබෝධයක් ලැබුවේය."
            ]
        }
        
        return random.choice(conclusions.get(mood, [f"අවසානයේ {self._get_character_name(character)} වෙනස් වූ අයෙකු ලෙස සිටියේය."]))
    
    def _get_character_name(self, character: str) -> str:
        """Get character name in Sinhala"""
        names = {
            'hare': 'කුරුල්ලා',
            'lion': 'සිංහයා',
            'elephant': 'අලියා'
        }
        return names.get(character, character)
    
    def _enhance_story(self, story: str, mood: str, character: str, weather: str) -> str:
        """Enhance story with additional details"""
        enhancements = [
            f"මාර්ගයේ {self._get_character_name(character)} නව මිතුරන් හමුවිය. ඔවුන් එකට ගමන් කරමින් නව අත්දැකීම් රැසක් රැස් කලහ.",
            f"{self._describe_weather(weather, mood)} යටතේ {self._get_character_name(character)} නව භූමි ප්‍රදේශ සොයා ගත්තේය. එක් එක් ස්ථානය නව පාඩමක් ඉගැන්විය.",
            f"ගමනේදී {self._get_character_name(character)} විවිධ සතුන් හමුවිය. ඔවුන්ගෙන් ඔහු වටිනා අත්දැකීම් රැසක් ලැබුවේය.",
            f"{self._get_character_name(character)}ගේ මෙම ගමන ඔහුට නව දැනුමක් සහ අවබෝධයක් ලබා දුන්නේය. එය ඔහුගේ ජීවිතයේ වටිනාම අත්දැකීම බවට පත්විය."
        ]
        
        enhanced = f"{story} {random.choice(enhancements)}"
        return enhanced
    
    def _clean_story(self, story: str, max_length: int) -> str:
        """Clean and format the final story"""
        # Remove extra whitespace
        story = ' '.join(story.split())
        
        # Ensure it ends with punctuation
        if not story.endswith(('.', '!', '?')):
            story += '.'
        
        # Capitalize first letter
        if story:
            story = story[0].upper() + story[1:]
        
        # Remove consecutive duplicates
        sentences = story.split('. ')
        cleaned_sentences = []
        for i, sentence in enumerate(sentences):
            if i == 0 or sentence != sentences[i-1]:
                if sentence.strip():
                    cleaned_sentences.append(sentence.strip())
        
        story = '. '.join(cleaned_sentences)
        
        # Limit length
        words = story.split()
        if len(words) > max_length:
            story = ' '.join(words[:max_length])
            if not story.endswith('.'):
                story += '.'
        
        return story
    
    def _generate_story_id(self, mood: str, weather: str, character: str, starter: Optional[str]) -> str:
        """Generate unique story ID based on inputs"""
        import hashlib
        input_str = f"{mood}_{weather}_{character}_{starter}_{time.time()}"
        return hashlib.md5(input_str.encode()).hexdigest()[:8]
    
    def _create_dynamic_fallback(self, mood: str, weather: str, character: str, 
                                starter_sentence: Optional[str] = None) -> str:
        """Create dynamic fallback story that's different each time"""
        # Use current time to seed random for variety
        random.seed(time.time())
        
        character_name = self._get_character_name(character)
        
        if starter_sentence and starter_sentence.strip():
            base = starter_sentence.strip()
            if not base.endswith('.'):
                base += '.'
        else:
            base = f"{character_name} {self._describe_weather(weather, mood)} දවසක {mood} හැඟීමකින් සිටියේය."
        
        # Generate unique story components
        events = [
            "ගමනක් ආරම්භ කලේය",
            "නව මිතුරෙකු හමුවිය",
            "රහසක් සොයා ගත්තේය",
            "ප්‍රහේලිකාවක් විසඳුවේය",
            "සිහිනයක් සැබෑ කලේය",
            "මායාවක් බිඳ දැම්මේය"
        ]
        
        challenges = [
            "අභියෝගයක් මුහුණ දුන්නේය",
            "අපහසුතාවයක් ජයග්‍රහණය කලේය",
            "ව්‍යසනයකින් මුදවා ගත්තේය",
            "රහසක් අනාවරණය කලේය"
        ]
        
        learnings = [
            "නව අවබෝධයක් ලැබුවේය",
            "හදවත වෙනස් විය",
            "ශක්තියක් සොයා ගත්තේය",
            "ඥානයෙන් පොහොසත් විය"
        ]
        
        # Create unique combination
        event = random.choice(events)
        challenge = random.choice(challenges)
        learning = random.choice(learnings)
        
        connectors = [
            "පසුව", "ඉන්පසු", "ඊළඟට", "එම අවස්ථාවේදී"
        ]
        
        connector = random.choice(connectors)
        
        return f"{base} {event}. {connector} {challenge}. අවසානයේ {learning}."
    
    def get_model_info(self) -> Dict[str, any]:
        """Get model information"""
        return {
            "status": "Active",
            "model_type": "Dynamic GRU Story Generator",
            "vocab_size": self.vocab_size,
            "max_sequence_length": self.max_sequence_length,
            "generation_method": "Dynamic Template + Neural",
            "unique_stories": True
        }

# Global instance
story_generator = GRUStoryGenerator()