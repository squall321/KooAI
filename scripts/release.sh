#!/bin/bash
set -e

VERSION=$1

if [ -z "$VERSION" ]; then
  echo "Usage: $0 v1.2.3"
  exit 1
fi

echo "Creating release $VERSION"

git tag -a "$VERSION" -m "Release $VERSION"
git push origin "$VERSION"

echo "✅ Release $VERSION created!"
