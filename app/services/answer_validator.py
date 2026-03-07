"""
Answer Validator Module for Question-Based Mood Check

This module validates student answers to ensure they are relevant and informative
before performing mood prediction.
"""

# Define answer categories
YES_WORDS = {
    "ඔව්", "ඔව්ව", "ඔහොමයි", "හරිමයි", 
    "ok", "okay", "ඔකේ", "ඔක"
}

NO_WORDS = {
    "නෑ", "නැහැ", "නොවෙයි", "නො", 
    "no", "nope"
}

UNKNOWN_SHORT = {
    "මං දන්නෙ නෑ", "දන්නෙ නෑ", "අමතකයි", "නොදන්නෙ", 
    "idk", "dont know"
}

# Neutral Phrases - valid "no issue" answers for Q2-Q5
NEUTRAL_PHRASES = {
    "එහෙම විශේෂ දෙයක් නෑ",
    "කිසිම දෙයක් නෑ",
    "ගැටලුවක් නෑ",
    "ප්‍රශ්නයක් නෑ",
    "අවුලක් නෑ",
    "මොකුත් නෑ",
    "එහෙම දෙයක් නෑ"
    "එම විශේෂ දෙයක් නෑ"
    " එහෙම අවුලක් තිබ්බේ නෑ"
    " එම අවුලක් තිබ්බේ නෑ"
}

# Q1 Neutral Phrases - reuse NEUTRAL_PHRASES for Q1 "no issue" answers
# Returns as Q1_DIRECT_MOOD with Normal mood
Q1_NEUTRAL_PHRASES = NEUTRAL_PHRASES

# Q1 Direct Mood Words - for recognizing short mood-indicating answers
Q1_HAPPY_WORDS = {
    "හොඳයි", "සතුටුයි", "විනෝදයි", "රසවත්", "happy",
    "සතුටු", "හොඳයි.", "සතුටුයි."
}

Q1_NORMAL_WORDS = {
    "සාමාන්‍යයි", "හරිමයි", "normal",
    "සාමාන්‍ය", "ok", "okay"
}

Q1_BAD_WORDS = {
    "නරකයි", "දුකයි", "හොඳ නෑ", "ආතතියි", "මහන්සියි",
    "stress", "bad", "වෙහෙසයි", "නරක", "දුක",
    "හොඳ නැහැ", "මහන්සි"
}

# Q1 Feeling/Mood signals - for detecting mood-related answers
Q1_FEELING_SIGNALS = {
    "හොඳ", "හොඳයි", "සතුටු", "සතුටුයි", "දුක", "දුකයි",
    "නරක", "නරකයි", "සාමාන්‍ය", "සාමාන්‍යයි", "විශේෂ"
    "මහන්සි", "මහන්සියි", "වෙහෙස", "වෙහෙසයි", "ආතතිය", "ආතතියි", "stress",
    "බය", "බයයි", "කේන්ති", "තරහ", "තරහයි", "කම්මැලි",
    "අමාරු", "හරිම අමාරු", "අසරණ", "ලැජ්ජා", "කනගාටු",
    "සැනසුම", "සතුටක්", "දුකක්", "විනෝද", "විනෝදයි", "රසවත්",
    "happy", "sad", "tired", "angry", "scared", "worried"
}

# Q1 Day/Context signals - for detecting day-related context
Q1_DAY_SIGNALS = {
    "අද", "ඊයේ", "අනිද්දා", "දවස", "දවස්", "මේ දවස",
    "ඉස්කෝලේ", "පාසල", "පාසලේ", "class", "school",
    "යාළුව", "යාළුවෝ", "යාළුවා", "ගුරුවර", "ගුරුතුමා",
    "පාඩම්", "පාඩම", "homework", "exam", "test", "විභාග", "පරීක්ෂණ"
}

