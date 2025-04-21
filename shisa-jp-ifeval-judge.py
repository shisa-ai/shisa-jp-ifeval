import click
import json
import re
import os
import pykakasi
from jamdict import Jamdict
import csv
from loguru import logger

# Load task configurations
TASK_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'task_config.json')
with open(TASK_CONFIG_PATH, 'r') as f:
    TASK_CONFIG = json.load(f)

# Global debug flag
DEBUG = False

# Initialize Jamdict
jam = Jamdict()

def set_debug(debug_mode: bool):
    global DEBUG
    DEBUG = debug_mode
    if DEBUG:
        logger.info("Debug mode enabled")

def process_output(output):
    # Extract the text between <answer> tags from the response output
    pattern = r'<answer>(.*?)</answer>'
    match = re.search(pattern, output, re.DOTALL)
    if match:
        return match.group(1)
    return output

def NoKatakana(text, prompt=None):
    # Check for presence of katakana characters (Unicode range U+30A0 to U+30FF)
    pattern = r'[\u30A0-\u30FF]'
    has_katakana = bool(re.search(pattern, text))
    return not has_katakana

def CharacterLimit(text, prompt=None):
    # Get max_length from config
    max_length = TASK_CONFIG['CharacterLimit']['max_length']
    return len(text) <= max_length

def KeywordFrequency(text, prompt=None):
    # Get keyword and min_frequency from config
    config = TASK_CONFIG['KeywordFrequency']
    keyword = config['keyword']
    min_frequency = config['min_frequency']
    
    if DEBUG:
        logger.debug(f"[KeywordFrequency] Looking for keyword: '{keyword}'")
        logger.debug(f"[KeywordFrequency] Minimum required frequency: {min_frequency}")
    
    # Count occurrences of the keyword
    count = text.count(keyword)
    
    if DEBUG:
        logger.debug(f"[KeywordFrequency] Found {count} occurrences of '{keyword}'")
        if count < min_frequency:
            logger.debug(f"[KeywordFrequency] Not enough occurrences. Need at least {min_frequency}, found {count}")
    
    return count >= min_frequency

def RepeatPrompt(text, prompt):

    # Extract the part after -----\n in the prompt
    pattern = r'-----\n(.*?)$'
    match = re.search(pattern, prompt, re.DOTALL)
    if not match:
        return False
    
    # Get the text and remove the question tags
    prompt_text = match.group(1)
    # Remove the closing question tag
    prompt_text = prompt_text.replace('</question>', '')
    
    # Remove all whitespace from both strings
    target_text = ''.join(prompt_text.split())
    answer_text = ''.join(text.split())    
    # Check if the stripped prompt is contained in the stripped answer
    return target_text in answer_text

def get_japanese_only(text):
    # Match hiragana, katakana, and kanji
    japanese_pattern = r'[ぁ-んァ-ンー一-龯]+'
    matches = re.findall(japanese_pattern, text)
    return ''.join(matches)

