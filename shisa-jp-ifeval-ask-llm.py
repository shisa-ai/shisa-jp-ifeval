import os
import json
import pandas as pd
import click
from datasets import load_dataset
from loguru import logger
from helpers.llmcaller.litellm_caller import LiteLLMCaller
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any

def process_single_item(item: Dict[str, Any], llm: LiteLLMCaller, temperature: float, max_tokens: int) -> Dict[str, Any]:
    try:
        prompt = item['prompt']
        response = llm.call(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
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

def is_openai_model(model_name: str) -> bool:
    """Heuristic to detect hosted/commercial API models based on their name."""
    openai_prefixes = [
        "gpt-",
        "text-davinci-",
        "davinci",
        "curie",
        "babbage",
        "ada",
        "whisper",
        "claude",
        "text-embedding",
        "openai/",
        "openai:",
        # Treat Gemini models as “commercial” APIs so we expect a
        # hosted endpoint + API key.
        "gemini",
    ]
    return any(model_name.startswith(prefix) for prefix in openai_prefixes)

@click.command()
@click.option('--model', required=True, help='Model name')
@click.option('--api-base', required=False, default="", help='API base URL')
@click.option('--api-key', required=False, default=None, help='API key (or set OPENAI_API_KEY environment variable)')
@click.option('--max-workers', default=128, help='Number of concurrent threads')
@click.option('--max-tokens', default=4096, help='Maximum number of tokens for model responses')
@click.option('--commercial-model', is_flag=True, default=False, help='Set to True if using a commercial API (overrides auto-detection)')
def main(model: str, api_base: str, api_key: str, max_workers: int, max_tokens: int, commercial_model: bool):
    """Main function to run the evaluation at multiple temperatures in parallel."""
    logger.info(f"Starting evaluation with model {model} using {max_workers} threads")

    temperatures = [0.0, 0.2, 0.5, 0.7, 1.0]
    all_results = []

    # Load dataset once
    dataset = load_dataset("shisa-ai/shisa-jp-if-eval", split="train")

    # Store original model name for output file
    original_model = model

    # Auto-detect if it's a commercial/hosted API model (unless explicitly specified).
    # We no longer rewrite model names for local endpoints; callers should pass the
    # exact model identifier exposed by their OpenAI-compatible server.
    is_commercial = commercial_model or is_openai_model(model)

    logger.info(f"Accessing model {model} (Commercial API: {'Yes' if is_commercial else 'No'})")
    
    # Use API key if provided or from environment
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if is_commercial and not api_key and "OPENAI_API_KEY" not in os.environ:
        logger.warning("Using commercial model but no API key provided. Ensure it's set in the environment or authentication may fail.")
    
    llm = LiteLLMCaller(model=model, api_base=api_base, api_key=api_key)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create all tasks upfront for all temperatures
        futures = []
        for temp in temperatures:
            for item in dataset:
                # Submit with initial max_tokens
                future = executor.submit(process_single_item, item, llm, temp, max_tokens)
                futures.append((future, item, temp))

        for future, item, temp in futures:
            try:
                result = future.result()  # This will raise any exception from the task
                if result is not None:
                    result['temperature'] = temp
                    all_results.append(result)
            except Exception as e:
                # Check if it's a token limit error
                if "exceeds the model's maximum context length" in str(e):
                    logger.info(f"Retrying item {item['guid']} at temperature {temp} with reduced tokens")
                    try:
                        # Directly process with reduced tokens (75% of original max_tokens)
                        reduced_tokens = int(max_tokens * 0.75)
                        result = process_single_item(item, llm, temp, reduced_tokens)
                        if result is not None:
                            result['temperature'] = temp
                            all_results.append(result)
                    except Exception as retry_e:
                        logger.error(f"Failed to process item {item['guid']} at temperature {temp} even with reduced tokens: {str(retry_e)}")
                else:
                    logger.error(f"Failed to process item {item['guid']} at temperature {temp}: {str(e)}")

    os.makedirs("output", exist_ok=True)
    # Use original model name for output file
    output_file = f"output/{original_model.replace('/', '__')}_ifeval_output.jsonl"

    df = pd.DataFrame(all_results)
    df.to_json(output_file, orient='records', lines=True, force_ascii=False)

    logger.info(f"Evaluation complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()
