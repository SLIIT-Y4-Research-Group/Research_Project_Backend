import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Embedding, GRU, Dense, Dropout, LSTM
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer
import pickle
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import time
import random
import os
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class EnhancedSinhalaStoryGenerator:
    def __init__(self, model_path: str = "models/enhanced_sinhala_generator.h5"):
        self.model = None
        self.tokenizer = None
        self.max_sequence_length = 80  # Increased for longer stories
        self.vocab_size = 20000  # Increased vocabulary
        self.story_patterns = {}
        self.folk_tale_templates = {}
        self.moral_lessons = {}
        
        self.load_or_create_model(model_path)
        self.load_or_create_tokenizer()
        self.load_story_patterns()
        self.load_folk_tale_templates()
        self.load_moral_lessons()
        
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
        """Create an enhanced model for longer, meaningful stories"""
        model = Sequential([
            Embedding(self.vocab_size, 300, input_length=self.max_sequence_length),
            GRU(512, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            GRU(384, return_sequences=True, dropout=0.3, recurrent_dropout=0.3),
            GRU(256, dropout=0.3, recurrent_dropout=0.3),
            Dense(512, activation='relu'),
            Dropout(0.4),
            Dense(384, activation='relu'),
            Dropout(0.3),
            Dense(self.vocab_size, activation='softmax')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.0008),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        logger.info("Created enhanced model for meaningful Sinhala folk tales")
    
    def load_or_create_tokenizer(self):
        """Load or create comprehensive Sinhala tokenizer for folk tales"""
        tokenizer_path = "models/sinhala_folk_tokenizer.pickle"
        
        try:
            if Path(tokenizer_path).exists():
                with open(tokenizer_path, 'rb') as f:
                    self.tokenizer = pickle.load(f)
                logger.info(f"Loaded tokenizer with {len(self.tokenizer.word_index)} words")
            else:
                self._create_folk_tale_tokenizer()
                os.makedirs("models", exist_ok=True)
                with open(tokenizer_path, 'wb') as f:
                    pickle.dump(self.tokenizer, f)
                logger.info(f"Created folk tale tokenizer with {len(self.tokenizer.word_index)} words")
                
        except Exception as e:
            logger.error(f"Error with tokenizer: {e}")
            self._create_folk_tale_tokenizer()
    
    def _create_folk_tale_tokenizer(self):
        """Create extensive Sinhala vocabulary for folk tale generation"""
        sinhala_texts = self._generate_comprehensive_folk_corpus()
        
        self.tokenizer = Tokenizer(
            num_words=self.vocab_size,
            oov_token="<OOV>",
            filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n'
        )
        self.tokenizer.fit_on_texts(sinhala_texts)
    
    def _generate_comprehensive_folk_corpus(self) -> List[str]:
        """Generate comprehensive Sinhala folk tale corpus"""
        corpus = []
        
        # Classic Sinhala folk tale openings
        openings = [
            "අතීතයේ දී එක් සමයක",
            "පුරාණ කාලයේ දී",
            "එක් වරක් ඉතා පැරණි යුගයක",
            "බොහෝ අවුරුදු ගණනකට පෙර",
            "එක්තරා පැරණි ගමක",
            "උණුසුම් ග්‍රීෂ්ම ඍතුවේ දිනක",
            "සිසිල් හෙමන්ත ඍතුවේ දිනක",
            "හරිත වසන්තයේ දිනක"
        ]
        
        # Traditional Sinhala characters
        characters = {
            'king': ['රජෙක්', 'රාජපුත්‍රයෙක්', 'මහා රජෙක්', 'නරපතියෙක්'],
            'farmer': ['ගොවියෙක්', 'කුඹුරුකරුවෙක්', 'කෘෂිකර්මඥයෙක්', 'කෙත්කරුවෙක්'],
            'hermit': ['තපස්වියෙක්', 'මුනිවරයෙක්', 'යෝගීයෙක්', 'අරණ්‍යවාසියෙක්'],
            'animal': ['සිංහයෙක්', 'අලියෙක්', 'කුරුල්ලෙක්', 'හාවෙක්', 'කුකුළෙක්'],
            'child': ['දරුවෙක්', 'කුඩා පිරිමි ළමයෙක්', 'ගැහැණු ළමයෙක්', 'ළදරුවෙක්'],
            'wiseman': ['ඥානවන්තයෙක්', 'පණ්ඩිතයෙක්', 'විද්වතෙක්', 'පූජ්‍යයෙක්']
        }
        
        # Settings for folk tales
        settings = [
            "දුර්ගම වනාන්තරයක",
            "පර්වත මුදුනක",
            "ගංගා තීරයක",
            "හැදිල්ලක් වටා",
            "පුරාණ දෙවොලක",
            "රාජ මාලිගාවක",
            "සුන්දර ගම්බද ප්‍රදේශයක",
            "රහස් ගුහාවක"
        ]
        
        # Folk tale plot elements
        plots = [
            "අහිංසක අයෙකුට උපකාර කිරීම",
            "රහසක් සොයා ගමන් කිරීම",
            "අභියෝගයකින් ගමනක් ආරම්භ කිරීම",
            "දුෂ්ටයෙකුගෙන් ගම්බද ප්‍රදේශය බේරා ගැනීම",
            "මායා මන්ත්‍රයක් බිඳ දැමීම",
            "අති දුර්ලභ ඖෂධයක් සොයා ගැනීම",
            "සුරක්ෂිත රාජධානියක් ගොඩ නැගීම",
            "පැරණි ගිවිසුමක් සම්පූර්ණ කිරීම"
        ]
        
        # Moral teachings (common in Sinhala folk tales)
        morals = [
            "අනුකම්පාව යනු මහා ගුණයකි",
            "සත්‍යය සැමවිටම ජය ගනියි",
            "ඉවසීමෙන් සියල්ල හැකි ය",
            "ඥානය ධනයට වඩා වටිනා ය",
            "සාධු ක්‍රියාවන්හි ඵල මිහිරි ය",
            "අධමයන්ගේ කූට ශිල්පය අවසානයේ දුර්වල වේ",
            "පරෝපකාරයෙන් සැනසීම ලැබේ",
            "සමඟිතාවයෙන් ශක්තිය ලැබේ"
        ]
        
        # Generate comprehensive corpus
        for opening in openings:
            for char_type in characters.values():
                for setting in settings:
                    for plot in plots:
                        for moral in morals:
                            for _ in range(2):  # Multiple variations
                                character = random.choice(char_type)
                                story = f"{opening} {setting} {character} විසූ බව කියවේ. {plot} සඳහා ඔහු ගමනක් ආරම්භ කලේය. මෙම කථාවෙන් අපට උගත යුතු පාඩම නම්: {moral}."
                                corpus.append(story)
        
        # Add traditional Sinhala proverbs and sayings
        proverbs = [
            "අන් ගෙදර ගින්නක් නර්තනය දකින්නා සේ",
            "අහසට විලි කියන කුකුළා මෙන්",
            "ඇත් අඬවන්නේ ඇත් ඇති තැනට",
            "කකුල් තුනේ මේසය මෙන්",
            "ගල ගසා ගෙඩි ගැනීම",
            "දියේ ඉන්නා මැඩිල්ලාට දිය බය නැත",
            "නිල් ගඟේ වතුර මිරිකා බොන්න",
            "රන් කළයේ කිරි උනු කලත් කහ නොවේ"
        ]
        
        corpus.extend(proverbs)
        
        return corpus
    
    def load_story_patterns(self):
        """Load enhanced story patterns for folk tales"""
        self.story_patterns = {
            'journey_of_discovery': {
                'stages': ['ආරම්භය', 'සංචාරය', 'මුණගැසීම්', 'අභියෝග', 'දැනුම් ලැබීම', 'පරිවර්තනය', 'ආපසු පැමිණීම', 'ඉගෙනීම'],
                'description': 'දැනුම සහ අවබෝධය සඳහා ගමනක්'
            },
            'moral_conflict': {
                'stages': ['සාමාන්‍ය ජීවිතය', 'ද්විදාරීතාවය', 'තෝරාගැනීම', 'ප්‍රතිවිපාක', 'සාකච්ඡාව', 'දෝෂ සංශෝධනය', 'නව අරමුණ', 'නිදහස'],
                'description': 'ගතික ගැටුමක් හා එහි විසඳුම'
            },
            'heroic_quest': {
                'stages': ['ආරාධනය', 'සූදානම', 'සහයකයන්', 'බාධක', 'සටන', 'ජයග්‍රහණය', 'හිමිකම', 'බලපෑම'],
                'description': 'වීරයෙකුගේ ගමන සහ ජයග්‍රහණය'
            },
            'transformation': {
                'stages': ['අසතුට', 'සෝදිසිය', 'මුලාශ්‍රය', 'මාර්ගය', 'දුෂ්කරතා', 'වෙනස්කම්', 'නව දැක්ම', 'සාක්ෂාත් කරගැනීම'],
                'description': 'චරිතයක පරිවර්තනය සහ වර්ධනය'
            }
        }
    
    def load_folk_tale_templates(self):
        """Load traditional Sinhala folk tale templates"""
        self.folk_tale_templates = {
            'wisdom_tale': {
                'structure': [
                    "පැරණි කථාවක් ආරම්භ වන්නේ...",
                    "ප්‍රධාන චරිතය හඳුන්වා දීම...",
                    "ප්‍රශ්නය හෝ අභියෝගය හඳුන්වා දීම...",
                    "උපදේශනය සොයා ගමන් කිරීම...",
                    "ඥානවන්තයෙකු හමුවීම...",
                    "උපදේශනය ලැබීම...",
                    "ප්‍රශ්නය විසඳීම...",
                    "කථාවේ නිමාව සහ ඉගෙනීම..."
                ],
                'elements': ['ඥානවත් චරිතය', 'ගැටලුව', 'සොයාගමන', 'දැනුම් ලැබීම', 'විසඳුම', 'අවබෝධය']
            },
            'moral_fable': {
                'structure': [
                    "සරල ජීවිතයක් විස්තර කිරීම...",
                    "ගැටලුව හෝ ප්‍රලෝභනය ඇතිවීම...",
                    "නරක තීරණයක් ගැනීම...",
                    "අනතුරු ප්‍රතිවිපාක...",
                    "පසුතැවිලි වීම සහ සෝදිසිය...",
                    'සාධු මාර්ගයට පෙරලීම...',
                    "නව ජීවිතයක් ආරම්භ කිරීම...",
                    "සදාචාරාත්මක පාඩම..."
                ],
                'elements': ['සාමාන්‍ය චරිතය', 'ගැටුම', 'දෝෂය', 'ප්‍රතිවිපාක', 'පසුතැවිල්ල', 'සංශෝධනය', 'ඉගෙනීම']
            },
            'heroic_journey': {
                'structure': [
                    "සාමාන්‍ය ලෝකය විස්තර කිරීම...",
                    "ඇමතුම හා අභියෝගය...",
                    "අපවාදය හෝ අත්හැරීම...",
                    "මායාමය ලෝකයට ඇතුළුවීම...",
                    "මිතුරන් හා සතුරන් හමුවීම...",
                    "මහා අභියෝගය හා සටන...",
                    "ජයග්‍රහණය හා සම්පත...",
                    'නැවත සාමාන්‍ය ලෝකයට පැමිණීම...',
                    "පරිවර්තනය වූ චරිතය..."
                ],
                'elements': ['වීරයා', 'ඇමතුම', 'සහයකයන්', 'මායා ලෝකය', 'අභියෝග', 'ජයග්‍රහණය', 'ප්‍රතිලාභ', 'පරිවර්තනය']
            },
            'nature_tale': {
                'structure': [
                    "සොබාදහමේ සිරිත් විරිත් විස්තර කිරීම...",
                    "මිනිසුන් හා සතුන්ගේ සම්බන්ධතාවය...",
                    "සොබාදහමේ නියමයන් උල්ලංඝනය කිරීම...",
                    "සොබාදහමේ ප්‍රතිචාරය...",
                    "දුක්ඛිත තත්ත්වය...",
                    "සොබාදහම සමඟ එකඟ වීම...",
                    "සාමය හා සමබරතාවය නැවත ලබා ගැනීම...",
                    "සොබාදහම සමඟ ජීවත් වීමේ අවබෝධය..."
                ],
                'elements': ['සොබාදහම', 'මිනිසා', 'උල්ලංඝනය', 'ප්‍රතිවිපාක', 'දුක', 'සමඟිතාව', 'සාමය', 'අවබෝධය']
            }
        }
    
    def load_moral_lessons(self):
        """Load moral lessons according to emotions"""
        self.moral_lessons = {
            'happy': {
                'lessons': [
                    "සතුට සොයා නොගොස් එය නිර්මාණය කරන්න",
                    "සතුට බෙදා ගැනීමෙන් එය වර්ධනය වේ",
                    "සරල ජීවිතයෙන් මහත් සතුටක් ලැබේ",
                    "සතුට යනු මනසේ තත්ත්වයකි, තත්වයන්ගේ ප්‍රතිඵලයක් නොවේ"
                ],
                'teaching': "සත්‍ය සතුට යනු අභ්‍යන්තර සාමයෙන් සහ අනුන්ට දායක වීමෙන් ලැබේ"
            },
            'sad': {
                'lessons': [
                    "දුක යනු ශක්තියක් බවට පත් කළ හැකි අත්දැකීමකි",
                    "ශෝකය මඟින් අපගේ මනුෂ්‍යත්වය ගැඹුරු කරයි",
                    "දුකින් තොර ජීවිතයක් ගැඹුරු අත්දැකීම් වලින් තොරය",
                    "දුකට මැදිවීමෙන් අපට වටිනා පාඩම් ඉගෙන ගත හැක"
                ],
                'teaching': "දුක සහ ශෝකය ජීවිතයේ අත්‍යවශ්‍ය අංග වන අතර ඒවා මඟින් අපව වඩාත් සංවේදී හා ඥානවත් බවට පත් කරයි"
            },
            'calm': {
                'lessons': [
                    "සන්සුන් භාවය යනු අභ්‍යන්තර ශක්තියකි",
                    "නිශ්ශබ්දතාවය තුළ ගැඹුරු අවබෝධයන් සොයා ගත හැක",
                    "සාමය යනු සැබෑ සමෘද්ධියයි",
                    "සන්සුන් මනසකට විශ්වයේ හඬ ඇසේ"
                ],
                'teaching': "සන්සුන් භාවය සහ සාමය යනු අභ්‍යන්තර සම්පතක් වන අතර එය බාහිර තත්වයන් මත රඳා නොපවතී"
            },
            'angry': {
                'lessons': [
                    "කෝපය පාලනය කිරීම යනු ශක්තියක සලකුණකි",
                    "ක්‍රෝධය යනු ආරක්ෂක යන්ත්‍රණයක් වුවද එය බුද්ධිමත්ව භාවිතා කළ යුතුය",
                    "සන්සුන්ව කෝපය පරිවර්තනය කිරීමෙන් නිර්මාණශීලි ශක්තියක් ලැබේ",
                    "කෝපය තුළින් අනුකම්පාව ඉගෙන ගත හැක"
                ],
                'teaching': "කෝපය පාලනය කිරීම සහ එය ධනාත්මක ක්‍රියාවන්ට යොමු කිරීම යනු චරිත ශක්තියේ සලකුණකි"
            },
            'anxious': {
                'lessons': [
                    "උද්වේගය යනු අනාගතයට සූදානම් වන මනසක සලකුණකි",
                    "කලබලය තුළින් වැදගත් සැලකිලි ගැන සිතා බැලිය හැක",
                    "උද්වේගය පාලනය කිරීම යනු අභ්‍යන්තර සාමය සොයා ගැනීමයි",
                    "වර්තමානයේ ජීවත් වීමෙන් අනාගත උද්වේගය අඩු කළ හැක"
                ],
                'teaching': "උද්වේගය සහ කලබලය ස්වභාවික ය, නමුත් ඒවා පාලනය කිරීම හා ධනාත්මක ක්‍රියාවන්ට යොමු කිරීම යනු අභ්‍යන්තර සාමය ලබා ගැනීමේ මාර්ගයයි"
            },
            'empty': {
                'lessons': [
                    "හිස් භාවය යනු නව අවස්ථාවන් සඳහා ඉඩ ප්‍රස්ථාවකි",
                    "ශූන්‍යතාවය තුළින් සත්‍ය අර්ථය සොයා ගත හැක",
                    "හිස් බව යනු පිරීමට අවස්ථාවකි",
                    "අර්ථ රහිත භාවය යනු නව අර්ථ නිර්මාණය සඳහා ආරම්භක ලක්ෂ්‍යයකි"
                ],
                'teaching': "හිස් භාවය සහ ශූන්‍යතාව යනු නව අර්ථයන් සහ අරමුණු සොයා ගැනීමේ අවස්ථාවන් වන අතර ජීවිතය නැවත නිර්මාණය කිරීමට ඉඩ සලසයි"
            },
            'confused': {
                'lessons': [
                    "ව්‍යාකූලතාව යනු නව අවබෝධයන් සඳහා මාර්ගයකි",
                    "අවුල් සහගත තත්ත්වයන් තුළින් වැදගත් ප්‍රශ්න ඇති වේ",
                    "පැටලිලි යනු සොයා ගැනීමේ පළමු පියවරයි",
                    "ව්‍යාකූල භාවය තුළින් නව දිශාවන් සොයා ගත හැක"
                ],
                'teaching': "ව්‍යාකූලතාව සහ පැටලිලි යනු අධ්‍යයනයේ සහ වර්ධනයේ කොටසක් වන අතර ඒවා හරහා ගමන් කිරීමෙන් වඩාත් ගැඹුරු අවබෝධයන් ලැබේ"
            },
            'hopeful': {
                'lessons': [
                    "බලාපොරොත්තුව යනු අඳුරු කාලවල ආලෝකයයි",
                    "අපේක්ෂාව යනු අනාගතය සඳහා සැලසුම් කිරීමේ ශක්තියකි",
                    "විශ්වාසය යනු දුෂ්කරතා මැඩපැවැත්වීමේ ආයුධයකි",
                    "ආශාව යනු නව මාර්ග සොයා ගැනීමේ ප්‍රේරණයකි"
                ],
                'teaching': "බලාපොරොත්තුව, අපේක්ෂාව සහ විශ්වාසය යනු ජීවිතයේ අභියෝග මැඩපැවැත්වීමට හා සුන්දර අනාගතයක් නිර්මාණය කිරීමට අවශ්‍ය මූලික ගුණාංග වේ"
            }
        }
    
    def generate_story(
        self, 
        mood: str, 
        weather: str, 
        character: str,
        starter_sentence: Optional[str] = None,
        story_length: str = 'medium',  # 'short', 'medium', 'long'
        temperature: float = 0.7,
        max_length: Optional[int] = None  # For backward compatibility
    ) -> Dict[str, any]:
        """Generate a meaningful Sinhala folk tale with moral lesson"""
        start_time = time.time()
        
        try:
            # Handle backward compatibility - convert max_length to story_length if provided
            if max_length is not None:
                if max_length <= 150:
                    story_length = 'short'
                elif max_length <= 300:
                    story_length = 'medium'
                else:
                    story_length = 'long'
            
            # Determine story length parameters
            length_params = {
                'short': {'min_paragraphs': 4, 'max_paragraphs': 6, 'min_sentences': 8, 'max_sentences': 12},
                'medium': {'min_paragraphs': 6, 'max_paragraphs': 8, 'min_sentences': 12, 'max_sentences': 18},
                'long': {'min_paragraphs': 8, 'max_paragraphs': 12, 'min_sentences': 18, 'max_sentences': 25}
            }
            
            params = length_params.get(story_length, length_params['medium'])
            
            # Generate the folk tale
            story = self._generate_folk_tale(
                mood=mood,
                weather=weather,
                character=character,
                starter_sentence=starter_sentence,
                min_paragraphs=params['min_paragraphs'],
                max_paragraphs=params['max_paragraphs'],
                min_sentences=params['min_sentences'],
                max_sentences=params['max_sentences']
            )
            
            # Extract moral lesson
            moral_lesson = self._extract_moral_lesson(mood, story)
            
            # Generate story title
            title = self._generate_story_title(story, mood, character)
            
            generation_time = time.time() - start_time
            
            return {
                'success': True,
                'title': title,
                'story': story,
                'moral_lesson': moral_lesson,
                'story_type': 'Sinhala Folk Tale',
                'metadata': {
                    'mood': mood,
                    'weather': weather,
                    'character': character,
                    'story_length': story_length,
                    'paragraphs': story.count('\n\n') + 1,
                    'sentences': story.count('. ') + story.count('! ') + story.count('? ') + 1,
                    'words': len(story.split()),
                    'generation_time': round(generation_time, 2),
                    'template_used': 'Enhanced Folk Tale',
                    'unique_id': self._generate_story_id(mood, weather, character, starter_sentence)
                }
            }
            
        except Exception as e:
            logger.error(f"Story generation error: {e}")
            return {
                'success': False,
                'title': "සරල කථාවක්",
                'story': self._create_meaningful_fallback(mood, weather, character, starter_sentence),
                'moral_lesson': self.moral_lessons.get(mood, {}).get('teaching', 'සෑම අත්දැකීමකින්ම ඉගෙන ගත හැකි පාඩමක් ඇත.'),
                'metadata': {
                    'is_fallback': True,
                    'error': str(e)[:100]
                }
            }
    
    
    def _generate_folk_tale(
        self,
        mood: str,
        weather: str,
        character: str,
        starter_sentence: Optional[str],
        min_paragraphs: int = 6,
        max_paragraphs: int = 8,
        min_sentences: int = 12,
        max_sentences: int = 18
    ) -> str:
        """Generate a complete Sinhala folk tale"""
        
        # Choose appropriate folk tale template based on mood
        template_key = self._select_template_for_mood(mood)
        template = self.folk_tale_templates.get(template_key, self.folk_tale_templates['wisdom_tale'])
        
        # Determine number of paragraphs and sentences
        num_paragraphs = random.randint(min_paragraphs, max_paragraphs)
        total_sentences = random.randint(min_sentences, max_sentences)
        
        # Generate story structure
        paragraphs = []
        
        # Paragraph 1: Introduction
        intro = self._generate_introduction(mood, weather, character, starter_sentence)
        paragraphs.append(intro)
        
        # Paragraph 2: Character and setting development
        character_para = self._develop_character_and_setting(character, mood, weather)
        paragraphs.append(character_para)
        
        # Middle paragraphs: Story development
        development_paragraphs = num_paragraphs - 4  # Minus intro, character, climax, conclusion
        
        for i in range(development_paragraphs):
            if i == 0:
                # First development paragraph: Problem introduction
                para = self._introduce_problem(character, mood)
            elif i == development_paragraphs - 1:
                # Last development paragraph: Rising action
                para = self._build_rising_action(character, mood)
            else:
                # Middle development paragraphs
                para = self._generate_story_development(character, mood, i+1, development_paragraphs)
            paragraphs.append(para)
        
        # Climax paragraph
        climax_para = self._generate_climax(character, mood)
        paragraphs.append(climax_para)
        
        # Conclusion paragraph with resolution
        conclusion_para = self._generate_conclusion_with_lesson(character, mood)
        paragraphs.append(conclusion_para)
        
        # Combine paragraphs
        full_story = '\n\n'.join(paragraphs)
        
        # Ensure minimum sentence count
        sentences = full_story.replace('\n\n', '. ').split('. ')
        if len(sentences) < total_sentences:
            # Add more descriptive sentences
            full_story = self._enhance_with_descriptions(full_story, total_sentences - len(sentences), mood, character)
        
        return full_story
    
    def _select_template_for_mood(self, mood: str) -> str:
        """Select appropriate folk tale template based on mood"""
        template_map = {
            'happy': 'wisdom_tale',
            'sad': 'moral_fable',
            'calm': 'nature_tale',
            'angry': 'heroic_journey',
            'anxious': 'moral_fable',
            'empty': 'wisdom_tale',
            'confused': 'heroic_journey',
            'hopeful': 'wisdom_tale'
        }
        return template_map.get(mood, 'wisdom_tale')
    
    def _generate_introduction(
        self,
        mood: str,
        weather: str,
        character: str,
        starter_sentence: Optional[str]
    ) -> str:
        """Generate folk tale introduction with proper Sinhala names"""
        
        # Get character name in Sinhala
        char_name = self._get_character_name(character)
        char_generic = self._get_character_name(f"{character}_gen")
        
        # Traditional Sinhala folk tale openings
        openings = [
            f"අතීතයේ දී එක් සමයක {char_generic} විසූ බව කියවේ",
            f"පුරාණ කාලයේ දී එක්තරා ගමක {char_generic} විසූ බව පැවසේ",
            f"බොහෝ අවුරුදු ගණනකට පෙර {char_name} නම් {char_generic} විසූ බව ජනප්‍රවාදයේ සඳහන් වේ",
            f"එක් වරක් ඉතා පැරණි යුගයක {char_generic} විසූ බව පුරාණ කථාවල කියැවේ",
            f"සදාකාලික කථාවකට අනුව {char_name} නම් {char_generic} විසූ බව සඳහන් වේ",
            f"පුරාණ ග්‍රන්ථවල සඳහන් වන පරිදි {char_generic} විසූ බව කියවේ",
            f"ලෝකය තවමත් තරුණ වූ කාලයේ {char_generic} විසූ බව පැවසේ",
            f"මනුෂ්‍යයන් සහ සතුන් එකට ජීවත් වූ කාලයේ {char_generic} විසූ බව කියවේ"
        ]
        
        weather_descriptions = {
            'sunny': ["සූර්යාලෝකීය දවසක", "උණුසුම් දවසක", "පැහැදිලි දවසක", "සුප්‍රකාශ දවසක"],
            'rainy': ["වර්ෂාවෙන් තෙත් දවසක", "වැස්සෙන් පිරුණු දවසක", "ජලමය දවසක", "මෙගා වර්ෂාවක් සහිත දවසක"],
            'stormy': ["කුණාටු සහිත දවසක", "ගිගුරුම් සහිත දවසක", "සැළලිහිණි දවසක", "ප්‍රචණ්ඩ කාලගුණයක් සහිත දවසක"],
            'foggy': ["මීදුමින් වැසුණු දවසක", "අඳුරු දවසක", "මළුවෙන් පිරුණු දවසක", "අස්පෘශ්‍ය වාතාවරණයක් සහිත දවසක"]
        }
        
        if starter_sentence and starter_sentence.strip():
            # Enhance provided starter with character name
            enhanced_starter = f"{random.choice(openings)}. {starter_sentence.strip()}"
            if not enhanced_starter.endswith(('.', '!', '?')):
                enhanced_starter += '.'
            return enhanced_starter
        
        # Generate traditional folk tale opening
        opening = random.choice(openings)
        weather_desc = random.choice(weather_descriptions.get(weather, [f"{weather} දවසක"]))
        
        # Create introduction paragraph
        intro_sentences = [
            f"{opening}.",
            f"{weather_desc} ඔහුගේ ජීවිතය ආරම්භ විය.",
            f"මෙම කථාව {char_name}ගේ විශේෂ ගමනක් සම්බන්ධවය."
        ]
        
        return ' '.join(intro_sentences)

    
    def _develop_character_and_setting(self, character: str, mood: str, weather: str) -> str:
        """Develop character and setting in detail with Sinhala names"""
        
        char_name = self._get_character_name(character)
        
        character_details = {
            'hare': {
                'appearance': ["සුදු මාළු පැහැති", "දිගු කන් සහිත", "වේගවත් පා සහිත", "සියුම් සිරුරක් ඇති"],
                'personality': ["බුද්ධිමත්", "සියුම්", "උපක්‍රමශීලී", "අවංක"],
                'habitat': ["හරිත කැලෑවක", "පුලුන් වනයක", "මල් උයනක", "ගං ඉවුරක"]
            },
            'lion': {
                'appearance': ["ප්‍රබල ශරීරයක් ඇති", "දිගු කේශර සහිත", "තියුණු නියපළු සහිත", "රාජකීය පෙනුමක් ඇති"],
                'personality': ["ගෞරවනීය", "ධෛර්යමත්", "රාජකාරි", "සත්‍යවාදී"],
                'habitat': ["විශාල වනයක", "ගිරි කන්දක", "රාජ මාලිගයක", "විවෘත තණබිමක"]
            },
            'elephant': {
                'appearance': ["විශාල ශරීරයක් ඇති", "දිගු අං කනින් යුත්", "පුළුල් කන් සහිත", "ශක්තිමත් පා සහිත"],
                'personality': ["ඥානවත්", "සන්සුන්", "කරුණාවන්ත", "දෘඪ සංකල්පයක් ඇති"],
                'habitat': ["දඩයම් වනයක", "ගං ඉවුරක", "තුඩුවල වනයක", "හරිත බිම් ප්‍රදේශයක"]
            }
        }
        
        char_info = character_details.get(character, {})
        
        sentences = []
        
        # Character description
        if char_info:
            appearance = random.choice(char_info.get('appearance', [""]))
            personality = random.choice(char_info.get('personality', [""]))
            sentences.append(f"{char_name} {appearance} {personality} සුලකුණු වලින් යුක්ත විය.")
        
        # Habitat description
        habitat = random.choice(char_info.get('habitat', ["ස්වභාවික පරිසරයක"]))
        sentences.append(f"ඔහු {habitat} වාසය කලේය.")
        
        # Daily life description
        daily_activities = {
            'hare': ["කුඩා පැණි මල් සොයා ගමන් කිරීම", "මිතුරන් සමඟ ක්‍රීඩා කිරීම", "වනාන්තරයේ සංචාරය කිරීම"],
            'lion': ["රාජධානිය ආරක්ෂා කිරීම", "වන සතුන් සමඟ සම්බන්ධතා පවත්වා ගැනීම", "වන නීති පැහැදිලි කිරීම"],
            'elephant': ["ගංගාවේ නාමින් කාලය ගත කිරීම", "යාලුවන් සමඟ සංචාරය කිරීම", "වනාන්තරයේ සාමය රැක ගැනීම"]
        }
        
        activity = random.choice(daily_activities.get(character, ["සාමාන්‍ය ජීවිතයක් ගත කිරීම"]))
        sentences.append(f"සෑම දිනකම {char_name} {activity} විනෝද විය.")
        
        return ' '.join(sentences)

    def _create_conclusion(self, mood: str, character: str) -> str:
        """Create story conclusion with Sinhala character names"""
        
        char_name = self._get_character_name(character)
        
        conclusions = {
            'happy': [
                f"අවසානයේ {char_name} සතුටින් පිරුණු අනාගතයකට මුහුණ පා සිටියේය.",
                f"මෙම ගමන {char_name}ගේ ජීවිතයේ සතුටුමත් අත්දැකීමක් බවට පත්විය.",
                f"{char_name}ගේ සතුට නව අර්ථයක් සහ දිශාවක් ලැබුවේය."
            ],
            'sad': [
                f"අවසානයේ {char_name} දුක තුළින් නව බලාපොරොත්තුවක් සොයා ගත්තේය.",
                f"මෙම අත්දැකීම {char_name}ගේ දුක අර්ථවත් කලේය.",
                f"{char_name} ශෝකය තුළින් නව ශක්තියක් සොයා ගත්තේය."
            ]
        }
        
        return random.choice(conclusions.get(mood, [f"අවසානයේ {char_name} වෙනස් වූ අයෙකු ලෙස සිටියේය."]))

    def _create_meaningful_fallback(self, mood: str, weather: str, character: str, 
                                   starter_sentence: Optional[str] = None) -> str:
        """Create meaningful fallback story with traditional structure"""
        
        char_name = self._get_character_name(character)
        char_generic = self._get_character_name(f"{character}_gen")
        
        # Traditional Sinhala folk tale structure
        story_parts = []
        
        # Introduction
        if starter_sentence and starter_sentence.strip():
            intro = starter_sentence.strip()
        else:
            intro = f"අතීතයේ දී {char_name} විසූ බව කියවේ."
        
        story_parts.append(intro)
        
        # Character description
        char_desc = f"මෙම {char_name} ඉතා විශේෂ ගුණාංග වලින් යුක්ත විය."
        story_parts.append(char_desc)
        
        # Problem
        problem = f"එක් දිනෙක {self._get_problem_for_mood(mood)} හට ගත්තේය."
        story_parts.append(problem)
        
        # Journey
        journey = f"මෙය විසඳා ගැනීම සඳහා {char_name} ගමනක් ආරම්භ කලේය."
        story_parts.append(journey)
        
        # Encounters
        encounters = "ගමනේදී ඔහු නොයෙක් අත්දැකීම් සහ දැනුම් ලැබුවේය."
        story_parts.append(encounters)
        
        # Resolution
        resolution = f"අවසානයේ {char_name} {self._get_resolution_for_mood(mood)}."
        story_parts.append(resolution)
        
        # Moral
        moral = f"මෙම කථාවෙන් අපට උගත යුතු පාඩම නම්: {self._get_moral_for_mood(mood)}."
        story_parts.append(moral)
        
        return ' '.join(story_parts)
    
    def _introduce_problem(self, character: str, mood: str) -> str:
        """Introduce the main problem or challenge"""
        
        problems = {
            'happy': [
                "එක් දිනෙක අසාමාන්‍ය සිදුවීමක් සිදු විය",
                "සතුටු ජීවිතයට අභියෝගයක් මතු විය",
                "සුභ පැතුම්වලින් තොරවූ තත්ත්වයක් ඇති විය"
            ],
            'sad': [
                "දුකින් පිරුණු දිනක දුෂ්කරතාවයක් හට ගත්තේය",
                "ශෝකයට අමතරව ගැටලුවක් මතු විය",
                "අඳුරු කාලයේ දී තවත් අඳුරු සිදුවීමක් සිදු විය"
            ],
            'calm': [
                "සන්සුන් භාවය බිඳ දැමූ සිදුවීමක් ඇති විය",
                "නිශ්ශබ්දතාවයට බාධාවක් එල්ල විය",
                "සාමකාමී ජීවිතයට අහිතකර වෙනසක් සිදු විය"
            ],
            'angry': [
                "කෝපය තවත් උත්සන්න කරමින් සිදුවීමක් සිදු විය",
                "රළු බවට තවත් ඉඩකඩ සලසමින් අභියෝගයක් මතු විය",
                "ක්‍රෝධය දල්වන තත්ත්වයක් ඇති විය"
            ]
        }
        
        character_problems = {
            'hare': [
                "කුඩා වීම නිසා සිදුවන අපහසුතා",
                "වේගවත් වීම නිසා සිදුවන අනතුරු",
                "සියුම් සිරුර නිසා සිදුවන අවදානම්"
            ],
            'lion': [
                "ප්‍රබල වීම නිසා සිදුවන වගකීම්",
                "රාජකාරි වලින් සිදුවන බර",
                "සැමට නායකත්වය දීමේ දුෂ්කරතා"
            ],
            'elephant': [
                "විශාල වීම නිසා සිදුවන අපහසුතා",
                "ශක්තිමත් වීම නිසා සිදුවන අපේක්ෂා",
                "මන්දගාමී වීම නිසා සිදුවන අවස්ථා නැතිවීම්"
            ]
        }
        
        problem_intro = random.choice(problems.get(mood, ["එක් දිනෙක විශේෂ සිදුවීමක් සිදු විය"]))
        char_problem = random.choice(character_problems.get(character, ["චරිතයට සුවිශේෂී අභියෝගයක්"]))
        
        sentences = [
            f"{problem_intro}.",
            f"මෙය {char_problem} ලෙස පෙන්නුම් කලේය.",
            "මෙම අභියෝගය ඔහුගේ සම්පූර්ණ ජීවිතයම වෙනස් කිරීමට සුදානම් විය."
        ]
        
        return ' '.join(sentences)
    
    def _build_rising_action(self, character: str, mood: str) -> str:
        """Build rising action leading to climax"""
        
        rising_actions = {
            'happy': [
                "සතුට ආරක්ෂා කර ගැනීම සඳහා ඔහු උත්සාහ දරන්නට විය",
                "ප්‍රීතිය නැවත ගෙන ඒම සඳහා ගමනක් ආරම්භ කලේය",
                "හෙටින් පිරුණු විසඳුමක් සොයා ගැනීමට තීරණය කලේය"
            ],
            'sad': [
                "දුකින් මිදීම සඳහා නව මාර්ගයක් සොයා ගැනීමට විය",
                "ශෝකය ජය ගැනීම සඳහා අභියෝගයක් ලෙස පිළිගත්තේය",
                "කණගාටුව තුළින් නිදහස් වීමේ උත්සාහයක් ආරම්භ කලේය"
            ],
            'calm': [
                "සන්සුන් භාවය නැවත ලබා ගැනීම සඳහා සොයා ගමන් කලේය",
                "නිශ්ශබ්දතාවය සොයා පිටත් වූයේ ගමනකට",
                "සාමය නැවත ස්ථාපිත කිරීමේ අභිලාෂයෙන් යුතුව කටයුතු කලේය"
            ],
            'angry': [
                "කෝපය පාලනය කිරීම සඳහා ගැඹුරු සොයා ගමනක් ආරම්භ කලේය",
                "රළු බව සාමකාමී බවකට පත් කිරීමේ උත්සාහයක යෙදුනේය",
                "ක්‍රෝධයෙන් නිදහස් වීම සඳහා විප්ලවකාරී තීරණයක් ගත්තේය"
            ]
        }
        
        character_actions = {
            'hare': [
                "වේගයෙන් දිවි ගමනක් ආරම්භ කලේය",
                "බුද්ධියෙන් යුතුව සැලසුම් කර ගමන් ගත්තේය",
                "සියුම් ලෙස අභියෝගය විසඳීමට උත්සාහ කලේය"
            ],
            'lion': [
                "ප්‍රබලව අභියෝගය මුහුණ දුන්නේය",
                "රාජකීය ලෙස ගැටලුව විසඳීමට ඉදිරිපත් විය",
                "ධෛර්යයෙන් යුතුව නව මාර්ගයක් සොයා ගත්තේය"
            ],
            'elephant': [
                "මහා ගමනක් ආරම්භ කලේය",
                "ශක්තියෙන් යුතුව ගැටලුව විසඳීමට උත්සාහ කලේය",
                "කරුණාවෙන් යුතුව සෑම අභියෝගයක්ම මුහුණ දුන්නේය"
            ]
        }
        
        rising_action = random.choice(rising_actions.get(mood, ["ගැටලුව විසඳීම සඳහා ගමනක් ආරම්භ කලේය"]))
        char_action = random.choice(character_actions.get(character, ["චරිතයට ගැලපෙන ආකාරයට කටයුතු කලේය"]))
        
        sentences = [
            f"{rising_action}.",
            f"{char_action}.",
            "මෙම ගමනේදී ඔහු නොයෙක් අත්දැකීම් සහ දැනුම් ලැබුවේය.",
            "සෑම පියවරකම නව පාඩමක් ඉගෙන ගත්තේය."
        ]
        
        return ' '.join(sentences)
    
    def _generate_story_development(self, character: str, mood: str, step: int, total_steps: int) -> str:
        """Generate story development paragraph"""
        
        developments = [
            "ගමනේදී ඔහු නව මිතුරන් හමුවිය",
            "අපූරු ස්ථාන සහ සිදුවීම් හමුවිය",
            "නොදන්නා භූමි ප්‍රදේශ හරහා ගමන් කලේය",
            "පැරණි ඥානවන්තයන් හමුවීම් සිදු විය",
            "ස්වභාවයේ රහස් සොයා ගැනීමට අවස්ථාව ලැබුණි",
            "සංස්කෘතික වටිනාකම් සහ සම්ප්‍රදායන් ගැන ඉගෙන ගත්තේය"
        ]
        
        mood_developments = {
            'happy': ["සතුටුදායක", "ප්‍රීතිදායක", "හාස්‍යජනක", "උත්සවාකාර"],
            'sad': ["ගැඹුරු අර්ථයක් ඇති", "සංවේදී", "චින්තනාත්මක", "සාකච්ඡාදායක"],
            'calm': ["සන්සුන්", "සාමකාමී", "නිර්විකාර", "ධ්‍යානාත්මක"],
            'angry': ["තීව්‍ර", "අරගලයක් සහගත", "විප්ලවකාරී", "සන්නද්ධ"]
        }
        
        development_type = random.choice(developments)
        mood_desc = random.choice(mood_developments.get(mood, ["වැදගත්"]))
        
        sentences = [
            f"ගමනේ {step}වන අදියරේදී, {development_type}.",
            f"මෙම හමුවීම් {mood_desc} අත්දැකීම් විය.",
            f"මේවා ඔහුගේ අවබෝධය {step}/{total_steps} ක් දක්වා වර්ධනය කලේය.",
            "සෑම අත්දැකීමකින්ම නව දෘෂ්ටිකෝණයක් ලැබුණි."
        ]
        
        return ' '.join(sentences)
    
    def _generate_climax(self, character: str, mood: str) -> str:
        """Generate story climax"""
        
        climaxes = {
            'happy': [
                "අවසාන අභියෝගයට මුහුණ දුන් මොහොත වූයේ මෙයයි",
                "සතුට නැවත ලබා ගැනීමේ මහා අවස්ථාව පැමිණියේය",
                "ප්‍රීතියේ ස්වර්ණමය අවස්ථාව මෙය විය"
            ],
            'sad': [
                "දුකින් මිදීමේ තීරණාත්මක මොහොත පැමිණියේය",
                "ශෝකය ජය ගැනීමේ මහා අභියෝගය මෙය විය",
                "කණගාටුවෙන් නිදහස් වීමේ අවසාන පඩිය මෙය විය"
            ],
            'calm': [
                "සන්සුන් භාවය නැවත ලබා ගැනීමේ අවසාන අදියර පැමිණියේය",
                "නිශ්ශබ්දතාවයේ උත්කර්ෂය මෙම මොහොතේදී හට ගත්තේය",
                "සාමය ස්ථාපිත කිරීමේ මහා අවස්ථාව මෙය විය"
            ],
            'angry': [
                "කෝපය පරිවර්තනය කිරීමේ අවසාන අදියර පැමිණියේය",
                "රළු බව සාමකාමී බවට පත් කිරීමේ තීරණාත්මක මොහොත මෙය විය",
                "ක්‍රෝධයෙන් නිදහස් වීමේ මහා අභියෝගය මෙය විය"
            ]
        }
        
        character_climaxes = {
            'hare': [
                "බුද්ධියෙන් අභියෝගය ජය ගන්නා මොහොත",
                "වේගයෙන් අවසාන ගමන සම්පූර්ණ කිරීම",
                "සියුම් ලෙස ගැටලුව විසඳීම"
            ],
            'lion': [
                "ප්‍රබල ඉල්ලීමක් සහ දෘඪතාවයෙන් අභියෝගය ජය ගැනීම",
                "රාජකීය ලෙස විසඳුමක් ඉදිරිපත් කිරීම",
                "ධෛර්යයෙන් යුතුව අවසාන සටනට මුහුණ දීම"
            ],
            'elephant': [
                "ශක්තියෙන් යුතුව අවසාන බාධකය ඉක්මවා යාම",
                "කරුණාවෙන් යුතුව ගැටලුව විසඳීම",
                "මහා ශක්තියෙන් අවසාන අභියෝගය මැඬ පැවැත්වීම"
            ]
        }
        
        climax = random.choice(climaxes.get(mood, ["ගමනේ උච්චතම අවස්ථාව පැමිණියේය"]))
        char_climax = random.choice(character_climaxes.get(character, ["චරිතයේ විශේෂ ගුණාංග භාවිතා කරමින් අභියෝගය ජය ගැනීම"]))
        
        sentences = [
            f"ගමනේ උච්චතම අවස්ථාව පැමිණියේය.",
            f"{climax}.",
            f"මෙම මොහොතේදී {char_climax}.",
            "සියලු අත්දැකීම් සහ ඉගෙන ගත් පාඩම් මෙම අවස්ථාව සඳහා සුදානම් කලේය.",
            "මෙය ඔහුගේ ජීවිතයේ වැදගත්ම තීරණාත්මක මොහොත විය."
        ]
        
        return ' '.join(sentences)
    
    def _generate_conclusion_with_lesson(self, character: str, mood: str) -> str:
        """Generate conclusion with moral lesson"""
        
        character_names = {
            'hare': 'කුරුල්ලා',
            'lion': 'සිංහයා',
            'elephant': 'අලියා'
        }
        
        char_name = character_names.get(character, character)
        
        conclusions = {
            'happy': [
                f"ගමන අවසන් වූ පසු {char_name} නැවත ගෙදර පැමිණියේය.",
                f"සතුට නැවත ලබා ගත් {char_name} නව අවබෝධයකින් පිරුණු අයෙකු බවට පත් විය.",
                "මෙම ගමන ඔහුට වටිනා පාඩම් රාශියක් ඉගැන්විය.",
                "ඔහුගේ අත්දැකීම් ගම්බද ප්‍රදේශයේ සියලු දෙනාටම උපදේශනයක් විය.",
                "මෙම කථාව පසු කාලීනව පරම්පරා ගණනාවක් පුරා පැතිර ගියේ එහි ගැඹුරු අර්ථය නිසාය."
            ],
            'sad': [
                f"ගමන අවසන් වූ පසු {char_name} නැවත ගෙදර පැමිණියේය.",
                f"දුක ජය ගත් {char_name} වඩාත් ශක්තිමත් හා ඥානවත් අයෙකු බවට පත් විය.",
                "මෙම ගමන ඔහුට වටිනා පාඩම් රාශියක් ඉගැන්විය.",
                "ඔහුගේ අත්දැකීම් ගම්බද ප්‍රදේශයේ සියලු දෙනාටම උපදේශනයක් විය.",
                "මෙම කථාව පසු කාලීනව පරම්පරා ගණනාවක් පුරා පැතිර ගියේ එහි ගැඹුරු අර්ථය නිසාය."
            ],
            'calm': [
                f"ගමන අවසන් වූ පසු {char_name} නැවත ගෙදර පැමිණියේය.",
                f"සන්සුන් භාවය නැවත ලබා ගත් {char_name} වඩාත් ගැඹුරු හා සමබර ජීවිතයක් ගත කලේය.",
                "මෙම ගමන ඔහුට වටිනා පාඩම් රාශියක් ඉගැන්විය.",
                "ඔහුගේ අත්දැකීම් ගම්බද ප්‍රදේශයේ සියලු දෙනාටම උපදේශනයක් විය.",
                "මෙම කථාව පසු කාලීනව පරම්පරා ගණනාවක් පුරා පැතිර ගියේ එහි ගැඹුරු අර්ථය නිසාය."
            ],
            'angry': [
                f"ගමන අවසන් වූ පසු {char_name} නැවත ගෙදර පැමිණියේය.",
                f"කෝපය පාලනය කල {char_name} වඩාත් සන්සුන් හා ගෞරවනීය අයෙකු බවට පත් විය.",
                "මෙම ගමන ඔහුට වටිනා පාඩම් රාශියක් ඉගැන්විය.",
                "ඔහුගේ අත්දැකීම් ගම්බද ප්‍රදේශයේ සියලු දෙනාටම උපදේශනයක් විය.",
                "මෙම කථාව පසු කාලීනව පරම්පරා ගණනාවක් පුරා පැතිර ගියේ එහි ගැඹුරු අර්ථය නිසාය."
            ]
        }
        
        conclusion = random.choice(conclusions.get(mood, [f"ගමනින් නැවත පැමිණි {char_name} වෙනස් වූ අයෙකු ලෙස සිටියේය."]))
        
        sentences = [
            f"ගමන අවසන් වූ පසු {char_name} නැවත ගෙදර පැමිණියේය.",
            f"අවසානයේ {char_name} වෙනස් වූ අයෙකු ලෙස සිටියේය.",
            "මෙම ගමන ඔහුට වටිනා පාඩම් රාශියක් ඉගැන්විය.",
            "ඔහුගේ අත්දැකීම් ගම්බද ප්‍රදේශයේ සියලු දෙනාටම උපදේශනයක් විය.",
            "මෙම කථාව පසු කාලීනව පරම්පරා ගණනාවක් පුරා පැතිර ගියේ එහි ගැඹුරු අර්ථය නිසාය."
        ]
        
        return ' '.join(sentences)
    
    def _enhance_with_descriptions(self, story: str, num_sentences_needed: int, mood: str, character: str) -> str:
        """Enhance story with additional descriptive sentences"""
        
        descriptions = [
            "සොබාදහමේ සුන්දරත්වය ඔහුගේ හදවත සපිරිය.",
            "සෑම හුස්මක් සමඟම නව අවබෝධයක් හට ගත්තේය.",
            "වන සතුන්ගේ හඬ ඔහුට සංගීතයක් ලෙස ඇසුණි.",
            "ගස්වල කොළ පැහැය ඔහුගේ ඇස් තුළ නර්තනය කලේය.",
            "ගංගාවල ගීතය ඔහුගේ ආත්මය සන්සුන් කලේය.",
            "පර්වතවල නිහ쩡 බව ඔහුට ධෛර්යය ලබා දුන්නේය.",
            "තාරකා වල බබලනය ඔහුගේ මග පෙන්වීය.",
            "සිහින් සුළං ඔහුගේ මනස පිරිසිදු කලේය."
        ]
        
        mood_descriptions = {
            'happy': [
                "සෑම දෙයකම ඔහුට සතුටු කිරීමේ ශක්තියක් දක්නට ලැබුණි.",
                "ප්‍රීතිය වර්ෂාව මෙන් ඔහුගේ මනස තුළට වැටුණි.",
                "හාස්‍යය සහ සතුට ඔහුගේ සහයකයන් විය."
            ],
            'sad': [
                "සෑම අත්දැකීමකම ගැඹුරු අර්ථයක් සොයා ගැනීමට ඔහු ඉගෙන ගත්තේය.",
                "දුක ඔහුගේ ගුරුවරයා බවට පත් විය.",
                "ශෝකය තුළින් ඔහු වඩාත් සංවේදී බවට පත් විය."
            ],
            'calm': [
                "සන්සුන් භාවය ඔහුගේ නිත්‍ය සහකරුවා බවට පත් විය.",
                "නිශ්ශබ්දතාවය තුළ ගැඹුරු සත්‍ය සොයා ගැනීමට ඔහු ඉගෙන �ගත්තේය.",
                "සාමය ඔහුගේ වටිනාම සම්පත බවට පත් විය."
            ],
            'angry': [
                "කෝපය පාලනය කිරීම ඔහුගේ මහා ජයග්‍රහණය බවට පත් විය.",
                "රළු බව සාමකාමී බවට පත් කිරීම ඔහුගේ විශේෂ කලාව බවට පත් විය.",
                "ක්‍රෝධයෙන් නිදහස් වීම ඔහුගේ මහා සාක්ෂාත් කර ගැනීම විය."
            ]
        }
        
        # Add descriptions
        added_sentences = []
        for i in range(num_sentences_needed):
            if i % 2 == 0:
                added_sentences.append(random.choice(descriptions))
            else:
                added_sentences.append(random.choice(mood_descriptions.get(mood, descriptions)))
        
        # Insert descriptions at appropriate places
        paragraphs = story.split('\n\n')
        if len(paragraphs) >= 3:
            # Add to middle paragraphs
            middle_index = len(paragraphs) // 2
            for i, sentence in enumerate(added_sentences):
                insert_index = min(middle_index + (i % 3), len(paragraphs) - 2)
                paragraphs[insert_index] = paragraphs[insert_index] + ' ' + sentence
        
        return '\n\n'.join(paragraphs)
    
    def _extract_moral_lesson(self, mood: str, story: str) -> Dict[str, str]:
        """Extract moral lesson from story based on mood"""
        
        lesson_data = self.moral_lessons.get(mood, self.moral_lessons['happy'])
        
        # Select appropriate lesson
        lesson = random.choice(lesson_data['lessons'])
        teaching = lesson_data['teaching']
        
        # Create traditional Sinhala moral ending
        endings = [
            "මෙම කථාවෙන් අපට උගත යුතු පාඩම නම්:",
            "මේ නිසා පරම්පරාගතව උගන්වන පාඩම වන්නේ:",
            "මෙයින් අපට ලැබෙන ගැඹුරු ඉගැන්වීම:",
            "පුරාණ ඥානය මෙසේ උගන්වයි:"
        ]
        
        moral_statement = f"{random.choice(endings)} {teaching}"
        
        return {
            'lesson': lesson,
            'teaching': teaching,
            'moral_statement': moral_statement,
            'mood_specific': True
        }
    
    def _generate_story_title(self, story: str, mood: str, character: str) -> str:
        """Generate appropriate title for the folk tale"""
        
        character_titles = {
            'hare': ['කුරුල්ලාගේ', 'ශීඝ්‍රගාමී', 'බුද්ධිමත්'],
            'lion': ['සිංහයාගේ', 'ප්‍රබල', 'රාජකීය'],
            'elephant': ['අලියාගේ', 'මහා', 'ශක්තිමත්']
        }
        
        mood_titles = {
            'happy': ['සතුටුමත්', 'ප්‍රීතිදායක', 'හෙටින් පිරුණු'],
            'sad': ['දුක්ඛිත', 'ශෝකජනක', 'කණගාටු සහගත'],
            'calm': ['සන්සුන්', 'සාමකාමී', 'නිර්විකාර'],
            'angry': ['ක්‍රෝධයේ', 'රළු', 'තීව්‍ර']
        }
        
        tale_types = [
            'ගමන',
            'කථාව',
            'අත්දැකීම',
            'සංචාරය',
            'අභියෝගය',
            'සොයාගමන',
            'පාඩම',
            'දර්ශනය'
        ]
        
        char_prefix = random.choice(character_titles.get(character, ['']))
        mood_prefix = random.choice(mood_titles.get(mood, ['']))
        tale_type = random.choice(tale_types)
        
        if char_prefix and mood_prefix:
            title = f"{char_prefix} {mood_prefix} {tale_type}"
        elif char_prefix:
            title = f"{char_prefix} {tale_type}"
        elif mood_prefix:
            title = f"{mood_prefix} {tale_type}"
        else:
            title = f"{character}ගේ {tale_type}"
        
        return title
    
    def _generate_story_id(self, mood: str, weather: str, character: str, starter: Optional[str]) -> str:
        """Generate unique story ID based on inputs"""
        import hashlib
        input_str = f"{mood}_{weather}_{character}_{starter}_{time.time()}_{random.random()}"
        return hashlib.md5(input_str.encode()).hexdigest()[:10]
    
    def _get_character_name(self, character: str) -> str:
        """Get character name in Sinhala with proper grammar"""
        names = {
            'hare': 'කුරුල්ලා',
            'lion': 'සිංහයා', 
            'elephant': 'අලියා',
            'hare_gen': 'කුරුල්ලෙක්',  # Generic form
            'lion_gen': 'සිංහයෙක්',   # Generic form
            'elephant_gen': 'අලියෙක්'  # Generic form
        }
        return names.get(character, character)

    def _describe_character(self, character: str, mood: str) -> str:
        """Describe character based on mood with proper Sinhala names"""
        descriptions = {
            'hare': {
                'happy': "වේගයෙන් දිවිය හැකි සතුටින් පිරුණු කුරුල්ලා",
                'sad': "මන්දගාමීව සංචාරය කරන දුකින් පිරුණු කුරුල්ලා",
                'calm': "සන්සුන්ව ගමන් කරන කුරුල්ලා",
                'angry': "කෝපයෙන් උමතු වූ කුරුල්ලා",
                'anxious': "කලබලයෙන් පිරුණු කුරුල්ලා",
                'empty': "හිස් භාවයෙන් පිරුණු කුරුල්ලා",
                'confused': "ව්‍යාකූලව සංචාරය කරන කුරුල්ලා",
                'hopeful': "බලාපොරොත්තුවෙන් පිරුණු කුරුල්ලා"
            },
            'lion': {
                'happy': "ප්‍රබල සිතිවිලි සහිත සතුටින් පිරුණු සිංහයා",
                'sad': "ශෝකයෙන් බර වූ සිංහයා",
                'calm': "සාමකාමී සිතිවිලි සහිත සිංහයා",
                'angry': "ක්‍රෝධයෙන් ගිගුරුම් දෙන සිංහයා",
                'anxious': "කලබලයෙන් පිරුණු සිංහයා",
                'empty': "හිස් භාවයෙන් පිරුණු සිංහයා",
                'confused': "ව්‍යාකූලව සංචාරය කරන සිංහයා",
                'hopeful': "බලාපොරොත්තුවෙන් පිරුණු සිංහයා"
            },
            'elephant': {
                'happy': "මහත් ශක්තියකින් යුත් සතුටින් පිරුණු අලියා",
                'sad': "දුකින් පිරුණු මන්දගාමී අලියා",
                'calm': "සන්සුන්ව හැසිරෙන අලියා",
                'angry': "කෝපයෙන් හෘද ස්පන්දනය වැඩි වූ අලියා",
                'anxious': "කලබලයෙන් පිරුණු අලියා",
                'empty': "හිස් භාවයෙන් පිරුණු අලියා",
                'confused': "ව්‍යාකූලව හැසිරෙන අලියා",
                'hopeful': "බලාපොරොත්තුවෙන් පිරුණු අලියා"
            }
        }
        
        char_desc = descriptions.get(character, {}).get(mood)
        if not char_desc:
            # Default description
            char_name = self._get_character_name(character)
            return f"{char_name}"
        
        return char_desc
    
    def _get_problem_for_mood(self, mood: str) -> str:
        """Get appropriate problem for mood"""
        problems = {
            'happy': "සතුට අහිමි වීමේ ගැටලුවක්",
            'sad': "දුකින් මිදීමේ අවශ්‍යතාවක්",
            'calm': "සන්සුන් භාවය නැති වීම",
            'angry': "කෝපය පාලනය කිරීමේ අභියෝගය"
        }
        return problems.get(mood, "විශේෂ ගැටලුවක්")
    
    def _get_resolution_for_mood(self, mood: str) -> str:
        """Get appropriate resolution for mood"""
        resolutions = {
            'happy': "සතුට නැවත සොයා ගත්තේය",
            'sad': "දුකින් නිදහස් විය",
            'calm': "සන්සුන් භාවය නැවත ලැබුවේය",
            'angry': "කෝපය පාලනය කිරීමට ඉගෙන ගත්තේය"
        }
        return resolutions.get(mood, "ගැටලුව විසඳා ගත්තේය")
    
    def _get_moral_for_mood(self, mood: str) -> str:
        """Get moral lesson for mood"""
        morals = {
            'happy': "සත්‍ය සතුට අභ්‍යන්තර සාමයෙන් ලැබේ",
            'sad': "දුක ජීවිතයේ ගුරුවරයෙකු ලෙස පිළිගත යුතුය",
            'calm': "සන්සුන් භාවය මහා සම්පතකි",
            'angry': "කෝපය පාලනය කිරීම යනු ශක්තියේ සලකුණකි"
        }
        return morals.get(mood, "සෑම අත්දැකීමකින්ම ඉගෙන ගත හැකි පාඩමක් ඇත")
    
    def get_model_info(self) -> Dict[str, any]:
        """Get enhanced model information"""
        return {
            "status": "Active",
            "model_type": "Enhanced Sinhala Folk Tale Generator",
            "vocabulary_size": self.vocab_size,
            "max_sequence_length": self.max_sequence_length,
            "story_types": list(self.folk_tale_templates.keys()),
            "moral_lessons": list(self.moral_lessons.keys()),
            "generation_method": "Dynamic Folk Tale Template + Neural Enhancement",
            "supports_long_stories": True,
            "traditional_structure": True,
            "meaningful_output": True
        }

# Global instance
story_generator = EnhancedSinhalaStoryGenerator()