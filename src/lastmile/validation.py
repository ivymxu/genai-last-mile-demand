"""Demand-only heldout diagnostics, with zero-demand-safe denominators."""
import numpy as np


def distribution_metrics(draws, observed):
    pred = draws.mean(axis=0)
    error = pred-observed
    lo, hi = np.quantile(draws, [.05, .95], axis=0)
    return {'mae': float(np.abs(error).mean()), 'rmse': float(np.sqrt((error**2).mean())),
            'wape': float(np.abs(error).sum()/max(float(observed.sum()), 1.)),
            'coverage_90': float(((observed >= lo) & (observed <= hi)).mean()),
            'mean_interval_width': float((hi-lo).mean()),
            'district_generated_mean': draws.mean(axis=(0,1)).tolist(),
            'district_heldout_mean': observed.mean(axis=0).tolist()}