def Shiritori(text, prompt=None):
    kks = pykakasi.kakasi()
    # Split on periods and newlines
    lines = [line.strip() for line in re.split(r'[.\n]', text) if line.strip()]
    
    if DEBUG and len(lines) < 3:
        logger.debug(f"[Shiritori] Not enough lines: found {len(lines)}, need at least 3")
        return False
    
    previous_last_mora = None
    chain_results = []
    last_moras = []  # Store all last moras to check specific positions
    
    for i, line in enumerate(lines, 1):
        # Get only Japanese characters
        japanese_text = get_japanese_only(line)
        if not japanese_text:
            if DEBUG:
                logger.debug(f"[Shiritori] Line {i} has no Japanese characters: {line}")
            continue
        
        # Look up the word in Jamdict and reject if not found
        result = jam.lookup(japanese_text)
        if not result.entries:
            if DEBUG:
                logger.debug(f"[Shiritori] Invalid word at line {i}: '{japanese_text}' (not found in dictionary)")
            return False
            
        # Convert to hiragana
        result = kks.convert(japanese_text)
        if not result:
            if DEBUG:
                logger.debug(f"[Shiritori] Line {i} failed conversion: {japanese_text}")
            continue
            
        # Get the hiragana text
        hiragana = ''.join(item['hira'] for item in result)
        if len(hiragana) > 0:
            first_mora = hiragana[0]
            last_mora = hiragana[-1]
            last_moras.append(last_mora)
            
            if previous_last_mora is not None:
                matches = first_mora == previous_last_mora
                if not matches and DEBUG:
                    logger.debug(f"[Shiritori] Chain broken at line {i}: {previous_last_mora} ≠ {first_mora}")
                chain_results.append(matches)
            
            previous_last_mora = last_mora
    
    # Check if all links in the chain match
    chain_valid = all(chain_results) if chain_results else False
    if not chain_valid and DEBUG:
        logger.debug("[Shiritori] Chain validation failed: not all links connect properly")
    
    # Check if we have enough links and the specific positions end with required characters
    if len(last_moras) >= 3:
        third_link_valid = last_moras[2] == 'り'  # Third link should end with り
        last_link_valid = last_moras[-1] == 'ん'  # Last link should end with ん
        
        if DEBUG:
            if not third_link_valid:
                logger.debug(f"[Shiritori] Third word should end with 'り', but ends with '{last_moras[2]}'")
            if not last_link_valid:
                logger.debug(f"[Shiritori] Last word should end with 'ん', but ends with '{last_moras[-1]}'")
        
        return chain_valid and third_link_valid and last_link_valid
    
    if DEBUG:
        logger.debug(f"[Shiritori] Not enough valid words: found {len(last_moras)}, need at least 3")
    return False

def NumberSentences(text, prompt=None):
    # Get expected number of sentences from config
    expected_sentences = TASK_CONFIG['NumberSentence']['expected_sentences']
    
    # Japanese sentence ending punctuation (。!?！？)
    jp_sentence_endings = r'[。!?！？]'
    
    # Split the text on sentence endings and filter out empty strings
    sentences = [s.strip() for s in re.split(jp_sentence_endings, text) if s.strip()]
    
    # Return True if the number of sentences matches the expected count
    return len(sentences) == expected_sentences

def HonorificsInversion(text, prompt=None):
    if DEBUG:
        logger.debug(f"[HonorificsInversion] Checking text: '{text}'")
        logger.debug(f"[HonorificsInversion] Against prompt: '{prompt}'")
    
    # Get pairs from config
    pairs = TASK_CONFIG['HonorificsInversion']['pairs']
    
    # Clean up the text (remove extra whitespace and normalize line endings)
    text = text.strip()
    
    # If the text is a key in our pairs, check if the prompt contains the expected value
    if text in pairs:
        if DEBUG:
            logger.debug(f"[HonorificsInversion] Found text as key in pairs")
            logger.debug(f"[HonorificsInversion] Expected value: '{pairs[text]}'")
            logger.debug(f"[HonorificsInversion] Actual prompt: '{prompt}'")
            if pairs[text] != prompt:
                logger.debug("[HonorificsInversion] Mismatch: prompt does not match expected value")
        return pairs[text] == prompt
    
    # If the text is a value in our pairs, check if the prompt contains the matching key
    for key, value in pairs.items():
        if text == value:
            if DEBUG:
                logger.debug(f"[HonorificsInversion] Found text as value in pairs")
                logger.debug(f"[HonorificsInversion] Expected key: '{key}'")
                logger.debug(f"[HonorificsInversion] Actual prompt: '{prompt}'")
                if key != prompt:
                    logger.debug("[HonorificsInversion] Mismatch: prompt does not match expected key")
            return key == prompt
    
    # If we didn't find a match in either direction, return False
    if DEBUG:
        logger.debug("[HonorificsInversion] Text not found in pairs (either as key or value)")
    return False

def JSONFormatting(text, prompt=None):
    # Try to parse the entire text as a single JSON object
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False

