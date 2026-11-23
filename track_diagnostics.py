"""Summarize raw tracker observations without claiming true vehicle identity."""
from collections import defaultdict
from pathlib import Path
import csv
import json


def analyze_observations(csv_path: Path) -> dict:
    if not Path(csv_path).is_file():
        raise FileNotFoundError(csv_path)
    observed = defaultdict(lambda: {'classes':set(), 'frames':set(), 'min_frame':None,
                                    'max_frame':None, 'conf_sum':0.0, 'samples':0})
    with Path(csv_path).open('r', newline='', encoding='utf-8') as handle:
        for record in csv.DictReader(handle):
            key = str(record['track_id'])
            item = observed[key]
            frame = int(record['frame'])
            item['classes'].add(record['class_name'])
            item['frames'].add(frame)
            item['min_frame'] = frame if item['min_frame'] is None else min(frame, item['min_frame'])
            item['max_frame'] = frame if item['max_frame'] is None else max(frame, item['max_frame'])
            item['samples'] += 1
            item['conf_sum'] += float(record['confidence'])
    by_track = []
    for tid,info in observed.items():
        span = info['max_frame'] - info['min_frame'] + 1
        by_track.append({
            'track_id': tid, 'first_frame': info['min_frame'], 'last_frame': info['max_frame'],
            'observed_frames': len(info['frames']), 'frame_span': span,
            'visibility_fraction': round(len(info['frames'])/span,3),
            'distinct_classes': len(info['classes']),
            'classes': ' / '.join(sorted(info['classes'])),
            'average_confidence': round(info['conf_sum'] / info['samples'],3),
        })
    by_track.sort(key=lambda item: int(item['track_id']))
    return {'unique_track_ids': len(observed),
            'ids_with_class_changes': sum(t['distinct_classes']>1 for t in by_track),
            'tracks': by_track,
            'disclaimer': 'Class changes are observable; this cannot detect fragmented identities without ground-truth tracking annotations.'}


def export_diagnostics(data: dict, folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    (folder/'track_diagnostics_summary.json').write_text(json.dumps({k:v for k,v in data.items() if k!='tracks'}, indent=2), encoding='utf-8')
    with (folder/'track_diagnostics.csv').open('w', newline='', encoding='utf-8') as handle:
        keys = ['track_id','first_frame','last_frame','observed_frames','frame_span',
                'visibility_fraction','distinct_classes','classes','average_confidence']
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data['tracks'])
