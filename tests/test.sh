#!/bin/bash
set -uo pipefail

cd "$(dirname "$0")/.."

mkdir -p /logs/verifier

echo "Running test suite..."
pytest tests/test_outputs.py -v -rA
rc=$?
if [ "$rc" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