# Keywords per question to determine relevance
KEYWORDS = {
    1: [
        "හොඳ", "නරක", "සාමාන්‍ය", "සතුටු", "දුක", "මහන්සි", "වෙහෙස", 
        "බය", "ආතතිය", "stress", "යාළුව", "ගුරුවර", "පාඩම්", 
        "විනෝද", "රසවත්"
    ],
    2: [
        "යාළුව", "ගුරුවර", "ගැටලුව", "රණ්ඩු", "බැන", "තරහ", 
        "කතා නැහැ", "ආරවුල", "ගැටුම", "වැරදි", " ගහ ගත්තා", "ගහගත්තා",
        " බැන ගත්තා", "බැන්නා","අපහාස කරා", "අපහාස වුණා","ප්‍රශ්නයක් ",
    ],
    3: [
        "පාඩම්", "homework", "exam", "පරීක්ෂණ", "විභාග", "ආතතිය", 
        "stress", "assignment", "test", "classwork",
    ],
    4: [
        "මහන්සි", "වෙහෙස", "නිදා", "නින්ද", "විවේක", 
        "rest", "sleep", "කම්මැලි",
    ],
    5: [
        "සතුටු", "හොඳ", "ජය", "win", "ලැබුණා", "gift", 
        "විනෝද", "හිනා", "ප්‍රීති", "happy",
    ]
}


def normalize_text(text: str) -> str:
    """
    Normalize text by stripping, lowercasing, and collapsing multiple spaces.
    
    Args:
        text: Raw input text
        
    Returns:
        Normalized text
    """
    text = text.strip()
    text = text.lower()
    # Collapse multiple spaces to one
    text = " ".join(text.split())
    return text


def is_yes_no_answer(normalized_text: str) -> bool:
    """
    Check if the answer is a simple yes/no response.
    
    Args:
        normalized_text: Normalized text
        
    Returns:
        True if the answer is yes/no, False otherwise
    """
    # Check exact match
    if normalized_text in YES_WORDS or normalized_text in NO_WORDS:
        return True
    
    # Check two-word phrases starting with yes/no (e.g., "ඔව් ඇත")
    tokens = normalized_text.split()
    if len(tokens) <= 2 and len(tokens) > 0:
        first_token = tokens[0]
        if first_token in YES_WORDS or first_token in NO_WORDS:
            return True
    
    return False


def starts_with_yes_no(normalized_text: str) -> tuple[bool, str]:
    """
    Check if the answer starts with a YES or NO token.
    Used for Q2-Q5 to prioritize YES/NO detection even if more words follow.
    
    Args:
        normalized_text: Normalized text
        
    Returns:
        Tuple of (is_yes_no, first_token)
        - is_yes_no: True if first token is yes/no, False otherwise
        - first_token: The first token if yes/no, empty string otherwise
    """
    tokens = normalized_text.split()
    if not tokens:
        return (False, "")
    
    first = tokens[0]
    if first in YES_WORDS or first in NO_WORDS:
        return (True, first)
    
    return (False, "")


def contains_keyword(normalized_text: str, question_id: int) -> bool:
    """
    Check if the text contains any relevant keyword for the given question.
    
    Args:
        normalized_text: Normalized text
        question_id: Question ID (1-5)
        
    Returns:
        True if at least one keyword is found, False otherwise
    """
    if question_id not in KEYWORDS:
        return True  # If no keywords defined, consider it valid
    
    keywords = KEYWORDS[question_id]
    for keyword in keywords:
        # Check if keyword appears in the text (whole word or substring)
        if keyword.lower() in normalized_text:
            return True
    
    return False


def contains_q1_signal(normalized_text: str) -> bool:
    """
    Check if Q1 answer contains signals indicating it's about mood/day/feelings.
    
    Args:
        normalized_text: Normalized text
        
    Returns:
        True if answer appears to be about student's day or mood, False otherwise
    """
    # Check for feeling/mood words
    has_feeling = any(signal in normalized_text for signal in Q1_FEELING_SIGNALS)
    if has_feeling:
        return True
    
    # Check for day-context words
    has_day_context = any(signal in normalized_text for signal in Q1_DAY_SIGNALS)
    if has_day_context:
        return True
    
    # Pattern: contains "මට" or "මම" with feeling/mood words
    if ("මට" in normalized_text or "මම" in normalized_text):
        if any(signal in normalized_text for signal in Q1_FEELING_SIGNALS):
            return True
    
    # Pattern: contains "අද" with feeling/mood or day-context words
    if "අද" in normalized_text:
        if any(signal in normalized_text for signal in Q1_FEELING_SIGNALS):
            return True
        if any(signal in normalized_text for signal in Q1_DAY_SIGNALS):
            return True
    
    return False


