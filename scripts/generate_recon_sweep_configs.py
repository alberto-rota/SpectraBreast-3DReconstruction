#!/usr/bin/env python3
"""Generate configs/recon_sweep/*.yaml from configs/default.yaml.

Re-run after editing default.yaml or adding variants below:
    python scripts/generate_recon_sweep_configs.py
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = REPO_ROOT / "configs" / "default.yaml"
OUT_DIR = REPO_ROOT / "configs" / "recon_sweep"

# (filename_stem, run_name_suffix, overrides, description)
VARIANTS: list[tuple[str, str, dict[str, object], str]] = [
    (
        "01_baseline",
        "01_baseline",
        {},
        "Default MASt3R + surface settings (control run).",
    ),
    (
        "02_strict_dense",
        "02_strict_dense",
        {
            "vision.mast3r.dense_conf_thr": 16.0,
            "vision.mast3r.sfm_min_conf_thr": 2.5,
            "vision.mast3r.sfm_matching_conf_thr": 7.0,
            "vision.mast3r.desc_conf_thr": 0.2,
        },
        "Stricter confidence thresholds to drop low-confidence dense points.",
    ),
    (
        "03_fine_voxel",
        "03_fine_voxel",
        {
            "vision.mast3r.voxel_size": 0.001,
            "vision.mast3r.max_points": 3_000_000,
            "vision.mast3r.pixel_tol": 1.0,
        },
        "Finer voxel fusion for sharper geometry (more points).",
    ),
    (
        "04_coarse_smooth",
        "04_coarse_smooth",
        {
            "vision.mast3r.voxel_size": 0.0025,
            "vision.surface.smooth_iters": 3,
            "vision.surface.fill_iters": 4,
            "vision.surface.min_neighbors": 4,
        },
        "Coarser fusion plus heavier surface smoothing and hole filling.",
    ),
    (
        "05_more_sfm_iters",
        "05_more_sfm_iters",
        {
            "vision.mast3r.sfm_niter1": 500,
            "vision.mast3r.sfm_niter2": 500,
            "vision.mast3r.sfm_lr2": 0.005,
            "vision.mast3r.pose_refine_iters": 3,
            "vision.mast3r.dense_refine_iters": 2,
        },
        "Longer SfM optimization and extra pose/dense refinement passes.",
    ),
    (
        "06_smooth_surface",
        "06_smooth_surface",
        {
            "vision.surface.smooth_iters": 4,
            "vision.surface.fill_iters": 3,
            "vision.surface.max_resolution": 1536,
            "vision.mast3r.dense_conf_thr": 14.0,
        },
        "Surface-focused: more smoothing, moderate dense filtering.",
    ),
    (
        "07_loose_dense",
        "07_loose_dense",
        {
            "vision.mast3r.dense_conf_thr": 8.0,
            "vision.mast3r.sfm_min_conf_thr": 1.0,
            "vision.mast3r.sfm_matching_conf_thr": 3.5,
            "vision.mast3r.desc_conf_thr": 0.05,
        },
        "Permissive thresholds — denser cloud, may include more outliers.",
    ),
    (
        "08_fine_strict_combo",
        "08_fine_strict_combo",
        {
            "vision.mast3r.voxel_size": 0.001,
            "vision.mast3r.max_points": 3_000_000,
            "vision.mast3r.pixel_tol": 1.0,
            "vision.mast3r.dense_conf_thr": 16.0,
            "vision.mast3r.sfm_min_conf_thr": 2.5,
            "vision.mast3r.sfm_matching_conf_thr": 7.0,
            "vision.surface.smooth_iters": 2,
        },
        "Fine voxel fusion combined with strict dense filtering.",
    ),
    (
        "09_high_res_surface",
        "09_high_res_surface",
        {
            "vision.surface.max_resolution": 3072,
            "vision.surface.smooth_iters": 2,
            "vision.surface.fill_iters": 2,
            "vision.mast3r.voxel_size": 0.0012,
        },
        "Higher-resolution height field with moderately fine fusion.",
    ),
    (
        "10_low_res_heavy_smooth",
        "10_low_res_heavy_smooth",
        {
            "vision.surface.max_resolution": 1024,
            "vision.surface.smooth_iters": 5,
            "vision.surface.fill_iters": 5,
            "vision.surface.min_neighbors": 5,
            "vision.mast3r.voxel_size": 0.003,
            "vision.mast3r.dense_conf_thr": 15.0,
        },
        "Low-res, heavily smoothed surface — prioritizes clean global shape.",
    ),
    (
        "11_sfm_subsample2",
        "11_sfm_subsample2",
        {
            "vision.mast3r.sfm_subsample": 2,
            "vision.mast3r.neighbor_window": 3,
            "vision.mast3r.sfm_niter1": 400,
            "vision.mast3r.sfm_niter2": 400,
        },
        "Finer SfM subsampling and wider pair window for better alignment.",
    ),
    (
        "12_active_refine",
        "12_active_refine",
        {
            "vision.mast3r.pose_refine_iters": 3,
            "vision.mast3r.pose_refine_lr": 0.01,
            "vision.mast3r.dense_refine_iters": 3,
            "vision.mast3r.dense_refine_lr": 0.01,
            "vision.mast3r.pose_prior_weight": 0.1,
        },
        "Active pose + dense refinement with stronger pose prior.",
    ),
    (
        "13_coarse_strict_combo",
        "13_coarse_strict_combo",
        {
            "vision.mast3r.voxel_size": 0.0025,
            "vision.mast3r.dense_conf_thr": 16.0,
            "vision.mast3r.sfm_min_conf_thr": 2.5,
            "vision.surface.smooth_iters": 2,
            "vision.surface.fill_iters": 3,
        },
        "Coarse denoised fusion + strict filtering + light smoothing.",
    ),
    (
        "14_fixed_grid_fine",
        "14_fixed_grid_fine",
        {
            "vision.surface.grid_step": 0.0008,
            "vision.surface.smooth_iters": 2,
            "vision.mast3r.voxel_size": 0.0012,
            "vision.mast3r.dense_conf_thr": 13.0,
        },
        "Fixed fine grid step instead of auto-estimated step.",
    ),
]


def set_nested(d: dict, dotted_key: str, value: object) -> None:
    keys = dotted_key.split(".")
    for k in keys[:-1]:
        d = d[k]
    d[keys[-1]] = value


def main() -> None:
    with BASE_PATH.open(encoding="utf-8") as f:
        base = yaml.safe_load(f)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = base.get("sample_name", "SAMPLE1")

    for stem, suffix, overrides, description in VARIANTS:
        run_name = f"recon_sweep_{suffix}"
        cfg = copy.deepcopy(base)
        cfg["vision"]["output"]["run_name"] = run_name
        cfg["vision"]["output"]["update_most_recent_symlink"] = False
        cfg["vision"]["rerun"]["enabled"] = False
        for k, v in overrides.items():
            set_nested(cfg, k, v)

        out_path = OUT_DIR / f"{stem}.yaml"
        header = (
            "# MASt3R / surface reconstruction sweep variant.\n"
            "# Run all:  bash scripts/run_recon_sweep.sh\n"
            f"# Output:   RESULTS/{sample}/{run_name}/\n"
            "#\n"
            f"# {description}\n"
        )
        with out_path.open("w", encoding="utf-8") as f:
            f.write(header)
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"Wrote {out_path.relative_to(REPO_ROOT)}")

    print(f"Generated {len(VARIANTS)} configs in {OUT_DIR.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
