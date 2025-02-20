import click
import pandas as pd
from datasets import Dataset
from huggingface_hub import HfApi
import uuid
import os

PROMPT_TEMPLATE = """以下の質問に答えてください。答えは必ず<answer>タグで囲んでください
<question>{}</question>"""

@click.command()
@click.argument('csv_path', type=click.Path(exists=True))
def main(csv_path):
    """Process CSV file and create HuggingFace dataset."""
    # Read CSV file
    df = pd.read_csv(csv_path)
    
    # Print first row for verification
    print("First row of the CSV:")
    print(df.iloc[0].to_dict())
    
    # Get the source filename without extension
    source = os.path.splitext(os.path.basename(csv_path))[0]
    
    # Create dataset entries
    dataset_dict = {
        'guid': [],
        'source': [],
        'prompt': [],
        'task_type': [],
    }
    
    # Process each row
    for _, row in df.iterrows():
        dataset_dict['guid'].append(str(uuid.uuid4()))
        dataset_dict['source'].append(source)
        dataset_dict['prompt'].append(PROMPT_TEMPLATE.format(row['question']))
        dataset_dict['task_type'].append(row['task_type'])
    
    # Create HuggingFace dataset
    dataset = Dataset.from_dict(dataset_dict)
    
    # Push to hub
    dataset.push_to_hub("shisa-ai/shisa-jp-if-eval", private=True)
    
    print(f"Successfully processed {len(dataset)} entries and uploaded to HuggingFace")

if __name__ == '__main__':
    main()