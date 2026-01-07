# debug_tokenizer.py
import pickle
from pathlib import Path

def inspect_tokenizer():
    """Inspect the tokenizer file structure"""
    tokenizer_path = "models/tokenizer.pkl"
    
    if not Path(tokenizer_path).exists():
        print(f"Tokenizer file not found: {tokenizer_path}")
        return
    
    with open(tokenizer_path, 'rb') as f:
        tokenizer_data = pickle.load(f)
    
    print("=" * 80)
    print(f"Tokenizer data type: {type(tokenizer_data)}")
    print("=" * 80)
    
    if isinstance(tokenizer_data, dict):
        print("Dictionary structure:")
        print(f"Number of keys: {len(tokenizer_data)}")
        print(f"Keys: {list(tokenizer_data.keys())}")
        
        for key in tokenizer_data.keys():
            value = tokenizer_data[key]
            print(f"\nKey: '{key}'")
            print(f"  Value type: {type(value)}")
            
            if isinstance(value, dict):
                print(f"  Is dictionary with {len(value)} items")
                if len(value) > 0:
                    sample_key = list(value.keys())[0]
                    sample_val = value[sample_key]
                    print(f"  Sample item: '{sample_key}' -> {type(sample_val)}: {sample_val}")
            elif isinstance(value, list):
                print(f"  Is list with {len(value)} items")
                if len(value) > 0:
                    print(f"  First item: {type(value[0])}: {value[0]}")
            elif isinstance(value, (int, float, str, bool)):
                print(f"  Value: {value}")
            else:
                print(f"  Value repr: {repr(value)[:200]}...")
    
    elif hasattr(tokenizer_data, '__dict__'):
        print("Object attributes:")
        for attr_name in dir(tokenizer_data):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(tokenizer_data, attr_name)
                    print(f"{attr_name}: {type(attr_value)}")
                except:
                    print(f"{attr_name}: [Error accessing]")
    
    else:
        print(f"Raw data: {repr(tokenizer_data)[:500]}...")

if __name__ == "__main__":
    inspect_tokenizer()