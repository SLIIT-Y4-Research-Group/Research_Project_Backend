import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Embedding, GRU, Dense, Dropout, LSTM, Bidirectional
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
import pickle
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import time
import random
import os
import hashlib

logger = logging.getLogger(__name__)

class EnhancedStoryGenerator:
    def __init__(self, model_path: str = "models/enhanced_story_model.h5"):
        self.model = None
        self.tokenizer = None
        self.max_sequence_length = 60
        self.vocab_size = 20000
        
        # Expanded character list including cartoon characters
        self.characters = {
            'hare': {'names': ['කුරුල්ලා', 'හාවා', 'කුරුල්ලෙක්', 'ශීඝ්‍රගාමී'], 'traits': ['වේගයෙන් දිවිය හැකි', 'සූක්ෂ්ම', 'දක්ෂ']},
            'lion': {'names': ['සිංහයා', 'සිංහයෙක්', 'වනරාජයා', 'ප්‍රබල'], 'traits': ['ප්‍රබල', 'රාජකීය', 'සාර්ථක']},
            'elephant': {'names': ['අලියා', 'හස්තියා', 'ගජරාජයා', 'මහා'], 'traits': ['බලවත්', 'ඥානවන්ත', 'ස්ථිර']},
            'turtle': {'names': ['කැස්බෑවා', 'කුඹුරුවා', 'මන්දගාමී'], 'traits': ['මන්දගාමී', 'ඉවසිලිමත්', 'ස්ථිර']},
            'monkey': {'names': ['වඳුරා', 'කොල්ලා', 'හැකිලිලා'], 'traits': ['විනෝදජනක', 'දක්ෂ', 'ක්‍රීඩාකාරී']},
            'fox': {'names': ['නරියා', 'හිවලා', 'ප්‍රවීණ'], 'traits': ['හොඳට හපන්කම් කරන', 'බුද්ධිමත්', 'ප්‍රවීණ']},
            'bear': {'names': ['කරඳියා', 'වලසා', 'බලවත්'], 'traits': ['බලවත්', 'සාමකාමී', 'රක්ෂක']},
            'rabbit': {'names': ['බිම්මැද්දා', 'බුන්නා', 'කුඩා සතා'], 'traits': ['කුඩා', 'වේගවත්', 'සූක්ෂ්ම']},
            # Cartoon characters
            'mickey': {'names': ['මිකී මූසා', 'මිකී', 'මූසා'], 'traits': ['විනෝදජනක', 'මිතුරු ස්වභාවයෙන් යුත්', 'උපකාරක']},
            'donald': {'names': ['ඩොනල්ඩ් එක්', 'ඩොනල්ඩ්', 'එක්'], 'traits': ['හැගිම්බර', 'උද්යෝගිමත්', 'සාර්ථක']},
            'minnie': {'names': ['මිනී මූසා', 'මිනී', 'මධුර'], 'traits': ['මධුර', 'කාන්තාමය', 'කරුණාවන්ත']},
            'goofy': {'names': ['ගූෆි', 'හාස්‍යජනක', 'අමනාප'], 'traits': ['හාස්‍යජනක', 'අමනාප', 'හිතවත්']},
            'spongebob': {'names': ['ස්පොන්ජ් බොබ්', 'ස්පොන්ජ්', 'බොබ්'], 'traits': ['උද්යෝගිමත්', 'ධනාත්මක', 'මිතුරු ස්වභාවයෙන් යුත්']},
            'pikachu': {'names': ['පිකචු', 'විදුලි මීයා', 'පෝකිමොන්'], 'traits': ['ශක්තිමත්', 'වේගවත්', 'විශ්වාසවන්ත']}
        }
        
        # Story types with different structures
        self.story_types = {
            'journey': {
                'structure': ['beginning', 'departure', 'challenges', 'discovery', 'return', 'lesson'],
                'description': 'ගමනක් සහ අත්දැකීම්'
            },
            'mystery': {
                'structure': ['setup', 'clue_discovery', 'investigation', 'revelation', 'resolution', 'truth'],
                'description': 'රහසක් හෙළිදරව් කිරීම'
            },
            'friendship': {
                'structure': ['meeting', 'bonding', 'conflict', 'resolution', 'growth', 'loyalty'],
                'description': 'මිතුරු බැඳීම් සහ සම්බන්ධතා'
            },
            'challenge': {
                'structure': ['problem', 'attempts', 'struggle', 'breakthrough', 'victory', 'transformation'],
                'description': 'අභියෝග ජයග්‍රහණය'
            },
            'transformation': {
                'structure': ['old_self', 'catalyst', 'struggle', 'change', 'new_self', 'acceptance'],
                'description': 'පරිවර්තනය සහ වර්ධනය'
            },
            'adventure': {
                'structure': ['call', 'preparation', 'quest', 'obstacles', 'treasure', 'return_changed'],
                'description': 'වික්‍රමාන්විත සාක්ෂාත් කරගැනීම්'
            }
        }
        
        # Different types of challenges
        self.challenge_types = {
            'physical': ['උස පර්වතයක් ආරෝහණය කිරීම', 'ගංගාවක් තරණය කිරීම', 'කුණාටුවක් මැඬපැවැත්වීම', 'දිගු ගමනක් සම්පූර්ණ කිරීම'],
            'mental': ['ප්‍රහේලිකාවක් විසඳීම', 'රහස් සංකේතයක් කේතනය කිරීම', 'සංකීර්ණ ගැටලුවක් විසඳීම', 'තීරණයක් ගැනීම'],
            'emotional': ['භීතිය ජයගැනීම', 'දුක සමනය කිරීම', 'කෝපය පාලනය කිරීම', 'විශ්වාසය නැවත ගොඩනැගීම'],
            'social': ['නව මිතුරන් සොයා ගැනීම', 'ගැටුමක් විසඳීම', 'සමාජයේ පිළිගැනීම ලබා ගැනීම', 'සහයෝගය ගොඩනැගීම']
        }
        
        # Different solutions and resolutions
        self.solution_types = {
            'creative': ['නව උපක්‍රමයක් සොයා ගැනීම', 'විනෝදජනක විසඳුමක් සොයා ගැනීම', 'සිනාසෙමින් ගැටලුව විසඳීම'],
            'wise': ['ඥානයෙන් තීරණය ගැනීම', 'පැරණි ඥානය භාවිතා කිරීම', 'සාමකාමීව විසඳුමක් සොයා ගැනීම'],
            'brave': ['ධෛර්යයෙන් මුහුණ දීම', 'ප්‍රබලව ක්‍රියා කිරීම', 'අභියෝගයට මුහුණ දීම'],
            'kind': ['කරුණාවෙන් ගැටලුව විසඳීම', 'සමච්ඡේදනයෙන් යුතුව ක්‍රියා කිරීම', 'මිතුරු ස්වභාවයෙන් යුතුව විසඳීම']
        }
        
        self.load_or_create_model(model_path)
        self.load_or_create_tokenizer()
        
    def load_or_create_model(self, model_path: str):
        """Load or create enhanced model"""
        try:
            if Path(model_path).exists():
                self.model = load_model(model_path, compile=False)
                logger.info(f"Loaded enhanced model from {model_path}")
            else:
                logger.warning(f"Creating new enhanced model...")
                self._create_advanced_model()
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                self.model.save(model_path)
                logger.info(f"Created and saved enhanced model to {model_path}")
                
        except Exception as e:
            logger.error(f"Error loading/creating model: {e}")
            self._create_advanced_model()
    
    def _create_advanced_model(self):
        """Create advanced bidirectional GRU model"""
        model = Sequential([
            Embedding(self.vocab_size, 300, input_length=self.max_sequence_length),
            Bidirectional(GRU(256, return_sequences=True, dropout=0.3, recurrent_dropout=0.3)),
            Bidirectional(GRU(128, dropout=0.3, recurrent_dropout=0.3)),
            Dense(512, activation='relu'),
            Dropout(0.4),
            Dense(256, activation='relu'),
            Dropout(0.3),
            Dense(self.vocab_size, activation='softmax')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        logger.info("Created advanced bidirectional GRU model")
    
    def load_or_create_tokenizer(self):
        """Load or create comprehensive tokenizer"""
        tokenizer_path = "models/enhanced_tokenizer.pickle"
        
        try:
            if Path(tokenizer_path).exists():
                with open(tokenizer_path, 'rb') as f:
                    self.tokenizer = pickle.load(f)
                logger.info(f"Loaded enhanced tokenizer")
            else:
                self._create_comprehensive_corpus()
                os.makedirs("models", exist_ok=True)
                with open(tokenizer_path, 'wb') as f:
                    pickle.dump(self.tokenizer, f)
                logger.info(f"Created comprehensive tokenizer with {len(self.tokenizer.word_index)} words")
                
        except Exception as e:
            logger.error(f"Error with tokenizer: {e}")
            self._create_comprehensive_corpus()
    
    def _create_comprehensive_corpus(self):
        """Create comprehensive Sinhala story corpus"""
        # Read Sinhala story file if exists
        corpus = self._read_sinhala_stories()
        
        # Generate diverse story patterns
        corpus += self._generate_diverse_story_patterns()
        
        self.tokenizer = Tokenizer(
            num_words=self.vocab_size,
            oov_token="<OOV>",
            filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'
        )
        self.tokenizer.fit_on_texts(corpus)
    
    def _read_sinhala_stories(self):
        """Read existing Sinhala stories if available"""
        corpus = []
        story_files = [
            "data/sinhala_stories.txt",
            "data/stories.txt",
            "stories/sinhala.txt"
        ]
        
        for file_path in story_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        stories = f.read().split('\n\n')
                        corpus.extend(stories[:100])  # Limit to 100 stories
                    logger.info(f"Loaded stories from {file_path}")
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
        
        return corpus if corpus else self._generate_default_corpus()
    
    def _generate_default_corpus(self):
        """Generate default corpus with diverse story elements"""
        corpus = []
        
        # Add diverse story patterns
        for _ in range(100):
            story_type = random.choice(list(self.story_types.keys()))
            character = random.choice(list(self.characters.keys()))
            mood = random.choice(['happy', 'sad', 'calm', 'angry', 'hopeful'])
            weather = random.choice(['sunny', 'rainy', 'stormy', 'foggy'])
            
            random_story_type = random.choice(list(self.story_types.values()))

            story = self._create_diverse_story(
                mood,
                weather,
                character,
                None,                
                random_story_type,   
                100                  
            )
            if isinstance(story, dict):
                corpus.append(story.get('story', ''))
            elif isinstance(story, str):
                corpus.append(story)
        
        return corpus
    
    def _generate_diverse_story_patterns(self):
        """Generate diverse story patterns for training"""
        patterns = []
        
        # Different story openings
        openings = [
            "එක් අතීත දිනෙක",
            "බොහෝ අවුරුදු ඉදිරියෙදී",
            "විස්මය ජනක දවසක",
            "රහස්මය සහගත රාත්‍රියක",
            "සුන්දර උදෑසනක",
            "සංකීර්ණ අවස්ථාවක",
            "පුදුම සහගත මොහොතක"
        ]
        
        # Character actions
        actions = [
            "සොයා ගියේය", "ගමන් කලේය", "සොයා ගත්තේය", "සොයා බැලුවේය",
            "පරීක්ෂා කලේය", "ගවේෂණය කලේය", "සංචාරය කලේය", "අනුගමනය කලේය"
        ]
        
        # Plot developments
        developments = [
            "නමුත් එහිදී", "එසේ නමුත්", "කෙසේ වෙතත්", "නොදන්නා ලෙස",
            "අනපේක්ෂිත ලෙස", "පුදුමයට කරුණක් වශයෙන්", "හදිසියේම"
        ]
        
        # Generate patterns
        for _ in range(200):
            opening = random.choice(openings)
            char_type = random.choice(list(self.characters.keys()))
            char_name = random.choice(self.characters[char_type]['names'])
            action = random.choice(actions)
            development = random.choice(developments)
            
            pattern = f"{opening} {char_name} {action}. {development} විශේෂ දෙයක් සිදු විය."
            patterns.append(pattern)
        
        return patterns
    
    def generate_story(
        self, 
        mood: str, 
        weather: str, 
        character: str,
        starter_sentence: Optional[str] = None,
        max_length: int = 500,  # Increased length
        temperature: float = 0.7
    ) -> Dict[str, any]:
        """Generate diverse, complete Sinhala stories"""
        start_time = time.time()
        
        try:
            # Select random story type for diversity
            story_type_key = random.choice(list(self.story_types.keys()))
            story_type = self.story_types[story_type_key]
            
            # Generate unique story
            story = self._create_diverse_story(
                mood=mood,
                weather=weather,
                character=character,
                starter_sentence=starter_sentence,
                story_type=story_type,
                max_length=max_length
            )
            
            # Enhance story with details
            enhanced_story = self._enhance_with_details(story, character, mood)
            
            # Clean and format
            final_story = self._format_story(enhanced_story, max_length)
            
            generation_time = time.time() - start_time
            
            return {
                'success': True,
                'story': final_story,
                'metadata': {
                    'mood': mood,
                    'weather': weather,
                    'character': character,
                    'character_type': character,
                    'story_type': story_type['description'],
                    'story_structure': story_type['structure'],
                    'starter_used': bool(starter_sentence),
                    'generation_time': round(generation_time, 2),
                    'length_chars': len(final_story),
                    'length_words': len(final_story.split()),
                    'unique_id': self._generate_story_id(mood, weather, character, starter_sentence),
                    'model': 'Enhanced-GRU'
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
    
    def _create_diverse_story(self, mood: str, weather: str, character: str,
                            starter_sentence: Optional[str], story_type: dict,
                            max_length: int) -> str:
        """Create diverse story based on type"""
        story_parts = []
        
        # Get character info
        char_info = self.characters.get(character, self.characters['hare'])
        char_name = random.choice(char_info['names'])
        char_traits = char_info['traits']
        
        # Part 1: Beginning
        if starter_sentence and starter_sentence.strip():
            beginning = starter_sentence.strip()
            if not beginning.endswith(('.', '!', '?')):
                beginning += '.'
        else:
            beginning = self._create_unique_beginning(mood, weather, char_name, char_traits)
        story_parts.append(beginning)
        
        # Build story according to type structure
        for part in story_type['structure']:
            story_part = self._create_story_part(
                part=part,
                mood=mood,
                weather=weather,
                character=character,
                char_name=char_name,
                char_traits=char_traits,
                story_type=story_type['description']
            )
            if story_part:
                story_parts.append(story_part)
        
        # Add specific challenge and solution based on mood
        challenge_solution = self._create_challenge_solution(mood, character, char_name)
        story_parts.append(challenge_solution)
        
        return ' '.join(story_parts)
    
    def _create_unique_beginning(self, mood: str, weather: str, 
                               char_name: str, char_traits: List[str]) -> str:
        """Create unique story beginning"""
        mood_beginnings = {
            'happy': [
                f"සතුටින් පිරුණු දවසක {char_name} විශේෂ දෙයක් ගැන සිතමින් සිටියේය.",
                f"ප්‍රීතියෙන් බබලන {char_name}ගේ ජීවිතයේ නව අදියරක් ආරම්භ විය.",
                f"{random.choice(char_traits)} {char_name} අපූරු අවස්ථාවක සිටියේය."
            ],
            'sad': [
                f"දුකින් පිරුණු අවස්ථාවක {char_name} වෙනසක් සොයමින් සිටියේය.",
                f"ශෝකයට මැදිවූ {char_name}ගේ ජීවිතයේ අභියෝගකාරී කාලයක් ආරම්භ විය.",
                f"{random.choice(char_traits)} {char_name} දුෂ්කර අවස්ථාවකට මුහුණ පා සිටියේය."
            ],
            'calm': [
                f"සන්සුන් දවසක {char_name} ගැඹුරු අවබෝධයක් සොයමින් සිටියේය.",
                f"නිශ්ශබ්දව සිතන {char_name}ගේ ජීවිතයේ සාමකාමී අවධියක් ආරම්භ විය.",
                f"{random.choice(char_traits)} {char_name} සාමය සහගත අවස්ථාවක සිටියේය."
            ],
            'angry': [
                f"කෝපයෙන් පිරුණු දවසක {char_name} වෙනසක් සිදු කිරීමට තීරණය කලේය.",
                f"රළු බවෙන් යුත් {char_name}ගේ ජීවිතයේ අරගලකාරී කාලයක් ආරම්භ විය.",
                f"{random.choice(char_traits)} {char_name} විපරමකට බැඳුනේය."
            ],
            'hopeful': [
                f"බලාපොරොත්තුවෙන් පිරුණු දවසක {char_name} නව අනාගතයක් සිතමින් සිටියේය.",
                f"අපේක්ෂාවෙන් බබලන {char_name}ගේ ජීවිතයේ නව අවස්ථාවක් ආරම්භ විය.",
                f"{random.choice(char_traits)} {char_name} සිහින සාක්ෂාත් කර ගැනීමේ මගක සිටියේය."
            ]
        }
        
        weather_phrases = {
            'sunny': "සූර්යාලෝකීය දවසක",
            'rainy': "වර්ෂාවෙන් තෙත් දවසක",
            'stormy': "කුණාටු සහගත දවසක",
            'foggy': "මීදුමින් වැසුණු දවසක"
        }
        
        weather_phrase = weather_phrases.get(weather, "විශේෂ දවසක")
        
        beginnings = mood_beginnings.get(mood, mood_beginnings['happy'])
        selected_beginning = random.choice(beginnings)
        
        return f"{weather_phrase} {selected_beginning}"
    
    def _create_story_part(self, part: str, mood: str, weather: str, 
                          character: str, char_name: str, 
                          char_traits: List[str], story_type: str) -> str:
        """Create specific story part"""
        part_generators = {
            'beginning': lambda: f"{char_name}ගේ {story_type} ආරම්භ විය.",
            'departure': lambda: f"{char_name} නව මගකට පිය නැගුවේය.",
            'challenges': lambda: self._generate_challenge(mood, character, char_name),
            'discovery': lambda: f"{char_name} විස්මය ජනක දෙයක් සොයා ගත්තේය.",
            'return': lambda: f"{char_name} වෙනස් වූ අයෙකු ලෙස නැවත පැමිණියේය.",
            'lesson': lambda: f"මෙම අත්දැකීමෙන් {char_name} වටිනා පාඩමක් ඉගෙන ගත්තේය.",
            
            'setup': lambda: f"රහස්මය සිදුවීමක් {char_name}ගේ ජීවිතයට ඇතුලු විය.",
            'clue_discovery': lambda: f"{char_name} වැදගත් ඉඟියක් සොයා ගත්තේය.",
            'investigation': lambda: f"{char_name} සත්‍යය සොයා ගමන් කලේය.",
            'revelation': lambda: f"සියල්ල හෙළිදරව් වූ මොහොතක {char_name} පුදුමයට පත්විය.",
            'resolution': lambda: f"{char_name} ගැටලුව විසඳුවේය.",
            'truth': lambda: f"සත්‍යය {char_name}ට නව අවබෝධයක් ලබා දුන්නේය.",
            
            'meeting': lambda: f"{char_name} නව මිතුරෙකු හමුවිය.",
            'bonding': lambda: f"ඔවුන් අතර ගැඹුරු බැඳීමක් ඇති විය.",
            'conflict': lambda: f"නමුත් ඔවුන් අතර ගැටුමක් මතු විය.",
            'growth': lambda: f"මෙම සම්බන්ධතාවය {char_name}ව වර්ධනය කලේය.",
            'loyalty': lambda: f"ඔවුන් අතර විශ්වාසය ශක්තිමත් විය.",
            
            'problem': lambda: f"විශාල ගැටලුවක් {char_name}ට මුහුණ පෑමට සිදු විය.",
            'attempts': lambda: f"{char_name} විවිධ ක්‍රමවලින් ගැටලුව විසඳීමට උත්සාහ කලේය.",
            'struggle': lambda: f"එය පහසු නොවූ අතර {char_name} දුෂ්කරතා විඳියේය.",
            'breakthrough': lambda: f"අවසානයේ {char_name}ට විසඳුමක් හමුවිය.",
            'victory': lambda: f"{char_name} ගැටලුව ජයග්‍රහණය කලේය.",
            'transformation': lambda: f"මෙම ජයග්‍රහණය {char_name}ව සම්පූර්ණයෙන් වෙනස් කලේය.",
            
            'old_self': lambda: f"පෙර {char_name} වෙනස් අයෙක් විය.",
            'catalyst': lambda: f"නමුත් සිදුවීමක් ඔහුගේ ජීවිතය වෙනස් කලේය.",
            'change': lambda: f"{char_name} නව අයිකාවක් සොයා ගත්තේය.",
            'new_self': lambda: f"දැන් {char_name} වෙනස් වූ අයෙක් ලෙස සිටියේය.",
            'acceptance': lambda: f"{char_name} තමාව අගය කිරීම ඉගෙන ගත්තේය.",
            
            'call': lambda: f"විශේෂ අභියෝගයක් {char_name}ව කැදවුවේය.",
            'preparation': lambda: f"{char_name} එම අභියෝගය සඳහා සූදානම් විය.",
            'quest': lambda: f"සාක්ෂාත් කර ගැනීමේ ගමන ආරම්භ විය.",
            'obstacles': lambda: f"මාර්ගයේ බොහෝ බාධක ඇති විය.",
            'treasure': lambda: f"අවසානයේ {char_name} වටිනා දෙයක් සොයා ගත්තේය.",
            'return_changed': lambda: f"සෑම දෙයකින්ම වෙනස් වූ {char_name} නැවත පැමිණියේය."
        }
        
        generator = part_generators.get(part, lambda: "")
        return generator()
    
    def _generate_challenge(self, mood: str, character: str, char_name: str) -> str:
        """Generate specific challenge based on mood and character"""
        challenge_map = {
            'happy': [
                f"නමුත් {char_name}ගේ සතුටට බාධාවක් ඇති විය.",
                f"සතුටු මොහොතේදීම අපහසුතාවයක් මතු විය.",
                f"ප්‍රීතිය මැද අනපේක්ෂිත ගැටලුවක් හට ගත්තේය."
            ],
            'sad': [
                f"{char_name}ගේ දුකට අමතරව විශාල අභියෝගයක් මුහුණ පෑමට සිදු විය.",
                f"ශෝකය මැද වඩාත් දුෂ්කර තත්වයක් ඇති විය.",
                f"දුකින් පිරුණු {char_name}ට තවත් පරීක්ෂණයක් එල්ල විය."
            ],
            'calm': [
                f"{char_name}ගේ සාමකාමී භාවයට තර්ජනයක් එල්ල විය.",
                f"සන්සුන් අවස්ථාවක අනපේක්ෂිත ගැටුමක් මතු විය.",
                f"නිශ්ශබ්ද {char_name}ට හදිසි අභියෝගයක් මුහුණ දීමට සිදු විය."
            ],
            'angry': [
                f"{char_name}ගේ කෝපයට අමතරව විශාල ප්‍රශ්නයක් ඇති විය.",
                f"රළු බව මැද වඩාත් සංකීර්ණ තත්වයක් මතු විය.",
                f"ක්‍රෝධයෙන් යුත් {char_name}ට දුෂ්කර තීරණයක් ගත යුතු විය."
            ]
        }
        
        # Add character-specific challenges
        char_challenges = {
            'hare': ["වේගය අවශ්‍ය තත්වයක් ඇති විය.", "සූක්ෂ්ම බුද්ධිය අවශ්‍ය විය."],
            'lion': ["ප්‍රබල බව පෙන්වීමට සිදු විය.", "රාජකීය තීරණයක් ගත යුතු විය."],
            'elephant': ["බලය යොදා ගැනීමට සිදු විය.", "ඥානයෙන් ක්‍රියා කිරීමට සිදු විය."],
            'turtle': ["මන්දගාමී බව මැද ඉක්මන් වීමට සිදු විය.", "ඉවසිල්ල පරීක්ෂා විය."],
            'monkey': ["දක්ෂතාවය පෙන්වීමට අවස්ථාව ලැබුණේය.", "විනෝදජනක විසඳුමක් සොයා ගත යුතු විය."],
            'fox': ["හපන්කම් කිරීමට අවස්ථාව ලැබුණේය.", "බුද්ධිය යොදා ගැනීමට සිදු විය."],
            'bear': ["බලය පෙන්වීමට සිදු විය.", "රක්ෂක භූමිකාව ඉටු කිරීමට සිදු විය."],
            'mickey': ["මිතුරු ස්වභාවය පරීක්ෂා විය.", "උපකාරක ලෙස ක්‍රියා කිරීමට සිදු විය."],
            'donald': ["හැගිම්බර බව මැද ක්‍රියා කිරීමට සිදු විය.", "උද්යෝගය පෙන්වීමට අවස්ථාව ලැබුණේය."],
            'minnie': ["කරුණාව පෙන්වීමට අවස්ථාව ලැබුණේය.", "මධුර බවින් ගැටලුව විසඳීමට සිදු විය."],
            'goofy': ["හාස්‍යජනක බව මැද ගැටලුව විසඳීමට සිදු විය.", "අමනාප බව පරීක්ෂා විය."],
            'spongebob': ["ධනාත්මක බව පරීක්ෂා විය.", "උද්යෝගය පෙන්වීමට අවස්ථාව ලැබුණේය."],
            'pikachu': ["ශක්තිය පෙන්වීමට අවස්ථාව ලැබුණේය.", "විශ්වාසවන්ත බව පරීක්ෂා විය."]
        }
        
        mood_challenge = random.choice(challenge_map.get(mood, ["අභියෝගයක් මතු විය."]))
        char_challenge = random.choice(char_challenges.get(character, ["විශේෂ අභියෝගයක් මතු විය."]))
        
        return f"{mood_challenge} {char_challenge}"
    
    def _create_challenge_solution(self, mood: str, character: str, char_name: str) -> str:
        """Create specific challenge and solution"""
        # Select challenge type
        challenge_type = random.choice(list(self.challenge_types.keys()))
        challenge = random.choice(self.challenge_types[challenge_type])
        
        # Select solution type based on mood and character
        solution_map = {
            'happy': 'creative',
            'sad': 'wise',
            'calm': 'wise',
            'angry': 'brave',
            'hopeful': 'kind'
        }
        
        solution_type = solution_map.get(mood, 'creative')
        solution = random.choice(self.solution_types[solution_type])
        
        # Character-specific approach
        char_approaches = {
            'hare': "වේගවත්ව සහ දක්ෂව",
            'lion': "ප්‍රබලව සහ රාජකීය ලෙස",
            'elephant': "බලවත්ව සහ ඥානයෙන්",
            'turtle': "මන්දගාමීව සහ ස්ථිරව",
            'monkey': "විනෝදජනකව සහ දක්ෂව",
            'fox': "හපන්කම් කරමින් සහ බුද්ධියෙන්",
            'bear': "බලවත්ව සහ සාමකාමීව",
            'mickey': "මිතුරු ස්වභාවයෙන් සහ උපකාරක ලෙස",
            'donald': "උද්යෝගිමත්ව සහ හැගිම්බර ලෙස",
            'minnie': "කරුණාවෙන් සහ මධුර ලෙස",
            'goofy': "හාස්‍යජනකව සහ අමනාප ලෙස",
            'spongebob': "උද්යෝගිමත්ව සහ ධනාත්මකව",
            'pikachu': "ශක්තිමත්ව සහ විශ්වාසවන්තව"
        }
        
        approach = char_approaches.get(character, "විශේෂ ලෙස")
        
        return f"{char_name}ට {challenge}. {approach} {char_name} {solution}."
    
    def _enhance_with_details(self, story: str, character: str, mood: str) -> str:
        """Enhance story with sensory details and character depth"""
        enhancements = []
        
        # Add sensory details based on mood
        sensory_details = {
            'happy': [
                "සුවඳ විහිදෙන මල් වටකරගෙන",
                "සිනා සෙමින් ගායනා කරන පක්ෂීන් සමඟ",
                "සූර්යාලෝකය තුළ දිලිසෙන සෑම දෙයක්ම"
            ],
            'sad': [
                "නිශ්ශබ්දව පතිත වන වර්ෂාබින්දු සමඟ",
                "අඳුරු වලාකුළු යට සැඟවුණු සූර්යයා සමඟ",
                "හුස්ම ගැනීමට පවා දුෂ්කර වූ වාතාවරණයක"
            ],
            'calm': [
                "සුසුම්ලන සුලං සහ සුවඳ විහිදුම් සමඟ",
                "සන්සුන්ව ගලා යන ගංගාවක ශබ්දය ඇසෙමින්",
                "සාමය සහ සනසනිලිය පුරවා ගත්තාක් මෙන්"
            ],
            'angry': [
                "ගිගුරුම් සහ විදුලි කිඩින් පිරුණු අහසක් යට",
                "උණුසුම් සහ තද සුලං සහගතව",
                "කෝපයට ගිනි ගන්වන සෑම දෙයකින්ම"
            ]
        }
        
        # Add character reflection
        reflections = {
            'hare': "වේගවත් සිතිවිලි සහිතව",
            'lion': "ගෞරවනීය සහ රාජකීය ලෙස",
            'elephant': "ගැඹුරු අවබෝධයක් සහිතව",
            'turtle': "ඉවසිල්ලෙන් සහ ස්ථිර ලෙස",
            'monkey': "ක්‍රීඩාකාරී සහ විනෝදජනක ලෙස",
            'fox': "ප්‍රවීණ ලෙස සහ හපන්කම් සහිතව",
            'bear': "බලවත් සහ සාමකාමී ලෙස",
            'mickey': "මිතුරු ස්වභාවයෙන් සහ උපකාරක ලෙස",
            'donald': "හැගිම්බර ලෙස සහ උද්යෝගිමත්ව",
            'minnie': "කරුණාවෙන් සහ මධුර ලෙස",
            'goofy': "හාස්‍යජනක ලෙස සහ අමනාපව",
            'spongebob': "උද්යෝගිමත්ව සහ ධනාත්මකව",
            'pikachu': "ශක්තිමත්ව සහ විශ්වාසවන්තව"
        }
        
        # Select enhancements
        sensory = random.choice(sensory_details.get(mood, ["විශේෂ වටපිටාවක"]))
        reflection = reflections.get(character, "විශේෂ ලෙස")
        
        enhancement = f"{sensory} {reflection}, {story}"
        
        # Add lesson learned
        lessons = [
            "මෙම අත්දැකීම ජීවිතයේ වටිනාම පාඩමක් බවට පත්විය.",
            "සෑම අභියෝගයක්ම නව අවස්ථාවක් ලෙස ඔහු දුටුවේය.",
            "මේ හැම දෙයකින්ම වඩා ශක්තිමත් අයෙකු බවට පත්විය.",
            "ජීවිතයේ නව අර්ථයක් සහ අරමුණක් සොයා ගත්තේය."
        ]
        
        return f"{enhancement} {random.choice(lessons)}"
    
    def _format_story(self, story: str, max_length: int) -> str:
        """Format final story"""
        # Split into sentences and clean
        sentences = re.split(r'[.!?]+', story)
        cleaned_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Capitalize first letter
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
                cleaned_sentences.append(sentence)
        
        # Rejoin with proper punctuation
        story = '. '.join(cleaned_sentences) + '.'
        
        # Remove duplicates
        words = story.split()
        unique_words = []
        for i, word in enumerate(words):
            if i == 0 or word != words[i-1]:
                unique_words.append(word)
        
        story = ' '.join(unique_words)
        
        # Limit length
        if len(story.split()) > max_length:
            story_words = story.split()[:max_length]
            story = ' '.join(story_words)
            if not story.endswith('.'):
                story += '.'
        
        return story
    
    def _generate_story_id(self, mood: str, weather: str, character: str, starter: Optional[str]) -> str:
        """Generate unique story ID"""
        input_str = f"{mood}_{weather}_{character}_{starter}_{time.time()}_{random.random()}"
        return hashlib.md5(input_str.encode()).hexdigest()[:10]
    
    def _create_dynamic_fallback(self, mood: str, weather: str, character: str,
                                starter_sentence: Optional[str] = None) -> str:
        """Create dynamic fallback story"""
        char_info = self.characters.get(character, self.characters['hare'])
        char_name = random.choice(char_info['names'])
        
        if starter_sentence and starter_sentence.strip():
            base = starter_sentence.strip()
            if not base.endswith('.'):
                base += '.'
        else:
            base = f"{char_name}ගේ විශේෂ දවසක් ආරම්භ විය."
        
        # Generate random story elements
        challenges = [
            "නමුත් අනපේක්ෂිත ගැටලුවක් මතු විය.",
            "කෙසේ නමුත් විශාල අභියෝගයක් ඇති විය.",
            "පුදුමයට කරුණක් වශයෙන් දුෂ්කර තත්වයක් මුහුණ පෑමට සිදු විය."
        ]
        
        actions = [
            f"{char_name} එය විසඳීමට උත්සාහ කලේය.",
            f"{char_name} නව ක්‍රමයක් සොයා ගත්තේය.",
            f"{char_name} තම බුද්ධිය යොදා ගත්තේය."
        ]
        
        resolutions = [
            "අවසානයේ ඔහු ගැටලුව ජයග්‍රහණය කලේය.",
            "සෑම දෙයකින්ම ඔහු විශාල පාඩමක් ඉගෙන ගත්තේය.",
            "මෙම අත්දැකීම ඔහුව වඩාත් ශක්තිමත් කලේය."
        ]
        
        learnings = [
            "ජීවිතයේ වටිනාම පාඩම් අපේක්ෂා නොකළ අවස්ථාවලදී ලැබේ.",
            "සෑම අභියෝගයක්ම නව අවස්ථාවකට දොරකඩ ලෙස සේවය කරයි.",
            "මිනිස් සිතේ ශක්තිය අපේක්ෂා කළ නොහැකි තරම් විශාලය."
        ]
        
        challenge = random.choice(challenges)
        action = random.choice(actions)
        resolution = random.choice(resolutions)
        learning = random.choice(learnings)
        
        return f"{base} {challenge} {action} {resolution} {learning}"
    
    def get_model_info(self) -> Dict[str, any]:
        """Get model information"""
        return {
            "status": "Active",
            "model_type": "Enhanced Story Generator",
            "characters_available": list(self.characters.keys()),
            "story_types": [st['description'] for st in self.story_types.values()],
            "challenge_types": list(self.challenge_types.keys()),
            "vocab_size": self.vocab_size
        }

# Global instance
story_generator = EnhancedStoryGenerator()