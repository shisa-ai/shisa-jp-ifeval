import pykakasi

def test_haiku(text):
    # Split into lines and remove empty ones
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check if we have exactly 3 lines
    if len(lines) != 3:
        return False
    
    # Initialize kakasi
    kks = pykakasi.kakasi()
    
    # Small kana that combine with previous character to form a single mora
    small_kana = 'ゃゅょ'
    
    # Count mora in each line
    mora_counts = []
    for line in lines:
        result = kks.convert(line)
        # Get hiragana and remove small kana before counting
        hiragana = ''.join(item['hira'] for item in result)
        for char in small_kana:
            hiragana = hiragana.replace(char, '')
        mora_counts.append(len(hiragana))
    
    # Check if pattern matches 5-7-5
    expected_pattern = [5, 7, 5]
    matches = mora_counts == expected_pattern
    print(f"Mora counts: {mora_counts}")
    print(f"Matches 5-7-5: {matches}")
    return matches

haiku = """猫じゃらし
揺れるしっぽに
春の風"""

test_haiku(haiku)