def MarkdownFormatting(text, prompt=None):
    # Get config values
    required_headers = TASK_CONFIG['MarkdownFormatting']['required_headers']
    min_pairs = TASK_CONFIG['MarkdownFormatting']['min_pairs']
    
    # Split into lines and remove empty ones
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Track the headers we find
    found_pairs = 0
    last_header = None
    
    for line in lines:
        # Check for h2 (##)
        if line.startswith('## '):
            header_text = line[3:].strip()  # Remove '## ' and whitespace
            if header_text != required_headers['h2']:
                return False
            if last_header == 'h2':  # Can't have two h2s in a row
                return False
            last_header = 'h2'
            
        # Check for h3 (###)
        elif line.startswith('### '):
            header_text = line[4:].strip()  # Remove '### ' and whitespace
            if header_text != required_headers['h3']:
                return False
            if last_header != 'h2':  # h3 must follow h2
                return False
            last_header = 'h3'
            found_pairs += 1
            
        # Non-header lines are allowed between headers
        else:
            continue
    
    # Check if we found enough pairs
    return found_pairs >= min_pairs

def HiraganaOnly(text, prompt=None):
    # Check if empty
    if not text.strip():
        if DEBUG:
            logger.debug("[HiraganaOnly] Text is empty")
        return False
    
    # Check if there are any spaces (words must be space-separated)
    if ' ' not in text:
        if DEBUG:
            logger.debug("[HiraganaOnly] No spaces found between words")
        return False
    
    # Define valid characters:
    # Hiragana: ぁ-ん
    # Punctuation: 。、！？．,
    # Quotes: 「」
    # Space: \s
    valid_pattern = r'^[ぁ-ーん。、！？．,「」\s]+$'
    
    # Check if text contains only valid characters
    if not re.match(valid_pattern, text):
        invalid_chars = set(re.findall(r'[^ぁ-ん。、！？．,「」\s]', text))
        if DEBUG:
            logger.debug(f"[HiraganaOnly] Invalid characters found: {invalid_chars}")
        return False
    
    # Check if there are at least two space-separated words
    words = [w for w in text.split() if w]
    if len(words) < 2:
        if DEBUG:
            logger.debug(f"[HiraganaOnly] Not enough words found: {len(words)}")
        return False
    
    if DEBUG:
        logger.debug("[HiraganaOnly] Text passed all checks")
    return True

def KatakanaOnly(text, prompt=None):
    # Check if empty
    if not text.strip():
        if DEBUG:
            logger.debug("[KatakanaOnly] Text is empty")
        return False
    
    # Check if there are any spaces (words must be space-separated)
    if ' ' not in text:
        if DEBUG:
            logger.debug("[KatakanaOnly] No spaces found between words")
        return False
    
    # Define valid characters:
    # Katakana: ァ-ン
    # Punctuation: 。、！？．,
    # Quotes: 「」
    # Space: \s
    valid_pattern = r'^[ァ-ーン。、！？．,「」\s]+$'
    
    # Check if text contains only valid characters
    if not re.match(valid_pattern, text):
        invalid_chars = set(re.findall(r'[^ァ-ーン。、！？．,「」\s]', text))
        if DEBUG:
            logger.debug(f"[KatakanaOnly] Invalid characters found: {invalid_chars}")
        return False
    
    # Check if there are at least two space-separated words
    words = [w for w in text.split() if w]
    if len(words) < 2:
        if DEBUG:
            logger.debug(f"[KatakanaOnly] Not enough words found: {len(words)}")
        return False
    
    # Check if each word contains at least one katakana
    katakana_pattern = r'[ァ-ン]'
    for word in words:
        if not re.search(katakana_pattern, word):
            if DEBUG:
                logger.debug(f"[KatakanaOnly] Word without katakana found: {word}")
            return False
    
    if DEBUG:
        logger.debug("[KatakanaOnly] Text passed all checks")
    return True

def ForbiddenWords(text, prompt=None):
    # Get forbidden words from config
    forbidden_words = TASK_CONFIG['ForbiddenWords']['words']
    
    # Check each forbidden word
    found_words = []
    for word in forbidden_words:
        if word in text:
            found_words.append(word)
    
    # For debugging, print which forbidden words were found
    if found_words:
        print(f"Found forbidden words: {found_words}")
        
    # Return True only if no forbidden words are found
    return len(found_words) == 0

