from sudachipy import tokenizer
from sudachipy import dictionary

# Initialize tokenizer
tokenizer_obj = dictionary.Dictionary().create()

# Analyze a word
tokens = tokenizer_obj.tokenize('ん')

# Check if it's recognized as a valid word
for token in tokens:
    print(f"Found word: {token.surface()}")
    print(f"Dictionary form: {token.dictionary_form()}")
    print(f"Part of speech: {token.part_of_speech()}")