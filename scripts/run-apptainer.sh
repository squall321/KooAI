#!/bin/bash

IMAGE="${1:-kooai-standard.sif}"
PORT="${2:-8000}"

if [ ! -f "$IMAGE" ]; then
  echo "Image not found: $IMAGE"
  exit 1
fi

echo "Starting KooAI API with Apptainer..."
echo "Image: $IMAGE"
echo "Port: $PORT"

apptainer run \
  --bind /data:/data \
  --env PORT="$PORT" \
  "$IMAGE"