def TranslationWithNumbersOrCode(text, prompt=None):
    if not prompt:
        return False
        
    # Function to keep only ASCII characters and whitespace
    def keep_ascii_and_whitespace(s):
        # Keep ASCII letters, numbers, punctuation and whitespace
        return ''.join(c for c in s if ord(c) < 128)
    
    # Clean both the prompt and submitted text
    clean_prompt = keep_ascii_and_whitespace(prompt)
    clean_text = keep_ascii_and_whitespace(text)
    
    # Compare the cleaned versions
    return clean_prompt == clean_text

def NumberOfSections(text, prompt=None):
    # Get expected sections and separator from config
    expected = TASK_CONFIG['NumberOfSections']['expected_sections']
    separator = TASK_CONFIG['NumberOfSections']['separator']
    
    # Split text by separator and filter out empty sections
    sections = [s.strip() for s in text.split(separator) if s.strip()]
    
    # Return True if number of sections matches expected
    return len(sections) == expected

def HaikuGeneration(text, prompt=None):
    """Check if text follows 5-7-5 haiku pattern."""
    if DEBUG:
        logger.debug(f"[HaikuGeneration] Checking text:\n{text}")
    
    # Split into lines and remove empty ones
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Check if we have exactly 3 lines
    if len(lines) != 3:
        if DEBUG:
            logger.debug(f"[HaikuGeneration] Invalid number of lines: found {len(lines)}, expected 3")
        return False
    
    if DEBUG:
        logger.debug("[HaikuGeneration] Lines found:")
        for i, line in enumerate(lines, 1):
            logger.debug(f"[HaikuGeneration] Line {i}: {line}")
    
    # Initialize kakasi
    kks = pykakasi.kakasi()
    
    # Small kana that combine with previous character to form a single mora
    small_kana = 'ゃゅょ'
    
    # Count mora in each line
    mora_counts = []
    for i, line in enumerate(lines, 1):
        result = kks.convert(line)
        # Get hiragana and remove small kana before counting
        hiragana = ''.join(item['hira'] for item in result)
        original_len = len(hiragana)
        for char in small_kana:
            hiragana = hiragana.replace(char, '')
        mora_count = len(hiragana)
        mora_counts.append(mora_count)
        
        if DEBUG:
            logger.debug(f"[HaikuGeneration] Line {i} analysis:")
            logger.debug(f"[HaikuGeneration]   Original text: {line}")
            logger.debug(f"[HaikuGeneration]   Hiragana: {hiragana}")
            logger.debug(f"[HaikuGeneration]   Mora count: {mora_count}")
    
    # Check if pattern matches 5-7-5
    expected_pattern = [5, 7, 5]
    pattern_matches = mora_counts == expected_pattern
    
    if DEBUG:
        logger.debug(f"[HaikuGeneration] Mora counts: {mora_counts}")
        logger.debug(f"[HaikuGeneration] Expected pattern: {expected_pattern}")
        if not pattern_matches:
            logger.debug("[HaikuGeneration] Pattern does not match 5-7-5")
    
    return pattern_matches

def KanjiRadicals(text, prompt=None):
    # Initialize Jamdict
    jam = Jamdict()
    
    # Extract all kanji characters from the text
    kanji_pattern = r'[一-龯]'
    kanji_chars = set(re.findall(kanji_pattern, text))
    
    # Check each kanji for water radical
    for kanji in kanji_chars:
        # Use KRADFILE mapping to check for water radical
        radicals = jam.krad.get(kanji, [])
        if '水' not in radicals and '氵' not in radicals:
            return False
    
    # Make sure we found at least one kanji
    return len(kanji_chars) > 0

def CounterTask(text, prompt=None):
    # Get required counters from config
    required_counters = TASK_CONFIG['CounterTask']['required_counters']
    
    # Check each counter
    found_counters = []
    for counter in required_counters:
        if counter in text:
            found_counters.append(counter)
    
    # For debugging, print which counters were found/missing
    missing_counters = set(required_counters) - set(found_counters)
    if missing_counters:
        return False
    
    # Return True only if all required counters are found
    return len(found_counters) == len(required_counters)

