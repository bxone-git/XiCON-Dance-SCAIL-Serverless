#!/bin/bash
set -e

echo "=========================================="
echo "Container startup (RTX 5090 + SageAttention2++) - $(date)"
echo "=========================================="

# SageAttention ENABLED for RTX 5090 (SM120)
export SAGEATTENTION_ENABLED=1
echo "SageAttention: ENABLED (RTX 5090 SM120 - SageAttention2++ kernels)"

echo "Starting ComfyUI with SageAttention2++ (RTX 5090 optimized)..."
python /ComfyUI/main.py --listen --use-sage-attention &

echo "Waiting for ComfyUI to be ready..."
max_wait=180
wait_count=0
while [ $wait_count -lt $max_wait ]; do
    if curl -s http://127.0.0.1:8188/ > /dev/null 2>&1; then
        echo "ComfyUI is ready!"
        break
    fi
    echo "Waiting for ComfyUI... ($wait_count/$max_wait)"
    sleep 2
    wait_count=$((wait_count + 2))
done

if [ $wait_count -ge $max_wait ]; then
    echo "Error: ComfyUI failed to start within $max_wait seconds"
    exit 1
fi

echo "Starting the handler..."
exec python handler.py
