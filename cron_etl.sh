#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
cd "$PROJECT_ROOT"

"$PYTHON" run_pipeline.py

# Friday's 8 PM run can also send the weekly HTML summary when SMTP_* variables are configured.
if [ "$(date +%u)" = "5" ]; then
  "$PYTHON" weekly_report.py --send
fi