def validate_answer(question_id: int, text: str) -> dict:
    """
    Validate student answer for relevance and informativeness.
    
    Args:
        question_id: Question ID (1-5)
        text: Student's answer text
        
    Returns:
        dict with keys:
            - status: "EMPTY" | "YES_NO" | "NEED_MORE_INFO" | "IRRELEVANT" | "VALID_TEXT" | "Q1_DIRECT_MOOD"
            - normalized: normalized text
            - is_yes_no: boolean indicating if answer is yes/no
            - direct_mood: (optional) "Happy" | "Normal" | "Bad" - only present when status is "Q1_DIRECT_MOOD"
    """
    # Normalize the text
    normalized = normalize_text(text)
    
    # Check if empty
    if not normalized:
        return {
            "status": "EMPTY",
            "normalized": normalized,
            "is_yes_no": False
        }
    
    # Q1 Direct Mood Detection - Check BEFORE yes/no rejection for Q1
    # This allows words like "හරි" to be recognized as mood indicators
    if question_id == 1:
        # Check for neutral phrases first ("no issue" answers)
        for phrase in Q1_NEUTRAL_PHRASES:
            if phrase in normalized:
                return {
                    "status": "Q1_DIRECT_MOOD",
                    "normalized": normalized,
                    "is_yes_no": False,
                    "direct_mood": "Normal"
                }
        
        tokens = normalized.split()
        if len(tokens) <= 3:
            # Check if it's a direct mood word
            if normalized in Q1_HAPPY_WORDS:
                return {
                    "status": "Q1_DIRECT_MOOD",
                    "normalized": normalized,
                    "is_yes_no": False,
                    "direct_mood": "Happy"
                }
            elif normalized in Q1_NORMAL_WORDS:
                return {
                    "status": "Q1_DIRECT_MOOD",
                    "normalized": normalized,
                    "is_yes_no": False,
                    "direct_mood": "Normal"
                }
            elif normalized in Q1_BAD_WORDS:
                return {
                    "status": "Q1_DIRECT_MOOD",
                    "normalized": normalized,
                    "is_yes_no": False,
                    "direct_mood": "Bad"
                }
    
    # For Q2-Q5, prioritize YES/NO detection if answer starts with YES/NO token
    # This prevents longer answers like "ඔව් අද ගොඩක් වැඩ තිබුණා" from being sent to ML
    if question_id in [2, 3, 4, 5]:
        yn, first_token = starts_with_yes_no(normalized)
        if yn:
            return {
                "status": "YES_NO",
                "normalized": first_token,
                "is_yes_no": True
            }
    
    # Check if it's a yes/no answer
    is_yes_no = is_yes_no_answer(normalized)
    
    # For Q2-Q5, YES_NO is acceptable
    if is_yes_no and question_id in [2, 3, 4, 5]:
        return {
            "status": "YES_NO",
            "normalized": normalized,
            "is_yes_no": True
        }
    
    # For Q1, YES_NO is not acceptable (need descriptive answer)
    if is_yes_no and question_id == 1:
        return {
            "status": "NEED_MORE_INFO",
            "normalized": normalized,
            "is_yes_no": True
        }
    
    # Check if answer is in UNKNOWN_SHORT set
    if normalized in UNKNOWN_SHORT:
        return {
            "status": "NEED_MORE_INFO",
            "normalized": normalized,
            "is_yes_no": False
        }
    
    # For Q2-Q5, check if answer contains neutral phrases (valid "no issue" answers)
    # Check this BEFORE word_count to allow short neutral phrases like "ගැටලුවක් නෑ"
    if question_id in [2, 3, 4, 5]:
        for phrase in NEUTRAL_PHRASES:
            if phrase in normalized:
                return {
                    "status": "VALID_TEXT",
                    "normalized": normalized,
                    "is_yes_no": False
                }
    
    # Count words
    word_count = len(normalized.split())
    
    # If word count < 3, need more info (for Q1, direct mood words already handled above)
    if word_count < 3:
        return {
            "status": "NEED_MORE_INFO",
            "normalized": normalized,
            "is_yes_no": False
        }
    
    # For Q1, check if answer is actually about mood/day (has Q1 signals)
    if question_id == 1:
        if not contains_q1_signal(normalized):
            return {
                "status": "IRRELEVANT",
                "normalized": normalized,
                "is_yes_no": False
            }
    
    # For Q2-Q5, check keyword relevance
    if question_id in [2, 3, 4, 5]:
        if not contains_keyword(normalized, question_id):
            return {
                "status": "IRRELEVANT",
                "normalized": normalized,
                "is_yes_no": False
            }
    
    # If we reach here, the answer is valid
    return {
        "status": "VALID_TEXT",
        "normalized": normalized,
        "is_yes_no": False
    }


