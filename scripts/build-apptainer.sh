#!/bin/bash
set -e

echo "================================"
echo "  Apptainer Image Builder"
echo "================================"

PROFILE="${1:-standard}"

case $PROFILE in
  minimal)
    DEF_FILE="containers/kooai-minimal.def"
    OUTPUT_FILE="kooai-minimal.sif"
    ;;
  standard)
    DEF_FILE="containers/kooai.def"
    OUTPUT_FILE="kooai-standard.sif"
    ;;
  full)
    DEF_FILE="containers/kooai-full.def"
    OUTPUT_FILE="kooai-full.sif"
    ;;
  *)
    echo "Unknown profile: $PROFILE"
    echo "Usage: $0 [minimal|standard|full]"
    exit 1
    ;;
esac

echo "Building $PROFILE image..."
echo "Definition file: $DEF_FILE"
echo "Output file: $OUTPUT_FILE"

sudo apptainer build --fakeroot "$OUTPUT_FILE" "$DEF_FILE"

echo "Build complete!"
ls -lh "$OUTPUT_FILE"

echo "Testing image..."
apptainer exec "$OUTPUT_FILE" python --version

echo "✅ Image built and tested successfully!"
