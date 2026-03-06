"""
Quick test script for answer validation functionality
"""
from app.services.answer_validator import validate_answer

# Test cases
test_cases = [
    # Q1 - General day question
    (1, "", "EMPTY"),
    (1, "ඔව්", "NEED_MORE_INFO"),  # Yes/no not allowed for Q1
    (1, "හොඳයි", "NEED_MORE_INFO"),  # Too short
    (1, "අද දවස හොඳයි මට සතුටුයි", "VALID_TEXT"),  # Good answer
    
    # Q2 - Conflict question
    (2, "ඔව්", "YES_NO"),  # Yes/no allowed
    (2, "නෑ", "YES_NO"),  # Yes/no allowed
    (2, "දන්නෙ නෑ", "NEED_MORE_INFO"),  # Unknown short
    (2, "අද කෑම කෑවා", "NEED_MORE_INFO"),  # Too short (< 4 words)
    (2, "යාළුවා එක්ක රණ්ඩු වුණා", "VALID_TEXT"),  # Valid with keywords
    (2, "අද දවස හොඳයි සතුටුයි", "IRRELEVANT"),  # 4+ words but no keywords
    
    # Q3 - Study stress question  
    (3, "ඔව්", "YES_NO"),
    (3, "පාඩම් වලින් ආතතිය ඇති", "VALID_TEXT"),
    
    # Q4 - Tired question
    (4, "හරි", "YES_NO"),
    (4, "මම හරිම වෙහෙසයි නිදා ගන්නවා", "VALID_TEXT"),  # 4+ words with keywords
    
    # Q5 - Happy question
    (5, "okay", "YES_NO"),
    (5, "මට ජය ගත් නිසා සතුටුයි", "VALID_TEXT"),
]

print("Testing Answer Validator\n" + "="*50)
passed = 0
failed = 0

for question_id, text, expected_status in test_cases:
    result = validate_answer(question_id, text)
    status = result["status"]
    
    if status == expected_status:
        print(f"✓ Q{question_id}: '{text[:20]}...' -> {status}")
        passed += 1
    else:
        print(f"✗ Q{question_id}: '{text[:20]}...' -> Expected: {expected_status}, Got: {status}")
        failed += 1

print("\n" + "="*50)
print(f"Results: {passed} passed, {failed} failed")

if failed == 0:
    print("✓ All tests passed!")
else:
    print(f"✗ {failed} test(s) failed")
