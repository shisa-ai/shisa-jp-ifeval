import os
import json
import pandas as pd
import click
from datasets import load_dataset
from loguru import logger
from helpers.llmcaller.litellm_caller import LiteLLMCaller
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

def process_single_item(item: Dict[str, Any], llm: LiteLLMCaller, temperature: float) -> Dict[str, Any]:
    try:
        prompt = item['prompt']
        response = llm.call(
            prompt=prompt,
            temperature=temperature,
            max_tokens=8092
        )
        result = {
            'guid': item['guid'],
            'prompt': prompt,
            'task_type': item['task_type'],
            'response': response
        }
        logger.info(f"Processed item {item['guid']}")
        return result
    except Exception as e:
        logger.error(f"Error processing item {item['guid']}: {str(e)}")
        return None

def process_dataset(model: str, api_base: str, temperature: float, commercial_model: bool = False, max_workers: int = 4):
    """Process the dataset by sending prompts to the LLM using multiple threads."""
    dataset = load_dataset("shisa-ai/shisa-jp-if-eval", split="train")
    
    if not commercial_model:
        model = "hosted_vllm/" + model
    logger.info(f"Accessing model {model}")
    llm = LiteLLMCaller(model=model, api_base=api_base)
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(process_single_item, item, llm, temperature): item 
            for item in dataset
        }
        
        for future in as_completed(future_to_item):
            result = future.result()
            if result is not None:
                results.append(result)
    
    return results

@click.command()
@click.option('--model', required=True, help='Model name')
@click.option('--api-base', required=False, default="", help='API base URL')
@click.option('--max-workers', default=128, help='Number of concurrent threads')
@click.option('--commercial-model', is_flag=True, default=False, help='Set to True if using a commercial API like OpenAI or Anthropic')
def main(model: str, api_base: str, max_workers: int, commercial_model: bool):
    """Main function to run the evaluation at multiple temperatures in parallel."""
    logger.info(f"Starting evaluation with model {model} using {max_workers} threads")
    
    temperatures = [0.0, 0.2, 0.5, 0.7, 1.0]
    all_results = []
    
    # Load dataset once
    dataset = load_dataset("shisa-ai/shisa-jp-if-eval", split="train")
    
    # Store original model name for output file
    original_model = model
    
    if not commercial_model:
        model = "hosted_vllm/" + model
    logger.info(f"Accessing model {model}")
    llm = LiteLLMCaller(model=model, api_base=api_base)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create all tasks upfront for all temperatures
        future_to_params = {
            executor.submit(process_single_item, item, llm, temp): (item, temp)
            for temp in temperatures
            for item in dataset
        }
        
        for future in as_completed(future_to_params):
            result = future.result()
            if result is not None:
                result['temperature'] = future_to_params[future][1]
                all_results.append(result)
    
    os.makedirs("output", exist_ok=True)
    # Use original model name for output file
    output_file = f"output/{original_model.replace('/', '__')}_ifeval_output.jsonl"
    
    df = pd.DataFrame(all_results)
    df.to_json(output_file, orient='records', lines=True, force_ascii=False)
    
    logger.info(f"Evaluation complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()
