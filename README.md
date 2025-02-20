# Shisa Japanese IF Evaluation

This repository contains tools for evaluating LLM responses using LiteLLM.

## Getting Started

### Generating LLM Results

To generate results using LiteLLM, use the following script:

```bash
python run_shisa-jp-ifeval-litellm.py --model MODEL [--api-base API_BASE] [--temperature TEMP] [--max-workers N]
```

Arguments:
- `--model`: (Required) Name of the model to use
- `--api-base`: Base URL for the API endpoint (default: "")
- `--temperature`: Sampling temperature (default: 0.7)
- `--max-workers`: Number of concurrent threads (default: 12)

The results will be saved to the `results` folder.

### Generating Judgements

#### For a Single LLM
```bash
python judge-answers.py INPUT_FILE [--debug]
```

Arguments:
- `INPUT_FILE`: Path to the input file to process
- `--debug`: Enable debug output

#### For All LLMs
To generate judgements for all LLMs and compile them into a table, use:
```bash
python run_all_evaluations.py
