#!/bin/bash

# Check if MODEL and OPENAI_URL environment variables are set
if [ -z "$MODEL" ]; then
    echo "Error: MODEL environment variable is not set"
    exit 1
fi

if [ -z "$OPENAI_URL" ]; then
    echo "Error: OPENAI_URL environment variable is not set"
    exit 1
fi

echo "Running evaluation for model: $MODEL"
echo "Using API base URL: $OPENAI_URL"

# Step 1: Run the LLM querying
echo "Step 1: Querying LLM..."
python shisa-jp-ifeval-ask-llm.py --model "$MODEL" --api-base "$OPENAI_URL"

# Check if the LLM querying was successful
if [ $? -ne 0 ]; then
    echo "Error: LLM querying failed"
    exit 1
fi

# Get the output file name (matches the pattern in ask-llm.py)
# Replace / with __ in model name to match Python's sanitization
SAFE_MODEL=${MODEL//\//__}
OUTPUT_FILE="output/results_hosted_vllm__${SAFE_MODEL}_ifeval_output.jsonl"

# Check if the output file exists
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Output file $OUTPUT_FILE not found"
    exit 1
fi

# Step 2: Run the evaluation
echo "Step 2: Running evaluation..."
python shisa-jp-ifeval-judge.py "$OUTPUT_FILE"

# Check if the evaluation was successful
if [ $? -ne 0 ]; then
    echo "Error: Evaluation failed"
    exit 1
fi

echo "Evaluation complete!"
echo "Results can be found in:"
echo "- Detailed results: results/results_hosted_vllm__${SAFE_MODEL}_ifeval_output_results.csv"
echo "- Scores: results/results_hosted_vllm__${SAFE_MODEL}_ifeval_output_scores.jsonl"
