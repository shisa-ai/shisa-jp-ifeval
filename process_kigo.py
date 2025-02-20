#!/usr/bin/env python3

def process_kigo_file(input_file, output_file):
    kigo_set = set()
    is_content = False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Check if this is a section header
            if line.startswith('【'):
                is_content = True
                continue
            
            # Skip empty lines or if we haven't found a section yet
            if not line or not is_content:
                continue
            
            # Remove parenthetical content
            while '(' in line and ')' in line:
                start = line.find('(')
                end = line.find(')')
                if start < end:
                    line = line[:start] + line[end + 1:]
                else:
                    break
            
            # Split by space and add to set
            words = line.split()
            kigo_set.update(words)
    
    # Write the processed kigo to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(' '.join(sorted(kigo_set)))

if __name__ == '__main__':
    process_kigo_file('kigo_raw.txt', 'kigo.txt')