def PunctuationUse(text, prompt=None):
    # Get required punctuation counts from config
    required_counts = TASK_CONFIG['PunctuationUse']['required_counts']
    
    # Count actual occurrences
    actual_counts = {}
    for punct, required_count in required_counts.items():
        if punct == "「」":
            # For paired punctuation, count pairs
            open_count = text.count("「")
            close_count = text.count("」")
            actual_counts[punct] = min(open_count, close_count)  # pairs must match
        else:
            actual_counts[punct] = text.count(punct)
    
    # Check if any counts don't match requirements
    for punct, required_count in required_counts.items():
        if actual_counts[punct] != required_count:
            return False
    
    return True

def NumberOfPlaceholders(text, prompt=None):
    # Get minimum required placeholders from config
    min_placeholders = TASK_CONFIG['NumberOfPlaceholders']['min_placeholders']
    
    # Find all placeholders using regex (matches text within square brackets)
    placeholders = re.findall(r'\[([^\]]+)\]', text)
    
    # Return True if we have at least the minimum number of placeholders
    return len(placeholders) >= min_placeholders

def FuriganaRewrite(text, prompt=None):
    """Check if both required answers are present in the text."""
    # Get expected answers from config
    expected_answers = TASK_CONFIG['FuriganaRewrite']['expected_answers']
    
    # Check if all expected answers are in the text
    return all(answer in text for answer in expected_answers)

def ForbiddenParticle(text, prompt=None):
    # Get config values
    forbidden = TASK_CONFIG['ForbiddenParticle']['forbidden_particle']
    min_length = TASK_CONFIG['ForbiddenParticle']['min_length']
    
    # Check text length
    if len(text) < min_length:
        return False
    
    # Check for forbidden particle
    if forbidden in text:
        return False
    
    return True

def MatchingMora(text, prompt=None):
    # Initialize kakasi
    kks = pykakasi.kakasi()
    
    # Split into sentences and remove empty ones
    sentences = [s.strip() for s in text.split('。') if s.strip()]
    
    # Check if we have exactly 3 sentences
    if len(sentences) != 3:
        return False
    
    # For each sentence
    for sentence in sentences:
        # Split into words (assuming space separation)
        words = [w for w in sentence.split() if w]
        if not words:
            return False
        
        # Convert each word to hiragana
        word_readings = []
        for word in words:
            result = kks.convert(word)
            reading = result[0]['hira']  # Get hiragana reading
            word_readings.append(reading)
            
        # Get first character of first word's reading
        first_char = word_readings[0][0]
        
        # Check if first character is katakana (not allowed)
        if re.match(r'[ァ-ン]', first_char):
            return False
            
        # Check if all words start with the same character in hiragana
        for reading in word_readings:
            if not reading.startswith(first_char):
                return False
        
        # Convert whole sentence to hiragana for end character check
        sentence_reading = ''.join(kks.convert(sentence.strip())[0]['hira'])
        if first_char != sentence_reading[-1]:
            print(sentence)
            print(f"First char: {first_char}, Last char: {sentence_reading[-1]}")
            return False
    
    return True

def DifferentResponses(text, prompt=None):
    # Split by exactly 6 asterisks
    responses = text.split('******')
    
    # We need exactly 2 non-empty responses
    responses = [r.strip() for r in responses]
    responses = [r for r in responses if r]  # Remove empty responses
    
    if len(responses) != 2:
        return False
    
    # Responses should be different
    if responses[0] == responses[1]:
        return False
    
    return True

def KanjiCounter(text, prompt=None):
    # Get target kanji and required count from config
    target_kanji = TASK_CONFIG['KanjiCounter']['target_kanji']
    required_count = TASK_CONFIG['KanjiCounter']['required_count']
    
    # Count occurrences of the target kanji
    actual_count = text.count(target_kanji)
    
    # Return True only if the count matches exactly
    return actual_count == required_count

def CountHiragana(text, prompt=None):
    """Check if the text contains the correct count of hiragana characters."""
    # Get expected count from config
    expected_count = TASK_CONFIG['CountHiragana']['expected_count']
    
    try:
        # Try to parse the text as a number
        actual_count = int(text.strip())
        return actual_count == expected_count
    except ValueError:
        # If the text can't be parsed as a number, return False
        return False

