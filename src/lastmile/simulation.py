"""SimPy parcel logistics, in hours and kilometres; all defaults are assumptions."""
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from collections import deque
import csv
import math
from pathlib import Path
import numpy as np
import simpy
from .model import DISTRICTS
from .hourly import allocate_hourly

DEPOTS = np.array([[0., 0.], [8., 0.], [8., 12.]])
SPEEDS = (18., 22., 28.)

@dataclass(frozen=True)
class Config:
    fleet: int = 48
    capacity: int = 24
    window_hours: float = 4.
    service_minutes: float = 3.
    dispatch_minutes: float = 15.
    speed_factor: float = 1.
    capacity_factor: float = 1.
    demand_factor: float = 1.
    seed: int = 42

    def __post_init__(self):
        for name in ('fleet', 'capacity', 'seed'):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool) or v < (0 if name == 'seed' else 1):
                raise ValueError(f'{name} must be an integer in range')
        for name in ('window_hours', 'service_minutes', 'dispatch_minutes', 'speed_factor', 'capacity_factor', 'demand_factor'):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f'{name} must be positive and finite')


def load_demand(source, sample_id=0):
    """Read one complete daily/hourly path. Reject mixed scenarios and missing cells."""
    if sample_id < 0:
        raise ValueError('sample_id must be nonnegative')
    with Path(source).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        required = {'date', 'district', 'parcels', 'scenario', 'sample_id'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'CSV needs {sorted(required)}')
        hourly = 'hour' in reader.fieldnames
        selected = []
        for row in reader:
            if int(row['sample_id']) != sample_id:
                continue
            day = date.fromisoformat(row['date'])
            hour = int(row['hour']) if hourly else 0
            count = int(row['parcels'])
            if row['district'] not in DISTRICTS or count < 0 or not 0 <= hour < 24:
                raise ValueError('invalid district/count/hour')
            selected.append((day, hour, DISTRICTS.index(row['district']), count, row['scenario']))
    if not selected:
        raise ValueError(f'no rows for sample_id={sample_id}')
    if len({r[4] for r in selected}) != 1:
        raise ValueError('select a CSV with one scenario')
    start, end = min(r[0] for r in selected), max(r[0] for r in selected)
    days = (end-start).days+1
    shape = (days, 24, 3) if hourly else (days, 3)
    counts = np.zeros(shape, dtype=np.int64)
    seen = set()
    for day, hour, district, count, _ in selected:
        key = ((day-start).days, hour, district) if hourly else ((day-start).days, district)
        if key in seen:
            raise ValueError('duplicate demand key')
        seen.add(key)
        counts[key] = count
    if len(seen) != counts.size:
        raise ValueError('incomplete demand path: every day/hour/district including zeros is required')
    if not hourly:
        counts = allocate_hourly(counts[None], seed=sample_id+7301)[0]
    return counts, {'start_date': start.isoformat(), 'days': days, 'sample_id': sample_id,
                    'source_scenario': selected[0][4], 'hourly_input': hourly}


def simulate(counts, config=Config(), trace=False):
    counts = np.asarray(counts)
    if counts.ndim != 3 or counts.shape[1:] != (24, 3) or not len(counts) or not np.isfinite(counts).all() or (counts < 0).any() or (counts != np.floor(counts)).any():
        raise ValueError('expected days x 24 x 3 nonnegative integer demand')
    counts = np.rint(counts * config.demand_factor).astype(int)
    # Separate streams: arrivals/coordinates remain paired across operational policies.
    rng = np.random.default_rng(config.seed)
    orders = []
    for d, h, k in np.ndindex(counts.shape):
        for arrival in np.sort(rng.uniform(d*24+h, d*24+h+1, counts[d,h,k])):
            xy = DEPOTS[k] + rng.uniform(-3, 3, 2)
            orders.append({'arrival': float(arrival), 'district': k, 'xy': xy})
    orders.sort(key=lambda o: o['arrival'])
    env = simpy.Environment()
    queues = [deque() for _ in DISTRICTS]
    vehicles = [{'id': i, 'xy': DEPOTS[i % 3].copy(), 'idle': True, 'busy': 0.} for i in range(config.fleet)]
    records = []
    arrived = 0
    cap = max(1, math.floor(config.capacity * config.capacity_factor))

    def arrivals():
        nonlocal arrived
        for oid, order in enumerate(orders):
            yield env.timeout(order['arrival']-env.now)
            order['id'] = oid
            queues[order['district']].append(order)
            arrived += 1

    def trip(vehicle, district, batch):
        start = env.now
        batch_size = len(batch)
        # Empty repositioning to district depot, then load and deliver nearest neighbour.
        yield env.timeout(float(np.linalg.norm(vehicle['xy']-DEPOTS[district])) / (SPEEDS[district]*config.speed_factor))
        xy = DEPOTS[district].copy()
        while batch:
            idx = min(range(len(batch)), key=lambda i: (float(np.linalg.norm(batch[i]['xy']-xy)), batch[i]['id']))
            order = batch.pop(idx)
            distance = float(np.linalg.norm(order['xy']-xy))
            yield env.timeout(distance/(SPEEDS[district]*config.speed_factor) + config.service_minutes/60)
            lead = env.now-order['arrival']
            records.append({'order_id': order['id'], 'district': DISTRICTS[district], 'arrival_hours': order['arrival'],
                            'completion_hours': env.now, 'delivery_hours': lead,
                            'delayed': lead > config.window_hours, 'vehicle_id': vehicle['id'],
                            'dispatch_hours': start, 'batch_size': batch_size})
            xy = order['xy']
        yield env.timeout(float(np.linalg.norm(xy-DEPOTS[district])) / (SPEEDS[district]*config.speed_factor))
        vehicle.update(xy=DEPOTS[district].copy(), idle=True, busy=vehicle['busy']+env.now-start)

    def dispatch():
        while arrived < len(orders) or any(queues) or any(not v['idle'] for v in vehicles):
            while any(queues) and any(v['idle'] for v in vehicles):
                district = min((k for k in range(3) if queues[k]), key=lambda k: queues[k][0]['arrival'])
                vehicle = min((v for v in vehicles if v['idle']), key=lambda v: (float(np.linalg.norm(v['xy']-DEPOTS[district])), v['id']))
                batch = [queues[district].popleft() for _ in range(min(cap, len(queues[district])))]
                vehicle['idle'] = False
                env.process(trip(vehicle, district, batch))
            yield env.timeout(config.dispatch_minutes/60)

    env.process(arrivals())
    env.process(dispatch())
    env.run()
    observation = max(len(counts)*24., env.now)
    n = len(records)
    result = {'parcels': n, 'delayed_parcels': sum(r['delayed'] for r in records),
              'delay_rate': sum(r['delayed'] for r in records)/n if n else 0.,
              'avg_delivery_hours': sum(r['delivery_hours'] for r in records)/n if n else 0.,
              'fleet_utilization': sum(v['busy'] for v in vehicles)/(config.fleet*observation),
              'observation_hours': observation, 'clearance_overtime_hours': max(0., env.now-len(counts)*24.),
              'fleet': config.fleet, 'effective_capacity': cap}
    if trace:
        result['orders'] = sorted(records, key=lambda r: r['order_id'])
    return result
