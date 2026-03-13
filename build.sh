#!/usr/bin/env bash
set -e

pip install -r requirements.txt
export PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.playwright-browsers
playwright install chromium
