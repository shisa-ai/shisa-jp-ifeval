import pykakasi
import re

def get_japanese_only(text):
    # Match hiragana, katakana, and kanji
    japanese_pattern = r'[ぁ-んァ-ンー一-龯]+'
    matches = re.findall(japanese_pattern, text)
    return ''.join(matches)

def analyze_shiritori(text):
    kks = pykakasi.kakasi()
    # Split on periods and newlines
    lines = [line.strip() for line in re.split(r'[.\n]', text) if line.strip()]
    
    previous_last_mora = None
    chain_results = []
    
    for line in lines:
        # Get only Japanese characters
        japanese_text = get_japanese_only(line)
        if not japanese_text:
            continue
            
        # Convert to hiragana
        result = kks.convert(japanese_text)
        if not result:
            continue
            
        # Get the hiragana text
        hiragana = ''.join(item['hira'] for item in result)
        if len(hiragana) > 0:
            # Get first and last mora
            first_mora = hiragana[0]
            last_mora = hiragana[-1]
            print(f"Line: {japanese_text}")
            print(f"Hiragana: {hiragana}")
            print(f"First mora: {first_mora}, Last mora: {last_mora}")
            
            if previous_last_mora is not None:
                matches = first_mora == previous_last_mora
                chain_results.append((previous_last_mora, first_mora, matches))
                print(f"Matches previous mora: {matches}")
            
            previous_last_mora = last_mora
            print("-" * 30)
    
    # Print chain summary
    print("\nShiritori Chain Summary:")
    for i, (prev_mora, curr_mora, matches) in enumerate(chain_results, 1):
        print(f"Link {i}: {prev_mora} → {curr_mora}: {'✓' if matches else '✗'}")
    
    # Calculate success rate
    if chain_results:
        success_rate = sum(1 for _, _, m in chain_results if m) / len(chain_results) * 100
        print(f"\nSuccess rate: {success_rate:.1f}%")

# Test with sample text
sample_text = '''1. りんご
2. ごま
3. dfdf まくら
4. らっぱ
5. ぱん
6. ん'''

print("Analyzing shiritori sequence:")
analyze_shiritori(sample_text)