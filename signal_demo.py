"""Offline four-direction demonstration and Unreal-readable JSON bridge example.

The waiting inputs are manual/simulated values, never inferred from the sample videos.
"""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from signal_controller import SignalController, DIRECTIONS

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'


def run_demo(demand: dict[str, int], seconds: int = 240):
    controller = SignalController.start(demand)
    OUT.mkdir(parents=True, exist_ok=True)
    timeline = OUT / 'signal_timeline.csv'
    bridge = OUT / 'signal_state.json'
    records = []
    for second in range(seconds):
        lights = controller.lights()
        assert sum(v == 'GREEN' for v in lights.values()) <= 1, 'Conflicting GREEN states!'
        records.append({'simulation_second': second, 'active': controller.active,
                        'phase': controller.state, 'remaining_seconds': controller.remaining,
                        **lights})
        controller.tick(demand)
    with timeline.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    state = {
        'source': 'simulation_manual_counts',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'simulation_seconds': seconds,
        'approach_waiting_counts': demand,
        'active_direction': controller.active,
        'signal_phase': controller.state,
        'remaining_seconds': controller.remaining,
        'lights': controller.lights(),
        'warning': 'Prototype simulation output; not certified for use with physical traffic signals.',
    }
    bridge.write_text(json.dumps(state, indent=2), encoding='utf-8')
    print('Generated:', timeline)
    print('Generated:', bridge)
    print('All directions received turns:', {d: any(row[d] == 'GREEN' for row in records) for d in DIRECTIONS})
    print('No conflicting GREEN directions across', seconds, 'simulated seconds.')


def main():
    p = argparse.ArgumentParser(description='Four-way single-green signal simulation')
    p.add_argument('--north', type=int, default=15)
    p.add_argument('--east', type=int, default=8)
    p.add_argument('--south', type=int, default=3)
    p.add_argument('--west', type=int, default=6)
    p.add_argument('--seconds', type=int, default=240)
    a = p.parse_args()
    if a.seconds < 1:
        p.error('Seconds must be positive')
    run_demo({"North":a.north,"East":a.east,"South":a.south,"West":a.west}, a.seconds)


if __name__ == '__main__':
    main()
