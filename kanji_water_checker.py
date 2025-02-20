from jamdict import Jamdict
import re

def check_water_radical_sentences(text):
    """
    Check if the given text contains 3 coherent sentences using only kanji with water radical (氵).
    
    Args:
        text (str): The text to check
        
    Returns:
        dict: A dictionary containing:
            - valid (bool): Whether the text meets all criteria
            - sentences (list): List of detected sentences
            - reasons (list): List of reasons if the text is invalid
    """
    jam = Jamdict()
    result = {
        'valid': False,
        'sentences': [],
        'reasons': []
    }
    
    # Split text into sentences (assuming sentences end with 。)
    sentences = text.split('。')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Check if we have exactly 3 sentences
    if len(sentences) != 3:
        result['reasons'].append(f"Found {len(sentences)} sentences, but need exactly 3")
        return result
    
    result['sentences'] = sentences
    
    # Check each sentence
    for i, sentence in enumerate(sentences, 1):
        # Extract all kanji from the sentence
        kanji_chars = re.findall(r'[一-龯]', sentence)
        
        if not kanji_chars:
            result['reasons'].append(f"Sentence {i} contains no kanji")
            continue
            
        # Check if each kanji contains water radical
        for kanji in kanji_chars:
            # Use KRADFILE mapping to check for water radical
            radicals = jam.krad.get(kanji, [])
            has_water = '水' in radicals or '氵' in radicals
            
            if not has_water:
                result['reasons'].append(f"Kanji '{kanji}' in sentence {i} does not contain water radical")
    
    # Text is valid if we found no reasons for invalidity
    result['valid'] = len(result['reasons']) == 0
    
    return result

# Example usage
if __name__ == "__main__":
    # Example text with three sentences using water-radical kanji
    # You can replace this with your own test text
    test_text = "海を泳ぐ。清い水が流れる。深い湖を渡る。"
    
    result = check_water_radical_sentences(test_text)
    print(f"Text is {'valid' if result['valid'] else 'invalid'}")
    print("\nSentences found:")
    for sentence in result['sentences']:
        print(f"- {sentence}")
    
    if not result['valid']:
        print("\nReasons for invalidity:")
        for reason in result['reasons']:
            print(f"- {reason}")
