set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
cd "$PROJECT_ROOT"

"$PYTHON" run_pipeline.py

if [ "$(date +%u)" = "5" ]; then
  "$PYTHON" weekly_report.py --send
fi