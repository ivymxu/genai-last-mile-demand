"""Explicit assumed intraday allocation; exact conservation of daily counts."""
import csv
import numpy as np
from .model import DISTRICTS

# Illustrative two-peak profile, shared by districts; not learned from daily data.
PROFILE = np.array([1,1,1,1,1,1,2,3,5,7,8,7,6,6,7,8,9,8,6,4,3,2,2,1], dtype=float)
PROFILE /= PROFILE.sum()
HEADER = ['date', 'hour', 'district', 'parcels', 'promotion', 'rain', 'holiday', 'scenario', 'sample_id']


def allocate_hourly(daily, seed=42):
    daily = np.asarray(daily)
    if daily.ndim != 3 or daily.shape[2] != 3 or not np.isfinite(daily).all() or (daily < 0).any() or (daily != np.floor(daily)).any():
        raise ValueError('expected nonnegative integer samples x days x 3 counts')
    rng = np.random.default_rng(seed)
    result = np.empty((*daily.shape[:2], 24, 3), dtype=np.int64)
    for s in range(daily.shape[0]):
        for d in range(daily.shape[1]):
            for k in range(3):
                result[s, d, :, k] = rng.multinomial(int(daily[s, d, k]), PROFILE)
    return result


def write_hourly(path, rows, daily, scenario, seed=42):
    hourly = allocate_hourly(daily, seed)
    if len(rows) != hourly.shape[1]:
        raise ValueError('calendar/count length mismatch')
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        for s in range(hourly.shape[0]):
            for d, row in enumerate(rows):
                for hour in range(24):
                    for k, district in enumerate(DISTRICTS):
                        writer.writerow([row['date'], hour, district, hourly[s,d,hour,k], row['promotion'], row['rain'], row['holiday'], scenario, s])