def CountMora(text, prompt=None):
    """Check if the text contains the correct count of mora."""
    # Get expected count from config
    expected_count = TASK_CONFIG['CountMora']['expected_count']
    
    try:
        # Try to parse the text as a number
        actual_count = int(text.strip())
        return actual_count == expected_count
    except ValueError:
        # If the text can't be parsed as a number, return False
        return False

def ForbiddenParticle(text, prompt=None):
    # Get config values
    forbidden = TASK_CONFIG['ForbiddenParticle']['forbidden_particle']
    min_length = TASK_CONFIG['ForbiddenParticle']['min_length']
    
    # Check text length
    if len(text) < min_length:
        return False
    
    # Check for forbidden particle
    if forbidden in text:
        return False
    
    return True

def DifferentFirstPersonPronouns(text, prompt=None):
    """Check if the text contains the required number of different first person pronouns."""
    # Get config values
    pronouns = TASK_CONFIG['DifferentFirstPersonPronouns']['pronouns']
    required_count = TASK_CONFIG['DifferentFirstPersonPronouns']['required_count']
    
    # Split on newlines and Japanese sentence endings
    lines = re.split(r'[\n。！？]', text)
    
    # Keep track of which pronouns we've found
    found_pronouns = set()
    
    # For each line/sentence
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Check each pronoun
        for pronoun in pronouns:
            if pronoun in line:
                found_pronouns.add(pronoun)
    
    # Return True if we found enough different pronouns
    return len(found_pronouns) >= required_count

def DifferentSecondPersonPronouns(text, prompt=None):
    """Check if the text contains the required number of different second person pronouns."""
    # Get config values
    pronouns = TASK_CONFIG['DifferentSecondPersonPronouns']['pronouns']
    required_count = TASK_CONFIG['DifferentSecondPersonPronouns']['required_count']
    
    # Split on newlines and Japanese sentence endings
    lines = re.split(r'[\n。！？]', text)
    
    # Keep track of which pronouns we've found
    found_pronouns = set()
    
    # For each line/sentence
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Check each pronoun
        for pronoun in pronouns:
            if pronoun in line:
                found_pronouns.add(pronoun)
    
    # Return True if we found enough different pronouns
    return len(found_pronouns) >= required_count

def RemoveHiragana(text, prompt=None):
    if DEBUG:
        logger.debug(f"[RemoveHiragana] Checking text:\n{text}")
    
    # Find all hiragana characters in the text
    hiragana_chars = [char for char in text if '\u3040' <= char <= '\u309F']
    
    if DEBUG and hiragana_chars:
        logger.debug("[RemoveHiragana] Found hiragana characters:")
        logger.debug(f"[RemoveHiragana] {' '.join(hiragana_chars)}")
    
    # Remove all hiragana characters while preserving everything else
    # Hiragana range in Unicode: U+3040 to U+309F
    result = ''.join(char for char in text if not ('\u3040' <= char <= '\u309F'))
    
    if DEBUG:
        if result != text:
            logger.debug("[RemoveHiragana] Text contains hiragana - validation failed")
        else:
            logger.debug("[RemoveHiragana] No hiragana found - validation passed")
    
    # Return True if no hiragana was removed (i.e., result equals original text)
    return result == text

def SeasonalWords(text, prompt=None):
    # Get required count from config
    required_count = TASK_CONFIG['SeasonalWords']['required_count']
    
    # Load kigo from file
    try:
        with open('kigo.txt', 'r', encoding='utf-8') as f:
            kigo_list = f.read().strip().split()
    except FileNotFoundError:
        print("Warning: kigo.txt not found")
        return False
    
    # Find all kigo in the text
    found_kigo = set()
    for kigo in kigo_list:
        if kigo in text:
            found_kigo.add(kigo)
    
    # Return True if we found at least the required number of kigo
    return len(found_kigo) >= required_count

def CharacterMinimum(text, prompt=None):
    # Get min_length from config
    min_length = TASK_CONFIG['CharacterMinimum']['min_length']
    
    if DEBUG:
        logger.debug(f"[CharacterMinimum] Required minimum length: {min_length}")
        logger.debug(f"[CharacterMinimum] Actual length: {len(text)}")
        
    return len(text) >= min_length

