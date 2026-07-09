#!/usr/bin/env bash
# Run all MASt3R / surface reconstruction sweep configs sequentially.
#
# Usage (from repo root):
#   bash scripts/run_recon_sweep.sh
#
# Each config writes to RESULTS/<sample_name>/<run_name>/ (see vision.output.run_name).
# Logs are saved under logs/recon_sweep/<config_stem>.log

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CONFIG_DIR="configs/recon_sweep"
LOG_DIR="logs/recon_sweep"
mkdir -p "$LOG_DIR"

# Regenerate after editing default.yaml or adding variants:
#   python scripts/generate_recon_sweep_configs.py
mapfile -t configs < <(find "$CONFIG_DIR" -maxdepth 1 -name '*.yaml' -type f | sort)
if ((${#configs[@]} == 0)); then
  echo "No configs found in $CONFIG_DIR. Run: python scripts/generate_recon_sweep_configs.py" >&2
  exit 1
fi

echo "Starting reconstruction sweep (${#configs[@]} configs)"
echo "Repo: $REPO_ROOT"
echo "Logs: $LOG_DIR"
echo

for cfg in "${configs[@]}"; do
  stem="$(basename "$cfg" .yaml)"
  log_file="$LOG_DIR/${stem}.log"

  echo "======================================================================"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running: $cfg"
  echo "Log: $log_file"
  echo "======================================================================"

  if uv run spectra recon -c "$cfg" 2>&1 | tee "$log_file"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] OK: $cfg"
  else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAILED: $cfg (see $log_file)" >&2
    exit 1
  fi
  echo
done

echo "Sweep complete. Compare meshes under RESULTS/SAMPLE1/recon_sweep_*/surface_mesh.ply"
