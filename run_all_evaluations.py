#!/usr/bin/env python3
import os
import glob
import subprocess
import pandas as pd
import json
from pathlib import Path

def run_evaluation(jsonl_file):
    """Run the evaluation script on a single jsonl file."""
    script_path = os.path.join(os.path.dirname(__file__), 'shisa-jp-if-eval-judge.py')
    try:
        subprocess.run(['python', script_path, jsonl_file], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {jsonl_file}: {e}")
        return False

def create_wide_format_results(results_dir):
    """Create a wide format dataframe where each row is a task and columns are model outputs/results."""
    # Get all CSV files
    csv_files = glob.glob(os.path.join(results_dir, '*_results.csv'))
    
    # Dictionary to store all results
    all_results = {}
    
    # Process each CSV file
    for csv_file in csv_files:
        model_name = os.path.basename(csv_file).replace('_results.csv', '')
        df = pd.read_csv(csv_file)
        
        # For each task in this file
        for _, row in df.iterrows():
            task_type = row['Task Type']
            if task_type not in all_results:
                all_results[task_type] = {}
            
            # Store both the output and the result
            all_results[task_type][f"{model_name}_output"] = row['Processed Output']
            all_results[task_type][f"{model_name}_success"] = row['Passed Test']
    
    # Convert to DataFrame
    results_df = pd.DataFrame.from_dict(all_results, orient='index')
    
    # Remove any 'combined' columns if they exist
    combined_cols = [col for col in results_df.columns if 'combined' in col.lower()]
    if combined_cols:
        results_df = results_df.drop(columns=combined_cols)
    
    # Sort index (task names)
    results_df.sort_index(inplace=True)
    
    return results_df

def get_model_scores(results_dir):
    """Get scores for each model from their scores.jsonl files."""
    scores = {}
    score_files = glob.glob(os.path.join(results_dir, '*_scores.jsonl'))
    
    for score_file in score_files:
        model_name = os.path.basename(score_file).replace('_scores.jsonl', '')
        try:
            with open(score_file, 'r') as f:
                # First line contains the total score
                total_score = json.loads(f.readline())
                scores[model_name] = total_score['total_score']
        except Exception as e:
            print(f"Error reading scores for {model_name}: {e}")
            continue
    
    return scores

def main():
    # Get the base directory (where this script is located)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'output')
    results_dir = os.path.join(base_dir, 'results')
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    # Find all jsonl files in the output directory
    jsonl_files = glob.glob(os.path.join(output_dir, '*.jsonl'))
    
    if not jsonl_files:
        print(f"No .jsonl files found in {output_dir}")
        return
    
    print(f"Found {len(jsonl_files)} .jsonl files to process")
    
    # Process each jsonl file
    for jsonl_file in jsonl_files:
        print(f"\nProcessing {os.path.basename(jsonl_file)}...")
        run_evaluation(jsonl_file)
    
    # Create wide format results
    print("\nCombining results...")
    combined_df = create_wide_format_results(results_dir)
    
    if combined_df.empty:
        print("No results files found!")
        return
    
    # Save the combined results to base directory
    combined_output = os.path.join(base_dir, 'combined_results.csv')
    combined_df.to_csv(combined_output)
    print(f"\nAll results have been combined in: {combined_output}")
    
    # Get and print scores from JSONL files
    print("\nScores by model:")
    scores = get_model_scores(results_dir)
    for model, score in scores.items():
        print(f"{model}: {score['percentage']}% ({score['passed']}/{score['total']} tasks)")

if __name__ == '__main__':
    main()
