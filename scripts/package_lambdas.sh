#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"

echo "=== Packaging Lambda Functions ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

zip_dir() {
    local src_dir="$1"
    local dest_zip="$2"
    if command -v zip &> /dev/null; then
        (cd "$src_dir" && zip -r -q "$dest_zip" .)
    elif command -v python &> /dev/null; then
        python -c "import os, sys, zipfile; z=sys.argv[1]; s=sys.argv[2]; f=zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED); [f.write(os.path.join(r, fn), os.path.relpath(os.path.join(r, fn), s)) for r, d, fs in os.walk(s) for fn in fs]; f.close()" "$dest_zip" "$src_dir"
    elif command -v python3 &> /dev/null; then
        python3 -c "import os, sys, zipfile; z=sys.argv[1]; s=sys.argv[2]; f=zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED); [f.write(os.path.join(r, fn), os.path.relpath(os.path.join(r, fn), s)) for r, d, fs in os.walk(s) for fn in fs]; f.close()" "$dest_zip" "$src_dir"
    else
        echo "ERROR: Neither 'zip' nor 'python' command was found." >&2
        exit 1
    fi
}

# Package 1: ingest_sensor_data.zip
TEMP_INGEST="$BUILD_DIR/temp_ingest"
mkdir -p "$TEMP_INGEST/shared"
cp "$ROOT_DIR/backend/ingest_sensor_data/app.py" "$TEMP_INGEST/"
cp "$ROOT_DIR/backend/shared/"*.py "$TEMP_INGEST/shared/"

zip_dir "$TEMP_INGEST" "$BUILD_DIR/ingest_sensor_data.zip"
rm -rf "$TEMP_INGEST"
echo "Created $BUILD_DIR/ingest_sensor_data.zip"

# Package 2: dashboard_api.zip
TEMP_API="$BUILD_DIR/temp_api"
mkdir -p "$TEMP_API/shared"
cp "$ROOT_DIR/backend/dashboard_api/app.py" "$TEMP_API/"
cp "$ROOT_DIR/backend/shared/"*.py "$TEMP_API/shared/"

zip_dir "$TEMP_API" "$BUILD_DIR/dashboard_api.zip"
rm -rf "$TEMP_API"
echo "Created $BUILD_DIR/dashboard_api.zip"

echo "=== Packaging Complete ==="