# Map of function names to actual functions
FUNCTION_MAP = {
    # Implemented functions
    'NoKatakana': NoKatakana,
    'CharacterLimit': CharacterLimit,
    'CharacterMinimum': CharacterMinimum,
    'KeywordFrequency': KeywordFrequency,
    'RepeatPrompt': RepeatPrompt,
    'Shiritori': Shiritori,
    'NumberSentences': NumberSentences,
    'JSONFormatting': JSONFormatting,
    'HiraganaOnly': HiraganaOnly,
    'KatakanaOnly': KatakanaOnly,
    'ForbiddenWords': ForbiddenWords,
    'NumberOfSections': NumberOfSections,
    'HaikuGeneration': HaikuGeneration,
    'KanjiRadicals': KanjiRadicals,
    'CounterTask': CounterTask,
    'Counter Task': CounterTask, #Needed because of a bug in earlier versions.
    'PunctuationUse': PunctuationUse,
    'NumberOfPlaceholders': NumberOfPlaceholders,
    'FuriganaRewrite': FuriganaRewrite,
    'ForbiddenParticle': ForbiddenParticle,
    'MatchingMora': MatchingMora,
    'DifferentResponses': DifferentResponses,
    'KanjiCounter': KanjiCounter,
    'CountHiragana': CountHiragana,
    'CountMora': CountMora,
    'DifferentFirstPersonPronouns': DifferentFirstPersonPronouns,
    'DifferentSecondPersonPronouns': DifferentSecondPersonPronouns,
    'RemoveHiragana': RemoveHiragana,
    'SeasonalWords': SeasonalWords,
    'TranslationWithNumbersOrCode': TranslationWithNumbersOrCode,
    'MarkdownFormatting': MarkdownFormatting,
    'HonorificsInversion': HonorificsInversion
}

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--debug', is_flag=True, help='Enable debug output')
def main(input_file, debug):
    set_debug(debug)
    total = 0
    passed = 0
    
    # Create results directory if it doesn't exist
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Create output CSV filename in results directory
    input_basename = os.path.basename(input_file)
    output_csv = os.path.join(results_dir, os.path.splitext(input_basename)[0] + '_results.csv')
    output_scores = os.path.join(results_dir, os.path.splitext(input_basename)[0] + '_scores.jsonl')
    
    # Keep track of test results
    test_results = []
    
    with open(input_file, 'r') as f, open(output_csv, 'w', newline='') as csvfile:
        # Create CSV writer and write headers
        writer = csv.writer(csvfile)
        writer.writerow(['Task Type', 'Processed Output', 'Passed Test'])
        
        for line in f:
            data = json.loads(line)
            
            # Process the output first
            try:
                processed_output = process_output(data['response']['output'])
            except:
                processed_output = ""
            
            # Get the function name from task_type and call it
            func_name = data.get('task_type', '')
            if func_name in FUNCTION_MAP:
                total += 1
                # Check if processed_output is empty and fail immediately if so
                if len(processed_output.strip()) == 0:
                    result = False
                else:
                    result = FUNCTION_MAP[func_name](processed_output, data.get('prompt', ''))
                if result:
                    passed += 1
                print(f"Result for {func_name}: {result}")
                
                # Keep track of test result
                test_results.append({
                    "task": func_name,
                    "passed": result
                })
                
                # Write to CSV
                writer.writerow([func_name, processed_output, str(result)])
            else:
                print(f"Error: Function {func_name} not found in function map")
                # Write error to CSV
                writer.writerow([func_name, processed_output, 'ERROR - Function not found'])
    
    if total > 0:
        print(f"\nPassed {passed}/{total} ({(passed/total)*100:.1f}%)")
        print(f"Results have been saved to: {output_csv}")
        
        # Save scores to JSONL
        with open(output_scores, 'w') as f:
            # Write summary first
            json.dump({
                "total_score": {
                    "passed": passed,
                    "total": total,
                    "percentage": round((passed/total)*100, 1)
                }
            }, f)
            f.write('\n')
            # Write individual test results
            for result in test_results:
                json.dump(result, f)
                f.write('\n')
        print(f"Scores have been saved to: {output_scores}")

if __name__ == '__main__':
    main()