# ============================================================================
# TEST EXAMPLES (Expected Behavior)
# ============================================================================
# Q1 Direct Mood Examples:
# validate_answer(1, "හොඳයි") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Happy"}
# validate_answer(1, "සතුටුයි") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Happy"}
# validate_answer(1, "නරකයි") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Bad"}
# validate_answer(1, "දුකයි") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Bad"}
# validate_answer(1, "හොඳ නෑ") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Bad"}
# validate_answer(1, "සාමාන්‍යයි") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Normal"}
# validate_answer(1, "හරි") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Normal"}
#
# Q1 Neutral Phrases ("no issue" answers):
# validate_answer(1, "මොකුත් නෑ") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Normal"}
# validate_answer(1, "එහෙම විශේෂ දෙයක් නෑ") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Normal"}
# validate_answer(1, "ගැටලුවක් නෑ") -> {"status": "Q1_DIRECT_MOOD", "direct_mood": "Normal"}
#
# Q1 Longer Answers:
# validate_answer(1, "අද දවස හොඳයි මට සතුටුයි") -> {"status": "VALID_TEXT"}
# validate_answer(1, "අද ටිකක් මහන්සියි") -> {"status": "VALID_TEXT"}
# validate_answer(1, "අද ඉස්කෝලේ දවස හොඳයි") -> {"status": "VALID_TEXT"}
# validate_answer(1, "අද මට ටිකක් ආතතියක් තිබුණා") -> {"status": "VALID_TEXT"}
#
# Q1 Invalid:
# validate_answer(1, "ඔව්") -> {"status": "NEED_MORE_INFO"} (yes/no not allowed)
# validate_answer(1, "xyz") -> {"status": "NEED_MORE_INFO"} (too short, no mood word)
#
# Q1 Irrelevant (no mood/day signals):
# validate_answer(1, "මම පාන් කෑවා") -> {"status": "IRRELEVANT"}
# validate_answer(1, "අද මම වාහනයෙන් ගියා") -> {"status": "IRRELEVANT"}
# validate_answer(1, "මම පොතක් ගත්තා") -> {"status": "IRRELEVANT"}
#
# Q2-Q5 YES/NO (unchanged behavior):
# validate_answer(2, "ඔව්") -> {"status": "YES_NO"}
# validate_answer(2, "නෑ") -> {"status": "YES_NO"}
#
# Q2-Q5 Descriptive:
# validate_answer(2, "යාළුවා එක්ක රණ්ඩු වුණා") -> {"status": "VALID_TEXT"}
# validate_answer(2, "අද කෑම කෑවා") -> {"status": "IRRELEVANT"} (no keywords)
#
# Q2-Q5 Neutral Phrases (valid "no issue" answers):
# validate_answer(2, "එහෙම විශේෂ දෙයක් නෑ") -> {"status": "VALID_TEXT"}
# validate_answer(2, "ගැටලුවක් නෑ") -> {"status": "VALID_TEXT"}
# validate_answer(3, "කිසිම දෙයක් නෑ") -> {"status": "VALID_TEXT"}
# validate_answer(4, "අවුලක් නෑ") -> {"status": "VALID_TEXT"}
# validate_answer(5, "මොකුත් නෑ") -> {"status": "VALID_TEXT"}
