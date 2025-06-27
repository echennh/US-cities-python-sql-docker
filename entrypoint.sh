#!/usr/bin/env bash
set -euo pipefail

echo "👉 Ingesting /data/cities.csv ..."
python -m src.app load \
  --file /data/cities.csv \
  --user loader \
  --pw-file /run/secrets/loader_pw

echo "✅  Ingestion complete."

# hand off to whatever CMD/args were supplied; default is no-op
exec "$@"