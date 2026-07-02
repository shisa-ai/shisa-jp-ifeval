# Shisa Japanese IF Evaluation

This repository contains tools for evaluating LLM responses on Japanese language tasks.

## Getting Started

### Quick Start

The easiest way to run the evaluation is using the provided shell script:

```bash
MODEL="your-model-name" OPENAI_URL="http://your-api-endpoint/v1" ./run_shisa_jp_ifeval_bench.sh
```

Example:
```bash
MODEL="Nexusflow/Athene-V2-Chat" OPENAI_URL="http://athenev2/v1"  ./run_shisa_jp_ifeval_bench.sh
```


This will:
1. Generate responses from your model
2. Evaluate the responses
3. Save results in both CSV and JSONL formats

### Manual Execution

If you need more control, you can run the individual components:

#### 1. Generating LLM Responses

To generate responses against an OpenAI-compatible endpoint:

```bash
python shisa-jp-ifeval-ask-llm.py --model MODEL [--api-base API_BASE] [--max-workers N] [--commercial-model]
```

Arguments:
- `--model`: (Required) Name of the model to use (must match what your endpoint returns from `/v1/models`)
- `--api-base`: Base URL for the API endpoint (default: "")
- `--max-workers`: Number of concurrent threads (default: 30)
- `--commercial-model`: Flag to indicate use of commercial APIs (default: False, used only for logging/warnings)

Note: The script no longer rewrites model names or adds a `hosted_vllm/` prefix automatically. If you are talking to a router that expects a prefix (e.g. `hosted_vllm/your-model`), pass that full identifier via `--model`. For local vLLM servers, use the exact model id shown by `/v1/models` (for example, `shisa-ai/175-llama3.3-70b-v2.1-dpo`).

The responses will be saved to `output/{model}_ifeval_output.jsonl`

#### 2. Evaluating Responses

To evaluate a single model's responses:

```bash
python shisa-jp-ifeval-judge.py INPUT_FILE [--debug]
```

Arguments:
- `INPUT_FILE`: Path to the JSONL file containing model responses
- `--debug`: Enable debug output

Results will be saved to:
- `results/{model}_ifeval_output_results.csv`: Detailed results with all responses
- `results/{model}_ifeval_output_scores.jsonl`: Summary scores and per-task results

#### 3. Combining Multiple Evaluations

To generate a combined table of results from multiple models:

```bash
python run_all_evaluations.py
```

This will:
1. Process all JSONL files in the `output` directory
2. Create a combined CSV with all model results
3. Show success rates for each model
