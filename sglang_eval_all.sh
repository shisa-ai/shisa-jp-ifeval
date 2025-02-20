#!/bin/bash

# Clear output and results directories
rm -rf output/* results/*

# Array of models to evaluate
declare -a models=(
    "shisa-ai/Llama-3.1-Tulu-3-405B-FP8-Dynamic"
    "allenai/Llama-3.1-Tulu-3-8B"
    "tokyotech-llm/Llama-3.1-Swallow-70B-Instruct-v0.3"
    "allenai/Llama-3.1-Tulu-3-70B"
    "Nexusflow/Athene-V2-Chat"
    "meta-llama/Llama-3.3-70B-Instruct"
)

# Run evaluations for each model
for model in "${models[@]}"; do
    echo "Running evaluation for $model"
    MODEL="$model" sbatch --wait run_shisa-jp-ifeval-litellm_sglang.slurm # Run one at a time because of an sqlite database locking error that happens when models are loaded too close together...
done

echo "All evaluation jobs submitted!"
