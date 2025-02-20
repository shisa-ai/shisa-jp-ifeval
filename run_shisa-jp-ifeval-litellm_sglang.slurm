#!/bin/bash
#SBATCH --partition=dev
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:8
#SBATCH --cpus-per-task=96
#SBATCH --mem=209715M
#SBATCH --time=24:00:00
#SBATCH --output=/fsx/ubuntu/_logs/%j-SGLANG-multinode.log

# Default values
MODEL=""
BASE_RESULTS_DIR="/fsx/ubuntu/meti/experiments/06-shisajpeval/logs"
CONFIG_FILE="configs/config.yaml"  # Default config file location

# Parse named arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --model=*)
            MODEL="${1#*=}"
            ;;
        --results-dir=*)
            BASE_RESULTS_DIR="${1#*=}"
            ;;
        --config-file=*)
            CONFIG_FILE="${1#*=}"
            ;;
        *)
            echo "Unknown parameter: $1"
            exit 1
            ;;
    esac
    shift
done

# Validate required arguments
if [ -z "$MODEL" ]; then
    echo "Error: --model parameter is required"
    echo "Usage: sbatch $0 --model=<model_name> [--results-dir=<path>] [--config-file=<path>]"
    exit 1
fi

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    log "Cleaning up (exit code: $exit_code)..."
        
    log "Cleanup complete"
    exit $exit_code
}

# Set up signal handling
trap cleanup EXIT SIGTERM SIGINT

# Create results directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="${BASE_RESULTS_DIR}/${SLURM_JOB_ID}-${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

# Symlink the slurm logs
ln -s "/fsx/ubuntu/_logs/${SLURM_JOB_ID}-SGLANG-multinode.log" "${RESULTS_DIR}/slurm.log"

# Activate mamba environment
source /fsx/ubuntu/miniforge3/etc/profile.d/conda.sh
source /fsx/ubuntu/miniforge3/etc/profile.d/mamba.sh
mamba activate /fsx/ubuntu/miniforge3/envs/sglang

# Change to working directory
cd /fsx/ubuntu/meti/experiments/06-shisajpeval

# Calculate cluster size and parallelism
TOTAL_GPUS=$((SLURM_NNODES * $(nvidia-smi -L | wc -l)))
GPUS_PER_NODE=$(nvidia-smi -L | wc -l)
TENSOR_PARALLEL_SIZE=$TOTAL_GPUS  # Use all GPUs across all nodes for tensor parallel

log "Cluster configuration:"
log "- Total nodes: $SLURM_NNODES"
log "- Total GPUs: $TOTAL_GPUS"
log "- GPUs per node: $GPUS_PER_NODE"
log "- Tensor parallel size: $TENSOR_PARALLEL_SIZE"

# Function to check if SGLANG server is responding
check_server() {
    local host=$1
    local port=$2
    curl -s -f "http://${host}:${port}/v1/models" > /dev/null
    return $?
}
if [ "${SLURM_PROCID}" -eq 0 ]; then
        log "Proceeding with SGLANG startup"
    
    # Start SGLANG server
    log "Starting SGLANG server with tensor parallel size: $TENSOR_PARALLEL_SIZE"
    log "Full SGLANG command:"
    log "sglang serve $MODEL --tensor-parallel-size $TENSOR_PARALLEL_SIZE --gpu-memory-utilization 0.95 --num-scheduler-steps 20 --host 0.0.0.0 --port 8000"
    
    # Create log file for SGLANG output
    SGLANG_LOG="${RESULTS_DIR}/SGLANG_server.log"
    touch "$SGLANG_LOG"
    log "SGLANG logs will be written to: $SGLANG_LOG"
    
    # Start SGLANG with output redirected to log file
    python -m sglang.launch_server --model-path $MODEL --tp $TENSOR_PARALLEL_SIZE --host 0.0.0.0 --port 8000 --trust-remote-code > "$SGLANG_LOG" 2>&1 &
    
    
    SERVER_PID=$!
    log "SGLANG server started with PID: $SERVER_PID"
    
    # Tail the log file in background to show startup progress
    tail -f "$SGLANG_LOG" & 
    TAIL_PID=$!
    
    # Wait for server to be ready with timeout and logging
    log "Waiting for SGLANG server to become ready..."
    server_attempts=0
    max_server_attempts=720  # 1 hour with 5 second sleep
    
    while true; do
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            log "ERROR: SGLANG server process died. Last 20 lines of log:"
            tail -n 20 "$SGLANG_LOG" | sed 's/^/    /'
            kill $TAIL_PID 2>/dev/null  # Stop the log tail
            exit 1
        fi
        
        # Check if server is responding
        if check_server "localhost" 8000; then
            log "SGLANG server is ready!"
            break
        fi
        
        # Check log for loading progress
        if tail -n 1 "$SGLANG_LOG" | grep -q "Loading safetensors checkpoint shards"; then
            PROGRESS=$(tail -n 1 "$SGLANG_LOG" | grep -o "[0-9]\+%" | head -n 1)
            log "Model loading in progress: $PROGRESS"
        fi
        
        server_attempts=$((server_attempts + 1))
        if [ $server_attempts -eq $max_server_attempts ]; then
            log "ERROR: Timeout waiting for SGLANG server. Last 20 lines of log:"
            tail -n 20 "$SGLANG_LOG" | sed 's/^/    /'
            kill $TAIL_PID 2>/dev/null  # Stop the log tail
            exit 1
        fi
        sleep 5
    done
    
    kill $TAIL_PID 2>/dev/null  # Stop the log tail
    log "SGLANG server is ready"
    
    # Run the translation script
    log "Starting translation script"
    python run_shisa-jp-ifeval-litellm.py --model "$MODEL" --api-base "http://localhost:8000/v1" 
    log "Translation script completed successfully."
    # Wait for the server process
    kill $SERVER_PID
    wait $SERVER_PID


else
    # Worker nodes wait for the head node to complete
    wait
fi

log "Job completed"
