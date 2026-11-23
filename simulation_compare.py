"""Deterministic *synthetic* traffic queues: adaptive versus fixed-time controller.

No claim that outputs estimate real video traffic or real waiting times.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from pathlib import Path
import csv
import json
import random
from typing import Mapping
from signal_controller import SignalController, DIRECTIONS


@dataclass
class FixedTimeController(SignalController):
    fixed_green: int = 30

    @classmethod
    def start(cls, demand: Mapping[str, int]) -> "FixedTimeController":
        return cls(remaining=30)

    def tick(self, demand: Mapping[str, int], seconds: int = 1) -> None:
        for _ in range(seconds):
            self.remaining -= 1
            if self.remaining > 0:
                continue
            if self.state == 'GREEN':
                self.completed_greens += 1
                self.state, self.remaining = 'YELLOW', self.yellow_seconds
            elif self.state == 'YELLOW':
                self.state, self.remaining = 'ALL_RED', self.all_red_seconds
            elif self.state == 'ALL_RED':
                self.active = DIRECTIONS[(DIRECTIONS.index(self.active) + 1) % len(DIRECTIONS)]
                self.state, self.remaining = 'GREEN', self.fixed_green
            else:
                raise RuntimeError('Invalid fixed signal state')
            self.lights()


def poisson(rng: random.Random, lam: float) -> int:
    """Generate Poisson arrivals for moderate user-provided per-second rates."""
    import math
    limit = math.exp(-lam)
    product, count = 1.0, 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


def compare(duration: int = 600, arrival_rates: Mapping[str, float] | None = None,
            seed: int = 42) -> dict:
    """Return synthetic simulation results for two policies given identical arrivals.

    Each GREEN approach serves up to 1 vehicle per simulated second. There
    are no turning movements, saturation effects, pedestrians, spillback or
    realistic clearance calibration. Average wait covers served vehicles only.
    """
    if duration < 60 or duration > 7200:
        raise ValueError('duration must be 60–7200 seconds')
    rates = dict(arrival_rates or {'North': .32, 'East': .22, 'South': .18, 'West': .25})
    if set(rates) != set(DIRECTIONS) or any(not (0 <= float(v) <= 3) for v in rates.values()):
        raise ValueError('Provide North, East, South, West rates between 0 and 3 vehicles/s')
    rng = random.Random(seed)
    policies = {
        'Adaptive (20/30/45)': SignalController.start({d: 0 for d in DIRECTIONS}),
        'Fixed (30s)': FixedTimeController.start({d: 0 for d in DIRECTIONS}),
    }
    queues = {p: {d: deque() for d in DIRECTIONS} for p in policies}
    observations = {p: {'served': 0, 'wait_seconds': 0, 'queued_sum': 0, 'peak_queue': 0,
                         'arrived': 0, 'timeline': []} for p in policies}

    for second in range(duration):
        arrivals = {d: poisson(rng, float(rates[d])) for d in DIRECTIONS}
        for name, controller in policies.items():
            obj = observations[name]
            for direction in DIRECTIONS:
                for _ in range(arrivals[direction]):
                    queues[name][direction].append(second)
                obj['arrived'] += arrivals[direction]
            greens = [d for d,s in controller.lights().items() if s == 'GREEN']
            assert len(greens) <= 1, 'Multiple simultaneous GREEN directions'
            if greens:
                active = greens[0]
                if queues[name][active]:
                    enter_time = queues[name][active].popleft()
                    obj['wait_seconds'] += second - enter_time
                    obj['served'] += 1
            remaining = sum(len(q) for q in queues[name].values())
            obj['queued_sum'] += remaining
            obj['peak_queue'] = max(obj['peak_queue'], remaining)
            obj['timeline'].append({
                'second': second, 'policy': name,
                'phase': controller.active, 'state': controller.state,
                'green_remaining': controller.remaining, 'queued': remaining,
                'served_cumulative': obj['served'],
                **{d.lower() + '_queued': len(queues[name][d]) for d in DIRECTIONS},
            })
            queue_demand = {d: len(q) for d, q in queues[name].items()}
            controller.tick(queue_demand)

    result = {'configuration': {
        'duration_seconds': duration, 'seed': seed, 'arrival_rates_vehicles_per_second': rates,
        'model': 'synthetic Poisson arrivals, one service per GREEN second',
        'disclaimer': 'Synthetic demonstration, not validated real-world performance; avg wait for served vehicles only',
    }, 'policies': {}}
    for name, obj in observations.items():
        result['policies'][name] = {
            'arrived': obj['arrived'], 'served': obj['served'],
            'end_queue': obj['arrived'] - obj['served'],
            'avg_wait_served_seconds': round(obj['wait_seconds'] / obj['served'], 2) if obj['served'] else None,
            'avg_queue_vehicles': round(obj['queued_sum'] / duration, 2),
            'peak_queue_vehicles': obj['peak_queue'],
            'timeline': obj['timeline'],
        }
    return result


def save_report(report: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / 'simulation_comparison.json'
    csv_path = folder / 'simulation_timeline.csv'
    json_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    all_rows = []
    for obj in report['policies'].values():
        all_rows.extend(obj['timeline'])
    if all_rows:
        with csv_path.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
            writer.writeheader()
            writer.writerows(all_rows)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Synthetic fixed-time versus adaptive traffic simulation')
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    report = compare(args.seconds, seed=args.seed)
    save_report(report, Path(__file__).resolve().parent / 'outputs' / 'simulation')
    print(json.dumps({k: {a:b for a,b in obj.items() if a != 'timeline'}
                      for k,obj in report['policies'].items()}, indent=2))
    print('Synthetic simulation written to outputs/simulation/')
