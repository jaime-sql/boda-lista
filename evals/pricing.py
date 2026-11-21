"""Optional cost estimates.

Gemma cost uses Modal's published GPU-only list price from
https://modal.com/pricing ($0.000222/s for L4, $0.000306/s for A10).
CPU, memory, and egress are not included. This is not an invoice.
Override the hourly GPU rate with EVALS_GPU_USD_PER_HOUR.
Rules and on-device Nano are zero. Cloud Gemini stays unknown unless a
future run records token counts and a rate.
"""

from __future__ import annotations

import os

# USD per GPU-second, GPU only. A10G is billed on Modal's A10 rate.
GPU_USD_PER_SECOND = {
    "T4": 0.000164,
    "L4": 0.000222,
    "A10": 0.000306,
    "A10G": 0.000306,
}


def gpu_usd_per_second(gpu: str | None) -> float | None:
    override = os.environ.get("EVALS_GPU_USD_PER_HOUR")
    if override:
        return float(override) / 3600.0
    if not gpu:
        return None
    return GPU_USD_PER_SECOND.get(gpu.upper())


def cost_per_thousand(backend: str, n: int, meta: dict | None) -> float | None:
    if n <= 0:
        return None
    if backend in {"rules", "nano"}:
        return 0.0
    if backend == "gemma" and meta and meta.get("estimated_gpu_seconds") is not None:
        rate = gpu_usd_per_second(meta.get("gpu") or "L4")
        if rate is None:
            return None
        return (float(meta["estimated_gpu_seconds"]) / n) * 1000.0 * rate
    return None
