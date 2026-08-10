#!/bin/bash

cd ~/follyizer

source .venv/bin/activate

exec python -m follyizer.app --config config.yaml
