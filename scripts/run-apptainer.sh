#!/bin/bash
set -e

IMAGE="${1:-kooai-standard.sif}"
PORT="${2:-8000}"
DATA_DIR="${3:-}"

if [ ! -f "$IMAGE" ]; then
  echo "❌ Image not found: $IMAGE"
  echo "Usage: $0 <image.sif> [port] [data_dir]"
  exit 1
fi

echo "🚀 Starting KooAI API with Apptainer..."
echo "Image: $IMAGE"
echo "Port: $PORT"

BIND_OPTS=""
if [ -n "$DATA_DIR" ] && [ -d "$DATA_DIR" ]; then
  echo "Data directory: $DATA_DIR"
  BIND_OPTS="--bind $DATA_DIR:/data"
fi

apptainer run \
  $BIND_OPTS \
  --env PORT="$PORT" \
  --env LOG_LEVEL="${LOG_LEVEL:-INFO}" \
  "$IMAGE"
